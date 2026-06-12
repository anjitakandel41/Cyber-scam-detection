import cv2
import numpy as np


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
    candidates = [
        image,
        cv2.cvtColor(image, cv2.COLOR_BGR2GRAY),
        cv2.resize(image, None, fx=4, fy=4, interpolation=cv2.INTER_NEAREST),
        cv2.resize(image, None, fx=2, fy=2, interpolation=cv2.INTER_CUBIC),
    ]

    for candidate in candidates:
        decoded_text, _, _ = detector.detectAndDecode(candidate)
        if decoded_text:
            return [decoded_text.strip()]

        _, decoded_texts, _, _ = detector.detectAndDecodeMulti(candidate)
        values = [text.strip() for text in decoded_texts if text.strip()]
        if values:
            return values

    return []


def decode_qr_upload(uploaded_file):
    image_bytes = np.frombuffer(uploaded_file.read(), np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

    if image is None:
        raise QRDecodeError('Upload a valid image file containing a QR code.')

    try:
        decoded_values = _decode_with_pyzbar(image)
    except ImportError:
        decoded_values = _decode_with_opencv(image)
    except OSError:
        decoded_values = _decode_with_opencv(image)

    if not decoded_values:
        raise QRDecodeError('No QR code content could be decoded from this image.')

    return decoded_values[0]


def infer_scan_type(content):
    lowered = content.strip().lower()
    if lowered.startswith(('http://', 'https://', 'www.')):
        return 'url'
    if '@' in content and len(content.split()) > 3:
        return 'email'
    return 'sms'
