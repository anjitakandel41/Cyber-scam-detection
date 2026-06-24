from urllib.parse import urlparse
from datetime import datetime
import whois


def check_domain_age(url):
    try:
        # Parse domain from URL
        parsed = urlparse(url if "://" in url else f"http://{url}")
        domain = parsed.netloc.replace("www.", "")

        # Skip local/private IP addresses
        if (
            not domain
            or domain.startswith("192.168.")
            or domain.startswith("127.")
            or domain.startswith("10.")
        ):
            return {
                "score": 0,
                "message": "WHOIS check skipped for local/private IP address."
            }

        # Fetch WHOIS information
        info = whois.whois(domain)
        creation_date = info.creation_date

        # WHOIS may return multiple creation dates
        if isinstance(creation_date, list):
            valid_dates = [
                d.replace(tzinfo=None) if d.tzinfo else d
                for d in creation_date
                if isinstance(d, datetime)
            ]

            creation_date = max(valid_dates) if valid_dates else None

        # No creation date found
        if not creation_date:
            return {
                "score": 20,
                "message": "WHOIS could not determine the domain registration date."
            }

        # Remove timezone if present
        if creation_date.tzinfo is not None:
            creation_date = creation_date.replace(tzinfo=None)

        # Calculate age
        age_days = (datetime.now() - creation_date).days

        # Risk scoring based on domain age
        if age_days < 30:
            score = 80
            message = f"Very new domain: {age_days} days old."
        elif age_days < 180:
            score = 50
            message = f"Recently registered domain: {age_days} days old."
        elif age_days < 365:
            score = 20
            message = f"Relatively new domain: {age_days} days old."
        else:
            score = 0
            message = f"Domain age: {age_days} days old."

        return {
            "score": score,
            "message": message
        }

    except Exception as e:
        return {
            "score": 0,
            "message": f"WHOIS check failed: {str(e)}"
        }