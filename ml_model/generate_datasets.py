import csv
import random
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
random.seed(42)

SAFE_DOMAINS = [
    "university.edu.np", "hospital.org.np", "library.example", "docs.djangoproject.com",
    "openai.com", "mozilla.org", "wikipedia.org", "github.com", "coursera.org",
    "khanacademy.org", "nepalbank.com.np", "nrb.org.np", "ird.gov.np",
    "company-intranet.example", "store-receipts.example", "city-services.example",
]
PHISHING_DOMAINS = [
    "secure-login-check.test", "account-verify-now.test", "wallet-kyc-alert.test",
    "bank-support-update.test", "np-prize-claim.test", "delivery-fee-pay.test",
    "192.168.45.12", "10.8.4.22", "paypal-security.example.ru",
    "google-login.example.net", "esewa-bonus-claim.test", "khalti-refund.test",
]
SAFE_SUBJECTS = [
    "Monthly statement is available", "Meeting notes", "Appointment reminder",
    "Receipt for your recent purchase", "Course update", "Password changed successfully",
    "Project status summary", "Library book reminder",
]
PHISHING_SUBJECTS = [
    "Urgent account verification required", "Your wallet is blocked",
    "Final warning: confirm your password", "Prize claim pending",
    "Refund failed: update card now", "Unusual login detected",
]
SAFE_MESSAGES = [
    "Your appointment is confirmed for Friday at 10:00 AM.",
    "The invoice has been received and marked paid.",
    "Class starts tomorrow. Please bring your notebook.",
    "Your delivery is scheduled for tomorrow afternoon.",
    "Your OTP is 123456. Do not share it with anyone.",
    "Thank you for your payment. No further action is required.",
]
SCAM_MESSAGES = [
    "URGENT: your bank account is blocked. Verify login now",
    "Congratulations, you won a cash prize. Claim reward immediately",
    "Customs fee pending. Pay now to release your parcel",
    "KYC expired. Confirm wallet PIN and OTP to continue",
    "Security alert. Update password within 24 hours",
    "Refund failed. Enter card details to receive money",
]


def _write(path, fieldnames, rows):
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def generate_url_rows():
    rows = []
    for i in range(1000):
        domain = random.choice(SAFE_DOMAINS)
        path = random.choice(["help", "profile", "docs", "receipt", "notice", "course", "status"])
        url = f"https://{domain}/{path}/{1000 + i}"
        rows.append({"content": url, "url": url, "category": "safe", "label": 0})
    for i in range(1000):
        domain = random.choice(PHISHING_DOMAINS)
        keyword = random.choice(["verify-account", "login-update", "claim-prize", "wallet-kyc", "pay-fee"])
        scheme = random.choice(["http", "https"])
        url = f"{scheme}://{domain}/{keyword}/{2000 + i}?session={random.randint(10000, 99999)}"
        if i % 7 == 0:
            url = f"http://bit.ly/{keyword}{i}"
        rows.append({"content": url, "url": url, "category": "phishing", "label": 1})
    random.shuffle(rows)
    return rows


def generate_email_rows():
    rows = []
    for i in range(1000):
        sender_domain = random.choice(SAFE_DOMAINS)
        sender = f"{random.choice(['support', 'billing', 'noreply', 'admin'])}@{sender_domain}"
        subject = random.choice(SAFE_SUBJECTS)
        message = random.choice(SAFE_MESSAGES)
        link = f"https://{sender_domain}/{random.choice(['help', 'receipt', 'profile'])}/{3000 + i}"
        content = f"From: {sender} Subject: {subject} {message} Link: {link}"
        rows.append({"sender": sender, "subject": subject, "message": message, "content": content, "label": 0})
    for i in range(1000):
        sender_domain = random.choice(PHISHING_DOMAINS)
        sender = f"{random.choice(['security', 'reward', 'support', 'verify'])}@{sender_domain}"
        subject = random.choice(PHISHING_SUBJECTS)
        message = random.choice(SCAM_MESSAGES)
        link = f"http://{sender_domain}/{random.choice(['verify', 'login', 'claim'])}/{4000 + i}"
        content = f"From: {sender} Subject: {subject} {message}. Click {link} and submit password OTP PIN card details."
        rows.append({"sender": sender, "subject": subject, "message": message, "content": content, "label": 1})
    random.shuffle(rows)
    return rows


def generate_sms_rows():
    rows = []
    for i in range(1000):
        phone = f"+977-98{random.randint(10000000, 99999999)}"
        message = random.choice(SAFE_MESSAGES)
        content = f"From: {phone} Message: {message}"
        rows.append({"phone_number": phone, "message": message, "content": content, "label": 0})
    for i in range(1000):
        phone = random.choice(["+977-9800000000", "BANKALERT", "WALLET", "DELIVERY"])
        link = f"http://{random.choice(PHISHING_DOMAINS)}/verify/{5000 + i}"
        message = f"{random.choice(SCAM_MESSAGES)}: {link}"
        content = f"From: {phone} Message: {message}"
        rows.append({"phone_number": phone, "message": message, "content": content, "label": 1})
    random.shuffle(rows)
    return rows


def generate_qr_rows(url_rows, email_rows, sms_rows):
    rows = []
    for row in url_rows[:400]:
        rows.append({"content": row["content"], "qr_type": "url", "label": row["label"]})
    for row in email_rows[:300]:
        rows.append({"content": f"mailto:{row['sender']}?subject={row['subject']}&body={row['message']}", "qr_type": "email", "label": row["label"]})
    for row in sms_rows[:300]:
        rows.append({"content": f"SMSTO:{row['phone_number']}:{row['message']}", "qr_type": "sms", "label": row["label"]})
    for i in range(120):
        rows.append({"content": f"WIFI:T:WPA;S:CampusGuest{i};P:StrongPass{i}2026;;", "qr_type": "wifi", "label": 0})
    for i in range(120):
        rows.append({"content": f"BEGIN:VCARD\nFN:Student {i}\nEMAIL:student{i}@university.edu.np\nURL:https://university.edu.np/profile/{i}\nEND:VCARD", "qr_type": "contact", "label": 0})
    random.shuffle(rows)
    return rows


def main():
    url_rows = generate_url_rows()
    email_rows = generate_email_rows()
    sms_rows = generate_sms_rows()
    qr_rows = generate_qr_rows(url_rows, email_rows, sms_rows)
    _write(BASE_DIR / "url_dataset.csv", ["content", "url", "category", "label"], url_rows)
    _write(BASE_DIR / "email_dataset.csv", ["sender", "subject", "message", "content", "label"], email_rows)
    _write(BASE_DIR / "sms_dataset.csv", ["phone_number", "message", "content", "label"], sms_rows)
    _write(BASE_DIR / "qr_dataset.csv", ["content", "qr_type", "label"], qr_rows)


if __name__ == "__main__":
    main()
