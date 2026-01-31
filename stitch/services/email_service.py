"""Email service for sending emails throughout the application."""
from flask import current_app, render_template
from flask_mail import Mail, Message
from threading import Thread
from typing import List, Optional, Tuple


# Global mail instance - initialized by init_mail()
mail = Mail()


def init_mail(app):
    """Initialize Flask-Mail with the application.

    Args:
        app: Flask application instance
    """
    mail.init_app(app)


class EmailService:
    """
    Service for sending emails.

    Supports both synchronous and asynchronous sending,
    plain text and HTML content, attachments, and template-based emails.
    """

    @staticmethod
    def _send_async(app, msg: Message):
        """
        Send email asynchronously in a background thread.

        Args:
            app: Flask application instance
            msg: Flask-Mail Message object
        """
        with app.app_context():
            mail.send(msg)

    @staticmethod
    def send(
        subject: str,
        recipients: List[str],
        text_body: str,
        html_body: Optional[str] = None,
        sender: Optional[str] = None,
        reply_to: Optional[str] = None,
        attachments: Optional[List[Tuple[str, str, bytes]]] = None,
        sync: bool = False
    ) -> bool:
        """
        Send an email with support for both text and HTML content.

        Args:
            subject: Email subject line
            recipients: List of recipient email addresses
            text_body: Plain text email body
            html_body: HTML email body (optional)
            sender: Sender email address (defaults to MAIL_DEFAULT_SENDER)
            reply_to: Reply-to email address (optional)
            attachments: List of tuples (filename, content_type, data)
            sync: If True, send synchronously. Default is False (async)

        Returns:
            True if email was sent/queued successfully

        Example:
            EmailService.send(
                subject='Welcome to Web Stitch',
                recipients=['user@example.com'],
                text_body='Welcome!',
                html_body='<h1>Welcome!</h1>'
            )
        """
        if sender is None:
            sender = current_app.config.get('MAIL_DEFAULT_SENDER')

        msg = Message(
            subject=subject,
            sender=sender,
            recipients=recipients,
            reply_to=reply_to
        )
        msg.body = text_body

        if html_body:
            msg.html = html_body

        if attachments:
            for filename, content_type, data in attachments:
                msg.attach(filename, content_type, data)

        try:
            if sync:
                mail.send(msg)
            else:
                Thread(
                    target=EmailService._send_async,
                    args=(current_app._get_current_object(), msg)
                ).start()
            return True
        except Exception as e:
            current_app.logger.error(f'Failed to send email: {e}')
            return False

    @staticmethod
    def send_template(
        subject: str,
        recipients: List[str],
        template: str,
        sync: bool = False,
        **kwargs
    ) -> bool:
        """
        Send email using template files.

        Looks for both text and HTML versions of the template:
        - templates/email/{template}.txt (required)
        - templates/email/{template}.html (optional)

        Args:
            subject: Email subject line
            recipients: List of recipient email addresses
            template: Template name (without extension)
            sync: If True, send synchronously
            **kwargs: Variables to pass to the template

        Returns:
            True if email was sent/queued successfully

        Example:
            EmailService.send_template(
                subject='Welcome!',
                recipients=['user@example.com'],
                template='welcome',
                user=user
            )
        """
        text_body = render_template(f'email/{template}.txt', **kwargs)
        html_body = None

        try:
            html_body = render_template(f'email/{template}.html', **kwargs)
        except Exception:
            # HTML template is optional
            pass

        return EmailService.send(
            subject=subject,
            recipients=recipients,
            text_body=text_body,
            html_body=html_body,
            sync=sync
        )

    @staticmethod
    def send_welcome(user) -> bool:
        """
        Send welcome email to new user.

        Args:
            user: User object with email attribute

        Returns:
            True if email was sent/queued successfully
        """
        return EmailService.send_template(
            subject='Welcome to Web Stitch!',
            recipients=[user.email],
            template='welcome',
            user=user
        )

    @staticmethod
    def send_magic_link(user, magic_link: str) -> bool:
        """
        Send magic link email for passwordless authentication.

        Args:
            user: User object with email attribute
            magic_link: Full URL of the magic link for authentication

        Returns:
            True if email was sent/queued successfully
        """
        return EmailService.send_template(
            subject='Sign in to Web Stitch',
            recipients=[user.email],
            template='magic_link',
            user=user,
            magic_link=magic_link
        )

    @staticmethod
    def send_pattern_shared(recipient_email: str, sender_name: str, pattern_name: str, pattern_url: str) -> bool:
        """
        Send notification when a pattern is shared with someone.

        Args:
            recipient_email: Email of the person receiving the shared pattern
            sender_name: Name of the person sharing
            pattern_name: Name of the shared pattern
            pattern_url: URL to view the pattern

        Returns:
            True if email was sent/queued successfully
        """
        return EmailService.send_template(
            subject=f'{sender_name} shared a pattern with you!',
            recipients=[recipient_email],
            template='pattern_shared',
            sender_name=sender_name,
            pattern_name=pattern_name,
            pattern_url=pattern_url
        )

    @staticmethod
    def send_test(recipient: str) -> bool:
        """
        Send a test email to verify email configuration.

        Args:
            recipient: Email address to send test email to

        Returns:
            True if email was sent successfully
        """
        return EmailService.send(
            subject='[Web Stitch] Test Email',
            recipients=[recipient],
            text_body='This is a test email from Web Stitch. If you receive this, your email configuration is working correctly!',
            html_body='<p>This is a test email from <strong>Web Stitch</strong>.</p><p>If you receive this, your email configuration is working correctly!</p>',
            sync=True  # Send synchronously for testing
        )
