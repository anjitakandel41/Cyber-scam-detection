import base64


def extract_body(payload):
    """
    Extract plain text body from Gmail message.
    """

    body = ""

    if "parts" in payload:

        for part in payload["parts"]:

            if part["mimeType"] == "text/plain":

                data = part["body"].get("data")

                if data:
                    body = base64.urlsafe_b64decode(
                        data.encode("UTF-8")
                    ).decode("utf-8", errors="ignore")

                    break

    else:

        data = payload["body"].get("data")

        if data:
            body = base64.urlsafe_b64decode(
                data.encode("UTF-8")
            ).decode("utf-8", errors="ignore")

    return body

from .gmail_service import get_gmail_service


def gmail_inbox(user):
    """
    Returns latest 20 Gmail emails.
    """

    service = get_gmail_service(user)

    results = service.users().messages().list(
        userId="me",
        maxResults=20,
    ).execute()

    messages = results.get("messages", [])

    emails = []

    for message in messages:

        msg = service.users().messages().get(
            userId="me",
            id=message["id"],
        ).execute()

        headers = msg["payload"].get("headers", [])

        subject = ""
        sender = ""

        for header in headers:

            if header["name"] == "Subject":
                subject = header["value"]

            if header["name"] == "From":
                sender = header["value"]

        body = extract_body(msg["payload"])

        emails.append({

            "id": message["id"],

            "sender": sender,

            "subject": subject,

            "body": body,

        })

    return emails