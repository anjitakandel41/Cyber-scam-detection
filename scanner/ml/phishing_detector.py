import re
from .threat_intelligence import check_virustotal
from pathlib import Path
from urllib.parse import urlparse

import joblib
import numpy as np
from django.conf import settings
from sklearn.ensemble import RandomForestClassifier
from .google_safe_browsing import check_google_safe_browsing
from .whois_lookup import check_domain_age
from ml_model.train import load_datasets


MODEL_PATH = Path(settings.BASE_DIR) / 'ml_model' / 'model.pkl'
SUSPICIOUS_WORDS = (
    'verify',
    'urgent',
    'login',
    'password',
    'account',
    'suspended',
    'winner',
    'prize',
    'free',
    'click',
    'bank',
    'security',
    'limited',
    'confirm',
    'update',
)
SHORTENERS = ('bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly')


def _count_suspicious_words(text):
    lowered = text.lower()
    return sum(1 for word in SUSPICIOUS_WORDS if word in lowered)


def _has_ip_address(text):
    return int(bool(re.search(r'(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)', text)))


def _count_urls(text):
    return len(re.findall(r'https?://|www\.', text.lower()))


def _has_money_or_reward(text):
    return int(bool(re.search(r'(\$|rs\.?|usd|gift|bonus|reward|prize|winner)', text.lower())))


def _has_urgency(text):
    return int(bool(re.search(r'(urgent|immediately|now|limited|expire|suspended|blocked)', text.lower())))


def extract_features(content, scan_type):
    text = content.strip()
    lowered = text.lower()
    parsed = urlparse(text if '://' in text else f'//{text}')
    domain = parsed.netloc.lower()

    return np.array([[
        len(text),
        _count_suspicious_words(text),
        _count_urls(text),
        int('@' in text),
        int('-' in domain),
        int(any(shortener in domain for shortener in SHORTENERS)),
        _has_ip_address(text),
        int(lowered.startswith('http://')),
        int(scan_type == 'url'),
        int(scan_type == 'email'),
        int(scan_type == 'sms'),
        _has_money_or_reward(text),
        _has_urgency(text),
        int(bool(re.search(r'(password|otp|pin|ssn|card|bank)', lowered))),
        int(len(domain.split('.')) > 3 if domain else False),
    ]])


def training_samples():
    rows = [
        ('https://example.com/account/profile', 'url', 0),
        ('https://openai.com/security', 'url', 0),
        ('https://docs.djangoproject.com/en/stable/', 'url', 0),
        ('https://accounts.google.com/signin', 'url', 0),
        ('https://mybank.example.com/dashboard', 'url', 0),
        ('http://192.168.1.44/verify-account', 'url', 1),
        ('http://secure-login-bank.example.verify-now.ru/password', 'url', 1),
        ('https://bit.ly/free-prize-login', 'url', 1),
        ('http://paypal-security-update.example.com@evil.test/login', 'url', 1),
        ('https://account-suspended-bank-login.example.net', 'url', 1),
        ('Your weekly report is attached for review.', 'email', 0),
        ('Meeting moved to 3 PM. Please confirm availability.', 'email', 0),
        ('Welcome to your dashboard. Your account is ready.', 'email', 0),
        ('Invoice received from verified vendor.', 'email', 0),
        ('Urgent: verify your password now or your account will be suspended.', 'email', 1),
        ('Winner! Click this link to claim your prize and enter bank details.', 'email', 1),
        ('Security alert: update login at http://192.168.0.8 immediately.', 'email', 1),
        ('Your mailbox is full. Confirm your password to continue.', 'email', 1),
        ('Your delivery arrives tomorrow between 10 and 12.', 'sms', 0),
        ('Your appointment is confirmed for Friday.', 'sms', 0),
        ('Your OTP is 123456. Do not share it with anyone.', 'sms', 0),
        ('URGENT: Your bank account is blocked. Click http://bit.ly/verify-bank', 'sms', 1),
        ('You won a free gift card. Claim now at http://tinyurl.com/prize', 'sms', 1),
        ('Confirm your card PIN immediately or service expires today.', 'sms', 1),
    ]
    return rows


def train_and_save_model():
    try:
        samples = load_datasets()
    except FileNotFoundError:
        samples = training_samples()

    x_train = np.vstack([extract_features(content, scan_type) for content, scan_type, _ in samples])
    y_train = np.array([label for _, _, label in samples])
    model = RandomForestClassifier(n_estimators=160, max_depth=8, random_state=42)
    model.fit(x_train, y_train)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({'model': model}, MODEL_PATH)
    return MODEL_PATH


