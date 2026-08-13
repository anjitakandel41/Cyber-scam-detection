import re
from dataclasses import dataclass, field
from email.utils import parseaddr
from urllib.parse import parse_qs

import joblib
import numpy as np
from django.conf import settings
from sklearn.ensemble import RandomForestClassifier

from .feature_extraction import (
    BRAND_WORDS,
    SHORTENERS,
    count_suspicious_words,
    count_urls,
    extract_features,
    extract_urls,
    get_domain,
    has_ip_address,
    has_money_or_reward,
    has_sensitive_request,
    has_urgency,
    normalize_url,
    parse_url,
)
from .google_safe_browsing import check_google_safe_browsing
from .threat_intelligence import check_virustotal
from .whois_lookup import check_domain_age


MODEL_PATH = settings.BASE_DIR / "ml_model" / "model.pkl"


@dataclass
class Signal:
    score: int
    reason: str
    confidence: int = 70


@dataclass
class ScanEvidence:
    signals: list[Signal] = field(default_factory=list)
    positive: list[str] = field(default_factory=list)

    def add(self, score, reason, confidence=70):
        self.signals.append(Signal(score, reason, confidence))

    @property
    def rule_score(self):
        return min(sum(signal.score for signal in self.signals), 100)

    @property
    def confidence(self):
        if not self.signals:
            return 62
        return min(95, round(sum(signal.confidence for signal in self.signals) / len(self.signals)))

    @property
    def reasons(self):
        reasons = [signal.reason for signal in self.signals]
        if not reasons:
            reasons.extend(self.positive or ["No strong scam indicators were detected."])
        else:
            reasons.extend(self.positive[:2])
        return reasons


def training_samples():
    return [
        ("https://example.com/account/profile", "url", 0),
        ("https://docs.djangoproject.com/en/stable/", "url", 0),
        ("http://192.168.1.44/verify-account", "url", 1),
        ("https://bit.ly/free-prize-login", "url", 1),
        ("Your weekly report is attached for review.", "email", 0),
        ("Urgent: verify your password now or your account will be suspended.", "email", 1),
        ("Your delivery arrives tomorrow between 10 and 12.", "sms", 0),
        ("URGENT: Your bank account is blocked. Click http://bit.ly/verify-bank", "sms", 1),
    ]


def _load_dataset_rows():
    try:
        from ml_model.train import load_datasets
        return load_datasets()
    except Exception:
        return training_samples()


def train_and_save_model():
    samples = _load_dataset_rows()
    x_train = np.array([extract_features(content, scan_type) for content, scan_type, _ in samples])
    y_train = np.array([label for _, _, label in samples])
    model = RandomForestClassifier(
        n_estimators=220,
        max_depth=12,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
    )
    model.fit(x_train, y_train)
    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "feature_count": x_train.shape[1]}, MODEL_PATH)
    return MODEL_PATH


def load_model():
    if not MODEL_PATH.exists():
        return train_and_save_model() and joblib.load(MODEL_PATH)["model"]
    bundle = joblib.load(MODEL_PATH)
    model = bundle["model"]
    expected = getattr(model, "n_features_in_", None)
    if expected and expected != len(extract_features("https://example.com", "url")):
        train_and_save_model()
        bundle = joblib.load(MODEL_PATH)
    return bundle["model"]


def _ml_score(content, scan_type):
    model = load_model()
    features = np.array([extract_features(content, scan_type)])
    if hasattr(model, "predict_proba"):
        class_index = _dangerous_class_index(model)
        return round(float(model.predict_proba(features)[0][class_index]) * 100)
    return int(model.predict(features)[0]) * 100


def _dangerous_class_index(model):
    classes = list(getattr(model, "classes_", []))
    preferred = {1, "1", True, "phishing", "malicious", "scam", "dangerous", "high risk", "high_risk"}
    for index, class_value in enumerate(classes):
        normalized = str(class_value).strip().lower()
        if class_value in preferred or normalized in preferred:
            return index
    if len(classes) == 2:
        return int(np.argmax(classes))
    raise ValueError(f"Unable to identify dangerous class from model.classes_: {classes}")


def _classification(score):
    if score >= 70:
        return "High Risk"
    if score >= 40:
        return "Medium Risk"
    return "Low Risk"


def _recommendation(risk_score, scan_type, evidence=None):
    if scan_type == "wifi":
        return (
            "Use this network only if you trust the owner. Prefer WPA2/WPA3, avoid open public networks for banking, "
            "and use a VPN on shared Wi-Fi."
        )
    if scan_type == "payment":
        return (
            "Verify the merchant name, amount, and payment app before paying. Payment QR codes are not marked safe "
            "or dangerous unless there is concrete evidence such as suspicious links or social engineering."
        )
    if risk_score >= 70:
        return (
            "Treat this as malicious. Do not click links, reply, pay, download files, or share passwords, OTPs, card "
            "details, or wallet credentials. Report and delete it if it came unexpectedly."
        )
    if risk_score >= 40:
        return (
            "Verify through an official website, app, or phone number before acting. Avoid links and attachments until "
            "the sender and destination are confirmed."
        )
    return (
        "No major threat indicators were found. Continue normal caution with unexpected links, payment requests, login "
        "pages, and requests for personal information."
    )


