from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from scanner.models import ScanResult


@login_required
def reports_home(request):
    scans = ScanResult.objects.filter(user=request.user).exclude(report_file='')[:25]
    return render(request, 'reports/home.html', {'scans': scans})


@login_required
def history(request):
    scans = ScanResult.objects.filter(user=request.user)[:50]
    return render(request, 'reports/history.html', {'scans': scans})
