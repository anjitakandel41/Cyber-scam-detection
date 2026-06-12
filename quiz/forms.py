from django import forms

from .models import Question


class QuizAttemptForm(forms.Form):
    def __init__(self, *args, questions=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.questions = list(questions or [])

        for question in self.questions:
            choices = [
                (Question.CorrectOption.A, question.option_a),
                (Question.CorrectOption.B, question.option_b),
                (Question.CorrectOption.C, question.option_c),
                (Question.CorrectOption.D, question.option_d),
            ]
            self.fields[f'question_{question.pk}'] = forms.ChoiceField(
                label=question.text,
                choices=choices,
                widget=forms.RadioSelect,
                required=True,
            )
