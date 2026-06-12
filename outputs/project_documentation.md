# Phishing Detection and Awareness System Documentation

## 1. Project Overview

This Django project is a role-based phishing detection and awareness platform. It supports user registration, email verification, login, phishing scans, QR decoding, PDF report generation, high-risk email alerts, cybersecurity quizzes, and a rule-based phishing awareness chatbot.

The system has two user experiences:

- Admin: manages users, quiz questions, scan results, alerts, and dashboard analytics.
- User: scans URLs/emails/SMS/QR codes, receives risk results, downloads PDF reports, attempts quizzes, and asks the chatbot for phishing awareness guidance.

## 2. Login and Roles

There is one login page, not two separate login forms.

After login, the system checks the logged-in user's role:

- Admin users are redirected to `/dashboard/admin/`
- Normal users are redirected to `/dashboard/user/`

Admin detection uses:

- `role = admin`
- or Django `is_staff`
- or Django `is_superuser`

Normal users are assigned `role = user` by default during registration.

## 3. Real Email and Gmail SMTP

The project is configured to use Gmail SMTP through environment variables.

Required environment variables:

```powershell
$env:EMAIL_HOST_USER="yourgmail@gmail.com"
$env:EMAIL_HOST_PASSWORD="your_google_app_password"
$env:DEFAULT_FROM_EMAIL="yourgmail@gmail.com"
```

Important: Gmail requires a Google App Password. A normal Gmail password will not work.

Email is used in two places:

- Email verification after registration.
- High-risk phishing alerts when `risk_score >= 70`.

If Gmail credentials are configured correctly, the system sends real emails to the user's registered email address.

## 4. Real-Time Notification Flow

When a scan result has `risk_score >= 70`, the system automatically:

1. Saves the scan result.
2. Generates a PDF report.
3. Attaches the PDF report to an email.
4. Sends the email to the user.
5. Stores an alert record in the database.

This is real-time in the normal Django request flow, meaning it happens immediately after the scan is submitted. It is not WebSocket/live push notification. For production, Celery or Django-Q could be added to send email asynchronously.

## 5. Phishing Detection Module

The phishing detector supports:

- URL scan
- Email scan
- SMS scan
- QR upload scan

The model uses `RandomForestClassifier` from scikit-learn and is saved with joblib at:

```text
scanner/ml/phishing_model.joblib
```

The detector extracts features such as:

- suspicious keywords
- shortened URLs
- HTTP links
- IP-address links
- urgent language
- prize/reward language
- sensitive terms such as password, OTP, PIN, card, bank
- URL/domain patterns

Each scan returns:

- risk score
- classification
- explanation
- recommendation

## 6. Does It Detect Real Data?

Yes, the system can scan real user-entered URLs, email text, SMS text, and uploaded QR images.

However, the current machine learning model is trained on a small built-in sample dataset. That means it is suitable for a college/project prototype, demonstration, and learning workflow, but it is not production-grade phishing intelligence.

To make it stronger, train it with a larger real-world dataset containing verified phishing and legitimate samples.

## 7. QR Upload Flow

The QR scanner uses:

- OpenCV for image reading and QR fallback decoding.
- pyzbar when native zbar dependencies are available.

Flow:

1. User uploads QR image.
2. System decodes QR content.
3. System infers whether decoded content is URL, email-like text, or SMS-like text.
4. Decoded content is sent to the phishing detector.
5. Result is saved and shown to the user.

## 8. Scan Result Storage

Every successful scan is stored in `ScanResult`.

Stored fields:

- user
- input
- risk score
- classification
- explanation
- recommendation
- PDF report file
- timestamp

This allows dashboards, history, reporting, and alerts to use real scan data.

## 9. PDF Report Generation

The project uses ReportLab to generate PDF reports.

Reports are saved in:

```text
media/reports/
```

Each PDF includes:

- user info
- scanned input
- scan timestamp
- risk score
- classification
- explanation
- recommendation

For high-risk scans, the PDF is attached to the alert email.

## 10. Alert System

The alert system stores high-risk scan notifications.

Alert records include:

- user
- scan result
- subject
- message
- status
- error message if email fails
- sent timestamp

If email sending fails, the alert is still stored with `failed` status and the error message.

## 11. Cybersecurity Quiz

Admins manage quiz questions from Django admin.

Admin can:

- add questions
- edit questions
- delete questions
- set correct answer
- add explanation
- activate/deactivate questions

Users can:

- attempt quiz
- submit answers
- view score
- review selected and correct answers

Quiz attempts are stored in the database for dashboard analytics.

## 12. Phishing Awareness Chatbot

The chatbot is rule-based, not AI/API-based.

It responds to phishing awareness topics such as:

- phishing definition
- suspicious emails
- suspicious URLs
- QR code safety
- SMS phishing
- OTP/password safety
- reporting suspicious messages
- high-risk scan meaning

Each chat message and response is stored per user.

## 13. Dashboard

The dashboard now uses real project data.

Admin dashboard shows:

- total users
- total scans
- high-risk scans
- alerts sent
- quiz attempts
- chatbot messages
- pending email verification
- admin count
- user registration chart
- scan activity chart
- role distribution chart
- risk distribution chart

User dashboard shows:

- scans completed
- high-risk scans
- reports created
- quiz progress
- alerts
- chatbot messages
- weekly scan activity
- module usage
- risk distribution
- recent scans
- recent alerts
- quick action buttons

## 14. Recommended Production Improvements

For a real deployment, add:

- stronger phishing dataset
- scheduled model retraining
- Celery for background email sending
- production database such as PostgreSQL
- environment-based secret key
- secure HTTPS deployment
- rate limiting for scans and login
- audit logs
- user scan history page
- admin alert management page
- real-time WebSocket notifications if instant in-browser alerts are required

## 15. How the Full Flow Works

1. User registers with email.
2. User verifies email.
3. User logs in.
4. Role redirects user:
   - admin to admin dashboard
   - user to user dashboard
5. User scans URL/email/SMS/QR.
6. Detector generates score, classification, explanation, and recommendation.
7. Scan result is saved.
8. PDF report is generated.
9. If score is 70 or higher:
   - email alert is sent
   - PDF is attached
   - alert is stored
10. User can attempt quiz.
11. User can ask chatbot for awareness guidance.
12. Dashboards show analytics from stored data.
