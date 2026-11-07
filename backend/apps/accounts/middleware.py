from django.contrib.auth import logout
from django.shortcuts import render
import secrets

from .devices import touch_session
from .models import UserSession


class BrowserSessionMiddleware:
    """A revoked website/admin session stops working on its next request."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.browser_device_id = request.COOKIES.get("pharmenta.device") or secrets.token_urlsafe(24)
        if request.user.is_authenticated:
            session_id = request.session.get("tracked_session_id")
            if session_id:
                session = UserSession.objects.filter(pk=session_id, user=request.user).first()
                if not session or not session.is_active:
                    logout(request)
                    # An old cookie must not consume the user's next login
                    # attempt after another device has replaced its session.
                    login_path = request.path in {
                        "/manage/login/", "/admin/login/", "/account/login/", "/account/code/",
                    }
                    # API auth endpoints check their own bearer tokens or login
                    # credentials; a stale browser cookie must not block them.
                    api_auth_path = request.path.startswith(("/api/v1/auth/", "/api/auth/"))
                    if not login_path and not api_auth_path:
                        return self.denied(request, "این نشست پایان یافته است؛ دوباره وارد شوید.", 401)
                else:
                    touch_session(session, request)
                    request.device_session = session
            else:
                # Adopt browser cookies issued before device tracking existed.
                from .signals import browser_signed_in

                browser_signed_in(None, request, request.user)
        response = self.get_response(request)
        if not request.COOKIES.get("pharmenta.device"):
            response.set_cookie("pharmenta.device", request.browser_device_id, max_age=365 * 86400, httponly=True, secure=request.is_secure(), samesite="Lax")
        return response

    @staticmethod
    def denied(request, message, status):
        return render(request, "accounts/session_denied.html", {
            "message": message,
            "login_path": "/manage/login/" if request.path.startswith(("/manage/", "/admin/")) else "/account/login/",
        }, status=status)
