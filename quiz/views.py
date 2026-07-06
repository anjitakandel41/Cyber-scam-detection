from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import QuizAttemptForm
from .models import Question, QuizAnswer, QuizAttempt

QUESTIONS_PER_PAGE = 10


@login_required
def quiz_home(request):
    """
    Quiz Home Page
    """

    latest_attempt = (
        QuizAttempt.objects.filter(
            user=request.user
        )
        .order_by("-completed_at")
        .first()
    )

    total_questions = Question.objects.filter(
        is_active=True
    ).count()

    return render(
        request,
        "quiz/home.html",
        {
            "latest_attempt": latest_attempt,
            "total_questions": total_questions,
        },
    )


def get_questions(request):
    """
    Returns all questions or only incorrect questions
    during Retry Quiz.
    """

    retry_attempt = request.session.get("retry_attempt")

    if retry_attempt:

        attempt = get_object_or_404(
            QuizAttempt,
            pk=retry_attempt,
        )

        wrong_question_ids = (
            attempt.answers.filter(
                is_correct=False
            )
            .values_list(
                "question_id",
                flat=True,
            )
        )

        return Question.objects.filter(
            id__in=wrong_question_ids,
            is_active=True,
        ).order_by("id")

    return Question.objects.filter(
        is_active=True
    ).order_by("id")

@login_required
def attempt_quiz(request, page=1):
    """
    Quiz with pagination.
    """

    questions = get_questions(request)

    if not questions.exists():
        return render(
            request,
            "quiz/no_questions.html",
        )

    paginator = Paginator(
        questions,
        QUESTIONS_PER_PAGE,
    )

    page_obj = paginator.get_page(page)

    current_questions = page_obj.object_list

    # Session stores all answers across pages
    if "quiz_answers" not in request.session:
        request.session["quiz_answers"] = {}

    answers = request.session["quiz_answers"]

    # Create form
    if request.method == "POST":

        form = QuizAttemptForm(
            request.POST,
            questions=current_questions,
            initial_answers=answers,
        )

        if form.is_valid():

            # Save answers from current page
            for question in current_questions:
                answers[str(question.pk)] = form.cleaned_data[
                    f"question_{question.pk}"
                ]

            request.session["quiz_answers"] = answers
            request.session.modified = True

            # Previous page
            if "previous" in request.POST:
                return redirect(
                    "quiz:attempt_page",
                    page=page - 1,
                )

            # Next page
            if "next" in request.POST:
                return redirect(
                    "quiz:attempt_page",
                    page=page + 1,
                )
                        # If not last page, go to next page
            if page_obj.has_next():
                return redirect(
                    "quiz:attempt_page",
                    page=page + 1,
                )

            # ==========================
            # Last Page -> Save Attempt
            # ==========================

            retry_attempt_id = request.session.get("retry_attempt")

            parent_attempt = None
            is_retry = False

            if retry_attempt_id:
                parent_attempt = get_object_or_404(
                    QuizAttempt,
                    pk=retry_attempt_id,
                )
                is_retry = True

            attempt = QuizAttempt.objects.create(
                user=request.user,
                parent_attempt=parent_attempt,
                is_retry=is_retry,
                total_questions=questions.count(),
            )

            score = 0

            for question in questions:

                selected = answers.get(str(question.pk))

                if not selected:
                    continue

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

            if attempt.total_questions > 0:
                attempt.percentage = Decimal(
                    str(
                        round(
                            (score / attempt.total_questions) * 100,
                            2,
                        )
                    )
                )
            else:
                attempt.percentage = Decimal("0.00")

            attempt.save()

            # Clear Session
            request.session.pop("quiz_answers", None)
            request.session.pop("retry_attempt", None)

            return redirect(
                "quiz:result",
                attempt_id=attempt.pk,
            )
    else:

        form = QuizAttemptForm(
            questions=current_questions,
            initial_answers=answers,
        )

    progress = int(
        (page_obj.number / paginator.num_pages) * 100
    )

    return render(
        request,
        "quiz/attempt.html",
        {
            "form": form,
            "page_obj": page_obj,
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "progress": progress,
        },
    )

@login_required
def quiz_result(request, attempt_id):
    """
    Display quiz result.
    """

    attempt = get_object_or_404(
        QuizAttempt.objects.prefetch_related(
            "answers__question"
        ),
        pk=attempt_id,
        user=request.user,
    )

    wrong_answers = attempt.answers.filter(
        is_correct=False
    )

    return render(
        request,
        "quiz/result.html",
        {
            "attempt": attempt,
            "wrong_answers": wrong_answers,
        },
    )


@login_required
def retry_quiz(request, attempt_id):
    """
    Retry only incorrect questions.
    """

    attempt = get_object_or_404(
        QuizAttempt,
        pk=attempt_id,
        user=request.user,
    )

    wrong_answers = attempt.answers.filter(
        is_correct=False
    )

    # No incorrect answers
    if not wrong_answers.exists():
        return redirect(
            "quiz:result",
            attempt_id=attempt.pk,
        )

    # Clear previous session answers
    request.session.pop(
        "quiz_answers",
        None,
    )

    # Store attempt id for retry
    request.session["retry_attempt"] = attempt.pk

    # Start retry quiz
    return redirect(
        "quiz:attempt"
    )
        