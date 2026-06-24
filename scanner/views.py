from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from alerts.services import send_high_risk_alert

from .forms import ScanForm
from .ml.phishing_detector import scan_content
from .models import ScanResult
from .qr_decoder import QRDecodeError, decode_qr_upload, infer_scan_type
from .report_generator import generate_scan_report


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
    if scan_type == 'email':
        form.fields['email_sender'].widget.attrs['placeholder'] = 'sender@example.com'
        form.fields['email_subject'].widget.attrs['placeholder'] = 'Enter the email subject'
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
        else:
            result = scan_content(form.cleaned_data['content'], scan_type)
        save_scan_result(request.user, result)

    return render(
        request,
        'scanner/scan.html',
        {
            'form': form,
            'result': result,
            'scan_type': scan_type,
            'config': config,
            'scan_types': SCAN_CONFIG,
        },
    )


@login_required
def qr_upload_view(request):
    from .forms import QRUploadForm

    result = None
    decoded_content = None
    decode_error = None
    form = QRUploadForm(request.POST or None, request.FILES or None)

    if request.method == 'POST' and form.is_valid():
        try:
            decoded_content = decode_qr_upload(form.cleaned_data['qr_image'])
            inferred_type = infer_scan_type(decoded_content)
            result = scan_content(decoded_content, inferred_type)
            result['scan_type'] = f'QR {result["scan_type"]}'
            save_scan_result(request.user, result)
        except QRDecodeError as exc:
            decode_error = str(exc)

    return render(
        request,
        'scanner/qr_upload.html',
        {
            'form': form,
            'result': result,
            'decoded_content': decoded_content,
            'decode_error': decode_error,
            'scan_type': 'qr',
            'config': SCAN_CONFIG['qr'],
            'scan_types': SCAN_CONFIG,
        },
    )
