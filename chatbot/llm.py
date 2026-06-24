import os
import requests


DEFAULT_LLAMA_MODEL = os.getenv('LLAMA_MODEL', 'meta-llama/Llama-3-1b-chat-hf')


def llama3_response(message: str, system_prompt: str | None = None, model: str | None = None) -> str | None:
    """Return a Meta Llama 3 chat response via Hugging Face Inference API."""
    token = os.getenv('HUGGINGFACE_API_TOKEN')
    if not token:
        return None

    model_name = model or DEFAULT_LLAMA_MODEL
    url = f'https://api-inference.huggingface.co/models/{model_name}'
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json',
    }

    system_content = system_prompt or (
        'You are a concise cybersecurity assistant specialized in phishing awareness. '
        'Answer the user clearly with practical guidance on phishing, suspicious links, QR codes, emails, SMS scams, and safe reporting steps.'
    )

    payload = {
        'inputs': [
            {'role': 'system', 'content': system_content},
            {'role': 'user', 'content': message},
        ],
        'parameters': {
            'max_new_tokens': 256,
            'temperature': 0.2,
            'top_p': 0.95,
            'repetition_penalty': 1.05,
            'return_full_text': False,
        },
    }

    try:
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        response.raise_for_status()
        data = response.json()

        if isinstance(data, dict):
            text = data.get('generated_text') or data.get('text') or data.get('output_text')
            if text:
                return text.strip()

            if isinstance(data.get('outputs'), list) and data['outputs']:
                output = data['outputs'][0]
                return output.get('generated_text', output.get('text', '')).strip()

        if isinstance(data, list) and data:
            first = data[0]
            if isinstance(first, dict):
                return first.get('generated_text', first.get('text', '')).strip()

    except requests.RequestException:
        return None
    except ValueError:
        return None

    return None
