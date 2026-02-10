"""Tag service for managing project tags."""
import re
from typing import List

from stitch.database import db
from stitch.models.tag import Tag
from stitch.models.project_tag import ProjectTag


class TagService:
    """Service for managing tags and project-tag associations."""

    @staticmethod
    def normalize_tag_name(name: str) -> str:
        """Lowercase, strip, collapse whitespace, remove special characters, max 50 chars."""
        name = name.strip().lower()
        name = re.sub(r'[^a-z0-9\s\-]', '', name)
        name = re.sub(r'\s+', ' ', name)
        return name[:50]

    @staticmethod
    def get_or_create_tag(name: str) -> Tag:
        """Find existing tag by normalized name, or create new one. Flushes but does not commit."""
        normalized = TagService.normalize_tag_name(name)
        if not normalized:
            raise ValueError("Tag name cannot be empty")

        tag = Tag.query.filter_by(name=normalized).first()
        if not tag:
            tag = Tag(name=normalized)
            db.session.add(tag)
            db.session.flush()
        return tag

    @staticmethod
    def search_tags(query: str, limit: int = 20) -> List[Tag]:
        """Search tags by prefix match (case-insensitive). For autocomplete API."""
        normalized = TagService.normalize_tag_name(query)
        if not normalized:
            return []
        return Tag.query.filter(
            Tag.name.ilike(f'{normalized}%')
        ).order_by(Tag.name).limit(limit).all()

    @staticmethod
    def set_project_tags(project_id: str, tag_names: List[str]) -> List[Tag]:
        """Replace all tags for a project. Normalizes names, creates new tags as needed. Flushes but does not commit."""
        # Remove existing project-tag associations
        ProjectTag.query.filter_by(project_id=project_id).delete()

        # Normalize and deduplicate tag names
        seen = set()
        tags = []
        for name in tag_names:
            normalized = TagService.normalize_tag_name(name)
            if normalized and normalized not in seen:
                seen.add(normalized)
                tag = TagService.get_or_create_tag(normalized)
                pt = ProjectTag(project_id=project_id, tag_id=tag.id)
                db.session.add(pt)
                tags.append(tag)

        db.session.flush()
        return tags

    @staticmethod
    def get_project_tags(project_id: str) -> List[Tag]:
        """Get all tags for a project, ordered by name."""
        return Tag.query.join(
            ProjectTag, Tag.id == ProjectTag.tag_id
        ).filter(
            ProjectTag.project_id == project_id
        ).order_by(Tag.name).all()

    @staticmethod
    def get_all_tags() -> List[Tag]:
        """Get all tags ordered by name. For autocomplete pre-population."""
        return Tag.query.order_by(Tag.name).all()
