import os

from openai import OpenAI


DEFAULT_LLAMA_MODEL = os.getenv(
    "LLAMA_MODEL",
    "meta-llama/Llama-3.2-3B-Instruct"
)


SYSTEM_PROMPT = """
You are CyberShield AI, a cybersecurity awareness assistant.

Your purpose is to help users understand:

- phishing emails
- suspicious URLs
- SMS scams
- QR-code scams
- passwords
- OTP security
- online fraud
- suspicious messages
- safe browsing
- cyber scam reporting

Give clear, simple and practical answers.

Important rules:

1. Do not claim that you have scanned an email, URL, SMS, or QR code
   unless the application explicitly provides the scan result.

2. Do not invent security results.

3. Do not ask users to share passwords, OTPs, API keys, or private credentials.

4. If a user provides a suspicious message, explain possible warning signs.

5. Encourage users to verify suspicious requests through official channels.

6. Keep answers suitable for a university cybersecurity awareness project.

7. Prefer concise answers with useful bullet points when appropriate.

8. If the question is unrelated to cybersecurity, politely explain that
   you are specialized in cybersecurity awareness.
"""


def llama3_response(
    message: str,
    system_prompt: str | None = None,
    model: str | None = None,
) -> str | None:

    token = os.getenv("HUGGINGFACE_API_TOKEN")

    if not token:
        print("ERROR: HUGGINGFACE_API_TOKEN is not configured.")
        return None

    model_name = model or DEFAULT_LLAMA_MODEL

    try:

        client = OpenAI(
            base_url="https://router.huggingface.co/v1",
            api_key=token,
        )

        response = client.chat.completions.create(
            model=model_name,

            messages=[
                {
                    "role": "system",
                    "content": system_prompt or SYSTEM_PROMPT,
                },
                {
                    "role": "user",
                    "content": message,
                },
            ],

            max_tokens=256,
            temperature=0.2,
        )

        if not response.choices:
            return None

        answer = response.choices[0].message.content

        if not answer:
            return None

        return answer.strip()

    except Exception as exc:

        print("Hugging Face / Llama error:")
        print(exc)

        return None