from allauth.account.adapter import DefaultAccountAdapter
from rest_framework.exceptions import ValidationError

class CustomAccountAdapter(DefaultAccountAdapter):
    def validate_unique_email(self, email):
        if self.is_email_taken(email):
            raise ValidationError(
                "An account with this email already exists."
            )
        return email