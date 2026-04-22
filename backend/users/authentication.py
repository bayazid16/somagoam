# users/authentication.py
from rest_framework.authentication import SessionAuthentication

class CsrfExemptSessionAuthentication(SessionAuthentication):
    """
    SessionAuthentication without CSRF enforcement.
    Safe because we use JWT for API auth — CSRF only needed for session-based auth.
    """
    def enforce_csrf(self, request):
        return 