def _url_rules(url):
    evidence = ScanEvidence()
    parsed = parse_url(url)
    domain = get_domain(url)
    lowered = normalize_url(url).lower()

    if not domain:
        evidence.add(20, "The URL could not be parsed into a clear domain.", 65)
        return evidence
    if has_ip_address(domain):
        evidence.add(28, "The URL uses an IP address instead of a recognizable domain.", 86)
    if lowered.startswith("http://"):
        evidence.add(12, "The URL uses insecure HTTP instead of HTTPS.", 75)
    if "@" in parsed.netloc:
        evidence.add(30, "The URL contains @ in the authority section, which can hide the real destination.", 90)
    if any(shortener == domain or domain.endswith(f".{shortener}") for shortener in SHORTENERS):
        evidence.add(24, "The URL uses a shortening service that hides the final destination.", 82)
    if "-" in domain:
        evidence.add(8, "The domain contains hyphens, a common impersonation pattern.", 60)
    if len([part for part in domain.split(".") if part]) > 3:
        evidence.add(10, "The URL has many subdomains, which can be used to bury the real domain.", 68)
    if count_suspicious_words(url) >= 2:
        evidence.add(15, "The URL contains multiple phishing-related terms.", 75)
    if any(brand in domain and not domain.endswith(f"{brand}.com") for brand in BRAND_WORDS):
        evidence.add(18, "The domain appears to reference a known brand without matching the official domain.", 76)
    if re.search(r"\.(zip|exe|apk|scr|js|msi|bat)(?:$|\?)", lowered):
        evidence.add(22, "The URL points to a risky executable or archive file type.", 84)
    if parsed.query and len(parse_qs(parsed.query)) >= 5:
        evidence.add(8, "The URL contains many tracking or query parameters.", 55)
    if not evidence.signals and parsed.scheme == "https":
        evidence.positive.append("The URL is parseable and uses HTTPS.")
    return evidence


