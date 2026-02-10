"""
PDF generation service for cross-stitch patterns.

Uses ReportLab to generate printable PDF documents with pattern overview,
color legend, and paginated symbol charts.
"""
import io
import os
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

from stitch.services.pattern_renderer import PatternRenderer
from stitch.services.project_service import ProjectService


def _register_unicode_font() -> str:
    """Register a Unicode-capable TrueType font with ReportLab.

    Returns the registered font name, or 'Helvetica' as fallback.
    """
    font_candidates = [
        ('DejaVuSans', 'DejaVuSans.ttf'),
        ('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'),
        ('DejaVuSans', '/usr/share/fonts/TTF/DejaVuSans.ttf'),
        ('ArialUnicode', '/System/Library/Fonts/Supplemental/Arial Unicode.ttf'),
        ('NotoSans', 'NotoSans-Regular.ttf'),
    ]

    for font_name, font_path in font_candidates:
        try:
            pdfmetrics.registerFont(TTFont(font_name, font_path))
            return font_name
        except Exception:
            continue

    return 'Helvetica'


UNICODE_FONT = _register_unicode_font()


class PatternPDFService:
    """
    Generate PDF documents for cross-stitch patterns.

    Creates multi-page PDFs with:
    - Page 1: Overview with colored pattern preview and project info
    - Page 2: Color legend with thread requirements
    - Pages 3+: Paginated symbol charts (50x50 stitches with overlap)
    """

    # Page settings
    PAGE_SIZE = A4
    MARGIN = 1.5 * cm

    # Brand info
    SITE_URL = "ourstitch.com"
    SITE_NAME = "OurStitch"

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
        state = ProjectService.assemble_state(project)

        # Generate pattern data
        legend = PatternRenderer.generate_legend(
            state, project.width, project.height
        )
        total_stitches = sum(color['count'] for color in legend)

        # Legend grouped by stitch type
        legend_by_stitch = PatternRenderer.generate_legend_by_stitch_type(
            state, project.width, project.height
        )

        # Page 1: Overview
        elements.extend(PatternPDFService._build_overview_page(
            project, state, legend, total_stitches, styles, logo_path
        ))

        # Page 2+: Color legend + stitch type breakdown (flows together)
        elements.append(PageBreak())
        elements.extend(PatternPDFService._build_legend_pages(
            legend, legend_by_stitch, total_stitches, styles
        ))

        # Pattern grid pages
        page_definitions = PatternRenderer.calculate_pattern_pages(
            project.width, project.height, page_size=50, overlap=5
        )

        for page_def in page_definitions:
            elements.append(PageBreak())
            elements.extend(PatternPDFService._build_pattern_page(
                project, state, page_def, styles, render_mode=render_mode
            ))

        # Calculate total pages for footer
        # 1 (overview) + 1 (legend) + pattern pages
        # Note: legend may flow to multiple pages but ReportLab handles that automatically
        total_pages = 2 + len(page_definitions)

        # Build PDF with custom footer
        doc.build(
            elements,
            onFirstPage=lambda c, d: PatternPDFService._add_footer(c, d, 1, total_pages, logo_path),
            onLaterPages=lambda c, d: PatternPDFService._add_footer(c, d, d.page, total_pages, logo_path)
        )

        buffer.seek(0)
        return buffer.getvalue()

    @staticmethod
    def _get_styles():
        """Get paragraph styles for the document."""
        styles = getSampleStyleSheet()

        styles.add(ParagraphStyle(
            name='PatternTitle',
            parent=styles['Heading1'],
            fontSize=18,
            spaceAfter=6 * mm
        ))

        styles.add(ParagraphStyle(
            name='PatternSubtitle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.gray,
            spaceAfter=4 * mm
        ))

        styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=styles['Heading2'],
            fontSize=14,
            spaceBefore=4 * mm,
            spaceAfter=3 * mm
        ))

        styles.add(ParagraphStyle(
            name='SmallNote',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.gray
        ))

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

        # Calculate image dimensions to fit
        img_width = min(8 * cm, (PatternPDFService.PAGE_SIZE[0] - 2 * PatternPDFService.MARGIN) * 0.45)
        pattern_image = Image(img_buffer, width=img_width, height=img_width)

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
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('SPAN', (0, 0), (1, 0)),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
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
            '• Grid lines mark every 10 stitches for easier counting',
            '• Each pattern page shows 50×50 stitches with 5-stitch overlap',
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
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            # Content
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('FONTNAME', (0, 1), (0, -1), UNICODE_FONT),  # Symbol column
            ('ALIGN', (0, 0), (0, -1), 'CENTER'),   # Symbol centered
            ('ALIGN', (4, 0), (5, -1), 'RIGHT'),    # Stitches and skeins right-aligned
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            # Grid (exclude totals row)
            ('GRID', (0, 0), (-1, -2), 0.5, colors.lightgrey),
            # Totals row
            ('FONTNAME', (3, -1), (4, -1), 'Helvetica-Bold'),
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
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
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
    def _build_pattern_page(project, state, page_def: Dict, styles, render_mode: dict = None) -> List:
        """Build a pattern grid page."""
        elements = []

        if render_mode is None:
            render_mode = {
                'show_color': False, 'show_stitch': False,
                'show_symbol': True, 'show_line': True,
            }

        # Page header
        if page_def['total_rows'] > 1 or page_def['total_cols'] > 1:
            title = f"Pattern Grid (Row {page_def['row']} of {page_def['total_rows']}, Column {page_def['col']} of {page_def['total_cols']})"
        else:
            title = "Pattern Grid"

        elements.append(Paragraph(title, styles['SectionHeader']))
        elements.append(Paragraph(
            f"Stitches: {page_def['label']}",
            styles['PatternSubtitle']
        ))

        # Generate pattern image for this page
        page_image = PatternRenderer.render_symbol_page(
            state,
            project.width,
            project.height,
            page_def['x_start'],
            page_def['y_start'],
            page_def['x_end'],
            page_def['y_end'],
            cell_size=20,
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
                'This page overlaps with adjacent pages by 5 stitches for easier alignment.',
                styles['SmallNote']
            ))

        return elements

    @staticmethod
    def _add_footer(canvas, doc, page_num: int, total_pages: int, logo_path: str = None):
        """Add footer to each page."""
        canvas.saveState()

        width, height = PatternPDFService.PAGE_SIZE
        footer_y = 1 * cm

        # Left side: logo and URL
        if logo_path:
            try:
                canvas.drawImage(logo_path, PatternPDFService.MARGIN, footer_y - 2 * mm,
                               width=6 * mm, height=6 * mm, preserveAspectRatio=True)
                text_x = PatternPDFService.MARGIN + 8 * mm
            except:
                text_x = PatternPDFService.MARGIN
        else:
            text_x = PatternPDFService.MARGIN

        canvas.setFont('Helvetica', 8)
        canvas.setFillColor(colors.gray)
        canvas.drawString(text_x, footer_y, PatternPDFService.SITE_URL)

        # Right side: page number
        page_text = f"Page {page_num} / {total_pages}"
        canvas.drawRightString(width - PatternPDFService.MARGIN, footer_y, page_text)

        # Line above footer
        canvas.setStrokeColor(colors.lightgrey)
        canvas.line(PatternPDFService.MARGIN, footer_y + 5 * mm,
                   width - PatternPDFService.MARGIN, footer_y + 5 * mm)

        canvas.restoreState()

    @staticmethod
    def _numpy_to_image_buffer(img_array) -> io.BytesIO:
        """Convert numpy array to PNG image buffer."""
        from PIL import Image as PILImage

        # PatternRenderer already returns RGB arrays, no conversion needed
        pil_image = PILImage.fromarray(img_array.astype('uint8'))

        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        return buffer
