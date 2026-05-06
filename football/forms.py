from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Video


class RegisterForm(UserCreationForm):

    email = forms.EmailField(required=True)

    account_type = forms.ChoiceField(
        choices=[
            ("player", "Player"),
            ("fan", "Fan"),
            ("scout", "Scout"),
            ("coach", "Coach/Club"),
        ],
        required=True
    )

    accept_terms = forms.BooleanField(
        required=True,
        label="I agree to the Terms & Conditions"
    )

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password1",
            "password2"
        ]

    def clean_email(self):

        email = self.cleaned_data.get("email")

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                "This email is already registered."
            )

        return email


class VideoUploadForm(forms.ModelForm):

    class Meta:
        model = Video

        fields = [
            "title",
            "description",
            "category",
            "video_file",
            "thumbnail",
        ]

        widgets = {

            "title": forms.TextInput(
                attrs={
                    "class": "form-input",
                    "placeholder": "Video title"
                }
            ),

            "description": forms.Textarea(
                attrs={
                    "class": "form-input",
                    "placeholder": "Describe the video...",
                    "rows": 5
                }
            ),

            "category": forms.Select(
                attrs={
                    "class": "form-input"
                }
            ),

            "video_file": forms.FileInput(
                attrs={
                    "class": "form-input",
                    "accept": "video/*"
                }
            ),

            "thumbnail": forms.FileInput(
                attrs={
                    "class": "form-input",
                    "accept": "image/*"
                }
            ),
        }