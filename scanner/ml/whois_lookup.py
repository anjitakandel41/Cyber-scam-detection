from urllib.parse import urlparse
from datetime import datetime
import whois


def check_domain_age(url):
    try:
        parsed = urlparse(url if "://" in url else f"http://{url}")
        domain = parsed.netloc.replace("www.", "")

        if not domain or domain.startswith("192.168.") or domain.startswith("127."):
            return {
                "score": 0,
                "message": "WHOIS check skipped for local/private IP address."
            }

        info = whois.whois(domain)
        creation_date = info.creation_date

        if isinstance(creation_date, list):
            creation_date = creation_date[0]

        if not creation_date:
            return {
                "score": 20,
                "message": "WHOIS could not find domain creation date."
            }
        if creation_date.tzinfo is not None:
            creation_date = creation_date.replace(tzinfo=None)

        age_days = (datetime.now() - creation_date).days

        if age_days < 30:
            score = 80
            message = f"Domain is very new: {age_days} days old."
        elif age_days < 180:
            score = 50
            message = f"Domain is relatively new: {age_days} days old."
        else:
            score = 0
            message = f"Domain is old enough: {age_days} days old."

        return {
            "score": score,
            "message": message
        }

    except Exception as e:
        return {
            "score": 0,
            "message": f"WHOIS check failed: {str(e)}"
        }