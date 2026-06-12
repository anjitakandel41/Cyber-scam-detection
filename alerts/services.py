from pathlib import Path

from django.conf import settings
from django.core.mail import EmailMessage

from .models import Alert


def send_high_risk_alert(scan_result):
    user = scan_result.user
    subject = f'High-risk phishing scan detected ({scan_result.risk_score}%)'
    message = (
        f'Hello {user.get_username()},\n\n'
        'A high-risk phishing scan was detected on your account.\n\n'
        f'Risk score: {scan_result.risk_score}%\n'
        f'Classification: {scan_result.classification}\n\n'
        f'Recommendation:\n{scan_result.recommendation}\n\n'
        'The detailed PDF report is attached.'
    )

    alert = Alert.objects.create(
        user=user,
        scan_result=scan_result,
        subject=subject,
        message=message,
        status=Alert.Status.SENT,
    )

    if not user.email:
        alert.status = Alert.Status.FAILED
        alert.error_message = 'User does not have an email address.'
        alert.save(update_fields=['status', 'error_message'])
        return alert

    try:
        email = EmailMessage(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])
        if scan_result.report_file:
            report_path = Path(settings.MEDIA_ROOT) / scan_result.report_file.name
            if report_path.exists():
                email.attach_file(report_path)
        email.send(fail_silently=False)
    except Exception as exc:
        alert.status = Alert.Status.FAILED
        alert.error_message = str(exc)
        alert.save(update_fields=['status', 'error_message'])

    return alert
