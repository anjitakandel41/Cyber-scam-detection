# ML Model Datasets

This directory contains training data and model code for phishing detection.

## Dataset files
- `url_dataset.csv` - URL examples labeled for phishing detection.
- `email_dataset.csv` - Email text examples labeled for phishing detection.
- `sms_dataset.csv` - SMS text examples labeled for phishing detection.
- `qr_dataset.csv` - QR code payload examples labeled for phishing detection.
- `phishing_dataset.csv` - Legacy URL-only dataset maintained for backward compatibility.

## How it works
- `scanner/ml/phishing_detector.py` trains and loads the model using `load_datasets()` from `ml_model/train.py`.
- `ml_model/train.py` reads all available dataset CSV files and merges them into a single training set.
- Each dataset must include `content` and `label` columns.

## To retrain
Run the Django management command:

```bash
python manage.py train_phishing_model
```

Or run training directly:

```bash
python ml_model/train.py
```

## Improving accuracy
- Add more real-world samples to the CSV files.
- For each scan type, keep both legitimate (`label=0`) and phishing (`label=1`) examples.
- Use more varied content patterns, including sender names, subject lines, URLs, and SMS phrasing.
