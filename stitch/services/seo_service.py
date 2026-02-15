"""
SEO metadata service for generating page titles and meta tags.

This service provides utilities for constructing SEO-friendly metadata
for different page types throughout the application.
"""
from dataclasses import dataclass
from typing import Optional


@dataclass
class SEOMetadata:
    """Container for SEO metadata fields."""

    title: str
    description: str
    canonical_url: Optional[str] = None
    og_image: Optional[str] = None
    keywords: Optional[str] = None


class SEOService:
    """
    Service for generating SEO metadata.

    Provides methods to retrieve SEO metadata for different page types.
    All methods return SEOMetadata dataclass instances.
    """

    # Site-wide defaults
    SITE_NAME = "OurStitch"
    SITE_URL = "https://ourstitch.com"
    DEFAULT_TITLE = "OurStitch — Free Online Cross-Stitch Pattern Editor"
    DEFAULT_DESCRIPTION = (
        "Design cross-stitch patterns directly in your browser for free. "
        "Draw stitch by stitch, convert images into patterns, and export "
        "print-ready PDFs with symbols and color guides."
    )

    @staticmethod
    def get_index_metadata() -> SEOMetadata:
        """
        Get SEO metadata for the home/index page.

        Returns:
            SEOMetadata with home page title, description, and canonical URL.
        """
        return SEOMetadata(
            title=SEOService.DEFAULT_TITLE,
            description=SEOService.DEFAULT_DESCRIPTION,
            canonical_url=SEOService.SITE_URL,
            keywords="cross stitch, cross-stitch patterns, pattern editor, "
            "needlework, embroidery patterns, stitch design, pattern maker",
        )

    @staticmethod
    def get_page_metadata(
        page_title: str,
        description: Optional[str] = None,
        canonical_path: Optional[str] = None,
        og_image: Optional[str] = None,
        keywords: Optional[str] = None,
    ) -> SEOMetadata:
        """
        Get SEO metadata for a generic static page.

        Args:
            page_title: The page-specific title (will be appended with site name).
            description: Page description (defaults to site default).
            canonical_path: Path for canonical URL (e.g., "/about").
            og_image: URL for Open Graph image.
            keywords: Comma-separated keywords for the page.

        Returns:
            SEOMetadata with formatted title and metadata.
        """
        full_title = f"{page_title} — {SEOService.SITE_NAME}"
        canonical_url = None
        if canonical_path:
            canonical_url = f"{SEOService.SITE_URL}{canonical_path}"

        return SEOMetadata(
            title=full_title,
            description=description or SEOService.DEFAULT_DESCRIPTION,
            canonical_url=canonical_url,
            og_image=og_image,
            keywords=keywords,
        )
