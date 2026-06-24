import re

from .llm import llama3_response


RULES = [
    (
        ('phishing', 'what is'),
        'Phishing is a social engineering attack where someone pretends to be a trusted person or organization to steal passwords, payment details, OTPs, or other sensitive information.',
    ),
    (
        ('email', 'identify'),
        'To identify a phishing email, check the sender address, unexpected attachments, urgent wording, spelling mistakes, suspicious links, and requests for passwords or payment information.',
    ),
    (
        ('link', 'url'),
        'Before clicking a link, hover over it or copy it into the URL scanner. Watch for misspelled domains, shortened links, HTTP instead of HTTPS, IP addresses, and extra login or verify words.',
    ),
    (
        ('qr', 'code'),
        'Treat QR codes like links. Scan only trusted QR codes, check the decoded URL before opening it, and use the QR Upload scanner if the source is unknown.',
    ),
    (
        ('sms', 'text'),
        'Smishing is phishing through SMS. Be careful with urgent delivery, bank, prize, or account-lock messages, especially if they include a link or ask for OTPs.',
    ),
    (
        ('password', 'otp'),
        'Never share passwords, OTPs, recovery codes, card PINs, or security answers in chat, email, forms, or phone calls. Real services will not ask for them that way.',
    ),
    (
        ('report', 'suspicious'),
        'If something looks suspicious, do not click or reply. Capture the message, scan it, report it to your security/admin team, and delete it after reporting.',
    ),
    (
        ('high risk', 'risk score'),
        'A high risk score means the content matched several phishing indicators. Avoid interaction, use the generated PDF report, and follow the recommendation shown with the scan.',
    ),
    (
        ('safe', 'protect'),
        'Protect yourself by enabling multi-factor authentication, using a password manager, keeping software updated, and verifying requests through official websites or phone numbers.',
    ),
]


def chatbot_response(message):
    text = message.lower()

    for keywords, response in RULES:
        if all(keyword in text for keyword in keywords):
            return response

    if re.search(r'\b(urgent|verify|blocked|suspended|winner|prize|free|bank|login|password|otp)\b', text):
        return (
            'That message contains wording commonly seen in phishing. Do not click links or share sensitive data. '
            'Use the URL, Email, SMS, or QR scanner to get a risk score and recommendation.'
        )

    if '?' in message:
        return (
            'Good question. For phishing awareness, focus on sender identity, link destination, urgency, requests for sensitive data, '
            'and whether the message was expected. You can paste suspicious content into the scanner for a risk score.'
        )

    return (
        'I can help with phishing awareness, suspicious URLs, emails, SMS messages, QR codes, passwords, OTPs, and reporting steps. '
        'Try asking: "How do I identify a phishing email?"'
    )


def hybrid_response(message):
    """Try rule-based first; if the reply is generic, fall back to Meta Llama 3 for a richer answer.

    Requires environment variable `HUGGINGFACE_API_TOKEN` to call the Hugging Face Inference API.
    If not set or the LLM call fails, the rule-based reply is returned.
    """
    rule_reply = chatbot_response(message)

    generic = (
        'I can help with phishing awareness, suspicious URLs, emails, SMS messages, QR codes, passwords, OTPs, and reporting steps. '
        'Try asking: "How do I identify a phishing email?"'
    )

    if rule_reply and rule_reply != generic:
        return rule_reply

    llm_answer = llama3_response(message)
    return llm_answer or rule_reply
