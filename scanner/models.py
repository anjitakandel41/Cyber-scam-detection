from django.conf import settings
from django.db import models


class ScanResult(models.Model):
    class Classification(models.TextChoices):
        LOW = 'Low Risk', 'Low Risk'
        MEDIUM = 'Medium Risk', 'Medium Risk'
        HIGH = 'High Risk', 'High Risk'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='scan_results')
    input = models.TextField()
    risk_score = models.PositiveSmallIntegerField()
    classification = models.CharField(max_length=20, choices=Classification)
    explanation = models.JSONField(default=list)
    recommendation = models.TextField()
    report_file = models.FileField(upload_to='reports/', blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f'{self.user} - {self.classification} ({self.risk_score}%)'
