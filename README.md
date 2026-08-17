# 🛡️ Cyber Scam and Phishing Detection System

A Django-based **Cyber Scam and Phishing Detection System** that detects and analyzes potentially malicious **URLs, emails, SMS messages, QR codes, and Gmail spam messages** using a hybrid approach combining **Machine Learning, Rule-Based Detection, Threat Intelligence, and Explainable AI (SHAP & LIME)**.

---

## 📌 Project Overview

Cyber scams and phishing attacks are increasingly used to steal sensitive information such as passwords, OTPs, banking credentials, personal information, and financial data.

This project provides a centralized web-based platform for detecting suspicious content before users interact with it.

The system uses a **Hybrid Phishing Detection Framework** that combines:

* 🤖 Machine Learning
* 🔍 Rule-Based Detection
* 🌐 Threat Intelligence
* 🧠 Explainable AI
* 📊 Risk Scoring
* 📄 PDF Reporting
* 📧 High-Risk Email Alerts
* 📜 Scan History

The Machine Learning component uses a **Random Forest Classifier** to estimate phishing/scam probability. Rule-based security checks provide deterministic evidence, while external threat intelligence services provide additional real-world security information.

**SHAP and LIME are used only for explaining the Machine Learning prediction and do not modify the final risk score.**

---

# 🎯 Objectives

The main objectives of the project are:

1. Detect phishing and scam URLs.
2. Detect phishing emails.
3. Detect SMS-based scams.
4. Analyze QR codes for potentially malicious content.
5. Scan Gmail messages for spam/phishing indicators.
6. Extract meaningful security features from user input.
7. Use Machine Learning to predict phishing probability.
8. Apply rule-based security checks.
9. Integrate external threat intelligence.
10. Generate explainable predictions using SHAP and LIME.
11. Calculate a final hybrid risk score.
12. Store scan results and history.
13. Generate downloadable PDF security reports.
14. Send alerts for high-risk scans.
15. Improve user awareness about phishing and online scams.

---

# 🏗️ System Architecture

The overall system follows this architecture:

```text
                    ┌──────────────────────┐
                    │        User          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Django Web Interface │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Scanner Selection  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
           URL Scan         Email Scan       SMS Scan
              │                │                │
              └────────────────┼────────────────┘
                               │
                         QR / Gmail Scan
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Input Validation &   │
                    │ QR Decoding          │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Feature Extraction   │
                    └──────────┬───────────┘
                               │
                 ┌─────────────┼─────────────┐
                 │             │             │
                 ▼             ▼             ▼
          Random Forest    Rule Engine   Threat Intel
             Model             │             │
                 │             │             │
                 ▼             ▼             ▼
             ML Score      Rule Score   External Score
                 │             │             │
                 └─────────────┼─────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Hybrid Risk Scoring  │
                    └──────────┬───────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │ Risk Classification  │
                    └──────────┬───────────┘
                               │
                ┌──────────────┼──────────────┐
                │              │              │
                ▼              ▼              ▼
             SHAP             LIME       Rule Evidence
                │              │              │
                └──────────────┼──────────────┘
                               │
                               ▼
                    ┌──────────────────────┐
                    │   Result Dashboard   │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ▼                ▼                ▼
         PDF Report       Scan History    High-Risk Alert
```

---

# 🔄 Complete System Workflow

## 1. User Authentication

The user registers or logs into the Django application.

The system provides:

* User registration
* Secure login
* Session management
* User dashboard
* User-specific scan history

After authentication, the user can select the required scanner.

---

## 2. Scanner Selection

The system supports multiple scanning modules:

* URL Scanner
* Email Scanner
* SMS Scanner
* QR Code Scanner
* Gmail Spam Scanner

---

## 3. User Input

### URL Scanner

The user enters a URL such as:

```text
https://example.com/login
```

The system extracts URL-based security features and performs phishing analysis.

### Email Scanner

The user provides:

* Sender
* Subject
* Email body

The system analyzes the email content for phishing indicators.

### SMS Scanner

