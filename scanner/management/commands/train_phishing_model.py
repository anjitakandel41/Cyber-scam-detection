from django.core.management.base import BaseCommand

from scanner.ml.phishing_detector import train_and_save_model


class Command(BaseCommand):
    help = 'Train and save the phishing detection RandomForest model.'

    def handle(self, *args, **options):
        model_path = train_and_save_model()
        self.stdout.write(self.style.SUCCESS(f'Phishing model saved to {model_path}'))
