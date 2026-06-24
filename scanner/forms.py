from django import forms


class ScanForm(forms.Form):
    email_sender = forms.EmailField(
        required=False,
        label='Sender',
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'sender@example.com',
        }),
    )
    email_subject = forms.CharField(
        required=False,
        label='Subject',
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter the email subject',
        }),
    )
    content = forms.CharField(
        label='Content to scan',
        widget=forms.Textarea(attrs={
            'rows': 6,
            'class': 'form-control',
            'placeholder': 'Paste a URL, email, or SMS message here',
        }),
    )


class QRUploadForm(forms.Form):
    qr_image = forms.ImageField(
        label='QR image',
        widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
    )
