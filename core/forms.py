from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.core.exceptions import ValidationError
from questions.models import Profile
from django.contrib.auth.password_validation import validate_password
import uuid

User = get_user_model()

class LoginForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'xixi@example.com'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': '••••••'}))
    remember = forms.BooleanField(required=False, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}))

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')

        if email and password:
            user = authenticate(username=email, password=password)
            if user is None:
                raise forms.ValidationError('Неверный email или пароль')
            cleaned_data['user'] = user

        return cleaned_data


class SignupForm(forms.Form):
    email = forms.EmailField(widget=forms.EmailInput(
        attrs={'class': 'form-control', 'placeholder': 'xixi@example.com', 'autocomplete': 'email', 'id': 'id_email'}))
    
    nickname = forms.CharField(max_length=50, min_length=3, widget=forms.TextInput(
        attrs={'class': 'form-control', 'placeholder': 'Как к вам обращаться', 'autocomplete': 'username', 'id': 'id_nickname'}))
    
    password1 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': '••••••••', 'autocomplete': 'new-password', 'id': 'id_password1'}))
    
    password2 = forms.CharField(widget=forms.PasswordInput(
        attrs={'class': 'form-control', 'placeholder': '••••••••', 'autocomplete': 'new-password', 'id': 'id_password2'}))

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('Этот email уже зарегистрирован')
        return email

    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if Profile.objects.filter(nickname=nickname).exists():
            raise ValidationError('Этот никнейм уже занят')
        return nickname

    def clean(self):
        cleaned_data = super().clean()
        p1 = cleaned_data.get('password1')
        p2 = cleaned_data.get('password2')
        
        if p1 and p2 and p1 != p2:
            raise ValidationError('Пароли не совпадают')
        if p1:
            try:
                validate_password(p1)
            except ValidationError as e:
                self.add_error('password1', e)
        return cleaned_data
    
    def save(self):
        email = self.cleaned_data['email']
        nickname = self.cleaned_data['nickname']
        password = self.cleaned_data['password1']
        tech_username = f"user_{email.split('@')[0]}_{uuid.uuid4().hex[:6]}"
        
        user = User.objects.create_user(email=email, username=tech_username, password=password, is_active=True)
        Profile.objects.create(user=user, nickname=nickname)
        return user
    

class EditProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ['nickname', 'avatar', 'bio']
        widgets = {
            'nickname': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ваш никнейм'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control'}),
            'bio': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Расскажите о себе'}),
        }

    def clean_nickname(self):
        nickname = self.cleaned_data.get('nickname')
        if not nickname:
            raise ValidationError("Никнейм не может быть пустым")
        if Profile.objects.filter(nickname=nickname).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Этот никнейм уже занят')
        return nickname
    