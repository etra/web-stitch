"""Vote service for managing project votes."""
from sqlalchemy import func

from stitch.database import db
from stitch.models.project import Project
from stitch.models.project_vote import ProjectVote


class VoteService:
    """Service for casting, removing, and querying project votes."""

    @staticmethod
    def vote(project_id: str, user_id: str, value: int) -> dict:
        """
        Cast or change a vote on a project.

        Args:
            project_id: Project ID
            user_id: User ID
            value: +1 (upvote) or -1 (downvote)

        Returns:
            dict with vote_score and user_vote
        """
        if value not in (1, -1):
            raise ValueError("Vote value must be +1 or -1")

        existing = ProjectVote.query.filter_by(
            project_id=project_id, user_id=user_id
        ).first()

        if existing:
            if existing.value == value:
                # Same vote again → toggle off (remove)
                return VoteService.remove_vote(project_id, user_id)
            else:
                # Switch vote direction
                existing.value = value
        else:
            vote = ProjectVote(
                project_id=project_id,
                user_id=user_id,
                value=value
            )
            db.session.add(vote)

        db.session.flush()
        VoteService._recalculate_score(project_id)
        db.session.commit()

        project = Project.query.get(project_id)
        return {
            'vote_score': project.vote_score,
            'user_vote': value
        }

    @staticmethod
    def remove_vote(project_id: str, user_id: str) -> dict:
        """
        Remove a user's vote from a project.

        Args:
            project_id: Project ID
            user_id: User ID

        Returns:
            dict with vote_score and user_vote (0)
        """
        existing = ProjectVote.query.filter_by(
            project_id=project_id, user_id=user_id
        ).first()

        if existing:
            db.session.delete(existing)
            db.session.flush()
            VoteService._recalculate_score(project_id)
            db.session.commit()

        project = Project.query.get(project_id)
        return {
            'vote_score': project.vote_score,
            'user_vote': 0
        }

    @staticmethod
    def get_user_vote(project_id: str, user_id: str) -> int:
        """
        Get a user's current vote for a project.

        Returns:
            1, -1, or 0 (no vote)
        """
        vote = ProjectVote.query.filter_by(
            project_id=project_id, user_id=user_id
        ).first()
        return vote.value if vote else 0

    @staticmethod
    def get_user_votes_bulk(project_ids: list[str], user_id: str) -> dict[str, int]:
        """
        Get a user's votes for multiple projects at once.

        Args:
            project_ids: List of project IDs
            user_id: User ID

        Returns:
            dict mapping project_id → vote value (1, -1, or 0)
        """
        if not project_ids:
            return {}

        votes = ProjectVote.query.filter(
            ProjectVote.project_id.in_(project_ids),
            ProjectVote.user_id == user_id
        ).all()

        vote_map = {v.project_id: v.value for v in votes}
        return {pid: vote_map.get(pid, 0) for pid in project_ids}

    @staticmethod
    def _recalculate_score(project_id: str):
        """Recalculate and update the cached vote_score on a project."""
        total = db.session.query(
            func.coalesce(func.sum(ProjectVote.value), 0)
        ).filter(
            ProjectVote.project_id == project_id
        ).scalar()

        Project.query.filter_by(id=project_id).update({'vote_score': total})