The user provides:

* Phone number
* SMS message

The system analyzes the message for scam indicators.

### QR Scanner

The user uploads a QR code image.

The system first decodes the QR code and determines what type of content it contains.

### Gmail Scanner

The system can retrieve selected Gmail messages through Gmail integration and analyze them for spam/phishing indicators.

---

# 📷 QR Code Detection

The QR scanner first decodes the uploaded QR image.

A QR code may contain:

* URL
* Email address
* SMS
* Wi-Fi information
* Contact card
* Payment information
* Product information
* Plain text

If the decoded content contains a URL, email, or SMS, it is passed to the corresponding detection workflow.

```text
QR Image
   ↓
QR Decoding
   ↓
Extract Content
   ↓
Identify Content Type
   ↓
URL / Email / SMS / Text
   ↓
Normal Detection Pipeline
```

---

# 🧮 Feature Extraction

The system extracts **25 features** from the input.

| #  | Feature                        | Description                                    |
| -- | ------------------------------ | ---------------------------------------------- |
| 1  | `text_length`                  | Length of the input text                       |
| 2  | `suspicious_word_count`        | Number of suspicious/phishing-related words    |
| 3  | `url_count`                    | Number of URLs detected                        |
| 4  | `has_at`                       | Detects `@` symbol                             |
| 5  | `has_hyphen`                   | Detects hyphen usage                           |
| 6  | `is_shortener`                 | Detects URL shortening services                |
| 7  | `has_ip`                       | Detects IP address-based URLs                  |
| 8  | `is_http`                      | Detects insecure HTTP connections              |
| 9  | `is_url`                       | Identifies URL input                           |
| 10 | `is_email`                     | Identifies email input                         |
| 11 | `is_sms`                       | Identifies SMS input                           |
| 12 | `is_qr`                        | Identifies QR-based input                      |
| 13 | `money_reward`                 | Detects money/reward-related language          |
| 14 | `urgency`                      | Detects urgent or threatening language         |
| 15 | `sensitive_data_request`       | Detects requests for sensitive information     |
| 16 | `many_subdomains`              | Detects excessive subdomains                   |
| 17 | `domain_length`                | Measures domain length                         |
| 18 | `path_depth`                   | Measures URL path depth                        |
| 19 | `query_param_count`            | Counts URL query parameters                    |
| 20 | `percent_encoding`             | Detects percent-encoded content                |
| 21 | `brand_impersonation_mismatch` | Detects possible brand impersonation           |
| 22 | `high_digit_ratio`             | Detects unusually high numeric content         |
| 23 | `high_entropy`                 | Detects potentially obfuscated/random content  |
| 24 | `risky_file_extension`         | Detects suspicious file extensions             |
| 25 | `legitimate_mail_markers`      | Detects indicators of legitimate email content |

These features are used by the Random Forest model to estimate phishing/scam probability.

---

# 🤖 Machine Learning

The project uses a **Random Forest Classifier** for Machine Learning-based detection.

```text
Input
  ↓
Feature Extraction
  ↓
25 Features
  ↓
Random Forest Classifier
  ↓
Phishing Probability
  ↓
ML Score
```

The model produces a phishing/malicious probability which is converted into the ML score.

The trained model is serialized and stored for use during prediction.

Example:

```text
model.pkl
```

---

# 🌲 Why Random Forest?

Random Forest was selected because:

* It works well with structured/tabular data.
* It can handle nonlinear relationships.
* It combines multiple decision trees.
* It is relatively robust to noisy features.
* It provides feature importance information.
* It performs well without requiring excessive preprocessing.
* It is suitable for a hybrid security detection system.

Random Forest is also well suited for SHAP TreeExplainer, which makes it useful for Explainable AI.

---

# 🔍 Rule-Based Detection

Machine Learning is combined with deterministic security rules.

The rule engine checks indicators such as:

* IP address instead of domain
* URL shortener
* HTTP instead of HTTPS
* Suspicious phishing words
* Urgent language
* Sensitive information requests
* Money/reward language
* Risky file extensions
* Brand impersonation
* Excessive subdomains
* Generic emails pretending to be official organizations