def _message_rules(content, scan_type):
    evidence = ScanEvidence()
    text = str(content)
    lowered = text.lower()
    urls = extract_urls(text)

    if has_urgency(text):
        evidence.add(15, "Uses urgency, threats, or deadline pressure.", 78)
    if has_money_or_reward(text):
        evidence.add(13, "Mentions money, prizes, refunds, rewards, or fees.", 72)
    if has_sensitive_request(text):
        evidence.add(22, "Requests or references sensitive information such as OTPs, PINs, passwords, cards, or wallets.", 86)
    if count_suspicious_words(text) >= 3:
        evidence.add(14, "Contains several phishing/scam keywords in one message.", 76)
    if urls:
        evidence.add(8, "Includes one or more links that should be verified before opening.", 64)
        for url in urls[:2]:
            url_evidence = _url_rules(url)
            for signal in url_evidence.signals[:3]:
                evidence.add(min(signal.score, 18), f"Linked URL: {signal.reason}", signal.confidence)
    if scan_type == "email":
        sender_match = re.search(r"^from:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
        sender = parseaddr(sender_match.group(1))[1] if sender_match else ""
        subject_match = re.search(r"^subject:\s*(.+)$", text, re.IGNORECASE | re.MULTILINE)
        subject = subject_match.group(1) if subject_match else ""
        sender_domain = sender.split("@")[-1].lower() if "@" in sender else ""
        if sender and sender_domain in {"gmail.com", "yahoo.com", "outlook.com"} and any(word in lowered for word in ("bank", "wallet", "security", "support")):
            evidence.add(16, "A generic mailbox is claiming to represent a sensitive service.", 72)
        if subject and has_urgency(subject):
            evidence.add(10, "The email subject line uses urgent or threatening wording.", 75)
    if scan_type == "sms":
        if re.search(r"\b\d{4,8}\b", text) and any(word in lowered for word in ("share", "send", "reply", "confirm")):
            evidence.add(20, "The SMS asks the user to share or confirm a numeric code.", 84)
        if len(text) < 170 and has_urgency(text) and urls:
            evidence.add(10, "A short urgent SMS with a link is a common smishing pattern.", 78)
    if not evidence.signals:
        evidence.positive.append("The message does not combine urgency, sensitive-data requests, suspicious links, or reward pressure.")
    return evidence


def _plain_text_rules(content):
    evidence = _message_rules(content, "text")
    lowered = str(content).lower()
    if re.search(r"\b(seed phrase|private key|recovery phrase)\b", lowered):
        evidence.add(35, "The text references wallet recovery secrets, which should never be shared.", 92)
    return evidence


def _external_url_checks(url):
    checks = {
        "virustotal_score": 0,
        "google_safe_browsing_score": 0,
        "whois_score": 0,
        "messages": [],
    }
    vt_result = check_virustotal(url)
    checks["virustotal_score"] = int(vt_result.get("score", 0))
    checks["messages"].append(vt_result.get("message", "VirusTotal check completed."))

    google_result = check_google_safe_browsing(url)
    checks["google_safe_browsing_score"] = int(google_result.get("score", 0))
    checks["messages"].append(google_result.get("message", "Google Safe Browsing check completed."))

    whois_result = check_domain_age(url)
    checks["whois_score"] = int(whois_result.get("score", 0))
    checks["messages"].append(whois_result.get("message", "WHOIS check completed."))
    return checks


def scan_content(content, scan_type):
    scan_type = (scan_type or "text").lower()
    if scan_type == "qr":
        scan_type = "text"
    normalized_content = normalize_url(content) if scan_type == "url" else str(content).strip()

    ml_score = _ml_score(normalized_content, scan_type if scan_type in {"url", "email", "sms"} else "qr")
    evidence = _url_rules(normalized_content) if scan_type == "url" else _message_rules(normalized_content, scan_type)
    if scan_type == "text":
        evidence = _plain_text_rules(normalized_content)

    external = {"virustotal_score": 0, "google_safe_browsing_score": 0, "whois_score": 0, "messages": []}
    if scan_type == "url":
        external = _external_url_checks(normalized_content)

    external_score = max(
        external["virustotal_score"],
        external["google_safe_browsing_score"],
        round(external["whois_score"] * 0.75),
    )
    if external["google_safe_browsing_score"] >= 100 or external["virustotal_score"] >= 80:
        risk_score = max(85, external_score)
    else:
        risk_score = round((ml_score * 0.35) + (evidence.rule_score * 0.45) + (external_score * 0.20))
    risk_score = max(0, min(risk_score, 100))

    confidence_score = round(
        (abs(risk_score - 50) * 1.15)
        + (evidence.confidence * 0.35)
        + (25 if external_score >= 80 else 0)
    )
    confidence_score = max(35, min(confidence_score, 99))

    explanations = evidence.reasons + external["messages"]
    try:
        from .xai_explainer import get_combined_explanation

        xai = get_combined_explanation(
            normalized_content,
            scan_type if scan_type in {"url", "email", "sms"} else "qr",
            rules=evidence.reasons,
            external=external,
        )
    except Exception as exc:
        import logging

        logging.getLogger(__name__).exception("XAI explanation failed: %s", exc)
        xai = {
            "shap": {"method": "SHAP", "available": False, "message": "SHAP explanation unavailable.", "top_features": []},
            "lime": {"method": "LIME", "available": False, "message": "LIME explanation unavailable.", "top_features": []},
            "rules": evidence.reasons,
            "external": external,
            "comparison": [],
            "statement": (
                "SHAP and LIME explain the machine-learning prediction. They do not directly determine the final hybrid risk score."
            ),
        }
    return {
        "scan_type": scan_type.title(),
        "content": normalized_content,
        "ml_score": ml_score,
        "rule_score": evidence.rule_score,
        "virustotal_score": external["virustotal_score"],
        "google_safe_browsing_score": external["google_safe_browsing_score"],
        "whois_score": external["whois_score"],
        "risk_score": risk_score,
        "confidence_score": confidence_score,
        "label": _classification(risk_score),
        "explanation": explanations,
        "xai": xai,
        "recommendation": _recommendation(risk_score, scan_type, evidence),
    }


def scan_passive_content(content, scan_type, reasons, risk_score=15, confidence_score=70):
    risk_score = max(0, min(int(risk_score), 100))
    return {
        "scan_type": scan_type.title(),
        "content": content,
        "ml_score": 0,
        "rule_score": risk_score,
        "virustotal_score": 0,
        "google_safe_browsing_score": 0,
        "whois_score": 0,
        "risk_score": risk_score,
        "confidence_score": confidence_score,
        "label": _classification(risk_score),
        "explanation": reasons,
        "xai": {
            "shap": {"method": "SHAP", "available": False, "message": "SHAP explanation unavailable for passive QR content.", "top_features": []},
            "lime": {"method": "LIME", "available": False, "message": "LIME explanation unavailable for passive QR content.", "top_features": []},
            "rules": reasons,
            "external": {"virustotal_score": 0, "google_safe_browsing_score": 0, "whois_score": 0, "messages": []},
            "comparison": [],
            "statement": (
                "Rule-based explanations provide deterministic reasons based on predefined security signals. "
                "SHAP and LIME explain machine-learning predictions when the Random Forest model is used."
            ),
        },
        "recommendation": _recommendation(risk_score, scan_type),
    }
