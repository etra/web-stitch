"""Community service for querying public patterns."""
from stitch.models.project import Project, ProjectStatus


class CommunityService:
    """Service for querying public community patterns."""

    @staticmethod
    def get_latest_patterns(limit: int = 6) -> list[Project]:
        """
        Get latest public projects ordered by creation date.

        Args:
            limit: Maximum number of projects to return

        Returns:
            List of public Project instances
        """
        return Project.query.filter(
            Project.status == ProjectStatus.PUBLIC
        ).order_by(
            Project.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_best_patterns(limit: int = 6) -> list[Project]:
        """
        Get best public projects ordered by vote score, then creation date.

        Args:
            limit: Maximum number of projects to return

        Returns:
            List of public Project instances
        """
        return Project.query.filter(
            Project.status == ProjectStatus.PUBLIC
        ).order_by(
            Project.vote_score.desc(),
            Project.created_at.desc()
        ).limit(limit).all()

    @staticmethod
    def get_patterns_page(sort: str = 'latest', page: int = 1, per_page: int = 12) -> tuple[list[Project], int]:
        """
        Get paginated public projects.

        Args:
            sort: 'latest' or 'popular'
            page: Page number (1-indexed)
            per_page: Items per page

        Returns:
            Tuple of (projects list, total count)
        """
        query = Project.query.filter(
            Project.status == ProjectStatus.PUBLIC
        )

        if sort == 'popular':
            query = query.order_by(
                Project.vote_score.desc(),
                Project.created_at.desc()
            )
        else:
            query = query.order_by(Project.created_at.desc())

        total = query.count()
        offset = (page - 1) * per_page
        projects = query.offset(offset).limit(per_page).all()

        return projects, total
