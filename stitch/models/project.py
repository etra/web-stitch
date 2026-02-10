"""Project model for storing cross-stitch patterns"""
from stitch.database import db
from datetime import datetime
from enum import IntEnum
import uuid


SAMPLE_PROJECT = {
    "project": {
        "canvas": {
            "color": "#ffffff",
            "height": 10,
            "width": 10
        },
        "clothColor": "#ffffff",
        "name": "My Project",
        "description": "My first cross-stitch project",
        "properties": {
            "defaultStitchType": "full",
            "majorGridInterval": 10,
            "showGridNumbers": False
        },
        "status": 0,
        "width": 10,
        "height": 10,
        "layers": [
            {
                "activeForExport": True,
                "cells": {
                    "12": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "13": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "16": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "17": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "21": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "22": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "23": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "24": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "25": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "26": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "27": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "28": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "31": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "32": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "33": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "34": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "35": {
                        "vendor": "DMC",
                        "colorId": 158,
                        "stitch": "full"
                    },
                    "36": {
                        "vendor": "DMC",
                        "colorId": 158,
                        "stitch": "full"
                    },
                    "37": {
                        "vendor": "DMC",
                        "colorId": 158,
                        "stitch": "full"
                    },
                    "38": {
                        "vendor": "DMC",
                        "colorId": 351,
                        "stitch": "full"
                    },
                    "41": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "42": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "43": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "44": {
                        "vendor": "DMC",
                        "colorId": 158,
                        "stitch": "full"
                    },
                    "45": {
                        "vendor": "DMC",
                        "colorId": 158,
                        "stitch": "full"
                    },
                    "46": {
                        "vendor": "DMC",
                        "colorId": 351,
                        "stitch": "full"
                    },
                    "47": {
                        "vendor": "DMC",
                        "colorId": 351,
                        "stitch": "full"
                    },
                    "48": {
                        "vendor": "DMC",
                        "colorId": 420,
                        "stitch": "full"
                    },
                    "52": {
                        "vendor": "DMC",
                        "colorId": 14,
                        "stitch": "full"
                    },
                    "53": {
                        "vendor": "DMC",
                        "colorId": 158,
                        "stitch": "full"
                    },
                    "54": {
                        "vendor": "DMC",
                        "colorId": 158,
                        "color": "a57ba8a4-b12e-40c8-9fde-69e0fb337294",
                        "stitch": "full"
                    },
                    "55": {
                        "vendor": "DMC",
                        "colorId": 351,
                        "color": "16bf1752-0d77-4960-8ba7-f7fcb0e7a3e2",
                        "stitch": "full"
                    },
                    "56": {
                        "vendor": "DMC",
                        "colorId": 420,
                        "color": "d75190b4-2b54-4631-bc1f-f291711e432b",
                        "stitch": "full"
                    },
                    "57": {
                        "vendor": "DMC",
                        "colorId": 420,
                        "color": "d75190b4-2b54-4631-bc1f-f291711e432b",
                        "stitch": "full"
                    },
                    "63": {
                        "vendor": "DMC",
                        "colorId": 351,
                        "color": "16bf1752-0d77-4960-8ba7-f7fcb0e7a3e2",
                        "stitch": "full"
                    },
                    "64": {
                        "vendor": "DMC",
                        "colorId": 351,
                        "color": "16bf1752-0d77-4960-8ba7-f7fcb0e7a3e2",
                        "stitch": "full"
                    },
                    "65": {
                        "vendor": "DMC",
                        "colorId": 420,
                        "color": "d75190b4-2b54-4631-bc1f-f291711e432b",
                        "stitch": "full"
                    },
                    "66": {
                        "vendor": "DMC",
                        "colorId": 420,
                        "color": "d75190b4-2b54-4631-bc1f-f291711e432b",
                        "stitch": "full"
                    },
                    "74": {
                        "vendor": "DMC",
                        "colorId": 420,
                        "color": "d75190b4-2b54-4631-bc1f-f291711e432b",
                        "stitch": "full"
                    },
                    "75": {
                        "vendor": "DMC",
                        "colorId": 420,
                        "color": "d75190b4-2b54-4631-bc1f-f291711e432b",
                        "stitch": "full"
                    },
                    "84": {
                        "vendor": "DMC",
                        "colorId": 420,
                        "color": "d75190b4-2b54-4631-bc1f-f291711e432b",
                        "stitch": "quarter-tr"
                    },
                    "85": {
                        "vendor": "DMC",
                        "colorId": 420,
                        "color": "d75190b4-2b54-4631-bc1f-f291711e432b",
                        "stitch": "quarter-tl"
                    }
                },
                "name": "Main stitches",
                "paths": [
                    {
                        "color": "876cf9e7-92a3-4a47-8ac4-6d1b48934dfd",
                        "endX": 1,
                        "endY": 2,
                        "startX": 2,
                        "startY": 1,
                        "stitch": "line"
                    },
                    {
                        "color": "876cf9e7-92a3-4a47-8ac4-6d1b48934dfd",
                        "endX": 0,
                        "endY": 2,
                        "startX": 2,
                        "startY": 0,
                        "stitch": "line"
                    },
                    {
                        "color": "876cf9e7-92a3-4a47-8ac4-6d1b48934dfd",
                        "endX": 0,
                        "endY": 4,
                        "startX": 0,
                        "startY": 2,
                        "stitch": "line"
                    },
                    {
                        "color": "876cf9e7-92a3-4a47-8ac4-6d1b48934dfd",
                        "endX": 4,
                        "endY": 8,
                        "startX": 0,
                        "startY": 4,
                        "stitch": "line"
                    },
                    {
                        "color": "876cf9e7-92a3-4a47-8ac4-6d1b48934dfd",
                        "endX": 3,
                        "endY": 0,
                        "startX": 2,
                        "startY": 0,
                        "stitch": "line"
                    },
                    {
                        "color": "876cf9e7-92a3-4a47-8ac4-6d1b48934dfd",
                        "endX": 4,
                        "endY": 1,
                        "startX": 3,
                        "startY": 0,
                        "stitch": "line"
                    },
                    {
                        "color": "876cf9e7-92a3-4a47-8ac4-6d1b48934dfd",
                        "endX": 5,
                        "endY": 1,
                        "startX": 4,
                        "startY": 1,
                        "stitch": "line"
                    },
                    {
                        "color": "876cf9e7-92a3-4a47-8ac4-6d1b48934dfd",
                        "endX": 6,
                        "endY": 0,
                        "startX": 5,
                        "startY": 1,
                        "stitch": "line"
                    },
                    {
                        "color": "876cf9e7-92a3-4a47-8ac4-6d1b48934dfd",
                        "endX": 7,
                        "endY": 0,
                        "startX": 6,
                        "startY": 0,
                        "stitch": "line"
                    },
                    {
                        "color": "876cf9e7-92a3-4a47-8ac4-6d1b48934dfd",
                        "endX": 9,
                        "endY": 2,
                        "startX": 7,
                        "startY": 0,
                        "stitch": "line"
                    },
                    {
                        "color": "876cf9e7-92a3-4a47-8ac4-6d1b48934dfd",
                        "endX": 9,
                        "endY": 4,
                        "startX": 9,
                        "startY": 2,
                        "stitch": "line"
                    },
                    {
                        "color": "876cf9e7-92a3-4a47-8ac4-6d1b48934dfd",
                        "endX": 5,
                        "endY": 8,
                        "startX": 9,
                        "startY": 4,
                        "stitch": "line"
                    }
                ],
            }
        ]
    }
}

