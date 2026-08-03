import os
import requests


def check_virustotal(url):
    api_key = os.getenv("VIRUSTOTAL_API_KEY")

    if not api_key:
        return {
            "score": 0,
            "message": "VirusTotal API key not configured."
        }

    headers = {
        "x-apikey": api_key
    }

    try:
        response = requests.post(
            "https://www.virustotal.com/api/v3/urls",
            headers=headers,
            data={"url": url},
            timeout=15
        )

        if response.status_code not in [200, 201]:
            return {
                "score": 0,
                "message": "VirusTotal request failed."
            }

        analysis_id = response.json()["data"]["id"]

        result = requests.get(
            f"https://www.virustotal.com/api/v3/analyses/{analysis_id}",
            headers=headers,
            timeout=15
        )

        stats = result.json()["data"]["attributes"]["stats"]

        malicious = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)

        score = min((malicious * 25) + (suspicious * 10), 100)
        if malicious or suspicious:
            message = (
                f"VirusTotal reported {malicious} malicious and "
                f"{suspicious} suspicious engine result(s)."
            )
        else:
            message = "VirusTotal found no known malicious or suspicious reports."

        return {
            "score": score,
            "message": message
        }

    except Exception as e:
        return {
            "score": 0,
            "message": f"VirusTotal error: {str(e)}"
        }
