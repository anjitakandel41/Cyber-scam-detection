from django import forms

from .models import Question


class QuizAttemptForm(forms.Form):
    """
    Dynamic Quiz Form

    Features:
    - Pagination support
    - Retry support
    - Remembers selected answers
    """

    def __init__(self, *args, questions=None, initial_answers=None, **kwargs):
        super().__init__(*args, **kwargs)

        self.questions = list(questions or [])
        initial_answers = initial_answers or {}

        for question in self.questions:

            field_name = f"question_{question.pk}"

            choices = [
                (Question.CorrectOption.A, question.option_a),
                (Question.CorrectOption.B, question.option_b),
                (Question.CorrectOption.C, question.option_c),
                (Question.CorrectOption.D, question.option_d),
            ]

            self.fields[field_name] = forms.ChoiceField(
                label=question.text,
                choices=choices,
                required=True,
                widget=forms.RadioSelect(
                    attrs={
                        "class": "form-check-input",
                    }
                ),
                initial=initial_answers.get(str(question.pk)),
            )

    def get_answer(self, question):
        return self.cleaned_data.get(
            f"question_{question.pk}"
        )