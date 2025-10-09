# FILE: exams/forms.py

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

# Get the active User model your project is using
User = get_user_model()

class CustomUserCreationForm(UserCreationForm):
    """
    This is a custom, simplified form for creating new users.
    It only asks for a username and password.
    """
    class Meta:
        # Tell the form it is for creating a 'User' model object
        model = User
        
        # Specify which fields to show on the form.
        # The 'password' fields are handled automatically by UserCreationForm.
        fields = ('username',)

