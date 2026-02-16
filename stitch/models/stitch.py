"""
Stitch type definitions.

Static data — not stored in the database. Defines all available stitch types
with their display metadata (name, category, icon, sort order, render mode).
"""
from dataclasses import dataclass
from typing import Dict, List


STITCH_TYPES = {
    # ── Full Cross ──────────────────────────────────────────────
    'full': {
        'type': 'full',
        'name': 'Full Cross',
        'category': 'Full Cross',
        'icon': '✕',
        'sort_order': 0,
        'render_mode': 'path',
        'occupancy': ['tl', 'tr', 'bl', 'br'],
        'path_data': [
            [[0.1, 0.1], [0.9, 0.9]],
            [[0.9, 0.1], [0.1, 0.9]]
        ]
    },

    # ── Half Stitch (disabled) ─────────────────────────────────
    # 'half-slash': {
    #     'type': 'half-slash',
    #     'name': 'Half Stitch (Slash)',
    #     'category': 'Half Stitch',
    #     'icon': '/',
    #     'sort_order': 1,
    #     'render_mode': 'path',
    #     'occupancy': ['bl', 'tr'],
    #     'path_data': [
    #         [[0.1, 0.9], [0.9, 0.1]]
    #     ]
    # },
    # 'half-backslash': {
    #     'type': 'half-backslash',
    #     'name': 'Half Stitch (Backslash)',
    #     'category': 'Half Stitch',
    #     'icon': '\\',
    #     'sort_order': 1,
    #     'render_mode': 'path',
    #     'occupancy': ['tl', 'br'],
    #     'path_data': [
    #         [[0.1, 0.1], [0.9, 0.9]]
    #     ]
    # },

    # ── Quarter Stitch ──────────────────────────────────────────
    'quarter-tl': {
        'type': 'quarter-tl',
        'name': 'Quarter Stitch (Top-Left)',
        'category': 'Quarter Stitch',
        'icon': '◸',
        'sort_order': 2,
        'render_mode': 'path',
        'occupancy': ['tl'],
        'path_data': [
            [[0.1, 0.1], [0.5, 0.5]]
        ]
    },
    'quarter-tr': {
        'type': 'quarter-tr',
        'name': 'Quarter Stitch (Top-Right)',
        'category': 'Quarter Stitch',
        'icon': '◹',
        'sort_order': 2,
        'render_mode': 'path',
        'occupancy': ['tr'],
        'path_data': [
            [[0.9, 0.1], [0.5, 0.5]]
        ]
    },
    'quarter-bl': {
        'type': 'quarter-bl',
        'name': 'Quarter Stitch (Bottom-Left)',
        'category': 'Quarter Stitch',
        'icon': '◺',
        'sort_order': 2,
        'render_mode': 'path',
        'occupancy': ['bl'],
        'path_data': [
            [[0.1, 0.9], [0.5, 0.5]]
        ]
    },
    'quarter-br': {
        'type': 'quarter-br',
        'name': 'Quarter Stitch (Bottom-Right)',
        'category': 'Quarter Stitch',
        'icon': '◿',
        'sort_order': 2,
        'render_mode': 'path',
        'occupancy': ['br'],
        'path_data': [
            [[0.9, 0.9], [0.5, 0.5]]
        ]
    },

    # ── Three-Quarter ────────────────────────────────────────────
    # Each combines one full diagonal + a quarter from the named
    # corner to the center. Occupancy is diagonal-half so two
    # opposite three-quarters (tl+br or tr+bl) can coexist to
    # form a full cross.
    'three-quarter-tl': {
        'type': 'three-quarter-tl',
        'name': 'Three-Quarter (Top-Left)',
        'category': 'Three-Quarter Stitch',
        'icon': '⟋',
        'sort_order': 1,
        'render_mode': 'path',
        'occupancy': ['tl', 'bl'],
        'path_data': [
            [[0.1, 0.9], [0.9, 0.1]],   # full slash /
            [[0.1, 0.1], [0.5, 0.5]]     # quarter from top-left
        ]
    },
    'three-quarter-tr': {
        'type': 'three-quarter-tr',
        'name': 'Three-Quarter (Top-Right)',
        'category': 'Three-Quarter Stitch',
        'icon': '⟍',
        'sort_order': 1,
        'render_mode': 'path',
        'occupancy': ['tl', 'tr'],
        'path_data': [
            [[0.1, 0.1], [0.9, 0.9]],   # full backslash \
            [[0.9, 0.1], [0.5, 0.5]]     # quarter from top-right
        ]
    },
    'three-quarter-bl': {
        'type': 'three-quarter-bl',
        'name': 'Three-Quarter (Bottom-Left)',
        'category': 'Three-Quarter Stitch',
        'icon': '⟍',
        'sort_order': 1,
        'render_mode': 'path',
        'occupancy': ['bl', 'br'],
        'path_data': [
            [[0.1, 0.1], [0.9, 0.9]],   # full backslash \
            [[0.1, 0.9], [0.5, 0.5]]     # quarter from bottom-left
        ]
    },
    'three-quarter-br': {
        'type': 'three-quarter-br',
        'name': 'Three-Quarter (Bottom-Right)',
        'category': 'Three-Quarter Stitch',
        'icon': '⟋',
        'sort_order': 1,
        'render_mode': 'path',
        'occupancy': ['tr', 'br'],
        'path_data': [
            [[0.1, 0.9], [0.9, 0.1]],   # full slash /
            [[0.9, 0.9], [0.5, 0.5]]     # quarter from bottom-right
        ]
    },

    # ── Special (disabled) ─────────────────────────────────────
    # 'petite': {
    #     'type': 'petite',
    #     'name': 'Petite Stitch',
    #     'category': 'Special Stitch',
    #     'icon': '✕',
    #     'sort_order': 4,
    #     'render_mode': 'path',
    #     'occupancy': ['tl', 'tr', 'bl', 'br'],
    #     'path_data': [
    #         [[0.3, 0.3], [0.7, 0.7]],
    #         [[0.7, 0.3], [0.3, 0.7]]
    #     ]
    # },
    # 'french-knot': {
    #     'type': 'french-knot',
    #     'name': 'French Knot',
    #     'category': 'Special Stitch',
    #     'icon': '•',
    #     'sort_order': 4,
    #     'render_mode': 'path',
    #     'occupancy': ['tl', 'tr', 'bl', 'br'],
    #     'path_data': [
    #         [[0.5, 0.35], [0.65, 0.5], [0.5, 0.65],
    #          [0.35, 0.5], [0.5, 0.35]]
    #     ]
    # },

    # ── Line (linear mode) ───────────────────────────────────────
    'line': {
        'type': 'line',
        'name': 'Line',
        'category': 'Line',
        'icon': '-',
        'sort_order': 5,
        'render_mode': 'linear',
        'occupancy': [],
        'path_data': []
    }
}


