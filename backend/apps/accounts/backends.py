"""Django authentication backend for `django.contrib.auth.authenticate()`
(used by `LoginView`) — not to be confused with `authentication.py`'s
`SessionTokenAuthentication`, which authenticates *incoming requests* by
bearer token, a separate DRF concept.
"""

from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q

from .models import LearnerProfile
from .phone import looks_like_phone, normalize_phone


class EmailOrUsernameBackend(ModelBackend):
    """Accept the account's mobile number, its `email`, or the real
    `username` in the `username` credential. A mobile number (any usual
    spelling) is matched to the verified number on the learner profile --
    the normal sign-in for accounts made by phone sign-up.

    Registration (`RegisterSerializer.validate`) derives `username` from the
    email's local part (`name@example.com` -> `name`) purely as an internal
    identifier — the product only ever shows/asks for "email", never
    "username". Without this backend, Django's default `ModelBackend` matches
    on the `username` field alone, so logging in with the email a learner
    just registered with (which is exactly what the login screen asks for)
    fails every time with "Invalid username or password.", not just
    occasionally.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return None
        if looks_like_phone(username):
            # A mobile number: the account that verified it at sign-up.
            profile = (
                LearnerProfile.objects.select_related("user")
                .filter(phone=normalize_phone(username))
                .first()
            )
            if profile is None:
                UserModel().set_password(password)  # same timing as a miss below
                return None
            user = profile.user
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
            return None
        try:
            user = UserModel._default_manager.get(
                Q(**{f"{UserModel.USERNAME_FIELD}__iexact": username})
                | Q(email__iexact=username)
            )
        except UserModel.DoesNotExist:
            # Hash a password anyway so a nonexistent account doesn't respond
            # measurably faster than a wrong-password one (timing side
            # channel; mirrors ModelBackend's own behaviour).
            UserModel().set_password(password)
            return None
        except UserModel.MultipleObjectsReturned:
            # Only possible if a username and an unrelated account's email
            # happen to collide; prefer the exact username match.
            user = UserModel._default_manager.filter(
                **{f"{UserModel.USERNAME_FIELD}__iexact": username}
            ).first()
            if user is None:
                return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
