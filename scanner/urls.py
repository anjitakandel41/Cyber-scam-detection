from django.urls import path

from .views import (
    qr_upload_view,
    scan_view,
    scanner_home,
    gmail_inbox,
    scan_gmail_email,
)

app_name = "scanner"

urlpatterns = [
    path("", scanner_home, name="scanner_home"),
    path("", scanner_home, name="home"),

    # Existing Scanner
    path("url/", scan_view, {"scan_type": "url"}, name="url_scan"),
    path("email/", scan_view, {"scan_type": "email"}, name="email_scan"),
    path("sms/", scan_view, {"scan_type": "sms"}, name="sms_scan"),
    path("qr/", qr_upload_view, name="qr_upload"),

    # Gmail Scanner
    path("gmail/", gmail_inbox, name="gmail_inbox"),
    path(
        "gmail/<str:message_id>/",
        scan_gmail_email,
        name="scan_gmail_email",
    ),
]