The rule engine generates:

```text
Rule Score
+
Human-readable security explanations
```

Example explanations:

```text
Urgent language detected.
URL shortener detected.
Sensitive information request detected.
Possible brand impersonation detected.
```

---

# 🌐 Threat Intelligence

For URL analysis, the system can use external threat intelligence sources.

## VirusTotal

VirusTotal is used to check URLs/domains against multiple security engines and threat intelligence sources.

It provides additional evidence about whether a URL may be malicious.

## Google Safe Browsing

Google Safe Browsing helps identify URLs associated with:

* Phishing
* Malware
* Social engineering
* Dangerous websites

## WHOIS

WHOIS/domain information is used to obtain domain-related information such as domain registration details and domain age.

A newly registered or suspicious domain can contribute additional risk evidence.

---

# 🧠 Hybrid Detection Engine

The project does not rely only on Machine Learning.

Instead, it combines:

```text
Machine Learning
       +
Rule-Based Detection
       +
Threat Intelligence
       ↓
Hybrid Risk Score
```

This approach helps improve detection by combining statistical predictions with deterministic security evidence and external intelligence.

---

# 📊 Hybrid Risk Score

The system uses the following hybrid scoring approach:

```python
external_score = max(
    virustotal,
    safe_browsing,
    round(whois * 0.75)
)

if safe_browsing >= 100 or virustotal >= 80:
    risk = max(85, external_score)
else:
    risk = round(
        ml * 0.35 +
        rule * 0.45 +
        external * 0.20
    )

risk = clamp(risk, 0, 100)
```

### Weight Distribution

| Component                    | Weight |
| ---------------------------- | -----: |
| Machine Learning             |    35% |
| Rule-Based Detection         |    45% |
| External Threat Intelligence |    20% |

The rule engine receives the highest weight because deterministic security indicators provide strong direct evidence of suspicious behavior.

External threat intelligence can override the normal weighted calculation when strong malicious evidence is detected.

---

# 🚦 Risk Classification

The final risk score is classified into three categories:

| Risk Score | Classification |
| ---------: | -------------- |
|       0–39 | 🟢 Low Risk    |
|      40–69 | 🟡 Medium Risk |
|     70–100 | 🔴 High Risk   |

### Low Risk

The input contains few or no significant indicators of malicious activity.

### Medium Risk

The input contains suspicious characteristics and should be handled carefully.

### High Risk

The input contains strong phishing/scam/malicious indicators.

Users should avoid interacting with the content.

---

# 🧠 Explainable AI

The project uses **SHAP and LIME** to explain the Machine Learning prediction.

Important:

> SHAP and LIME explain the Machine Learning prediction only. They do not change the final hybrid risk score.

---

# 📈 SHAP

SHAP stands for **SHapley Additive exPlanations**.

For the Random Forest model, the project uses TreeExplainer where applicable.

SHAP identifies which features contributed toward increasing or decreasing the model's phishing probability.

Example:

```text
Feature                         Contribution

URL shortener                  ↑ Risk
Urgency                        ↑ Risk
Sensitive data request         ↑ Risk
Suspicious word count          ↑ Risk
Legitimate mail markers        ↓ Risk
```

### Why SHAP?

SHAP is useful because:

* It provides feature-level explanations.
* It can show positive and negative contributions.
* It works efficiently with tree-based models.
* It helps understand Random Forest predictions.
* It improves model transparency.

---

# 🔬 LIME

LIME stands for **Local Interpretable Model-agnostic Explanations**.

LIME explains an individual prediction by creating a local approximation of the model around the specific input.

For example:

```text
Input:
"Your account is suspended. Verify your password immediately."

LIME Explanation:

Sensitive data request      → Increased risk
Urgency                     → Increased risk
Suspicious words            → Increased risk
```

### Why LIME?

LIME is useful because:

* It explains individual predictions.
* It is model-agnostic.
* It provides local explanations.
* It helps users understand why a particular input was classified as suspicious.

