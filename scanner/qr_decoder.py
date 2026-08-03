import cv2
import numpy as np
import re
from urllib.parse import parse_qs, unquote, urlparse


class QRDecodeError(ValueError):
    pass


def _decode_with_pyzbar(image):
    from pyzbar.pyzbar import decode

    decoded_items = decode(image)
    return [
        item.data.decode('utf-8', errors='replace').strip()
        for item in decoded_items
        if item.data
    ]


def _decode_with_opencv(image):
    detector = cv2.QRCodeDetector()
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, otsu = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    adaptive = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        31,
        5,
    )
    candidates = [
        image,
        gray,
        otsu,
        adaptive,
        cv2.resize(image, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST),
        cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC),
        cv2.resize(gray, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST),
        cv2.resize(otsu, None, fx=3, fy=3, interpolation=cv2.INTER_NEAREST),
    ]

    for candidate in candidates:
        decoded_text, _, _ = detector.detectAndDecode(candidate)
        if decoded_text:
            return [decoded_text.strip()]

        try:
            decoded_text, _, _ = detector.detectAndDecodeCurved(candidate)
            if decoded_text:
                return [decoded_text.strip()]
        except cv2.error:
            pass

        _, decoded_texts, _, _ = detector.detectAndDecodeMulti(candidate)
        values = [text.strip() for text in decoded_texts if text.strip()]
        if values:
            return values

    return []


def _opencv_detects_qr(image):
    detector = cv2.QRCodeDetector()
    candidates = [
        image,
        cv2.cvtColor(image, cv2.COLOR_BGR2GRAY),
    ]

    for candidate in candidates:
        detected, _ = detector.detect(candidate)
        if detected:
            return True

        try:
            detected_multi, _ = detector.detectMulti(candidate)
            if detected_multi:
                return True
        except cv2.error:
            pass

    return False


