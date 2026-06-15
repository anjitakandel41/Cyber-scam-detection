from pathlib import Path
from urllib.parse import urlparse
import re

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / 'phishing_dataset.csv'
MODEL_PATH = BASE_DIR / 'model.pkl'

SUSPICIOUS_WORDS = (
    'verify', 'urgent', 'login', 'password', 'account',
    'suspended', 'winner', 'prize', 'free', 'click',
    'bank', 'security', 'limited', 'confirm', 'update',
)

SHORTENERS = ('bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly')


def _count_suspicious_words(text):
    lowered = text.lower()
    return sum(1 for word in SUSPICIOUS_WORDS if word in lowered)


def _has_ip_address(text):
    return int(bool(re.search(r'(?<!\d)(?:\d{1,3}\.){3}\d{1,3}(?!\d)', text)))


def _count_urls(text):
    return len(re.findall(r'https?://|www\.', text.lower()))


def _has_money_or_reward(text):
    return int(bool(re.search(r'(\$|rs\.?|usd|gift|bonus|reward|prize|winner)', text.lower())))


def _has_urgency(text):
    return int(bool(re.search(r'(urgent|immediately|now|limited|expire|suspended|blocked)', text.lower())))


def extract_features(content, scan_type='url'):
    text = str(content).strip()
    lowered = text.lower()
    parsed = urlparse(text if '://' in text else f'//{text}')
    domain = parsed.netloc.lower()

    return [
        len(text),
        _count_suspicious_words(text),
        _count_urls(text),
        int('@' in text),
        int('-' in domain),
        int(any(shortener in domain for shortener in SHORTENERS)),
        _has_ip_address(text),
        int(lowered.startswith('http://')),
        int(scan_type == 'url'),
        int(scan_type == 'email'),
        int(scan_type == 'sms'),
        _has_money_or_reward(text),
        _has_urgency(text),
        int(bool(re.search(r'(password|otp|pin|ssn|card|bank)', lowered))),
        int(len(domain.split('.')) > 3 if domain else False),
    ]


def train():
    dataset = pd.read_csv(DATASET_PATH)

    x = np.array([extract_features(url, 'url') for url in dataset['url']])
    y = dataset['label']

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(n_estimators=160, max_depth=8, random_state=42)
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)

    print('Accuracy:', accuracy_score(y_test, predictions))
    print('Precision:', precision_score(y_test, predictions))
    print('Recall:', recall_score(y_test, predictions))
    print('F1 Score:', f1_score(y_test, predictions))
    print('Confusion Matrix:')
    print(confusion_matrix(y_test, predictions))
    print('Classification Report:')
    print(classification_report(y_test, predictions, target_names=['Legitimate', 'Phishing']))

    joblib.dump({'model': model}, MODEL_PATH)
    print(f'Model saved to: {MODEL_PATH}')


if __name__ == '__main__':
    train()