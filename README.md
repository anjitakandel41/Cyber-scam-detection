Cyber Scam Awareness and Detection System

A Django-based web application for detecting and analyzing potential cyber scams and phishing attempts. The system combines Machine Learning, rule-based analysis, threat intelligence, Gmail integration, QR-code decoding, cybersecurity awareness features, and an AI chatbot.

Features

User registration and authentication

User dashboard and analytics

URL, Email, SMS, Gmail, and QR scanning

Random Forest Machine Learning detection

Rule-based security analysis

Google Safe Browsing and VirusTotal integration

WHOIS/domain information

Risk score and Low/Medium/High classification

Scan history and PDF reports

High-risk alerts

Cybersecurity awareness quiz

Llama-based cybersecurity chatbot through Hugging Face

Technology Stack

Backend: Python, Django
Frontend: HTML5, CSS3, Bootstrap, JavaScript, Chart.js
Database: SQLite
ML: pandas, NumPy, scikit-learn, Random Forest, joblib
QR: OpenCV, pyzbar
External services: Google OAuth, Gmail API, Google Safe Browsing API, VirusTotal, WHOIS
AI: Meta Llama through Hugging Face Inference API
Reports: ReportLab
Version control: Git/GitHub

System Workflow

User
 ↓
Authentication
 ↓
Dashboard
 ↓
URL / Email / SMS / Gmail / QR Scanner
 ↓
Input Validation
 ↓
Feature Extraction
 ↓
Rule-Based Analysis
 ↓
Random Forest Prediction
 ↓
Threat Intelligence Checks
(Google Safe Browsing / VirusTotal / WHOIS)
 ↓
Risk Assessment
 ↓
Low / Medium / High Risk
 ↓
Database + PDF Report + Alerts

Machine Learning

The project uses a Random Forest Classifier. The model is trained using a labeled dataset, evaluated on a held-out test set, and saved as model.pkl using Joblib.

Training:

Dataset
 ↓
Preprocessing
 ↓
Feature Extraction
 ↓
80:20 Train/Test Split
 ↓
Random Forest Training
 ↓
Accuracy / Precision / Recall / F1
 ↓
model.pkl

Prediction:

New Input
 ↓
Feature Extraction
 ↓
Load model.pkl
 ↓
Prediction
 ↓
Risk Assessment

The training dataset is not required every time a user performs a scan; the trained model.pkl is loaded for prediction.

Gmail Scanning

Gmail scanning uses Google OAuth and Gmail API.

Continue with Google
 ↓
OAuth Authorization
 ↓
Gmail API
 ↓
Retrieve permitted messages
 ↓
User selects an email
 ↓
Extract Sender / Subject / Body
 ↓
Scan Content
 ↓
Risk Result

The application should request only the permissions required by the implementation and should never request the user's Google password.

If Spam scanning is implemented, the Gmail API request must explicitly target the Spam label; Gmail access does not automatically mean every folder is scanned.

QR Scanning

Upload QR Image
 ↓
OpenCV / pyzbar
 ↓
Decode QR Content
 ↓
Identify Content Type
 ↓
Route to Appropriate Scanner
 ↓
Detection Engine
 ↓
Result

Chatbot

The chatbot is separate from the Random Forest phishing classifier.

User Question
 ↓
Django Chatbot
 ↓
Hugging Face Inference API
 ↓
Llama
 ↓
Generated Cybersecurity Response

Random Forest is used for classification; Llama is used for natural-language assistance.

Environment Configuration

Create a .env file in the project root. Use .env.example as a template.

Example:

DEBUG=True
SECRET_KEY=replace-with-a-long-random-secret-key
ALLOWED_HOSTS=127.0.0.1,localhost

GOOGLE_CLIENT_ID=your-google-oauth-client-id
GOOGLE_CLIENT_SECRET=your-google-oauth-client-secret

VIRUSTOTAL_API_KEY=your-virustotal-api-key
GOOGLE_SAFE_BROWSING_API_KEY=your-google-safe-browsing-api-key

HUGGINGFACE_API_TOKEN=your-huggingface-api-token
LLAMA_MODEL=meta-llama/Llama-3-1b-chat-hf

Use the exact variable names already expected by your settings.py and service modules.

Installation

1. Clone

git clone <your-repository-url>
cd Cyber-scam-detection

2. Create environment

python -m venv .venv

Windows:

.venv\Scripts\activate

If using uv:

uv sync

3. Install dependencies

pip install -r requirements.txt

or, with uv:

uv pip install -r requirements.txt

4. Configure .env

Copy .env.example to .env and replace the placeholder values with real credentials.

5. Migrate database

python manage.py migrate

6. Create admin

python manage.py createsuperuser

7. Run

python manage.py runserver

Open http://127.0.0.1:8000/.

API Setup

Google OAuth / Gmail

Configure a Google Cloud project.

Enable Gmail API.

Configure the OAuth consent screen.

Create OAuth credentials.

Configure the authorized redirect URI used by your Django/Allauth setup.

Put the client ID and secret in .env.

VirusTotal

VIRUSTOTAL_API_KEY=your-key

Google Safe Browsing

GOOGLE_SAFE_BROWSING_API_KEY=your-key

Hugging Face

HUGGINGFACE_API_TOKEN=your-token
LLAMA_MODEL=meta-llama/Llama-3-1b-chat-hf

Project Structure

Cyber-scam-detection/
├── manage.py
├── .env
├── .env.example
├── .gitignore
├── README.md
├── requirements.txt
├── config/
├── scanner/
│   ├── views.py
│   ├── models.py
│   ├── forms.py
│   ├── gmail_service.py
│   ├── gmail_reader.py
│   ├── qr_decoder.py
│   ├── report_generator.py
│   └── ml/
├── ml_model/
│   ├── train.py
│   ├── phishing_dataset.csv
│   └── model.pkl
├── chatbot/
├── dashboard/
├── quiz/
├── reports/
├── alerts/
├── templates/
├── static/
└── media/

The exact structure may differ in your current repository.

Security

Never commit real secrets:

.env
GOOGLE_CLIENT_SECRET
VIRUSTOTAL_API_KEY
GOOGLE_SAFE_BROWSING_API_KEY
HUGGINGFACE_API_TOKEN
DJANGO SECRET_KEY

Use .gitignore:

.env
.venv/
__pycache__/
*.pyc
db.sqlite3
media/

For production, use DEBUG=False, HTTPS, secure cookies, a strong secret key, restricted ALLOWED_HOSTS, and production-grade database/deployment settings.

Testing and Evaluation

The ML component should be evaluated using:

Accuracy

Precision

Recall

F1-score

Confusion Matrix

Classification Report

Other testing should cover authentication, scanners, Gmail integration, QR decoding, APIs, PDF generation, alerts, and responsive UI.

Disclaimer

This is an academic cybersecurity detection and awareness system. A detection result is not a guarantee that an item is completely safe or malicious.

Contributors

Add project team members and supervisor information here.