---

# ⚖️ SHAP vs LIME

| Feature          | SHAP                                | LIME                                            |
| ---------------- | ----------------------------------- | ----------------------------------------------- |
| Full Form        | SHapley Additive exPlanations       | Local Interpretable Model-agnostic Explanations |
| Explanation      | Feature contribution                | Local feature importance                        |
| Scope            | Can provide local/global analysis   | Mainly local                                    |
| Model Dependency | Model-specific explainers available | Model-agnostic                                  |
| Random Forest    | Highly suitable                     | Suitable                                        |
| Explanation Type | Contribution toward prediction      | Local approximation                             |
| Main Purpose     | Understand feature contribution     | Explain individual prediction                   |

Using both methods provides complementary explanations.

---

# 🔐 Explainable Detection Flow

```text
Input
  ↓
Feature Extraction
  ↓
Random Forest
  ↓
ML Prediction
  ↓
 ┌───────────────┬───────────────┐
 │               │               │
 ▼               ▼               ▼
SHAP            LIME        Rule Engine
 │               │               │
 └───────────────┼───────────────┘
                 ↓
        Human-readable Explanation
```

---

# 📋 Result Display

After scanning, the system displays:

* Final Risk Score
* Risk Classification
* Confidence Score
* Detection Reasons
* Recommendation
* SHAP Analysis
* LIME Analysis
* Rule-Based Evidence
* External Threat Intelligence
* SHAP vs LIME Comparison
* PDF Report Download

Example:

```text
Risk Score: 86/100

Classification: HIGH RISK

Reasons:
✓ Urgent language detected
✓ Suspicious URL detected
✓ Sensitive information requested
✓ URL shortener detected

Recommendation:
Do not click the link or provide personal information.
```

---

# 🗄️ Database Storage

Each scan is stored in the database using the `ScanResult` model.

Stored information includes:

* User
* Input content
* Risk score
* Classification
* Explanation JSON
* Recommendation
* PDF report
* Timestamp

Example explanation structure:

```json
{
    "summary": [],
    "shap": {},
    "lime": {},
    "rules": [],
    "external": {},
    "comparison": [],
    "statement": "SHAP and LIME explain the ML prediction only."
}
```

This structure allows the system to preserve detailed detection evidence for future review.

---

# 📄 PDF Report Generation

The system generates a downloadable PDF security report.

The report contains:

* User information
* Scanned input
* Risk score
* Risk classification
* Detection explanation
* SHAP analysis
* LIME analysis
* SHAP vs LIME comparison
* Rule-based evidence
* External threat intelligence
* Security recommendation

The PDF allows users to keep a permanent record of scan results.

---

# 📧 High-Risk Email Alerts

If the final risk score is **70 or above**, the system considers the input high risk.

The system can:

1. Create a high-risk alert.
2. Send an email notification.
3. Attach the generated PDF report when available.
4. Store the scan in the user's history.

```text
Final Risk Score
       ↓
   Score >= 70?
       ↓
      YES
       ↓
High-Risk Alert
       ↓
Email Notification
       ↓
PDF Report Attachment
```

---

# 📜 Scan History

Users can view their previous scans through the dashboard.

The history includes:

* Scan type
* Input
* Risk score
* Classification
* Date/time
* Explanation
* PDF report

This allows users to track previously detected threats.

---

# 📧 Gmail Spam Scanner

The Gmail scanner allows the system to retrieve and analyze Gmail messages.

The workflow is:

```text
Gmail Account
     ↓
Gmail API
     ↓
Retrieve Selected Email
     ↓
Extract Sender / Subject / Body
     ↓
Feature Extraction
     ↓
ML + Rules + Threat Intelligence
     ↓
Risk Score
     ↓
Result + Explanation
```

The Gmail module helps users analyze potentially suspicious messages without manually copying the complete email content.

---

# 🧩 Main Modules

## 1. User Authentication

Handles:

* Registration
* Login
* Logout
* Session management
* User-specific data

