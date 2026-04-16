from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model

from .supabase_client import get_supabase_client

User = get_user_model()


class SupabaseBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        email = username or kwargs.get('email')

        if not email or not password:
            return None

        try:
            supabase = get_supabase_client()
            result = supabase.auth.sign_in_with_password({
                'email': email,
                'password': password,
            })
        except Exception:
            return None

        if isinstance(result, dict):
            error = result.get('error')
            data = result.get('data')
        else:
            error = getattr(result, 'error', None)
            data = getattr(result, 'data', None)

        if error or not data:
            return None

        user, created = User.objects.get_or_create(email=email)

        if created:
            user.is_active = True
            user.set_unusable_password()
            user.save()

        return user

    def user_can_authenticate(self, user):
        return True