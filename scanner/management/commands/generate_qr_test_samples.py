from pathlib import Path
from io import BytesIO

import cv2
from django.conf import settings
from django.core.management.base import BaseCommand

from scanner.qr_decoder import QRDecodeError, decode_qr_upload


class Command(BaseCommand):
    help = "Generate local QR images for scanner demonstration and testing."

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=120,
            help="Number of QR images to generate. Default: 120.",
        )

    def handle(self, *args, **options):
        count = max(options["count"], 100)
        output_dir = Path(settings.MEDIA_ROOT) / "qr_test_samples_verified"
        output_dir.mkdir(parents=True, exist_ok=True)

        encoder = cv2.QRCodeEncoder_create()
        samples = self._build_verified_samples(encoder, count)

        for index, (name, payload) in enumerate(samples, start=1):
            image = self._make_qr_image(encoder, payload)
            file_path = output_dir / f"{index:03d}_{name}.png"
            cv2.imwrite(str(file_path), image)

        self.stdout.write(self.style.SUCCESS(
            f"Generated {len(samples)} QR test images in {output_dir}"
        ))

    def _build_verified_samples(self, encoder, count):
        builders = [
            self._url_safe,
            self._url_phishing,
            self._email_safe,
            self._email_phishing,
            self._sms_safe,
            self._sms_scam,
            self._wifi_secure,
            self._wifi_open,
            self._contact,
            self._payment,
            self._product,
            self._plain_text,
        ]

        samples = []
        attempt = 1
        max_attempts = count * 8

        while len(samples) < count and attempt <= max_attempts:
            builder = builders[(attempt - 1) % len(builders)]
            name, payload = builder(attempt)
            image = self._make_qr_image(encoder, payload)
            if self._can_decode(image):
                samples.append((name, payload))
            attempt += 1

        if len(samples) < count:
            raise RuntimeError(
                f"Only generated {len(samples)} verified QR images after {max_attempts} attempts."
            )
        return samples

    def _make_qr_image(self, encoder, payload):
        image = encoder.encode(payload)
        image = cv2.resize(image, None, fx=12, fy=12, interpolation=cv2.INTER_NEAREST)
        return cv2.copyMakeBorder(
            image,
            48,
            48,
            48,
            48,
            cv2.BORDER_CONSTANT,
            value=255,
        )

    def _can_decode(self, image):
        success, buffer = cv2.imencode(".png", image)
        if not success:
            return False
        try:
            decode_qr_upload(BytesIO(buffer.tobytes()))
        except QRDecodeError:
            return False
        return True

    def _url_safe(self, index):
        return (
            f"url_safe_{index}",
            f"https://docs.djangoproject.com/en/stable/topics/security/{index}",
        )

    def _url_phishing(self, index):
        return (
            f"url_phishing_{index}",
            f"http://bit.ly/verify-bank-login-{index}",
        )

    def _email_safe(self, index):
        return (
            f"email_safe_{index}",
            f"mailto:student{index}@university.edu.np?subject=Class%20Reminder&body=Your%20class%20starts%20tomorrow%20at%2010%20AM.",
        )

    def _email_phishing(self, index):
        return (
            f"email_phishing_{index}",
            f"mailto:security{index}@verify.test?subject=Urgent&body=Verify%20OTP%20at%20http://bit.ly/claim{index}",
        )

    def _sms_safe(self, index):
        return (
            f"sms_safe_{index}",
            f"SMSTO:+97798123{index:04d}:Your appointment is confirmed for Friday at 10 AM.",
        )

    def _sms_scam(self, index):
        return (
            f"sms_scam_{index}",
            f"SMSTO:+97798000{index:04d}:URGENT wallet blocked verify OTP http://bit.ly/w{index}",
        )

    def _wifi_secure(self, index):
        return (
            f"wifi_secure_{index}",
            f"WIFI:T:WPA;S:CampusDemo{index};P:StrongPass{index}2026;H:false;;",
        )

    def _wifi_open(self, index):
        return (
            f"wifi_open_{index}",
            f"WIFI:T:nopass;S:FreePublicWiFi{index};P:;H:false;;",
        )

    def _contact(self, index):
        return (
            f"contact_{index}",
            "BEGIN:VCARD\n"
            "VERSION:3.0\n"
            f"FN:Demo Student {index}\n"
            f"EMAIL:student{index}@university.edu.np\n"
            f"TEL:+97798123{index:04d}\n"
            f"URL:https://university.edu.np/profile/{index}\n"
            "END:VCARD",
        )

    def _payment(self, index):
        return (
            f"payment_{index}",
            f"upi://pay?pa=merchant{index}@example&pn=Demo%20Store%20{index}&am={100 + index}&cu=NPR",
        )

    def _product(self, index):
        return (
            f"product_{index}",
            f"SKU-DEMO-{100000 + index}",
        )

    def _plain_text(self, index):
        return (
            f"plain_text_{index}",
            f"Awareness {index}: never share OTP PIN password.",
        )
