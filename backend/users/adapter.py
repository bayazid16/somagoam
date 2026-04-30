from allauth.account.adapter import DefaultAccountAdapter
from rest_framework.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


class CustomAccountAdapter(DefaultAccountAdapter):


    def send_mail(self, template_prefix, email, context):
        subject = render_to_string(
            f"{template_prefix}_subject.txt", context
        ).strip()

        text_body = render_to_string(
            f"{template_prefix}_message.txt", context
        )

        html_body = render_to_string(
            f"{template_prefix}_message.html", context
        )

        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_body,
            from_email=self.get_from_email(),
            to=[email],
        )
        msg.attach_alternative(html_body, "text/html")
        msg.send()

    
    def validate_unique_email(self, email):
        if self.is_email_taken(email):
            raise ValidationError(
                "An account with this email already exists."
            )
        return email