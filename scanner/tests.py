from django.test import SimpleTestCase

from scanner.qr_decoder import detect_qr_type, extract_qr_content
from scanner.views import scan_qr_content


class QRContentDetectionTests(SimpleTestCase):
    def test_detects_supported_qr_types(self):
        samples = {
            "https://example.com/login": "url",
            "mailto:admin@example.com?subject=Hello&body=Meeting today": "email",
            "SMSTO:+9779812345678:Your appointment is confirmed": "sms",
            "WIFI:T:WPA;S:Campus;P:Secret123;;": "wifi",
            "BEGIN:VCARD\nFN:Test User\nEMAIL:test@example.com\nEND:VCARD": "contact",
            "upi://pay?pa=merchant@example&pn=Shop&am=100&cu=NPR": "payment",
            "SKU-ABC12345": "product",
            "Remember to submit the assignment tomorrow": "text",
        }
        for content, expected in samples.items():
            self.assertEqual(detect_qr_type(content), expected)

    def test_extracts_wifi_security_fields(self):
        qr_data = extract_qr_content("WIFI:T:WPA2;S:CampusNet;P:StrongPass123;H:false;;")

        self.assertEqual(qr_data["type"], "wifi")
        self.assertEqual(qr_data["extracted"]["ssid"], "CampusNet")
        self.assertEqual(qr_data["extracted"]["encryption"], "WPA2")
        self.assertTrue(qr_data["extracted"]["has_password"])
        self.assertFalse(qr_data["extracted"]["hidden"])

    def test_payment_qr_is_not_overclassified_without_evidence(self):
        result = scan_qr_content("upi://pay?pa=shop@example&pn=Local%20Shop&am=100&cu=NPR")

        self.assertEqual(result["qr_type"], "payment")
        self.assertLess(result["risk_score"], 40)
        self.assertIn("Payment QR decoded", result["explanation"][0])
