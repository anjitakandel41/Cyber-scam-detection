from .feature_extraction import (
    SHORTENERS,
    SUSPICIOUS_WORDS,
    count_suspicious_words as _count_suspicious_words,
    count_urls as _count_urls,
    extract_features,
    has_ip_address as _has_ip_address,
    has_money_or_reward as _has_money_or_reward,
    has_urgency as _has_urgency,
)
from .hybrid_engine import load_model, scan_content, train_and_save_model


def explain(content, scan_type, risk_score):
    result = scan_content(content, scan_type)
    return result["explanation"]


def build_recommendation(risk_score, scan_type):
    result = scan_content("", scan_type)
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
    return result["recommendation"]
