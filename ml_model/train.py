from pathlib import Path

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.model_selection import train_test_split


BASE_DIR = Path(__file__).resolve().parent
DATASET_PATH = BASE_DIR / 'phishing_dataset.csv'
MODEL_PATH = BASE_DIR / 'model.pkl'

SUSPICIOUS_KEYWORDS = [
    'verify',
    'login',
    'password',
    'account',
    'suspended',
    'winner',
    'prize',
    'free',
    'click',
    'bank',
    'security',
    'confirm',
    'update',
    'urgent',
    'blocked',
]


def count_suspicious_keywords(url):
    lowered = str(url).lower()
    return sum(1 for keyword in SUSPICIOUS_KEYWORDS if keyword in lowered)


def extract_features(url):
    url = str(url)
    lowered = url.lower()
    return {
        'url_length': len(url),
        'has_at_symbol': int('@' in url),
        'uses_https': int(lowered.startswith('https://')),
        'dot_count': url.count('.'),
        'suspicious_keyword_count': count_suspicious_keywords(url),
    }


def build_feature_frame(urls):
    return pd.DataFrame([extract_features(url) for url in urls])


def train():
    dataset = pd.read_csv(DATASET_PATH)
    x = build_feature_frame(dataset['url'])
    y = dataset['label']

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(n_estimators=100, random_state=42)
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

    joblib.dump(
        {
            'model': model,
            'feature_columns': list(x.columns),
            'suspicious_keywords': SUSPICIOUS_KEYWORDS,
        },
        MODEL_PATH,
    )
    print(f'Model saved to: {MODEL_PATH}')


if __name__ == '__main__':
    train()