class DifficultyLevel(IntEnum):
    """Project difficulty levels"""
    BEGINNER = 1
    INTERMEDIATE = 2
    ADVANCED = 3


class ProjectStatus(IntEnum):
    """Project visibility/status values"""
    DELETED = -1
    DEFAULT = 0
    PUBLIC = 1
    PRIVATE = 2


class Project(db.Model):
    """
    Project model storing cross-stitch patterns.

    Project state (layers, palette, properties) is normalized into
    ProjectLayer and ProjectColor tables.

    Use ProjectService.assemble_state() to reconstruct the full state dict.
    Use ProjectService.save_state() to decompose and persist state.
    """
    __tablename__ = 'projects'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)  # Reference to users.id (no FK)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text, nullable=True)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    cloth_color = db.Column(db.String(7), default='#ffffff')
    status = db.Column(db.SmallInteger, default=ProjectStatus.DEFAULT, nullable=False, index=True)
    difficulty = db.Column(db.SmallInteger, nullable=True)

    vote_score = db.Column(db.Integer, default=0, nullable=False, server_default='0')

    # Normalized project-level properties
    active_layer_id = db.Column(db.String(36), nullable=True)
    major_grid_interval = db.Column(db.Integer, default=10)
    show_grid_numbers = db.Column(db.Boolean, default=False)
    default_stitch_type = db.Column(db.String(30), default='full')

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to user (no database FK constraint)
    user = db.relationship('User',
                          primaryjoin='Project.user_id==User.id',
                          foreign_keys='[Project.user_id]',
                          back_populates='projects')

    # Relationships to normalized child tables (no database FK constraints)
    colors = db.relationship('ProjectColor',
                             primaryjoin='Project.id==ProjectColor.project_id',
                             foreign_keys='[ProjectColor.project_id]',
                             order_by='ProjectColor.sort_order')

    layers = db.relationship('ProjectLayer',
                             primaryjoin='Project.id==ProjectLayer.project_id',
                             foreign_keys='[ProjectLayer.project_id]',
                             order_by='ProjectLayer.sort_order')

    tags = db.relationship('Tag',
                           secondary='project_tags',
                           primaryjoin='Project.id == ProjectTag.project_id',
                           secondaryjoin='ProjectTag.tag_id == Tag.id',
                           foreign_keys='[ProjectTag.project_id, ProjectTag.tag_id]',
                           order_by='Tag.name')

    def __repr__(self):
        return f'<Project {self.name}>'

    def to_dict(self):
        """Convert project to dictionary (use assemble_state for full state with layers/palette)"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'description': self.description,
            'width': self.width,
            'height': self.height,
            'cloth_color': self.cloth_color,
            'status': self.status,
            'difficulty': self.difficulty,
            'vote_score': self.vote_score,
            'active_layer_id': self.active_layer_id,
            'major_grid_interval': self.major_grid_interval,
            'show_grid_numbers': self.show_grid_numbers,
            'default_stitch_type': self.default_stitch_type,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
        }

    @property
    def difficulty_label(self) -> str | None:
        """Get human-readable difficulty label."""
        if self.difficulty is None:
            return None
        try:
            return DifficultyLevel(self.difficulty).name.capitalize()
        except ValueError:
            return None

    @property
    def is_deleted(self) -> bool:
        """Check if project is soft-deleted"""
        return self.status == ProjectStatus.DELETED

    @property
    def is_public(self) -> bool:
        """Check if project is public"""
        return self.status == ProjectStatus.PUBLIC
