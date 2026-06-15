import os
import requests


def check_google_safe_browsing(url):
    api_key = os.getenv("GOOGLE_SAFE_BROWSING_API_KEY")

    if not api_key:
        return {
            "score": 0,
            "message": "Google Safe Browsing API key not configured."
        }

    api_url = f"https://safebrowsing.googleapis.com/v4/threatMatches:find?key={api_key}"

    payload = {
        "client": {
            "clientId": "cyber-scam-detector",
            "clientVersion": "1.0"
        },
        "threatInfo": {
            "threatTypes": [
                "MALWARE",
                "SOCIAL_ENGINEERING",
                "UNWANTED_SOFTWARE",
                "POTENTIALLY_HARMFUL_APPLICATION"
            ],
            "platformTypes": ["ANY_PLATFORM"],
            "threatEntryTypes": ["URL"],
            "threatEntries": [
                {"url": url}
            ]
        }
    }

    try:
        response = requests.post(api_url, json=payload, timeout=15)
        data = response.json()

        if "matches" in data:
            return {
                "score": 100,
                "message": "Google Safe Browsing flagged this URL as dangerous."
            }

        return {
            "score": 0,
            "message": "Google Safe Browsing found no threat."
        }

    except Exception as e:
        return {
            "score": 0,
            "message": f"Google Safe Browsing error: {str(e)}"
        }