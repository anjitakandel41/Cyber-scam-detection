import math
import re
from urllib.parse import parse_qs, unquote, urlparse


SUSPICIOUS_WORDS = (
    "verify", "urgent", "login", "password", "account", "suspended",
    "winner", "prize", "free", "click", "bank", "security", "limited",
    "confirm", "update", "blocked", "otp", "pin", "card", "reward",
    "claim", "expire", "expired", "immediately", "wallet", "esewa",
    "khalti", "invoice", "customs", "delivery", "refund", "kyc",
)

SHORTENERS = (
    "bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly", "is.gd",
    "buff.ly", "shorturl.at", "cutt.ly", "rebrand.ly", "lnkd.in",
)

BRAND_WORDS = (
    "paypal", "google", "facebook", "microsoft", "apple", "amazon",
    "netflix", "bank", "esewa", "khalti", "nabil", "imepay",
)

SENSITIVE_WORDS = (
    "password", "otp", "pin", "ssn", "card", "cvv", "bank", "account",
    "wallet", "recovery phrase", "seed phrase", "login code",
)

URL_RE = re.compile(r"(?:https?://|www\.)[^\s<>'\"]+", re.IGNORECASE)
IP_RE = re.compile(r"(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)")


def normalize_url(value):
    text = str(value).strip()
    if text.lower().startswith("www."):
        return f"https://{text}"
    if "://" not in text and "." in text and not any(ch.isspace() for ch in text):
        return f"https://{text}"
    return text


def parse_url(value):
    return urlparse(normalize_url(value))


def extract_urls(text):
    return [match.rstrip(").,;]") for match in URL_RE.findall(str(text))]


def get_domain(value):
    parsed = parse_url(value)
    domain = parsed.netloc.lower()
    if "@" in domain:
        domain = domain.rsplit("@", 1)[-1]
    if ":" in domain:
        domain = domain.split(":", 1)[0]
    return domain[4:] if domain.startswith("www.") else domain


def count_suspicious_words(text):
    lowered = str(text).lower()
    return sum(1 for word in SUSPICIOUS_WORDS if word in lowered)


def has_ip_address(text):
    return int(bool(IP_RE.search(str(text))))


def count_urls(text):
    return len(extract_urls(text))


def has_money_or_reward(text):
    lowered = str(text).lower()
    return int(bool(re.search(
        r"(\$|rs\.?|npr|rupee|usd|gift|bonus|reward|prize|winner|cash|lottery|refund)",
        lowered,
    )))


def has_urgency(text):
    lowered = str(text).lower()
    return int(bool(re.search(
        r"(urgent|immediately|now|limited|expire|expired|suspended|blocked|final warning|within 24)",
        lowered,
    )))


def has_sensitive_request(text):
    lowered = str(text).lower()
    return int(any(word in lowered for word in SENSITIVE_WORDS))


def shannon_entropy(text):
    value = str(text)
    if not value:
        return 0.0
    frequencies = {char: value.count(char) for char in set(value)}
    return -sum((count / len(value)) * math.log2(count / len(value)) for count in frequencies.values())


def extract_features(content, scan_type="url"):
    text = str(content).strip()
    lowered = text.lower()
    parsed = parse_url(text)
    domain = get_domain(text)
    path = parsed.path or ""
    query = parse_qs(parsed.query)
    digits = sum(char.isdigit() for char in text)
    letters = sum(char.isalpha() for char in text)
    urls = extract_urls(text)

    return [
        len(text),
        count_suspicious_words(text),
        len(urls),
        int("@" in text),
        int("-" in domain),
        int(any(shortener == domain or domain.endswith(f".{shortener}") for shortener in SHORTENERS)),
        has_ip_address(text),
        int(lowered.startswith("http://")),
        int(scan_type == "url"),
        int(scan_type == "email"),
        int(scan_type == "sms"),
        int(scan_type == "qr"),
        has_money_or_reward(text),
        has_urgency(text),
        has_sensitive_request(text),
        int(len([part for part in domain.split(".") if part]) > 3),
        len(domain),
        path.count("/"),
        len(query),
        int("%" in text or unquote(text) != text),
        int(any(brand in domain and not domain.endswith(f"{brand}.com") for brand in BRAND_WORDS)),
        int(digits / max(len(text), 1) > 0.28),
        int(letters > 0 and shannon_entropy(domain) > 3.7),
        int(bool(re.search(r"\.(zip|exe|apk|scr|js|msi|bat)(?:$|\?)", lowered))),
        int(bool(re.search(r"(unsubscribe|newsletter|receipt|appointment|meeting|invoice #?\d{3,})", lowered))),
    ]
