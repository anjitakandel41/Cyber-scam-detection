from pathlib import Path

import joblib
import numpy as np
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

from scanner.ml.feature_extraction import extract_features


BASE_DIR = Path(__file__).resolve().parent
URL_DATASET_PATH = BASE_DIR / "url_dataset.csv"
EMAIL_DATASET_PATH = BASE_DIR / "email_dataset.csv"
SMS_DATASET_PATH = BASE_DIR / "sms_dataset.csv"
QR_DATASET_PATH = BASE_DIR / "qr_dataset.csv"
LEGACY_DATASET_PATH = BASE_DIR / "phishing_dataset.csv"
MODEL_PATH = BASE_DIR / "model.pkl"


def load_datasets():
    dataset_files = {
        "url": URL_DATASET_PATH,
        "email": EMAIL_DATASET_PATH,
        "sms": SMS_DATASET_PATH,
        "qr": QR_DATASET_PATH,
    }
    rows = []

    for scan_type, path in dataset_files.items():
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "content" not in df.columns or "label" not in df.columns:
            raise ValueError(f"{path.name} must contain 'content' and 'label' columns.")
        df = df.dropna(subset=["content", "label"])
        for _, row in df.iterrows():
            rows.append((str(row["content"]), scan_type, int(row["label"])))
        print(f"Loaded {len(df)} rows from {path.name}")

    if not rows and LEGACY_DATASET_PATH.exists():
        df = pd.read_csv(LEGACY_DATASET_PATH)
        if "url" in df.columns and "label" in df.columns:
            df = df.dropna(subset=["url", "label"])
            for _, row in df.iterrows():
                rows.append((str(row["url"]), "url", int(row["label"])))
            print(f"Loaded {len(df)} rows from {LEGACY_DATASET_PATH.name}")

    if not rows:
        raise FileNotFoundError(
            "No training datasets found. Add url_dataset.csv, email_dataset.csv, sms_dataset.csv, or qr_dataset.csv in ml_model/."
        )
    return rows


def train():
    dataset = load_datasets()
    x = np.array([extract_features(content, scan_type) for content, scan_type, _ in dataset])
    y = np.array([label for _, _, label in dataset])

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y,
    )

    model = RandomForestClassifier(
        n_estimators=220,
        max_depth=12,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
    )
    model.fit(x_train, y_train)

    predictions = model.predict(x_test)
    print("\nTraining completed")
    print("------------------")
    print("Accuracy:", accuracy_score(y_test, predictions))
    print("Precision:", precision_score(y_test, predictions, zero_division=0))
    print("Recall:", recall_score(y_test, predictions, zero_division=0))
    print("F1 Score:", f1_score(y_test, predictions, zero_division=0))
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions))
    print("\nClassification Report:")
    print(classification_report(
        y_test,
        predictions,
        target_names=["Legitimate", "Phishing"],
        zero_division=0,
    ))

    joblib.dump(
        {
            "model": model,
            "feature_count": x.shape[1],
            "scan_types": ["url", "email", "sms", "qr"],
        },
        MODEL_PATH,
    )
    print(f"\nModel saved to: {MODEL_PATH}")


if __name__ == "__main__":
    train()
