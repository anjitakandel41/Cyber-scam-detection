from pathlib import Path
from xml.sax.saxutils import escape

from django.conf import settings
from django.utils import timezone
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def _paragraph(text, style):
    return Paragraph(escape(str(text)).replace('\n', '<br/>'), style)


def _risk_color(classification):
    if classification == 'High Risk':
        return colors.HexColor('#b91c1c')
    if classification == 'Medium Risk':
        return colors.HexColor('#ca8a04')
    return colors.HexColor('#0f766e')


def generate_scan_report(scan_result):
    reports_dir = Path(settings.MEDIA_ROOT) / 'reports'
    reports_dir.mkdir(parents=True, exist_ok=True)

    filename = f'scan_report_{scan_result.pk}_{timezone.now().strftime("%Y%m%d%H%M%S")}.pdf'
    file_path = reports_dir / filename
    relative_path = f'reports/{filename}'

    styles = getSampleStyleSheet()
    story = [
        Paragraph('Phishing Scan Report', styles['Title']),
        Spacer(1, 16),
    ]

    user = scan_result.user
    user_info = [
        ['Username', user.get_username()],
        ['Email', user.email or 'Not provided'],
        ['Role', getattr(user, 'role', 'User')],
        ['Generated', timezone.localtime(timezone.now()).strftime('%Y-%m-%d %H:%M')],
    ]
    user_table = Table(user_info, colWidths=[120, 360])
    user_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.extend([Paragraph('User Info', styles['Heading2']), user_table, Spacer(1, 14)])

    risk_table = Table([
        ['Risk Score', f'{scan_result.risk_score}%'],
        ['Classification', scan_result.classification],
        ['Scan Timestamp', timezone.localtime(scan_result.timestamp).strftime('%Y-%m-%d %H:%M')],
    ], colWidths=[120, 360])
    risk_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#f1f5f9')),
        ('TEXTCOLOR', (1, 0), (1, 1), _risk_color(scan_result.classification)),
        ('BOX', (0, 0), (-1, -1), 0.5, colors.HexColor('#cbd5e1')),
        ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.HexColor('#cbd5e1')),
        ('PADDING', (0, 0), (-1, -1), 8),
    ]))
    story.extend([Paragraph('Scan Result', styles['Heading2']), risk_table, Spacer(1, 14)])

    story.extend([
        Paragraph('Input', styles['Heading2']),
        _paragraph(scan_result.input, styles['BodyText']),
        Spacer(1, 14),
        Paragraph('Explanation', styles['Heading2']),
    ])
    explanation = scan_result.explanation or []
    for item in explanation:
        story.append(_paragraph(f'- {item}', styles['BodyText']))

    story.extend([
        Spacer(1, 14),
        Paragraph('Recommendation', styles['Heading2']),
        _paragraph(scan_result.recommendation, styles['BodyText']),
    ])

    document = SimpleDocTemplate(str(file_path), pagesize=letter, rightMargin=48, leftMargin=48, topMargin=48, bottomMargin=48)
    document.build(story)
    return relative_path
