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

    phone_number = forms.CharField(
        required=False,
        max_length=20,
        label='Phone Number',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+97798XXXXXXXX',
        }),
    )

    content = forms.CharField(
        label='Content to scan',
        widget=forms.Textarea(attrs={
            'rows': 6,
            'class': 'form-control',
            'placeholder': 'Paste URL, email, or SMS here',
        }),
    )


class QRUploadForm(forms.Form):
    qr_image = forms.ImageField(
        label='QR image',
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control',
        }),
    )
