from django.contrib.auth import get_user_model
from .models import SimbirGoUser


def simbir_go_authenticate(username=None, password=None, **kwargs):
    UserModel = get_user_model()
    try:
        user = UserModel._default_manager.get(username=username)
        if user.password == password:
            return user
    except UserModel.DoesNotExist:
        return None
    return None
