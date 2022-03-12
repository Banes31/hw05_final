from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (PasswordChangeForm, PasswordResetForm,
                                       SetPasswordForm, UserCreationForm)

User = get_user_model()


class CreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')


class PasswordChangingForm(PasswordChangeForm):
    class Meta:
        model = User
        fields = ('old_password', 'new_password1', 'new_password2')


class PasswordResForm(PasswordResetForm):
    class Meta:
        model = User
        fields = ('email')


class PasswordResConfirmForm(SetPasswordForm):
    class Meta:
        model = User
        fields = ('new_password1', 'new_password2')
