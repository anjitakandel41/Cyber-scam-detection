from django.shortcuts import render

from scanner.models import ScanResult
from users.decorators import view_mode_allowed
from users.remember import get_display_user


@view_mode_allowed
def reports_home(request):
    display_user = get_display_user(request)
    scans = ScanResult.objects.filter(user=display_user).exclude(report_file='')[:25]
    return render(request, 'reports/home.html', {'scans': scans})


@view_mode_allowed
def history(request):
    display_user = get_display_user(request)
    scans = ScanResult.objects.filter(user=display_user)[:50]
    return render(request, 'reports/history.html', {'scans': scans})