## 2. Dashboard

Provides:

* Scan statistics
* Recent scans
* Risk distribution
* Scan history
* Quick access to scanners

## 3. URL Scanner

Analyzes URLs using:

* URL features
* Random Forest
* Rule-based detection
* VirusTotal
* Google Safe Browsing
* WHOIS

## 4. Email Scanner

Analyzes:

* Sender
* Subject
* Email body
* Suspicious words
* Urgency
* Sensitive information requests
* URLs
* Attachments/file extensions

## 5. SMS Scanner

Analyzes:

* Message content
* Suspicious words
* Urgency
* Money/reward language
* Sensitive data requests
* URLs

## 6. QR Scanner

Decodes QR images and analyzes their content.

## 7. Gmail Scanner

Retrieves and analyzes Gmail messages.

## 8. Hybrid Detection Engine

Combines:

* ML
* Rules
* External threat intelligence

## 9. Explainable AI

Provides:

* SHAP explanation
* LIME explanation
* Rule-based explanation

## 10. Reporting System

Generates PDF security reports.

## 11. Alert System

Sends high-risk notifications.

## 12. Scan History

Stores and displays previous scan results.

---

# 🛠️ Technology Stack

## Frontend

* HTML5
* CSS3
* JavaScript
* Bootstrap
* Chart.js

## Backend

* Python
* Django

## Database

* SQLite
* Django ORM

## Machine Learning

* Scikit-learn
* Random Forest
* Pandas
* NumPy
* Joblib

## Explainable AI

* SHAP
* LIME

## Natural Language Processing

* NLTK
* spaCy

## QR Processing

* OpenCV
* pyzbar

## Threat Intelligence

* VirusTotal API
* Google Safe Browsing API
* WHOIS

## Email Integration

* Gmail API
* Google OAuth

## Reporting

* PDF generation library

## Development Tools

* Git
* GitHub
* Visual Studio Code
* Python Virtual Environment

---

# 📁 Suggested Project Structure

```text
cyber-scam-detection/
│
├── manage.py
├── requirements.txt
├── README.md
├── db.sqlite3
│
├── project/
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
│
├── scanner/
│   ├── models.py
│   ├── views.py
│   ├── urls.py
│   ├── forms.py
│   ├── admin.py
│   ├── utils.py
│   ├── ml/
│   │   └── model.pkl
│   ├── templates/
│   └── static/
│
├── dashboard/
│   ├── views.py
│   ├── urls.py
│   └── templates/
│
├── authentication/
│   ├── views.py
│   ├── forms.py
│   └── templates/
│
├── reports/
│   └── pdf_generator.py
│
├── chatbot/
│   └── ...
│
├── quiz/
│   └── ...
│
└── media/
    └── reports/
```

> The exact directory structure may differ depending on the final implementation.

---

# ⚙️ Installation

## 1. Clone the Repository

```bash
git clone https://github.com/yourusername/cyber-scam-detection.git
cd cyber-scam-detection
```

Replace `yourusername/cyber-scam-detection` with your actual GitHub repository path.

---

## 2. Create a Virtual Environment

### Windows

```bash
python -m venv venv
```

Activate it:

```bash
venv\Scripts\activate
```

### Linux/macOS

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4. Configure Environment Variables

Create a `.env` file in the project root.

Example:

```env
SECRET_KEY=your_django_secret_key
DEBUG=True

VIRUSTOTAL_API_KEY=your_virustotal_api_key
GOOGLE_SAFE_BROWSING_API_KEY=your_google_safe_browsing_api_key

EMAIL_HOST_USER=your_email@example.com
EMAIL_HOST_PASSWORD=your_email_password

GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret
```

Never upload real API keys, passwords, OAuth credentials, or secret keys to GitHub.

Add the following to `.gitignore`:

```gitignore
.env
venv/
__pycache__/
*.pyc
db.sqlite3
media/
credentials.json
token.json
```

---

# 🗃️ Database Setup

Run migrations:

```bash
python manage.py makemigrations
python manage.py migrate
```