def decode_qr_upload(uploaded_file):
    image_bytes = np.frombuffer(uploaded_file.read(), np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

    if image is None:
        raise QRDecodeError('Upload a valid image file containing a QR code.')

    decoded_values = []

    try:
        decoded_values = _decode_with_pyzbar(image)
    except (ImportError, OSError):
        decoded_values = []

    if not decoded_values:
        decoded_values = _decode_with_opencv(image)

    if not decoded_values:
        if _opencv_detects_qr(image):
            raise QRDecodeError(
                'A QR code was found, but its content could not be decoded. '
                'This usually happens with blurry images, screenshots with low resolution, '
                'damaged QR blocks, or stylized QR codes with large center logos. '
                'Upload a clearer, plain QR image or crop only the QR area.'
            )
        raise QRDecodeError(
            'No QR code was detected in this image. Upload a clear PNG or JPG that contains one complete QR code.'
        )

    return decoded_values[0]


def infer_scan_type(content):
    lowered = content.strip().lower()
    if lowered.startswith(('http://', 'https://', 'www.')):
        return 'url'
    if lowered.startswith('mailto:'):
        return 'email'
    if lowered.startswith(('smsto:', 'sms:')):
        return 'sms'
    if '@' in content and len(content.split()) > 3:
        return 'email'
    return 'sms'


def _split_escaped_qr_fields(value):
    fields = []
    current = []
    escaped = False
    for char in value:
        if escaped:
            current.append(char)
            escaped = False
        elif char == '\\':
            escaped = True
        elif char == ';':
            fields.append(''.join(current))
            current = []
        else:
            current.append(char)
    fields.append(''.join(current))
    return fields


def parse_wifi_qr(content):
    body = content.strip()[5:] if content.strip().upper().startswith('WIFI:') else content
    parsed = {}
    for field in _split_escaped_qr_fields(body):
        if ':' not in field:
            continue
        key, value = field.split(':', 1)
        parsed[key.upper()] = value
    encryption = parsed.get('T', 'nopass') or 'nopass'
    password = parsed.get('P', '')
    return {
        'ssid': parsed.get('S', ''),
        'encryption': encryption.upper(),
        'has_password': bool(password),
        'hidden': parsed.get('H', '').lower() == 'true',
    }


def parse_mailto_qr(content):
    parsed = urlparse(content)
    params = parse_qs(parsed.query)
    recipient = unquote(parsed.path or '').strip()
    subject = unquote(params.get('subject', [''])[0])
    body = unquote(params.get('body', [''])[0])
    scan_text = '\n'.join(part for part in [
        f'From: {recipient}' if recipient else '',
        f'Subject: {subject}' if subject else '',
        '',
        body,
    ] if part is not None).strip()
    return {
        'recipient': recipient,
        'subject': subject,
        'body': body,
        'scan_text': scan_text or content,
    }


def parse_sms_qr(content):
    text = content.strip()
    if text.upper().startswith('SMSTO:'):
        _, remainder = text.split(':', 1)
        phone, _, message = remainder.partition(':')
    else:
        parsed = urlparse(text)
        phone = parsed.path
        params = parse_qs(parsed.query)
        message = params.get('body', [''])[0]
    return {
        'phone_number': phone.strip(),
        'message': unquote(message).strip(),
        'scan_text': f'Phone Number: {phone.strip()}\n\nMessage:\n{unquote(message).strip()}'.strip(),
    }


def parse_vcard_qr(content):
    details = {}
    emails = []
    urls = []
    phones = []
    for raw_line in content.replace('\r\n', '\n').split('\n'):
        line = raw_line.strip()
        if ':' not in line:
            continue
        key, value = line.split(':', 1)
        key_name = key.split(';', 1)[0].upper()
        if key_name == 'FN':
            details['name'] = value
        elif key_name == 'ORG':
            details['organization'] = value
        elif key_name == 'EMAIL':
            emails.append(value)
        elif key_name == 'URL':
            urls.append(value)
        elif key_name == 'TEL':
            phones.append(value)
    details['emails'] = emails
    details['urls'] = urls
    details['phones'] = phones
    return details


def parse_payment_qr(content):
    text = content.strip()
    parsed = urlparse(text)
    params = parse_qs(parsed.query)
    provider = parsed.scheme.upper() if parsed.scheme else 'Unknown'
    merchant = params.get('pa', params.get('merchant', params.get('pn', [''])))[0]
    amount = params.get('am', params.get('amount', ['']))[0]
    currency = params.get('cu', params.get('currency', ['']))[0]

    if text.startswith('000201') or 'merchant' in text.lower():
        provider = 'EMV/Payment QR'
        merchant_match = re.search(r'(merchant|name)[=: ]+([A-Za-z0-9 ._-]{3,40})', text, re.IGNORECASE)
        amount_match = re.search(r'(amount|amt)[=: ]+([0-9]+(?:\.[0-9]{1,2})?)', text, re.IGNORECASE)
        currency_match = re.search(r'\b(NPR|USD|INR|EUR)\b', text, re.IGNORECASE)
        merchant = merchant or (merchant_match.group(2).strip() if merchant_match else '')
        amount = amount or (amount_match.group(2) if amount_match else '')
        currency = currency or (currency_match.group(1).upper() if currency_match else '')

    return {
        'provider': provider,
        'merchant': unquote(merchant),
        'amount': amount,
        'currency': currency.upper() if currency else '',
    }


def parse_product_qr(content):
    text = content.strip()
    url_match = re.search(r'(https?://[^\s]+|www\.[^\s]+)', text, re.IGNORECASE)
    product_id = ''
    if not url_match:
        product_id = re.sub(r'^(EAN|UPC|SKU|GTIN|PRODUCT)[:\s-]*', '', text, flags=re.IGNORECASE).strip()
    return {
        'product_id': product_id,
        'url': url_match.group(1) if url_match else '',
    }


def detect_qr_type(content):
    text = content.strip()
    lowered = text.lower()
    if lowered.startswith(('http://', 'https://', 'www.')):
        return 'url'
    if lowered.startswith('mailto:'):
        return 'email'
    if lowered.startswith(('smsto:', 'sms:')):
        return 'sms'
    if lowered.startswith('wifi:'):
        return 'wifi'
    if 'begin:vcard' in lowered:
        return 'contact'
    if lowered.startswith(('upi:', 'bitcoin:', 'ethereum:', 'esewa:', 'khalti:', 'paypal:')) or text.startswith('000201'):
        return 'payment'
    if re.fullmatch(r'(?:EAN|UPC|SKU|GTIN|PRODUCT)?[:\s-]*[A-Z0-9-]{6,32}', text, re.IGNORECASE):
        return 'product'
    if '@' in text and len(text.split()) > 3:
        return 'email'
    return 'text'


def extract_qr_content(content):
    qr_type = detect_qr_type(content)
    if qr_type == 'email':
        extracted = parse_mailto_qr(content) if content.lower().startswith('mailto:') else {'scan_text': content}
    elif qr_type == 'sms':
        extracted = parse_sms_qr(content)
    elif qr_type == 'wifi':
        extracted = parse_wifi_qr(content)
    elif qr_type == 'contact':
        extracted = parse_vcard_qr(content)
    elif qr_type == 'payment':
        extracted = parse_payment_qr(content)
    elif qr_type == 'product':
        extracted = parse_product_qr(content)
    elif qr_type == 'url':
        extracted = {'url': content.strip()}
    else:
        extracted = {'text': content.strip()}
    return {
        'type': qr_type,
        'raw': content,
        'extracted': extracted,
    }
