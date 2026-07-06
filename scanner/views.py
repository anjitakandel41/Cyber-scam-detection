from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from alerts.services import send_high_risk_alert

from .forms import ScanForm, QRUploadForm
from .ml.phishing_detector import scan_content
from .models import ScanResult
from .qr_decoder import QRDecodeError, decode_qr_upload, infer_scan_type
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


@login_required
def scanner_home(request):
    return redirect('scanner:url_scan')

@login_required
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

@login_required
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


@login_required
def scan_view(request, scan_type):

    config = SCAN_CONFIG[scan_type]
    result = None

    form = ScanForm(request.POST or None)

    # ---------------- Placeholder ----------------

    if scan_type == 'url':
        form.fields['content'].widget.attrs['placeholder'] = \
            'https://example.com/login'

    elif scan_type == 'email':
        form.fields['email_sender'].widget.attrs['placeholder'] = \
            'sender@example.com'

        form.fields['email_subject'].widget.attrs['placeholder'] = \
            'Enter the email subject'

        form.fields['content'].widget.attrs['placeholder'] = \
            'Paste the email body here'

    elif scan_type == 'sms':
        form.fields['phone_number'].widget.attrs['placeholder'] = \
            '+977 98XXXXXXXX'

        form.fields['content'].widget.attrs['placeholder'] = \
            'Paste the SMS message here'

    # ---------------- Submit ----------------

    if request.method == "POST" and form.is_valid():

        # URL
        if scan_type == "url":

            url = form.cleaned_data["content"].strip()

            result = scan_content(url, "url")

            result["content"] = url
            result["scan_input"] = url

        # EMAIL
        elif scan_type == "email":

            sender = form.cleaned_data.get("email_sender", "").strip()
            subject = form.cleaned_data.get("email_subject", "").strip()
            body = form.cleaned_data.get("content", "").strip()

            scan_input = f"""
From: {sender}
Subject: {subject}

{body}
""".strip()

            result = scan_content(scan_input, "email")

            result["sender"] = sender
            result["subject"] = subject
            result["content"] = body
            result["scan_input"] = scan_input

        # SMS
        elif scan_type == "sms":

            phone_number = form.cleaned_data.get("phone_number", "").strip()
            message = form.cleaned_data.get("content", "").strip()

            scan_input = f"""
Phone Number: {phone_number}

Message:
{message}
""".strip()

            result = scan_content(scan_input, "sms")

            result["phone_number"] = phone_number
            result["content"] = message
            result["scan_input"] = scan_input

        save_scan_result(request.user, result)

    return render(
        request,
        "scanner/scan.html",
        {
            "form": form,
            "result": result,
            "scan_type": scan_type,
            "config": config,
            "scan_types": SCAN_CONFIG,
        },
    )


@login_required
def qr_upload_view(request):

    result = None
    decoded_content = None
    decode_error = None

    form = QRUploadForm(
        request.POST or None,
        request.FILES or None,
    )

    if request.method == "POST" and form.is_valid():

        try:

            decoded_content = decode_qr_upload(
                form.cleaned_data["qr_image"]
            )

            inferred_type = infer_scan_type(decoded_content)

            result = scan_content(
                decoded_content,
                inferred_type,
            )

            result["scan_type"] = f'QR {result["scan_type"]}'

            save_scan_result(request.user, result)

        except QRDecodeError as exc:

            decode_error = str(exc)

    return render(
        request,
        "scanner/qr_upload.html",
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