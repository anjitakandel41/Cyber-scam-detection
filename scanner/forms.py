from django import forms


class ScanForm(forms.Form):
    content = forms.CharField(
        label='Content to scan',
        widget=forms.Textarea(attrs={'rows': 6, 'placeholder': 'Paste a URL, email, or SMS message here'}),
    )


class QRUploadForm(forms.Form):
    qr_image = forms.ImageField(label='QR image')
