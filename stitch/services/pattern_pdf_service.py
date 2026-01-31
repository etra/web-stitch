"""
PDF generation service for cross-stitch patterns.

Uses ReportLab to generate printable PDF documents with pattern overview,
color legend, and paginated symbol charts.
"""
import io
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

from stitch.services.pattern_renderer import PatternRenderer


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
    def generate_pdf(project, logo_path: str = None, grid_style: str = 'symbols') -> bytes:
        """
        Generate a complete pattern PDF.

        Args:
            project: Project object with state, dimensions, etc.
            logo_path: Path to logo image file (optional)
            grid_style: 'symbols' for black symbols on white, 'colored' for symbols on colored backgrounds

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

        # Build document elements
        elements = []
        styles = PatternPDFService._get_styles()

        # Generate pattern data
        legend = PatternRenderer.generate_legend(
            project.state, project.width, project.height
        )
        total_stitches = sum(color['count'] for color in legend)

        # Legend grouped by stitch type
        legend_by_stitch = PatternRenderer.generate_legend_by_stitch_type(
            project.state, project.width, project.height
        )

        # Page 1: Overview
        elements.extend(PatternPDFService._build_overview_page(
            project, legend, total_stitches, styles, logo_path
        ))

        # Page 2: Legend by Color
        elements.append(PageBreak())
        elements.extend(PatternPDFService._build_legend_page(
            legend, total_stitches, styles
        ))

        # Page 3: Legend by Stitch Type
        elements.append(PageBreak())
        elements.extend(PatternPDFService._build_legend_by_stitch_page(
            legend_by_stitch, total_stitches, styles
        ))

        # Pages 4+: Pattern grids
        page_definitions = PatternRenderer.calculate_pattern_pages(
            project.width, project.height, page_size=50, overlap=5
        )

        for page_def in page_definitions:
            elements.append(PageBreak())
            elements.extend(PatternPDFService._build_pattern_page(
                project, page_def, styles, grid_style
            ))

        # Calculate total pages for footer
        # 1 (overview) + 1 (legend by color) + 1 (legend by stitch) + pattern pages
        total_pages = 3 + len(page_definitions)

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
    def _build_overview_page(project, legend, total_stitches, styles, logo_path) -> List:
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
            project.state, project.width, project.height, max_size=400
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
            ['Cloth Color:', project.cloth_color],
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
    def _build_legend_page(legend, total_stitches, styles) -> List:
        """Build the color legend page elements."""
        elements = []

        elements.append(Paragraph('Color Legend & Thread Requirements', styles['PatternTitle']))
        elements.append(Spacer(1, 5 * mm))

        if not legend:
            elements.append(Paragraph('No stitches found in exportable layers.', styles['Normal']))
            return elements

        # Legend table: Stitch Icon | Symbol | Color | Color Name | Thread Code | Stitches | Skeins
        table_data = [['Stitch', 'Symbol', 'Color', 'Color Name', 'Thread Code', 'Stitches', 'Skeins*']]

        for color in legend:
            thread_code = f"{color['vendor']} {color['code']}" if color.get('vendor') and color.get('code') else 'Custom'
            stitch_icon = color.get('stitchIcon', '✕')
            skeins = round(color['count'] / 200, 1)

            table_data.append([
                stitch_icon,
                color['symbol'],
                '',  # Color swatch placeholder - we'll style this cell
                color['name'],
                thread_code,
                f"{color['count']:,}",
                str(skeins)
            ])

        # Add totals row
        table_data.append(['', '', '', '', 'Total:', f"{total_stitches:,}", ''])

        col_widths = [1.2 * cm, 1.2 * cm, 1 * cm, 4.5 * cm, 2.5 * cm, 2 * cm, 1.5 * cm]
        legend_table = Table(table_data, colWidths=col_widths)

        # Build table style
        table_style = [
            # Header row
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            # Content rows
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ALIGN', (0, 0), (1, -1), 'CENTER'),  # Stitch icon and Symbol centered
            ('ALIGN', (5, 0), (6, -1), 'RIGHT'),  # Stitches and skeins right-aligned
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('TOPPADDING', (0, 1), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
            # Grid
            ('GRID', (0, 0), (-1, -2), 0.5, colors.lightgrey),
            # Totals row
            ('FONTNAME', (4, -1), (5, -1), 'Helvetica-Bold'),
            ('LINEABOVE', (0, -1), (-1, -1), 1, colors.black),
        ]

        # Add color swatches to each data row (column 2 now)
        for i, color in enumerate(legend):
            row_idx = i + 1  # Skip header
            hex_color = color['rgbHex']
            try:
                rgb = tuple(int(hex_color.lstrip('#')[j:j+2], 16) / 255 for j in (0, 2, 4))
                table_style.append(('BACKGROUND', (2, row_idx), (2, row_idx), colors.Color(*rgb)))
            except:
                pass

        legend_table.setStyle(TableStyle(table_style))
        elements.append(legend_table)

        # Skein calculation note
        elements.append(Spacer(1, 8 * mm))
        elements.append(Paragraph(
            '*Skein Calculation: Approximate 6-strand embroidery floss skeins required '
            '(estimated at ~200 stitches per skein on 14-count Aida). Actual usage varies '
            'based on fabric count, stitch type, and technique. Purchase 1-2 extra skeins per color.',
            styles['SmallNote']
        ))

        return elements

    @staticmethod
    def _build_legend_by_stitch_page(legend_by_stitch: Dict, total_stitches: int, styles) -> List:
        """Build the color legend page grouped by stitch type."""
        elements = []

        elements.append(Paragraph('Thread Requirements by Stitch Type', styles['PatternTitle']))
        elements.append(Spacer(1, 5 * mm))

        if not legend_by_stitch:
            elements.append(Paragraph('No stitches found in exportable layers.', styles['Normal']))
            return elements

        col_widths = [1.2 * cm, 1.2 * cm, 1 * cm, 4.5 * cm, 2.5 * cm, 2 * cm, 1.5 * cm]

        for category, color_list in legend_by_stitch.items():
            # Category header
            category_stitches = sum(c['count'] for c in color_list)
            elements.append(Paragraph(
                f"<b>{category}</b> — {len(color_list)} color{'s' if len(color_list) != 1 else ''}, "
                f"{category_stitches:,} stitches",
                styles['SectionHeader']
            ))

            # Category legend table: Stitch Icon | Symbol | Color | Color Name | Thread Code | Stitches | Skeins
            table_data = [['Stitch', 'Symbol', 'Color', 'Color Name', 'Thread Code', 'Stitches', 'Skeins*']]

            for color in color_list:
                thread_code = f"{color['vendor']} {color['code']}" if color.get('vendor') and color.get('code') else 'Custom'
                stitch_icon = color.get('stitchIcon', '✕')
                skeins = round(color['count'] / 200, 1)

                table_data.append([
                    stitch_icon,
                    color['symbol'],
                    '',  # Color swatch placeholder
                    color['name'],
                    thread_code,
                    f"{color['count']:,}",
                    str(skeins)
                ])

            category_table = Table(table_data, colWidths=col_widths)

            # Build table style
            table_style = [
                # Header row
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
                # Content rows
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('ALIGN', (0, 0), (1, -1), 'CENTER'),  # Stitch icon and Symbol centered
                ('ALIGN', (5, 0), (6, -1), 'RIGHT'),  # Stitches and skeins right-aligned
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 1), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 1), (-1, -1), 3),
                # Grid
                ('GRID', (0, 0), (-1, -1), 0.5, colors.lightgrey),
            ]

            # Add color swatches to each data row (column 2 now)
            for i, color in enumerate(color_list):
                row_idx = i + 1  # Skip header
                hex_color = color['rgbHex']
                try:
                    rgb = tuple(int(hex_color.lstrip('#')[j:j+2], 16) / 255 for j in (0, 2, 4))
                    table_style.append(('BACKGROUND', (2, row_idx), (2, row_idx), colors.Color(*rgb)))
                except:
                    pass

            category_table.setStyle(TableStyle(table_style))
            elements.append(category_table)
            elements.append(Spacer(1, 6 * mm))

        # Total summary
        elements.append(Paragraph(
            f"<b>Total: {total_stitches:,} stitches across {len(legend_by_stitch)} stitch type{'s' if len(legend_by_stitch) != 1 else ''}</b>",
            styles['Normal']
        ))

        # Skein calculation note
        elements.append(Spacer(1, 8 * mm))
        elements.append(Paragraph(
            '*Skein Calculation: Approximate 6-strand embroidery floss skeins required '
            '(estimated at ~200 stitches per skein on 14-count Aida). Actual usage varies '
            'based on fabric count, stitch type, and technique. Purchase 1-2 extra skeins per color.',
            styles['SmallNote']
        ))

        return elements

    @staticmethod
    def _build_pattern_page(project, page_def: Dict, styles, grid_style: str = 'symbols') -> List:
        """Build a pattern grid page."""
        elements = []

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
        colored = (grid_style == 'colored')
        page_image = PatternRenderer.render_symbol_page(
            project.state,
            project.width,
            project.height,
            page_def['x_start'],
            page_def['y_start'],
            page_def['x_end'],
            page_def['y_end'],
            cell_size=14,  # Smaller for PDF to fit on page
            colored_background=colored
        )

        img_buffer = PatternPDFService._numpy_to_image_buffer(page_image)

        # Calculate image size to fit page
        available_width = PatternPDFService.PAGE_SIZE[0] - 2 * PatternPDFService.MARGIN
        available_height = PatternPDFService.PAGE_SIZE[1] - 2 * PatternPDFService.MARGIN - 4 * cm  # Leave room for header/footer

        # Get image aspect ratio
        img_height, img_width = page_image.shape[:2]
        aspect_ratio = img_width / img_height

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
        import cv2

        # Ensure RGB format
        if len(img_array.shape) == 3 and img_array.shape[2] == 3:
            # Convert from BGR to RGB if needed (OpenCV uses BGR)
            img_rgb = cv2.cvtColor(img_array, cv2.COLOR_BGR2RGB) if img_array.dtype == 'uint8' else img_array
        else:
            img_rgb = img_array

        pil_image = PILImage.fromarray(img_rgb.astype('uint8'))

        buffer = io.BytesIO()
        pil_image.save(buffer, format='PNG', optimize=True)
        buffer.seek(0)

        return buffer
