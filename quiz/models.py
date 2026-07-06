from decimal import Decimal

from django.conf import settings
from django.db import models


class Question(models.Model):
    class CorrectOption(models.TextChoices):
        A = "A", "Option A"
        B = "B", "Option B"
        C = "C", "Option C"
        D = "D", "Option D"

    text = models.TextField()

    option_a = models.CharField(max_length=255)
    option_b = models.CharField(max_length=255)
    option_c = models.CharField(max_length=255)
    option_d = models.CharField(max_length=255)

    correct_option = models.CharField(
        max_length=1,
        choices=CorrectOption.choices,
    )

    explanation = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.text[:80]

    def option_text(self, option):
        return {
            self.CorrectOption.A: self.option_a,
            self.CorrectOption.B: self.option_b,
            self.CorrectOption.C: self.option_c,
            self.CorrectOption.D: self.option_d,
        }.get(option, "")


class QuizAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )

    # Retry support
    parent_attempt = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="retry_attempts",
    )

    is_retry = models.BooleanField(default=False)

    score = models.PositiveSmallIntegerField(default=0)

    total_questions = models.PositiveSmallIntegerField(default=0)

    percentage = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("0.00"),
    )

    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-completed_at"]

    def __str__(self):
        if self.is_retry:
            return f"Retry - {self.user} ({self.score}/{self.total_questions})"
        return f"{self.user} ({self.score}/{self.total_questions})"

    @property
    def correct_count(self):
        return self.answers.filter(is_correct=True).count()

    @property
    def incorrect_count(self):
        return self.answers.filter(is_correct=False).count()

    @property
    def incorrect_answers(self):
        return self.answers.filter(is_correct=False)


class QuizAnswer(models.Model):
    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
    )

    selected_option = models.CharField(
        max_length=1,
        choices=Question.CorrectOption.choices,
    )

    is_correct = models.BooleanField(default=False)

    class Meta:
        ordering = ["question__id"]
        unique_together = ("attempt", "question")

    def __str__(self):
        return f"{self.question} ({self.selected_option})"