Create an administrator account:

```bash
python manage.py createsuperuser
```

---

# 🚀 Run the Project

Start the Django development server:

```bash
python manage.py runserver
```

Open the application in your browser:

```text
http://127.0.0.1:8000/
```

---

# 🧪 Machine Learning Model

The project uses a trained Random Forest model.

The general training workflow is:

```text
Dataset
   ↓
Data Cleaning
   ↓
Feature Extraction
   ↓
Train/Test Split
   ↓
Random Forest Training
   ↓
Model Evaluation
   ↓
Model Serialization
   ↓
model.pkl
```

The trained model is loaded by the Django application during prediction.

---

# 📊 Model Evaluation

The Machine Learning model can be evaluated using:

### Accuracy

Measures the proportion of all correctly classified samples.

```text
Accuracy = (TP + TN) / (TP + TN + FP + FN)
```

### Precision

Measures how many predicted phishing samples were actually phishing.

```text
Precision = TP / (TP + FP)
```

### Recall

Measures how many actual phishing samples were correctly detected.

```text
Recall = TP / (TP + FN)
```

### F1-Score

The harmonic mean of precision and recall.

```text
F1 = 2 × (Precision × Recall) / (Precision + Recall)
```

---

# 🔒 Security Considerations

The system follows several security practices:

* Django authentication
* Session-based access control
* Environment variables for API credentials
* User-specific scan history
* Input validation
* Secure API key handling
* Role-based access where implemented
* Avoiding storage of unnecessary sensitive information
* Protection of secret credentials using `.env`

---

# ⚠️ Limitations

The system has some limitations:

1. Machine Learning performance depends on the quality and diversity of training data.
2. Synthetic training data may not represent every real-world phishing pattern.
3. External APIs may have rate limits.
4. VirusTotal and Google Safe Browsing require API access and may have usage restrictions.
5. WHOIS information may not always be available or accurate.
6. New phishing websites may not yet appear in threat intelligence databases.
7. QR decoding depends on image quality and supported QR formats.
8. Gmail scanning requires appropriate Google OAuth permissions.
9. Attackers can continuously change phishing techniques.
10. No automated detection system can guarantee 100% accuracy.

Therefore, the system should be considered a **security assistance tool**, not an absolute replacement for human security judgment.

---

# 🚀 Future Enhancements

Potential future improvements include:

* Deep Learning-based phishing detection
* Transformer-based NLP models
* Real-time browser extension
* Mobile application
* Advanced QR phishing detection
* More comprehensive Gmail monitoring
* More threat intelligence providers
* Real-time URL reputation monitoring
* Automated model retraining
* Larger real-world datasets
* Multilingual phishing detection
* Advanced behavioral analysis
* Improved phishing website screenshot analysis
* Federated learning
* Continuous threat intelligence updates
* Advanced user awareness training

---

# 🧪 Testing

The system should be tested using:

### Functional Testing

* Registration
* Login
* URL scanning
* Email scanning
* SMS scanning
* QR scanning
* Gmail scanning
* Scan history
* PDF generation
* Email alerts

### Machine Learning Testing

* Accuracy
* Precision
* Recall
* F1-score
* Confusion matrix
* False positives
* False negatives

### Security Testing

* Invalid URL handling
* Malicious input handling
* Authentication testing
* Authorization testing
* API key protection
* CSRF protection
* Session security
* Input validation

---

# 📚 Example Detection Scenarios

## Scenario 1: Suspicious URL

Input:

```text
http://192.168.1.10/login?verify=account
```

Possible indicators:

```text
✓ IP address detected
✓ HTTP connection
✓ Login-related suspicious path
✓ Sensitive account verification
```

Result:

```text
High Risk
```

---

## Scenario 2: Phishing Email

Example:

```text
Your account has been suspended.
Verify your password immediately to restore access.
```

Possible indicators:

```text
✓ Urgent language
✓ Account threat
✓ Sensitive information request
```

Result:

```text
High Risk
```

---

