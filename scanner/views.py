from django.shortcuts import redirect, render

from users.decorators import session_required

from alerts.services import send_high_risk_alert

from .forms import ScanForm, QRUploadForm
from .ml.phishing_detector import scan_content
from .ml.hybrid_engine import scan_passive_content
from .models import ScanResult
from .qr_decoder import QRDecodeError, decode_qr_upload, extract_qr_content
from .report_generator import generate_scan_report
import base64

from .gmail_service import get_gmail_service

SCAN_CONFIG = {
    'url': {
        'title': 'URL Scan',
        'description': 'Analyze suspicious links for phishing indicators.',
        'placeholder': 'https://example.com/login',
    },
    'email': {
        'title': 'Email Scan',
        'description': 'Paste email sender, subject, and body to detect phishing language and links.',
        'placeholder': 'Paste the email body here',
    },
    'sms': {
        'title': 'SMS Scan',
        'description': 'Check text messages for urgent, suspicious, or deceptive patterns.',
        'placeholder': 'Paste the SMS message here',
    },
    'qr': {
        'title': 'QR Upload',
        'description': 'Upload a QR image, decode its content, and scan it for phishing risk.',
        'placeholder': '',
    },
}


TEMPLATE_MAP = {
    'url': 'scanner/url_scan.html',
    'email': 'scanner/email_scan.html',
    'sms': 'scanner/sms_scan.html',
    'qr': 'scanner/qr_scan.html',
}


@session_required
def scanner_home(request):
    return redirect('scanner:url_scan')

@session_required
def gmail_inbox(request):
    """
    Display the latest Gmail emails of the logged-in user.
    """

    service = get_gmail_service(request.user)

    results = service.users().messages().list(
    userId="me",
    labelIds=["SPAM"],
    maxResults=20,
).execute()

    messages = results.get("messages", [])

    emails = []

    for msg in messages:

        message = service.users().messages().get(
            userId="me",
            id=msg["id"],
            format="metadata",
            metadataHeaders=["Subject", "From", "Date"],
        ).execute()

        subject = ""
        sender = ""
        date = ""

        for header in message["payload"]["headers"]:

            if header["name"] == "Subject":
                subject = header["value"]

            elif header["name"] == "From":
                sender = header["value"]

            elif header["name"] == "Date":
                date = header["value"]

        emails.append(
            {
                "id": msg["id"],
                "subject": subject,
                "sender": sender,
                "date": date,
            }
        )

    return render(
        request,
        "scanner/gmail_inbox.html",
        {
            "emails": emails,
        },
    )

@session_required
def scan_gmail_email(request, message_id):

    service = get_gmail_service(request.user)

    message = service.users().messages().get(
        userId="me",
        id=message_id,
        format="full",
    ).execute()

    payload = message["payload"]

    sender = ""
    subject = ""

    for header in payload.get("headers", []):

        if header["name"] == "Subject":
            subject = header["value"]

        elif header["name"] == "From":
            sender = header["value"]

    body = ""

    if "parts" in payload:

        for part in payload["parts"]:

            if part.get("mimeType") == "text/plain":

                data = part["body"].get("data")

                if data:
                    body = base64.urlsafe_b64decode(
                        data
                    ).decode("utf-8", errors="ignore")

                    break

    else:

        data = payload["body"].get("data")

        if data:

            body = base64.urlsafe_b64decode(
                data
            ).decode("utf-8", errors="ignore")

    scan_input = f"""
From: {sender}

Subject: {subject}

{body}
"""

    result = scan_content(scan_input, "email")

    result["sender"] = sender
    result["subject"] = subject
    result["content"] = body
    result["scan_input"] = scan_input

    save_scan_result(request.user, result)

    return render(
        request,
        "scanner/gmail_result.html",
        {
            "result": result,
        },
    )


def save_scan_result(user, result):
    scan_result = ScanResult.objects.create(
        user=user,
        input=result.get('scan_input', result['content']),
        risk_score=result['risk_score'],
        classification=result['label'],
        explanation=result['explanation'],
        recommendation=result['recommendation'],
    )

    scan_result.report_file = generate_scan_report(scan_result)
    scan_result.save(update_fields=['report_file'])

    result['report_url'] = scan_result.report_file.url

    if scan_result.risk_score >= 70:
        send_high_risk_alert(scan_result)

    return scan_result


def _format_qr_details(qr_data):
    details = qr_data.get('extracted', {})
    lines = [f"QR Type: {qr_data.get('type', 'text').title()}"]
    for key, value in details.items():
        if isinstance(value, list):
            value = ', '.join(value) if value else 'None'
        elif isinstance(value, bool):
            value = 'Yes' if value else 'No'
        elif value == '':
            value = 'Not provided'
        lines.append(f"{key.replace('_', ' ').title()}: {value}")
    return '\n'.join(lines)