def load_model():
    if not MODEL_PATH.exists():
        train_and_save_model()
    bundle = joblib.load(MODEL_PATH)
    return bundle['model']


def explain(content, scan_type, risk_score):
    text = content.strip()
    lowered = text.lower()
    parsed = urlparse(text if '://' in text else f'//{text}')
    domain = parsed.netloc.lower()
    reasons = []

    suspicious_count = _count_suspicious_words(text)
    if suspicious_count:
        reasons.append(f'Contains {suspicious_count} suspicious phishing keyword(s).')
    if _has_urgency(text):
        reasons.append('Uses urgent or threatening language.')
    if _has_money_or_reward(text):
        reasons.append('Mentions money, prizes, rewards, or gifts.')
    if _count_urls(text) > 0:
        reasons.append('Includes one or more links.')
    if any(shortener in domain for shortener in SHORTENERS):
        reasons.append('Uses a shortened URL that can hide the destination.')
    if _has_ip_address(text):
        reasons.append('Contains an IP address instead of a normal domain.')
    if '@' in text and scan_type == 'url':
        reasons.append('URL contains @, which can disguise the real destination.')
    if domain and '-' in domain:
        reasons.append('Domain contains hyphens, a common impersonation signal.')
    if lowered.startswith('http://'):
        reasons.append('Uses insecure HTTP instead of HTTPS.')
    if re.search(r'(password|otp|pin|ssn|card|bank)', lowered):
        reasons.append('Requests or references sensitive account information.')

    if not reasons:
        if risk_score < 35:
            reasons.append('No strong phishing indicators were detected.')
        else:
            reasons.append('The model found a risky pattern, but no single rule dominated.')

    return reasons


def scan_content(content, scan_type):
    model = load_model()
    features = extract_features(content, scan_type)

    # 1. Machine Learning prediction
    phishing_probability = model.predict_proba(features)[0][1]
    ml_score = round(phishing_probability * 100)

    # 2. Rule-based explanation
    explanations = explain(content, scan_type, ml_score)

    # 3. VirusTotal only for URL scan
    if scan_type == "url":
        vt_result = check_virustotal(content)
        vt_score = vt_result.get("score", 0)
        explanations.append(vt_result.get("message", "VirusTotal check completed."))

        google_result = check_google_safe_browsing(content)
        google_score = google_result.get("score", 0)
        explanations.append(google_result.get("message", "Google Safe Browsing check completed."))

        whois_result = check_domain_age(content)
        whois_score = whois_result.get("score", 0)
        explanations.append(whois_result.get("message", "WHOIS check completed."))
    else:
        vt_score = 0
        google_score = 0
        whois_score = 0

    # 4. Rule-based score
    rule_score = 0

    if _has_ip_address(content):
        rule_score += 20

    if content.lower().startswith("http://"):
        rule_score += 15

    if _count_suspicious_words(content) >= 2:
        rule_score += 15

    if _has_urgency(content):
        rule_score += 10

    if _has_money_or_reward(content):
        rule_score += 10

    # 5. Final risk aggregation
    risk_score = round(
    (ml_score * 0.40) +
    (vt_score * 0.20) +
    (google_score * 0.15) +
    (whois_score * 0.15) +
    (rule_score * 0.10)

    )

    risk_score = min(risk_score, 100)

    # 6. Risk label
    if risk_score >= 70:
        label = 'High Risk'
    elif risk_score >= 40:
        label = 'Medium Risk'
    else:
        label = 'Low Risk'

    # 7. Confidence score
    confidence_score = min(abs(risk_score - 50) * 2, 100)

    return {
        'scan_type': scan_type.title(),
        'content': content,
        'ml_score': ml_score,
        'rule_score': rule_score,
        'virustotal_score': vt_score,
        'risk_score': risk_score,
        'confidence_score': confidence_score,
        'label': label,
        'explanation': explanations,
        'recommendation': recommendation_for_score(risk_score),
    }
def recommendation_for_score(risk_score):
    if risk_score >= 70:
        return 'Do not click links, reply, download attachments, or enter credentials. Report this item for review.'
    if risk_score >= 40:
        return 'Treat with caution. Verify the sender or destination through an official channel before taking action.'
    return 'No major phishing indicators were found, but continue to verify unexpected requests before sharing information.'
