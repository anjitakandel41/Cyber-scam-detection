from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import QuizAttemptForm
from .models import Question, QuizAnswer, QuizAttempt


@login_required
def quiz_home(request):
    latest_attempt = QuizAttempt.objects.filter(user=request.user).first()
    total_questions = Question.objects.filter(is_active=True).count()
    return render(
        request,
        'quiz/home.html',
        {
            'latest_attempt': latest_attempt,
            'total_questions': total_questions,
        },
    )


@login_required
def attempt_quiz(request):
    questions = Question.objects.filter(is_active=True)

    if not questions.exists():
        return render(request, 'quiz/no_questions.html')

    form = QuizAttemptForm(request.POST or None, questions=questions)

    if request.method == 'POST' and form.is_valid():
        attempt = QuizAttempt.objects.create(user=request.user, total_questions=questions.count())
        score = 0

        for question in questions:
            selected = form.cleaned_data[f'question_{question.pk}']
            is_correct = selected == question.correct_option
            if is_correct:
                score += 1
            QuizAnswer.objects.create(
                attempt=attempt,
                question=question,
                selected_option=selected,
                is_correct=is_correct,
            )

        attempt.score = score
        attempt.percentage = round((score / attempt.total_questions) * 100, 2)
        attempt.save(update_fields=['score', 'percentage'])
        return redirect('quiz:result', attempt_id=attempt.pk)

    return render(request, 'quiz/attempt.html', {'form': form, 'questions': questions})


@login_required
def quiz_result(request, attempt_id):
    attempt = get_object_or_404(
        QuizAttempt.objects.prefetch_related('answers__question'),
        pk=attempt_id,
        user=request.user,
    )
    return render(request, 'quiz/result.html', {'attempt': attempt})