@dataclass
class Stitch:
    """
    Represents a stitch type.

    Attributes:
        type: Stitch type identifier (e.g. 'full', 'half-slash')
        name: Human-readable name (e.g. 'Full Cross')
        category: Category grouping (e.g. 'Full Cross', 'Half Stitch')
        icon: Unicode icon representing the stitch
        sort_order: Integer for sorting stitch types in UI
    """
    type: str
    name: str
    category: str
    icon: str
    sort_order: int
    render_mode: str = 'point'
    occupancy: List = None
    path_data: List = None

    def __str__(self):
        return f"{self.type}: {self.name}"

    def to_dict(self) -> Dict[str, str]:
        return {
            'type': self.type,
            'name': self.name,
            'category': self.category,
            'icon': self.icon,
            'sort_order': self.sort_order,
            'render_mode': self.render_mode,
            'occupancy': self.occupancy or [],
            'path_data': self.path_data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Stitch':
        return cls(
            type=data['type'],
            name=data['name'],
            category=data['category'],
            icon=data['icon'],
            sort_order=data['sort_order'],
            render_mode=data.get('render_mode', 'point'),
            occupancy=data.get('occupancy', []),
            path_data=data.get('path_data', None)
        )


def get_stitches() -> List[Stitch]:
    """Get all available stitch types as Stitch objects."""
    return [Stitch.from_dict(data) for data in STITCH_TYPES.values()]
