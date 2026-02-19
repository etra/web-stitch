"""
PDF generation service for cross-stitch patterns.

Uses ReportLab to generate printable PDF documents with pattern overview,
color legend, and paginated symbol charts.
"""
import io
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Tuple
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm, cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, PageBreak, KeepTogether
)
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from flask import current_app

from stitch.services.pattern_renderer import PatternRenderer
from stitch.services.project_service import ProjectService


def _register_unicode_fonts() -> tuple:
    """Register Unicode-capable TrueType fonts (regular + bold) with ReportLab.

    Tries font families in priority order. NotoSansCJK is preferred because it
    covers Latin, Cyrillic, Greek, AND CJK (Chinese/Japanese/Korean) scripts.
    DejaVuSans covers Latin, Cyrillic, Greek, Hebrew, Arabic, and more.
    Returns (regular_name, bold_name) tuple. Falls back to Helvetica.
    """
    from reportlab.pdfbase.pdfmetrics import registerFontFamily

    font_families = [
        {
            'name': 'NotoSansCJK',
            'regular': ['/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc'],
            'bold': ['/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc'],
        },
        {
            'name': 'DejaVuSans',
            'regular': ['DejaVuSans.ttf',
                        '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                        '/usr/share/fonts/TTF/DejaVuSans.ttf'],
            'bold': ['DejaVuSans-Bold.ttf',
                     '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',
                     '/usr/share/fonts/TTF/DejaVuSans-Bold.ttf'],
        },
        {
            'name': 'ArialUnicode',
            'regular': ['/System/Library/Fonts/Supplemental/Arial Unicode.ttf'],
            'bold': ['/System/Library/Fonts/Supplemental/Arial Unicode.ttf'],
        },
        {
            'name': 'NotoSans',
            'regular': ['NotoSans-Regular.ttf'],
            'bold': ['NotoSans-Bold.ttf'],
        },
    ]

    def _try_register(font_name, path):
        """Register a TTF/TTC font, handling TrueType Collections."""
        if path.endswith('.ttc'):
            pdfmetrics.registerFont(TTFont(font_name, path, subfontIndex=0))
        else:
            pdfmetrics.registerFont(TTFont(font_name, path))

    for family in font_families:
        name = family['name']
        bold_name = f'{name}-Bold'
        reg_ok = False
        bold_ok = False

        for path in family['regular']:
            try:
                _try_register(name, path)
                reg_ok = True
                break
            except Exception:
                continue

        if not reg_ok:
            continue

        for path in family['bold']:
            try:
                _try_register(bold_name, path)
                bold_ok = True
                break
            except Exception:
                continue

        if not bold_ok:
            bold_name = name  # fall back to regular for bold

        try:
            registerFontFamily(name, normal=name, bold=bold_name)
        except Exception:
            pass

        return (name, bold_name)

    return ('Helvetica', 'Helvetica-Bold')


UNICODE_FONT, UNICODE_FONT_BOLD = _register_unicode_fonts()


class PatternPDFService:
    """
    Generate PDF documents for cross-stitch patterns.

    Creates multi-page PDFs with:
    - Page 1: Overview with colored pattern preview and project info
    - Page 2: Color legend with thread requirements
    - Pages 3+: Paginated symbol charts (30x40 stitches with 3-stitch overlap)
    """

    # Page settings
    PAGE_SIZE = A4
    MARGIN = 1.5 * cm

    # Brand info
    SITE_URL = "https://ourstitch.com"
    SITE_NAME = "OurStitch"
    SITE_CTA = "Create your free pattern at https://ourstitch.com"

    @staticmethod
    def generate_pdf(project, logo_path: str = None, render_mode: dict = None) -> bytes:
        """
        Generate a complete pattern PDF.

        Args:
            project: Project object with state, dimensions, etc.
            logo_path: Path to logo image file (optional)
            render_mode: Dict with show_color, show_stitch, show_symbol, show_line flags

        Returns:
            PDF file as bytes
        """
        logger = logging.getLogger(__name__)
        t_total = time.perf_counter()

        buffer = io.BytesIO()

        doc = SimpleDocTemplate(
            buffer,
            pagesize=PatternPDFService.PAGE_SIZE,
            leftMargin=PatternPDFService.MARGIN,
            rightMargin=PatternPDFService.MARGIN,
            topMargin=PatternPDFService.MARGIN,
            bottomMargin=2 * cm,  # Extra space for footer
            title=f"{project.name} - {PatternPDFService.SITE_URL}",
            author=PatternPDFService.SITE_NAME,
            subject="Cross-stitch pattern",
            creator=PatternPDFService.SITE_NAME
        )

        if render_mode is None:
            render_mode = {
                'show_color': False,
                'show_stitch': False,
                'show_symbol': True,
                'show_line': True,
            }

        # Build document elements
        elements = []
        styles = PatternPDFService._get_styles()

        # Assemble state once for all rendering calls
        t0 = time.perf_counter()
        state = ProjectService.assemble_state(project)
        logger.info('[pdf] assemble_state: %.3fs', time.perf_counter() - t0)

        # Generate pattern data (single pass over all cells)
        t0 = time.perf_counter()
        legend, legend_by_stitch = PatternRenderer.generate_legends(
            state, project.width, project.height
        )
        total_stitches = sum(color['count'] for color in legend)
        logger.info('[pdf] legend generation: %.3fs', time.perf_counter() - t0)

        # Page 1: Overview
        t0 = time.perf_counter()
        elements.extend(PatternPDFService._build_overview_page(
            project, state, legend, total_stitches, styles, logo_path
        ))
        logger.info('[pdf] overview page: %.3fs', time.perf_counter() - t0)

        # Page 2+: Color legend + stitch type breakdown (flows together)
        elements.append(PageBreak())
        t0 = time.perf_counter()
        elements.extend(PatternPDFService._build_legend_pages(
            legend, legend_by_stitch, total_stitches, styles
        ))
        logger.info('[pdf] legend pages: %.3fs', time.perf_counter() - t0)

        # Pattern grid pages
        page_definitions = PatternRenderer.calculate_pattern_pages(
            project.width, project.height
        )
        logger.info('[pdf] rendering %d pattern pages...', len(page_definitions))

        t_pages = time.perf_counter()
        num_pages = len(page_definitions)

        # Pre-warm stamp cache in main thread — avoids redundant PIL rendering
        # across pages. Each unique (symbol, color, font_size, stitch_type) combo
        # is rendered once and shared by all pages.
        cell_size_pdf = 30
        t0 = time.perf_counter()
        shared_stamp_cache = PatternPDFService._prewarm_stamp_cache(
            state, cell_size_pdf, render_mode
        )
        logger.info('[pdf] stamp cache pre-warmed: %d stamps in %.3fs',
                     len(shared_stamp_cache), time.perf_counter() - t0)

        # Render page images sequentially with pre-warmed cache
        app = current_app._get_current_object()
        page_images = []
        for page_def in page_definitions:
            with app.app_context():
                t_page = time.perf_counter()
                img = PatternRenderer.render_symbol_page(
                    state, project.width, project.height,
                    page_def['x_start'], page_def['y_start'],
                    page_def['x_end'], page_def['y_end'],
                    cell_size=cell_size_pdf, stamp_cache=shared_stamp_cache,
                    **render_mode
                )
                logger.info('[pdf]   page %d/%d rendered: %.3fs',
                             page_def['page_num'], num_pages,
                             time.perf_counter() - t_page)
                page_images.append(img)

        logger.info('[pdf] all page images rendered: %.3fs',
                     time.perf_counter() - t_pages)

        # Build PDF elements sequentially (must maintain page order)
        for page_def, page_image in zip(page_definitions, page_images):
            elements.append(PageBreak())
            elements.extend(PatternPDFService._build_pattern_page(
                project, state, page_def, styles,
                render_mode=render_mode, page_image=page_image
            ))

        # Calculate total pages for footer
        # 1 (overview) + 1 (legend) + pattern pages
        # Note: legend may flow to multiple pages but ReportLab handles that automatically
        total_pages = 2 + len(page_definitions)

        # Build PDF with custom footer
        t0 = time.perf_counter()
        doc.build(
            elements,
            onFirstPage=lambda c, d: PatternPDFService._add_footer(c, d, 1, total_pages, logo_path, project.id),
            onLaterPages=lambda c, d: PatternPDFService._add_footer(c, d, d.page, total_pages, logo_path, project.id)
        )
        logger.info('[pdf] doc.build (ReportLab): %.3fs', time.perf_counter() - t0)

        logger.info('[pdf] TOTAL generate_pdf: %.3fs', time.perf_counter() - t_total)

        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def _get_styles():
        """Get paragraph styles for the document."""
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='PatternTitle',
            parent=styles['Heading1'],
            fontName=UNICODE_FONT_BOLD,
            fontSize=18,
            spaceAfter=6 * mm
        ))

        styles.add(ParagraphStyle(
            name='PatternSubtitle',
            parent=styles['Normal'],
            fontName=UNICODE_FONT,
            fontSize=10,
            textColor=colors.gray,
            spaceAfter=4 * mm
        ))

        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontName=UNICODE_FONT_BOLD,
            fontSize=14,
            spaceBefore=4 * mm,
            spaceAfter=3 * mm
        ))

        styles.add(ParagraphStyle(
            name='SmallNote',
            parent=styles['Normal'],
            fontName=UNICODE_FONT,
            fontSize=8,
            textColor=colors.gray
        ))

        # Override base styles so any Paragraph using them also gets Unicode
        styles['Normal'].fontName = UNICODE_FONT
        styles['Heading1'].fontName = UNICODE_FONT_BOLD
        styles['Heading2'].fontName = UNICODE_FONT_BOLD

        return styles

    @staticmethod
    def _build_overview_page(project, state, legend, total_stitches, styles, logo_path) -> List:
        """Build the overview page elements."""
        elements = []

        # Title
        elements.append(Paragraph(project.name, styles['PatternTitle']))
        elements.append(Paragraph(
            f"{project.width} × {project.height} stitches | {len(legend)} colors | {total_stitches:,} total stitches",
            styles['PatternSubtitle']
        ))
        elements.append(Spacer(1, 5 * mm))

        # Two-column layout: pattern image + info table
        # Generate overview pattern image
        overview_img = PatternRenderer.render_overview_pattern(
            state, project.width, project.height, max_size=400
        )

        # Convert numpy array to PIL Image then to ReportLab Image
        img_buffer = PatternPDFService._numpy_to_image_buffer(overview_img)

        # Calculate image dimensions preserving aspect ratio
        max_img_width = min(8 * cm, (PatternPDFService.PAGE_SIZE[0] - 2 * PatternPDFService.MARGIN) * 0.45)
        max_img_height = 10 * cm
        aspect_ratio = project.height / project.width if project.width > 0 else 1
        img_width = max_img_width
        img_height = img_width * aspect_ratio
        if img_height > max_img_height:
            img_height = max_img_height
            img_width = img_height / aspect_ratio
        pattern_image = Image(img_buffer, width=img_width, height=img_height)

        # Project info table
        info_data = [
            ['Project Information', ''],
            ['Title:', project.name],
            ['Dimensions:', f"{project.width} × {project.height} stitches"],
            ['Colors Used:', f"{len(legend)} colors"],
            ['Total Stitches:', f"{total_stitches:,}"],
            ['Pattern Pages:', f"{len(PatternRenderer.calculate_pattern_pages(project.width, project.height))}"],
            ['Created:', project.created_at.strftime('%Y-%m-%d')],
        ]

        if project.description:
            info_data.insert(2, ['Description:', project.description[:100]])

        info_table = Table(info_data, colWidths=[3 * cm, 5 * cm])
        info_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, 0), UNICODE_FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('SPAN', (0, 0), (1, 0)),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('FONTNAME', (0, 1), (0, -1), UNICODE_FONT_BOLD),
            ('FONTNAME', (1, 1), (1, -1), UNICODE_FONT),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        ]))

        # Combine in a layout table
        layout_data = [[pattern_image, info_table]]
        layout_table = Table(layout_data, colWidths=[9 * cm, 8.5 * cm])
        layout_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        elements.append(layout_table)
        elements.append(Spacer(1, 8 * mm))

        # Tips section
        elements.append(Paragraph('Tips for Stitching', styles['SectionHeader']))
        tips = [
            '• Grid lines mark every 5 stitches for easier counting',
            '• Each pattern page shows 30×40 stitches with 3-stitch overlap',
            '• Check off colors in the legend as you complete them',
            '• Start stitching from the center of your fabric for best results',
        ]
        for tip in tips:
            elements.append(Paragraph(tip, styles['Normal']))
            elements.append(Spacer(1, 2 * mm))

        return elements

    @staticmethod
    def _build_legend_pages(legend: List, legend_by_stitch: Dict,
                            total_stitches: int, styles) -> List:
        """Build legend pages: color table first, then by-stitch tables.

        Section 1 — Color Legend: one row per color (aggregated across stitch
        types). Columns: Symbol | Color | Color Name | Thread Code | Stitches | Skeins*

        Section 2 — By Stitch Type: one table per category with a rendered
        40×40 stitch preview image per row. Lines get a simplified table.
        """
        elements = []

        if not legend:
            elements.append(Paragraph('No stitches found in exportable layers.', styles['Normal']))
            return elements

        # ── Section 1: Color Legend ──────────────────────────────────
        elements.append(Paragraph('Color Legend', styles['PatternTitle']))
        elements.append(Spacer(1, 5 * mm))

        # Aggregate legend entries by paletteIndex (sum across stitch types)
        color_agg = {}
        for entry in legend:
            pi = entry['paletteIndex']
            if pi not in color_agg:
                color_agg[pi] = {
                    'symbol': entry['symbol'],
                    'rgbHex': entry['rgbHex'],
                    'name': entry['name'],
                    'vendor': entry.get('vendor'),
                    'code': entry.get('code'),
                    'count': 0,
                }
            color_agg[pi]['count'] += entry['count']

        color_list = sorted(
            color_agg.values(),
            key=lambda x: (x['vendor'] or '', x['code'] or '')
        )

        color_col_widths = [1.0 * cm, 0.8 * cm, 4.5 * cm, 2.5 * cm, 2 * cm, 1.5 * cm]
        color_table_data = [['Symbol', 'Color', 'Color Name', 'Thread Code', 'Stitches', 'Skeins*']]

        for color in color_list:
            thread_code = f"{color['vendor']} {color['code']}" if color.get('vendor') and color.get('code') else 'Custom'
            skeins = round(color['count'] / 200, 1)
            color_table_data.append([
                color['symbol'],
                '',  # Color swatch — styled via BACKGROUND
                color['name'],
                thread_code,
                f"{color['count']:,}",
                str(skeins)
            ])

        # Totals row
        color_table_data.append(['', '', '', 'Total:', f"{total_stitches:,}", ''])

        color_table = Table(color_table_data, colWidths=color_col_widths)

        color_style = [
            # Header
            ('FONTNAME', (0, 0), (-1, 0), UNICODE_FONT_BOLD),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            # Content
            ('FONTNAME', (0, 1), (-1, -1), UNICODE_FONT),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),   # Symbol centered
            ('ALIGN', (4, 0), (5, -1), 'RIGHT'),    # Stitches and skeins right-aligned
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            # Grid (exclude totals row)
            ('GRID', (0, 0), (-1, -2), 0.5, colors.lightgrey),
            # Totals row
            ('FONTNAME', (3, -1), (4, -1), UNICODE_FONT_BOLD),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ]

        # Color swatches
        for i, color in enumerate(color_list):
            row_idx = i + 1
            hex_color = color['rgbHex']
            try:
                rgb = tuple(int(hex_color.lstrip('#')[j:j+2], 16) / 255 for j in (0, 2, 4))
                color_style.append(('BACKGROUND', (1, row_idx), (1, row_idx), colors.Color(*rgb)))
            except:
                pass

        color_table.setStyle(TableStyle(color_style))
        elements.append(color_table)

        # Skein note (after color table)
        elements.append(Spacer(1, 4 * mm))
        elements.append(Paragraph(
            '*Skein Calculation: Approximate 6-strand embroidery floss skeins required '
            '(estimated at ~200 stitches per skein on 14-count Aida). Actual usage varies '
            'based on fabric count, stitch type, and technique. Purchase 1-2 extra skeins per color.',
            styles['SmallNote']
        ))

        # ── Section 2: By Stitch Type (disabled) ─────────────────────
        if not legend_by_stitch:
            return elements

        # Separate lines from cell-based stitch categories
        line_entries = legend_by_stitch.get('Line', [])

        # Cell-based stitch category tables are currently disabled.
        # To re-enable, uncomment the block below.
        #
        # cell_categories = {k: v for k, v in legend_by_stitch.items() if k != 'Line'}
        # stitch_col_widths = [1.2 * cm, 1.0 * cm, 0.8 * cm, 3.5 * cm, 2.5 * cm, 1.8 * cm, 1.5 * cm]
        # preview_size = 40
        # img_pt = 28
        #
        # for category, cat_colors in cell_categories.items():
        #     category_stitches = sum(c['count'] for c in cat_colors)
        #     elements.append(Paragraph(
        #         f"<b>{category}</b> — {len(cat_colors)} color{'s' if len(cat_colors) != 1 else ''}, "
        #         f"{category_stitches:,} stitches",
        #         styles['SectionHeader']
        #     ))
        #     table_data = [['Stitch', 'Symbol', 'Color', 'Color Name', 'Thread Code', 'Stitches', 'Skeins*']]
        #     for color in cat_colors:
        #         thread_code = f"{color['vendor']} {color['code']}" if color.get('vendor') and color.get('code') else 'Custom'
        #         skeins = round(color['count'] / 200, 1)
        #         preview_arr = PatternRenderer.render_stitch_preview(
        #             color['stitchType'], color['rgbHex'], color['symbol'], size=preview_size)
        #         img_buffer = PatternPDFService._numpy_to_image_buffer(preview_arr)
        #         preview_img = Image(img_buffer, width=img_pt, height=img_pt)
        #         table_data.append([
        #             preview_img, color['symbol'], '', color['name'],
        #             thread_code, f"{color['count']:,}", str(skeins)])
        #     category_table = Table(table_data, colWidths=stitch_col_widths)
        #     table_style = [
        #         ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        #         ('FONTSIZE', (0, 0), (-1, 0), 8),
        #         ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
        #         ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        #         ('FONTSIZE', (0, 1), (-1, -1), 8),
        #         ('FONTNAME', (1, 1), (1, -1), UNICODE_FONT),
        #         ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        #         ('ALIGN', (1, 0), (1, -1), 'CENTER'),
        #         ('ALIGN', (5, 0), (6, -1), 'RIGHT'),
        #         ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        #         ('TOPPADDING', (0, 1), (-1, -1), 3),
        #         ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
        #         ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
        #     ]
        #     for i, color in enumerate(cat_colors):
        #         row_idx = i + 1
        #         hex_color = color['rgbHex']
        #         try:
        #             rgb = tuple(int(hex_color.lstrip('#')[j:j+2], 16) / 255 for j in (0, 2, 4))
        #             table_style.append(('BACKGROUND', (2, row_idx), (2, row_idx), colors.Color(*rgb)))
        #         except: pass
        #     category_table.setStyle(TableStyle(table_style))
        #     elements.append(category_table)
        #     elements.append(Spacer(1, 6 * mm))

        # Lines section (simplified — no stitch preview needed)
        if line_entries:
            line_count = sum(c['count'] for c in line_entries)
            elements.append(Paragraph(
                f"<b>Line</b> — {len(line_entries)} color{'s' if len(line_entries) != 1 else ''}, "
                f"{line_count:,} lines",
                styles['SectionHeader']
            ))

            line_col_widths = [0.8 * cm, 4.0 * cm, 2.5 * cm, 1.8 * cm]
            line_table_data = [['Color', 'Color Name', 'Thread Code', 'Lines']]

            for color in line_entries:
                thread_code = f"{color['vendor']} {color['code']}" if color.get('vendor') and color.get('code') else 'Custom'
                line_table_data.append([
                    '',  # Color swatch
                    color['name'],
                    thread_code,
                    f"{color['count']:,}"
                ])

            line_table = Table(line_table_data, colWidths=line_col_widths)

            line_style = [
                ('FONTNAME', (0, 0), (-1, 0), UNICODE_FONT_BOLD),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                ('FONTNAME', (0, 1), (-1, -1), UNICODE_FONT),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (3, 0), (3, -1), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 1), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]

            for i, color in enumerate(line_entries):
                row_idx = i + 1
                hex_color = color['rgbHex']
                try:
                    rgb = tuple(int(hex_color.lstrip('#')[j:j+2], 16) / 255 for j in (0, 2, 4))
                    line_style.append(('BACKGROUND', (0, row_idx), (0, row_idx), colors.Color(*rgb)))
                except:
                    pass

            line_table.setStyle(TableStyle(line_style))
            elements.append(line_table)
            elements.append(Spacer(1, 6 * mm))

        # Total summary
        elements.append(Paragraph(
            f"<b>Total: {total_stitches:,} stitches across "
            f"{len(legend_by_stitch)} stitch type{'s' if len(legend_by_stitch) != 1 else ''}</b>",
            styles['Normal']
        ))

        return elements

    @staticmethod
    def _build_pattern_page(project, state, page_def: Dict, styles,
                            render_mode: dict = None, stamp_cache: dict = None,
                            page_image=None) -> List:
        """Build a pattern grid page.

        Args:
            page_image: Pre-rendered numpy array (skips rendering if provided).
        """
        elements = []

        if render_mode is None:
            render_mode = {
                'show_color': False, 'show_stitch': False,
                'show_symbol': True, 'show_line': True,
            }

        # Page header
        multi_page = page_def['total_rows'] > 1 or page_def['total_cols'] > 1
        if multi_page:
            title = (f"Pattern Grid (Row {page_def['row']} of "
                     f"{page_def['total_rows']}, Column {page_def['col']} "
                     f"of {page_def['total_cols']})")
        else:
            title = "Pattern Grid"

        title_para = Paragraph(title, styles['SectionHeader'])

        if multi_page:
            grid_indicator = PatternPDFService._build_grid_indicator(
                page_def['row'], page_def['col'],
                page_def['total_rows'], page_def['total_cols'],
            )
            header_table = Table(
                [[title_para, grid_indicator]],
                colWidths=[None, grid_indicator._width + 2 * mm],
            )
            header_table.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ]))
            elements.append(header_table)
        else:
            elements.append(title_para)

        elements.append(Paragraph(
            f"Stitches: {page_def['label']}",
            styles['PatternSubtitle']
        ))

        # Use pre-rendered image or render now
        if page_image is None:
            page_image = PatternRenderer.render_symbol_page(
                state,
                project.width,
                project.height,
                page_def['x_start'],
                page_def['y_start'],
                page_def['x_end'],
                page_def['y_end'],
                cell_size=30,
                stamp_cache=stamp_cache,
                **render_mode
            )

        img_buffer = PatternPDFService._numpy_to_image_buffer(page_image)

        # Calculate image size to fit page
        available_width = PatternPDFService.PAGE_SIZE[0] - 2 * PatternPDFService.MARGIN
        available_height = PatternPDFService.PAGE_SIZE[1] - 2 * PatternPDFService.MARGIN - 4 * cm  # Leave room for header/footer

        # Get image actual size in points (1 pixel = 1 point at 72 DPI)
        img_height, img_width = page_image.shape[:2]
        aspect_ratio = img_width / img_height

        # Start with actual rendered size (don't scale up small patterns)
        final_width = img_width
        final_height = img_height

        # Only scale down if the image exceeds available space
        if final_width > available_width or final_height > available_height:
            if aspect_ratio > available_width / available_height:
                # Width constrained
                final_width = available_width
                final_height = final_width / aspect_ratio
            else:
                # Height constrained
                final_height = available_height
                final_width = final_height * aspect_ratio

        pattern_img = Image(img_buffer, width=final_width, height=final_height)
        elements.append(pattern_img)

        # Overlap note
        if page_def['total_rows'] > 1 or page_def['total_cols'] > 1:
            elements.append(Spacer(1, 3 * mm))
            elements.append(Paragraph(
                'This page overlaps with adjacent pages by 3 stitches for easier alignment.',
                styles['SmallNote']
            ))

        return elements

    @staticmethod
    def _build_grid_indicator(row: int, col: int, total_rows: int, total_cols: int):
        """Build a small grid mini-map showing the current page position.

        Returns a Table flowable with the current cell highlighted.
        """
        cell_size = 4 * mm

        data = []
        style_cmds = [
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
            ('TOPPADDING', (0, 0), (-1, -1), 0),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 0),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
        ]

        for r in range(total_rows):
            data.append([''] * total_cols)

        # Highlight the current cell
        c_idx = col - 1
        r_idx = row - 1
        style_cmds.append(
            ('BACKGROUND', (c_idx, r_idx), (c_idx, r_idx), colors.HexColor('#5b6abf'))
        )

        grid_table = Table(
            data,
            colWidths=[cell_size] * total_cols,
            rowHeights=[cell_size] * total_rows,
        )
        grid_table.setStyle(TableStyle(style_cmds))
        grid_table._width = total_cols * cell_size
        return grid_table

    @staticmethod
    def _add_footer(canvas, doc, page_num: int, total_pages: int,
                    logo_path: str = None, project_id: str = None):
        """Add footer with logo, call-to-action link, and page number."""
        canvas.saveState()

        width, height = PatternPDFService.PAGE_SIZE
        footer_y = 1 * cm

        # Left side: logo + call-to-action
        if logo_path:
            try:
                canvas.drawImage(logo_path, PatternPDFService.MARGIN, footer_y - 2 * mm,
                               width=6 * mm, height=6 * mm, preserveAspectRatio=True)
                text_x = PatternPDFService.MARGIN + 8 * mm
            except Exception:
                text_x = PatternPDFService.MARGIN
        else:
            text_x = PatternPDFService.MARGIN

        cta = PatternPDFService.SITE_CTA
        canvas.setFont(UNICODE_FONT, 8)
        canvas.setFillColor(colors.HexColor('#5b6abf'))
        canvas.drawString(text_x, footer_y, cta)

        # Build tracked URL with UTM parameters
        tracked_url = (
            f"{PatternPDFService.SITE_URL}"
            f"?utm_source=pdf&utm_medium=document&utm_campaign=pattern_export"
        )
        if project_id:
            tracked_url += f"&utm_content={project_id}"

        # Make the CTA text a clickable link
        cta_width = canvas.stringWidth(cta, UNICODE_FONT, 8)
        canvas.linkURL(
            tracked_url,
            (text_x, footer_y - 1 * mm, text_x + cta_width, footer_y + 3 * mm),
        )

        # Right side: page number
        page_text = f"Page {page_num} / {total_pages}"
        canvas.setFillColor(colors.gray)
        canvas.drawRightString(width - PatternPDFService.MARGIN, footer_y, page_text)

        # Line above footer
        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(PatternPDFService.MARGIN, footer_y + 5 * mm,
                   width - PatternPDFService.MARGIN, footer_y + 5 * mm)

        canvas.restoreState()

    @staticmethod
    def _prewarm_stamp_cache(state: dict, cell_size: int, render_mode: dict) -> dict:
        """Pre-render all unique symbol stamps needed for the pattern.

        Scans all exportable cells once to collect unique
        (symbol, color, font_size, stitch_type) combinations, then renders
        each stamp. The returned cache dict is passed to every page render
        call so no page needs to create stamps on the fly.
        """
        from stitch.services.pattern_renderer import (
            PatternRenderer, SYMBOL_PLACEMENTS, _symbol_font_size
        )

        if not render_mode.get('show_symbol', True):
            return {}

        palette = state['palette']
        show_color = render_mode.get('show_color', False)
        keys_needed = set()

        for layer in state['layers']:
            if not layer.get('visible', True):
                continue
            if not layer.get('activeForExport', True):
                continue
            if layer['type'] != 'raster':
                continue

            for cell_stitches in layer.get('cells', {}).values():
                stitch_list = cell_stitches if isinstance(cell_stitches, list) else [cell_stitches]
                for cell_data in stitch_list:
                    palette_index = cell_data.get('paletteIndex', 0)
                    if palette_index >= len(palette):
                        continue

                    rgb = PatternRenderer._resolve_color(palette[palette_index])
                    symbol = palette[palette_index].get('symbol', '?')
                    symbol_color = PatternRenderer._get_contrasting_color(rgb) if show_color else (0, 0, 0)
                    stitch_type = cell_data.get('stitchType', 'full')
                    font_size = _symbol_font_size(cell_size, stitch_type)

                    keys_needed.add((symbol, symbol_color, font_size, stitch_type))

        cache = {}
        for key in keys_needed:
            symbol, symbol_color, font_size, stitch_type = key
            cx, cy, _scale = SYMBOL_PLACEMENTS.get(stitch_type, (0.5, 0.5, 0.8))
            cache[key] = PatternRenderer._render_symbol_stamp(
                symbol, symbol_color, font_size, cell_size, cx, cy
            )

        return cache

    @staticmethod
    def _numpy_to_image_buffer(img_array) -> io.BytesIO:
        """Convert numpy array to PNG image buffer."""
        from PIL import Image as PILImage

        # PatternRenderer already returns RGB arrays, no conversion needed
        pil_image = PILImage.fromarray(img_array.astype('uint8'))

        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG', compress_level=1)
        buffer.seek(0)

        return buffer
