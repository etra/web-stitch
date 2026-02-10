from flask import current_app
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
from stitch.models.user import User
from stitch.database import db
from typing import Optional


class AuthService:
    """Authentication service for email-only user management with magic link verification"""

    @staticmethod
    def generate_magic_token(email: str) -> str:
        """
        Generate a signed token containing the user's email for magic link authentication.

        Args:
            email: User's email address

        Returns:
            URL-safe signed token string
        """
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        return serializer.dumps(email, salt='magic-link')

    @staticmethod
    def verify_magic_token(token: str) -> Optional[str]:
        """
        Verify a magic link token and return the email if valid.

        Args:
            token: URL-safe signed token string

        Returns:
            Email address if token is valid and not expired, None otherwise
        """
        serializer = URLSafeTimedSerializer(current_app.config['SECRET_KEY'])
        max_age = current_app.config.get('MAGIC_LINK_EXPIRATION', 900)
        try:
            email = serializer.loads(token, salt='magic-link', max_age=max_age)
            return email
        except (SignatureExpired, BadSignature):
            return None

    @staticmethod
    def find_or_create_user(email: str) -> User:
        """
        Find existing user by email or create new one (email-only authentication)

        Args:
            email: User's email address

        Returns:
            User object (existing or newly created)
        """
        # Try to find existing user
        user = User.query.filter_by(email=email).first()

        # If user doesn't exist, create new one
        if not user:
            user = User(email=email)
            db.session.add(user)
            db.session.commit()

        return user

    @staticmethod
    def get_user_by_id(user_id: str) -> Optional[User]:
        """
        Get user by ID

        Args:
            user_id: User's unique identifier

        Returns:
            User object if found, None otherwise
        """
        return User.query.filter_by(id=user_id).first()

    @staticmethod
    def get_user_by_email(email: str) -> Optional[User]:
        """
        Get user by email

        Args:
            email: User's email address

        Returns:
            User object if found, None otherwise
        """
        return User.query.filter_by(email=email).first()
