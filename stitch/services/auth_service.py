from stitch.models.user import User
from stitch.database import db
from typing import Optional


class AuthService:
    """Authentication service for email-only user management (MVP)"""

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
