import json
from unittest.mock import patch

import numpy as np
from django.test import SimpleTestCase

from scanner.ml.feature_extraction import FEATURE_NAMES, extract_features
from scanner.ml.hybrid_engine import scan_content
from scanner.ml.xai_explainer import _dangerous_class_index, explain_with_lime, explain_with_shap
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

    def test_qr_url_scan_includes_xai(self):
        result = scan_qr_content("https://bit.ly/free-prize-login")

        self.assertEqual(result["qr_type"], "url")
        self.assertIn("xai", result)
        self.assertIn("shap", result["xai"])
        self.assertIn("lime", result["xai"])


class XAIExplanationTests(SimpleTestCase):
    sample = "Urgent: verify your bank password and OTP now at http://bit.ly/verify-bank"

    def test_feature_extraction_matches_expected_25_features(self):
        features = extract_features(self.sample, "email")

        self.assertEqual(len(FEATURE_NAMES), 25)
        self.assertEqual(len(features), 25)

    def test_shap_returns_json_serializable_top_features(self):
        explanation = explain_with_shap(self.sample, "email", top_n=5)

        self.assertEqual(explanation["method"], "SHAP")
        self.assertGreater(len(explanation["top_features"]), 0)
        self.assertIn("shap_value", explanation["top_features"][0])
        json.dumps(explanation)

    def test_lime_returns_json_serializable_top_features(self):
        explanation = explain_with_lime(self.sample, "email", top_n=5)

        self.assertEqual(explanation["method"], "LIME")
        self.assertGreater(len(explanation["top_features"]), 0)
        self.assertIn("weight", explanation["top_features"][0])
        json.dumps(explanation)

    def test_positive_and_negative_directions_are_assigned(self):
        result = scan_content(self.sample, "email")
        directions = {
            item["direction"]
            for item in result["xai"]["shap"]["top_features"] + result["xai"]["lime"]["top_features"]
        }

        self.assertTrue(directions <= {"increases_risk", "decreases_risk"})
        self.assertIn("increases_risk", directions)

    def test_correct_malicious_class_index_is_detected(self):
        class DummyModel:
            classes_ = np.array([0, 1])

        self.assertEqual(_dangerous_class_index(DummyModel()), 1)

    def test_ml_prediction_and_hybrid_formula_remain_available(self):
        result = scan_content(self.sample, "email")

        self.assertIn("ml_score", result)
        self.assertIn("rule_score", result)
        self.assertIn("risk_score", result)
        self.assertNotIn("shap_value", str(result["risk_score"]))

    def test_rule_explanations_still_work(self):
        result = scan_content(self.sample, "email")

        self.assertTrue(any("Urgency" in reason or "urgency" in reason for reason in result["explanation"]))
        self.assertGreater(len(result["xai"]["rules"]), 0)

    def test_shap_failure_does_not_break_scan(self):
        with patch("scanner.ml.xai_explainer.explain_with_shap", side_effect=RuntimeError("boom")):
            result = scan_content(self.sample, "email")

        self.assertEqual(result["xai"]["shap"]["message"], "SHAP explanation unavailable.")
        self.assertIn("risk_score", result)

    def test_lime_failure_does_not_break_scan(self):
        with patch("scanner.ml.xai_explainer.explain_with_lime", side_effect=RuntimeError("boom")):
            result = scan_content(self.sample, "email")

        self.assertEqual(result["xai"]["lime"]["message"], "LIME explanation unavailable.")
        self.assertIn("risk_score", result)