def scan_qr_content(decoded_content):
    qr_data = extract_qr_content(decoded_content)
    qr_type = qr_data['type']
    details = qr_data['extracted']

    if qr_type == 'url':
        result = scan_content(details['url'], 'url')
    elif qr_type == 'email':
        result = scan_content(details.get('scan_text', decoded_content), 'email')
    elif qr_type == 'sms':
        result = scan_content(details.get('scan_text', decoded_content), 'sms')
    elif qr_type == 'text':
        result = scan_content(details.get('text', decoded_content), 'text')
    elif qr_type == 'wifi':
        reasons = [
            f"Wi-Fi network decoded. SSID: {details.get('ssid') or 'Not provided'}.",
            f"Encryption type: {details.get('encryption') or 'Unknown'}.",
            f"Password protected: {'Yes' if details.get('has_password') else 'No'}.",
            f"Hidden network: {'Yes' if details.get('hidden') else 'No'}.",
        ]
        risk = 20
        if details.get('encryption') in {'NOPASS', 'WEP'}:
            risk = 45 if details.get('encryption') == 'NOPASS' else 35
            reasons.append('Open or weak Wi-Fi encryption can expose traffic on untrusted networks.')
        result = scan_passive_content(_format_qr_details(qr_data), 'wifi', reasons, risk, 78)
    elif qr_type == 'contact':
        reasons = [
            f"Contact QR decoded for {details.get('name') or 'an unnamed contact'}.",
            "Embedded emails and websites were extracted for validation.",
        ]
        nested_scores = []
        for url in details.get('urls', [])[:2]:
            nested = scan_content(url, 'url')
            nested_scores.append(nested['risk_score'])
            reasons.extend([f"Website check: {reason}" for reason in nested['explanation'][:3]])
        for email in details.get('emails', [])[:2]:
            nested = scan_content(f"From: {email}\n\nContact card email validation.", 'email')
            nested_scores.append(nested['risk_score'])
        risk = max(nested_scores) if nested_scores else 12
        result = scan_passive_content(_format_qr_details(qr_data), 'contact', reasons, risk, 74)
    elif qr_type == 'payment':
        reasons = [
            f"Payment QR decoded. Provider: {details.get('provider') or 'Unknown'}.",
            f"Merchant: {details.get('merchant') or 'Not provided'}.",
            f"Amount: {details.get('amount') or 'Not provided'} {details.get('currency') or ''}".strip(),
            "Payment QR codes require human verification of merchant identity and amount before payment.",
        ]
        risk = 25
        if not details.get('merchant'):
            risk += 10
            reasons.append('Merchant identity is missing or could not be verified from the QR content.')
        result = scan_passive_content(_format_qr_details(qr_data), 'payment', reasons, risk, 68)
    elif qr_type == 'product':
        if details.get('url'):
            result = scan_content(details['url'], 'url')
            result['explanation'].insert(0, 'Product QR contains a URL, so the complete URL scanner was used.')
        else:
            reasons = [
                f"Product identifier decoded: {details.get('product_id') or 'Not provided'}.",
                "No URL was present, so there is no web destination to classify.",
                "Validate the product ID against the official manufacturer, retailer, or inventory system.",
            ]
            result = scan_passive_content(_format_qr_details(qr_data), 'product', reasons, 10, 72)
    else:
        result = scan_content(decoded_content, 'text')

    result['scan_type'] = f"QR {qr_type.title()}"
    result['qr_type'] = qr_type
    result['qr_details'] = details
    result['content'] = decoded_content
    result['scan_input'] = _format_qr_details(qr_data)
    return result


@session_required
def scan_view(request, scan_type):
    config = SCAN_CONFIG.get(scan_type)

    if config is None:
        return redirect('scanner:url_scan')

    result = None
    form = ScanForm(request.POST or None)

    if scan_type == 'email':
        form.fields['email_sender'].widget.attrs['placeholder'] = 'sender@example.com'
        form.fields['email_subject'].widget.attrs['placeholder'] = 'Enter the email subject'
        form.fields['content'].widget.attrs['placeholder'] = config['placeholder']

    elif scan_type == 'sms':
        form.fields['phone_number'].widget.attrs['placeholder'] = '+97798XXXXXXXX'
        form.fields['content'].widget.attrs['placeholder'] = config['placeholder']

    else:
        form.fields['content'].widget.attrs['placeholder'] = config['placeholder']

    if request.method == 'POST' and form.is_valid():

        if scan_type == 'email':
            sender = form.cleaned_data.get('email_sender', '').strip()
            subject = form.cleaned_data.get('email_subject', '').strip()
            body = form.cleaned_data['content'].strip()

            scan_input_parts = []

            if sender:
                scan_input_parts.append(f'From: {sender}')

            if subject:
                scan_input_parts.append(f'Subject: {subject}')

            scan_input_parts.append('')
            scan_input_parts.append(body)

            scan_input = '\n'.join(scan_input_parts).strip()

            result = scan_content(scan_input, scan_type)
            result['sender'] = sender
            result['subject'] = subject
            result['content'] = body
            result['scan_input'] = scan_input

        elif scan_type == 'sms':
            phone_number = form.cleaned_data.get('phone_number', '').strip()
            message = form.cleaned_data.get('content', '').strip()

            scan_input = f"""
Phone Number: {phone_number}

Message:
{message}
""".strip()

            result = scan_content(scan_input, 'sms')
            result['phone_number'] = phone_number
            result['content'] = message
            result['scan_input'] = scan_input

        else:
            content = form.cleaned_data['content'].strip()

            result = scan_content(content, scan_type)
            result['content'] = content
            result['scan_input'] = content

        save_scan_result(request.user, result)

    return render(
        request,
        TEMPLATE_MAP[scan_type],
        {
            "form": form,
            "result": result,
            "scan_type": scan_type,
            "config": config,
            "scan_types": SCAN_CONFIG,
        },
    )


@session_required
def qr_upload_view(request):

    result = None
    decoded_content = None
    decode_error = None

    form = QRUploadForm(request.POST or None, request.FILES or None)

    form = QRUploadForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == "POST" and form.is_valid():

        try:

            decoded_content = decode_qr_upload(
                form.cleaned_data["qr_image"]
            )

            result = scan_qr_content(decoded_content)

            save_scan_result(request.user, result)

        except QRDecodeError as exc:

            decode_error = str(exc)

    return render(
        request,
        'scanner/qr_scan.html',
        {
            "form": form,
            "result": result,
            "decoded_content": decoded_content,
            "decode_error": decode_error,
            "scan_type": "qr",
            "config": SCAN_CONFIG["qr"],
            "scan_types": SCAN_CONFIG,
        },
    )
