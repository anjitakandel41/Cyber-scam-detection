from django.shortcuts import render
from django.utils import timezone

from alerts.models import Alert
from chatbot.models import ChatMessage
from quiz.models import Question, QuizAttempt
from scanner.models import ScanResult
from users.models import CustomUser
from users.decorators import admin_required, user_or_view_mode_required
from users.remember import get_display_user


def _last_seven_days():
    today = timezone.localdate()
    return [today - timezone.timedelta(days=offset) for offset in range(6, -1, -1)]


@admin_required
def admin_dashboard(request):
    days = _last_seven_days()
    labels = [day.strftime('%b %d') for day in days]
    registration_counts = [
        CustomUser.objects.filter(date_joined__date=day).count()
        for day in days
    ]
    scan_counts = [
        ScanResult.objects.filter(timestamp__date=day).count()
        for day in days
    ]
    admin_count = CustomUser.objects.filter(role=CustomUser.Role.ADMIN).count()
    user_count = CustomUser.objects.filter(role=CustomUser.Role.USER).count()
    high_risk_count = ScanResult.objects.filter(classification=ScanResult.Classification.HIGH).count()
    alert_count = Alert.objects.count()

    context = {
        'stats': [
            {'label': 'Total Users', 'value': CustomUser.objects.count(), 'note': 'Registered accounts'},
            {'label': 'Total Scans', 'value': ScanResult.objects.count(), 'note': 'URL, email, SMS, and QR scans'},
            {'label': 'High Risk', 'value': high_risk_count, 'note': 'Scans requiring action'},
            {'label': 'Alerts Sent', 'value': alert_count, 'note': 'Email notifications stored'},
            {'label': 'Quiz Attempts', 'value': QuizAttempt.objects.count(), 'note': 'Awareness training activity'},
            {'label': 'Chat Messages', 'value': ChatMessage.objects.count(), 'note': 'Chatbot interactions'},
            {'label': 'Pending Verification', 'value': CustomUser.objects.filter(is_active=False).count(), 'note': 'Awaiting email verification'},
            {'label': 'Admins', 'value': admin_count, 'note': 'Admin role accounts'},
        ],
        'registration_chart': {
            'labels': labels,
            'values': registration_counts,
        },
        'scan_chart': {
            'labels': labels,
            'values': scan_counts,
        },
        'role_chart': {
            'labels': ['Admins', 'Users'],
            'values': [admin_count, user_count],
        },
        'risk_chart': {
            'labels': ['Low Risk', 'Medium Risk', 'High Risk'],
            'values': [
                ScanResult.objects.filter(classification=ScanResult.Classification.LOW).count(),
                ScanResult.objects.filter(classification=ScanResult.Classification.MEDIUM).count(),
                high_risk_count,
            ],
        },
    }
    return render(request, 'dashboard/admin_dashboard.html', context)


@user_or_view_mode_required
def user_dashboard(request):
    # In view mode this is the remembered user; otherwise it is request.user.
    display_user = get_display_user(request)

    user_scans = ScanResult.objects.filter(user=display_user)
    user_alerts = Alert.objects.filter(user=display_user)
    latest_attempt = QuizAttempt.objects.filter(user=display_user).first()
    quiz_progress = f'{latest_attempt.percentage}%' if latest_attempt else '0%'
    days = _last_seven_days()
    labels = [day.strftime('%b %d') for day in days]

    context = {
        'stats': [
            {'label': 'Scans Completed', 'value': user_scans.count(), 'note': 'Your scanner activity'},
            {'label': 'High Risk Scans', 'value': user_scans.filter(classification=ScanResult.Classification.HIGH).count(), 'note': 'Needs attention'},
            {'label': 'Reports Created', 'value': user_scans.exclude(report_file='').count(), 'note': 'Generated PDF reports'},
            {'label': 'Quiz Progress', 'value': quiz_progress, 'note': 'Latest quiz score'},
            {'label': 'Alerts', 'value': user_alerts.count(), 'note': 'Email alerts created'},
            {'label': 'Chat Messages', 'value': ChatMessage.objects.filter(user=display_user).count(), 'note': 'Awareness chatbot usage'},
        ],
        'activity_chart': {
            'labels': labels,
            'values': [
                user_scans.filter(timestamp__date=day).count()
                for day in days
            ],
        },
        'module_chart': {
            'labels': ['Scanner', 'Alerts', 'Reports', 'Quiz', 'Chatbot'],
            'values': [
                user_scans.count(),
                user_alerts.count(),
                user_scans.exclude(report_file='').count(),
                QuizAttempt.objects.filter(user=display_user).count(),
                ChatMessage.objects.filter(user=display_user).count(),
            ],
        },
        'risk_chart': {
            'labels': ['Low Risk', 'Medium Risk', 'High Risk'],
            'values': [
                user_scans.filter(classification=ScanResult.Classification.LOW).count(),
                user_scans.filter(classification=ScanResult.Classification.MEDIUM).count(),
                user_scans.filter(classification=ScanResult.Classification.HIGH).count(),
            ],
        },
        'question_count': Question.objects.filter(is_active=True).count(),
        'latest_attempt': latest_attempt,
        'recent_scans': user_scans[:5],
        'recent_alerts': user_alerts[:5],
    }
    return render(request, 'dashboard/user_dashboard.html', context)
