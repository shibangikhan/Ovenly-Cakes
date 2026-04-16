from django import forms

class RegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=255)
    last_name = forms.CharField(max_length=255)
    mobile = forms.CharField(max_length=20, required=False)
    email = forms.EmailField()
    password1 = forms.CharField(widget=forms.PasswordInput)
    password2 = forms.CharField(widget=forms.PasswordInput)
    terms = forms.BooleanField(required=True)

    def clean(self):
        data = super().clean()
        if data.get('password1') != data.get('password2'):
            raise forms.ValidationError("Passwords do not match")
        return data


class LoginForm(forms.Form):
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)