## Scenario 3: Scam SMS

Example:

```text
Congratulations! You have won a cash reward.
Click the link immediately to claim your prize.
```

Possible indicators:

```text
✓ Money/reward language
✓ Urgency
✓ Suspicious URL
```

Result:

```text
High Risk
```

---



# 🌟 Key Features

| Feature                 | Status |
| ----------------------- | ------ |
| User Authentication     | ✅      |
| User Dashboard          | ✅      |
| URL Scanner             | ✅      |
| Email Scanner           | ✅      |
| SMS Scanner             | ✅      |
| QR Scanner              | ✅      |
| Gmail Scanner           | ✅      |
| Random Forest Detection | ✅      |
| Feature Extraction      | ✅      |
| Rule-Based Detection    | ✅      |
| VirusTotal Integration  | ✅      |
| Google Safe Browsing    | ✅      |
| WHOIS Analysis          | ✅      |
| Hybrid Risk Scoring     | ✅      |
| SHAP Explainability     | ✅      |
| LIME Explainability     | ✅      |
| Scan History            | ✅      |
| PDF Reports             | ✅      |
| High-Risk Alerts        | ✅      |

---

# 📈 Detection Philosophy

The system follows a defense-in-depth approach:

```text
              USER INPUT
                  │
                  ▼
          Input Validation
                  │
                  ▼
          Feature Extraction
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
       ML       Rules    Threat Intel
        │         │         │
        ▼         ▼         ▼
     ML Score  Rule Score  External Score
        │         │         │
        └─────────┼─────────┘
                  ▼
          Hybrid Risk Score
                  │
                  ▼
          Risk Classification
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
      SHAP      LIME     Rule Evidence
        │         │         │
        └─────────┼─────────┘
                  ▼
         Explainable Result
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
       PDF      History    Alert
```

---

# 🤝 Contribution

Contributions are welcome.

To contribute:

```bash
git clone https://github.com/yourusername/cyber-scam-detection.git
```

Create a new branch:

```bash
git checkout -b feature/new-feature
```

Make your changes and commit:

```bash
git add .
git commit -m "Add new feature"
```

Push the branch:

```bash
git push origin feature/new-feature
```

Then create a Pull Request.

---

# 📜 License

This project is developed for **academic and educational purposes**.

If you reuse or modify this project, please provide appropriate attribution to the original project.

---

# ⚠️ Disclaimer

This system is intended for **educational, research, and security-awareness purposes**.

Detection results are probabilistic and should not be considered a guarantee that a website, email, SMS, QR code, or message is completely safe or malicious.

Users should always exercise caution when interacting with unknown links, attachments, messages, and requests for sensitive information.

---

# 👩‍💻 Project Information

**Project Title:**
Cyber Scam and Phishing Detection System using Django, Machine Learning, Rule-Based Detection, Threat Intelligence, SHAP, and LIME

**Framework:** Django

**Machine Learning:** Random Forest

**Explainable AI:** SHAP & LIME

**Threat Intelligence:** VirusTotal, Google Safe Browsing, WHOIS

**Database:** SQLite / Django ORM

**Frontend:** HTML, CSS, JavaScript, Bootstrap

**Project Type:** Academic / Final Year Project

---

# ⭐ Acknowledgement

This project combines concepts from:

* Web Application Development
* Cybersecurity
* Machine Learning
* Natural Language Processing
* Threat Intelligence
* Explainable Artificial Intelligence
* Database Management
* Software Engineering

The objective is to demonstrate how these technologies can be integrated into a practical cybersecurity application for detecting and explaining potential phishing and scam threats.

---

## 🔑 Keywords

```text
Cybersecurity
Phishing Detection
Scam Detection
Django
Python
Machine Learning
Random Forest
Explainable AI
SHAP
LIME
Threat Intelligence
VirusTotal
Google Safe Browsing
WHOIS
URL Detection
Email Detection
SMS Scam Detection
QR Code Security
Gmail Security
Risk Scoring
Hybrid Detection
Cyber Threat Detection
```
