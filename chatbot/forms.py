from django import forms


class ChatForm(forms.Form):
    message = forms.CharField(
        label='Ask a phishing awareness question',
        widget=forms.Textarea(attrs={
            'rows': 3,
            'class': 'form-control',
            'placeholder': 'Example: How do I identify a phishing email?',
        }),
    )
