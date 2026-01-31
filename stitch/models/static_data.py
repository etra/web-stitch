"""
Static data for color palettes.

This module loads color palette data from JSON files and provides
helper functions to access them.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict

# Get the directory where this file is located
_MODELS_DIR = Path(__file__).parent

STITCH_TYPES = {
    'full': {
        'type': 'full',
        'name': 'Full Cross',
        'category': 'Full Cross',
        'icon': '✕',
        'sort_order': 0
    },
    'half-slash': {
        'type': 'half-slash',
        'name': 'Half Stitch (Slash)',
        'category': 'Half Stitch',
        'icon': '/',
        'sort_order': 1
    },
    'half-backslash': {
        'type': 'half-backslash',
        'name': 'Half Stitch (Backslash)',
        'category': 'Half Stitch',
        'icon': '\\',
        'sort_order': 1
    },
    'quarter-tl': {
        'type': 'quarter-tl',
        'name': 'Quarter Stitch (Top-Left)',
        'category': 'Quarter Stitch',
        'icon': '◸',
        'sort_order': 2
    },
    'quarter-tr': {
        'type': 'quarter-tr',
        'name': 'Quarter Stitch (Top-Right)',
        'category': 'Quarter Stitch',
        'icon': '◹',
        'sort_order': 2
    },
    'quarter-bl': {
        'type': 'quarter-bl',
        'name': 'Quarter Stitch (Bottom-Left)',
        'category': 'Quarter Stitch',
        'icon': '◺',
        'sort_order': 2
    },
    'quarter-br': {
        'type': 'quarter-br',
        'name': 'Quarter Stitch (Bottom-Right)',
        'category': 'Quarter Stitch',
        'icon': '◿',
        'sort_order': 2
    },
    'three-quarter-tl': {
        'type': 'three-quarter-tl',
        'name': 'Three-Quarter (Top-Left)',
        'category': 'Three-Quarter Stitch',
        'icon': '⟋',
        'sort_order': 3
    },
    'three-quarter-tr': {
        'type': 'three-quarter-tr',
        'name': 'Three-Quarter (Top-Right)',
        'category': 'Three-Quarter Stitch',
        'icon': '⟍',
        'sort_order': 3
    },
    'three-quarter-bl': {
        'type': 'three-quarter-bl',
        'name': 'Three-Quarter (Bottom-Left)',
        'category': 'Three-Quarter Stitch',
        'icon': '⟍',
        'sort_order': 3
    },
    'three-quarter-br': {
        'type': 'three-quarter-br',
        'name': 'Three-Quarter (Bottom-Right)',
        'category': 'Three-Quarter Stitch',
        'icon': '⟋',
        'sort_order': 3
    },
    'petite': {
        'type': 'petite',
        'name': 'Petite Stitch',
        'category': 'Special Stitch',
        'icon': '✕',
        'sort_order': 4
    },
    'french-knot': {
        'type': 'french-knot',
        'name': 'French Knot',
        'category': 'Special Stitch',
        'icon': '•',
        'sort_order': 4
    },
    'long-vertical': {
        'type': 'long-vertical',
        'name': 'Long Stitch (Vertical)',
        'category': 'Long Stitch',
        'icon': '|',
        'sort_order': 5
    },
    'long-horizontal': {
        'type': 'long-horizontal',
        'name': 'Long Stitch (Horizontal)',
        'category': 'Long Stitch',
        'icon': '―',
        'sort_order': 5
    },
    'backstitch-horizontal': {
        'type': 'backstitch-horizontal',
        'name': 'Backstitch (Horizontal)',
        'category': 'Backstitch',
        'icon': '─',
        'sort_order': 6
    },
    'backstitch-vertical': {
        'type': 'backstitch-vertical',
        'name': 'Backstitch (Vertical)',
        'category': 'Backstitch',
        'icon': '│',
        'sort_order': 6
    },
    'backstitch-slash': {
        'type': 'backstitch-slash',
        'name': 'Backstitch (Slash)',
        'category': 'Backstitch',
        'icon': '╱',
        'sort_order': 6
    },
    'backstitch-backslash': {
        'type': 'backstitch-backslash',
        'name': 'Backstitch (Backslash)',
        'category': 'Backstitch',
        'icon': '╲',
        'sort_order': 6
    }
}

@dataclass
class Stitch:
    """
    Represents a stitch type.

    Attributes:
        type: Stitch type identifier (e.g., "full", "half-slash")
        name: Human-readable name of the stitch
        category: Category of the stitch (e.g., "Full Cross", "Half Stitch")
        icon: Icon representing the stitch
        sort_order: Integer for sorting stitch types
    """
    type: str
    name: str
    category: str
    icon: str
    sort_order: int

    def __str__(self):
        """String representation of the stitch."""
        return f"{self.type}: {self.name}"

    def to_dict(self) -> Dict[str, str]:
        """Convert stitch to dictionary format."""
        return {
            'type': self.type,
            'name': self.name,
            'category': self.category,
            'icon': self.icon,
            'sort_order': self.sort_order
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Stitch':
        """Create Stitch instance from dictionary."""
        return cls(
            type=data['type'],
            name=data['name'],
            category=data['category'],
            icon=data['icon'],
            sort_order=data['sort_order']
        )


def get_stitches() -> List[Stitch]:
    """
    Get the list of available stitch types.

    Returns:
        List of Stitch objects
    """
    return [Stitch.from_dict(data) for data in STITCH_TYPES.values()]


@dataclass
class Color:
    """
    Represents a single color in a palette.

    Attributes:
        code: Color code (e.g., "310", "Blanc", "H01")
        name: Human-readable color name (e.g., "Black", "White")
        hex: Hex color value (e.g., "#000000")
    """
    code: str
    name: str
    hex: str
    default: bool = False

    def __str__(self) -> str:
        """String representation of the color."""
        return f"{self.code}: {self.name} ({self.hex})"

    def to_dict(self) -> Dict[str, str]:
        """Convert color to dictionary format."""
        return {
            'code': self.code,
            'name': self.name,
            'hex': self.hex,
            'default': self.default
        }

    @classmethod
    def from_dict(cls, data: Dict[str, str]) -> 'Color':
        """Create Color instance from dictionary."""
        return cls(
            code=data['code'],
            name=data['name'],
            hex=data['hex'],
            default=data.get('default', False)
        )


def _load_palette_from_json(filename: str) -> List[Color]:
    """
    Load palette data from a JSON file.

    Args:
        filename: Name of the JSON file in the models directory

    Returns:
        List of Color objects
    """
    filepath = _MODELS_DIR / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return [Color.from_dict(color_dict) for color_dict in data]
    except FileNotFoundError:
        return []


# Load DMC palette from JSON file
# To update: Run `python convert_dmc_palette.py dmc_colors.csv pixelstich/models/dmc.json`
DMC_PALETTE = _load_palette_from_json('dmc.json')

# Hama Color Palette (placeholder - replace with actual data)
HAMA_PALETTE = [
    Color("H01", "White", "#eceded", True),
    Color("H02", "Cream", "#f0e8b9"),
    Color("H03", "Yellow", "#f0b901"),
    Color("H04", "Orange", "#eb9534"),
    Color("H05", "Red", "#eb4034"),
    Color("H06", "Pink", "#f798ba"),
    Color("H07", "Brown", "#8b4a3b"),
    Color("H08", "Purple", "#9b4f96"),
    Color("H09", "Blue", "#0f68a8"),
    Color("H10", "Green", "#00a650"),
    Color("H18", "Black", "#1c1c1c", True)
]

# Artkal Color Palette (placeholder - replace with actual data)
ARTKAL_PALETTE = [
    Color("A01", "White", "#ffffff", True),
    Color("A02", "Cream", "#ffe4b5"),
    Color("A03", "Yellow", "#ffff00"),
    Color("A04", "Red", "#ff0000"),
    Color("A05", "Pink", "#ffc0cb"),
    Color("A06", "Brown", "#a52a2a"),
    Color("A07", "Blue", "#0000ff"),
    Color("A08", "Green", "#008000"),
    Color("A09", "Black", "#000000", True)
]

# Nabbi Color Palette (placeholder - replace with actual data)
NABBI_PALETTE = [
    Color("N01", "White", "#ffffff", True),
    Color("N02", "Cream", "#fffacd"),
    Color("N03", "Yellow", "#ffeb3b"),
    Color("N04", "Red", "#f44336"),
    Color("N05", "Pink", "#e91e63"),
    Color("N06", "Brown", "#795548"),
    Color("N07", "Blue", "#2196f3"),
    Color("N08", "Green", "#4caf50"),
    Color("N09", "Black", "#212121", True)
]

# Palette registry for easy lookup
PALETTES = {
    'dmc': DMC_PALETTE,
    'hama': HAMA_PALETTE,
    'artkal': ARTKAL_PALETTE,
    'nabbi': NABBI_PALETTE
}


def get_palette(palette_name: str) -> List[Color]:
    """
    Get color palette by name.

    Args:
        palette_name: Name of the palette ('dmc', 'hama', 'artkal', 'nabbi')

    Returns:
        List of Color objects

    Raises:
        ValueError: If palette name is not recognized
    """
    palette = PALETTES.get(palette_name.lower())
    if palette is None:
        raise ValueError(
            f"Unknown palette: {palette_name}. "
            f"Available: {', '.join(PALETTES.keys())}"
        )
    return palette


def get_color_by_code(palette_name: str, color_code: str) -> Color | None:
    """
    Get a specific color from a palette by its code.

    Args:
        palette_name: Name of the palette ('dmc', 'hama', 'artkal', 'nabbi')
        color_code: Color code to search for

    Returns:
        Color object if found, None otherwise
    """
    palette = get_palette(palette_name)
    for color in palette:
        if color.code == color_code:
            return color
    return None


def palette_to_dict_list(palette: List[Color]) -> List[Dict[str, str]]:
    """
    Convert a list of Color objects to a list of dictionaries.

    Useful for JSON serialization or API responses.

    Args:
        palette: List of Color objects

    Returns:
        List of color dictionaries
    """
    return [color.to_dict() for color in palette]


def reload_dmc_palette() -> None:
    """
    Reload DMC palette from JSON file.

    Useful if the JSON file has been updated and you want to refresh
    the palette data without restarting the application.
    """
    global DMC_PALETTE
    DMC_PALETTE = _load_palette_from_json('dmc.json')
    PALETTES['dmc'] = DMC_PALETTE
