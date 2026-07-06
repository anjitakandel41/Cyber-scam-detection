from django import forms


class ScanForm(forms.Form):
    # Email fields
    email_sender = forms.EmailField(
        required=False,
        label='Sender Email',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'sender@example.com',
        }),
    )

    email_subject = forms.CharField(
        required=False,
        label='Email Subject',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter the email subject',
        }),
    )

    # SMS field
    phone_number = forms.CharField(
        required=False,
        label='Phone Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+977 98XXXXXXXX',
        }),
    )

    # Shared field
    content = forms.CharField(
        label='Content',
        widget=forms.Textarea(attrs={
            'rows': 8,
            'class': 'form-control',
        }),
    )


class QRUploadForm(forms.Form):
    qr_image = forms.ImageField(
        label='QR Image',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
        }),
    )
