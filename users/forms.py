from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import CustomUser


class CustomUserCreationForm(UserCreationForm):

    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Enter Email'
            }
        )
    )

    role = forms.ChoiceField(
        choices=CustomUser.Role.choices,
        widget=forms.Select(
            attrs={
                'class': 'form-select'
            }
        )
    )

    class Meta:
        model = CustomUser
        fields = (
            'username',
            'email',
            'role',
            'password1',
            'password2'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['username'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Username'
        })

        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })

        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })

    def save(self, commit=True):
        user = super().save(commit=False)

        user.email = self.cleaned_data['email']
        user.role = self.cleaned_data['role']
        user.is_active = True

        if commit:
            user.save()

        return user











# from django import forms
# from django.contrib.auth.forms import UserCreationForm

# from .models import CustomUser


# class CustomUserCreationForm(UserCreationForm):
#     email = forms.EmailField(required=True)

#     class Meta:
#         model = CustomUser
#         fields = ('username', 'email', 'password1', 'password2')

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         for field in self.fields.values():
#             field.widget.attrs.setdefault('class', 'form-control')

#     def save(self, commit=True):
#         user = super().save(commit=False)
#         user.email = self.cleaned_data['email']
#         user.role = CustomUser.Role.USER
#         user.is_active = True
#         if commit:
#             user.save()
#         return user
