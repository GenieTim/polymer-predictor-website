from django.contrib.auth import get_user_model
from django.contrib.auth.backends import BaseBackend
from django.db.models import Q

User = get_user_model()


class EmailBackend(BaseBackend):
    """
    Authenticate using email address instead of username.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Try to find user by email or username
            user = User.objects.get(
                Q(email=username) | Q(username=username)
            )
        except User.DoesNotExist:
            return None
        except User.MultipleObjectsReturned:
            # If multiple users found, try exact email match first
            try:
                user = User.objects.get(email=username)
            except User.DoesNotExist:
                return None
        
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
    
    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom user models that don't have
        an `is_active` field are allowed.
        """
        is_active = getattr(user, 'is_active', None)
        return is_active or is_active is None
    
    def get_user(self, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None
