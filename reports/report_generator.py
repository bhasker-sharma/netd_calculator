import os
from datetime import datetime
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.netd_calculator import NETDResult

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY       = colors.HexColor("#1A3A6E")
LIGHT_BLUE = colors.HexColor("#E8EDF5")
DARK_GRAY  = colors.HexColor("#333355")
MID_GRAY   = colors.HexColor("#888899")
WHITE      = colors.white
BLACK      = colors.black

# ── Asset path ────────────────────────────────────────────────────────────────
_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(_ASSETS, "logo.png")

# ── Page dimensions ───────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
CONTENT_W = PAGE_W - 40 * mm   # usable width after L/R margins


class ReportGenerator:
    """Builds a PDF NETD analysis report using ReportLab."""

    def __init__(
        self,
        result: NETDResult,
        metadata: dict,
        image_path: Optional[str] = None,
    ):
        self.result = result
        self.metadata = metadata          # keys: model_name, serial_number, emissivity, datetime, verified_by
        self.image_path = image_path

    # ── Public ────────────────────────────────────────────────────────────────

    def generate(self, output_path: str) -> None:
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=15 * mm,
            bottomMargin=28 * mm,
            title="NETD Analysis Report — TIPL",
            author="TIPL",
        )
        story = self._build_story()
        doc.build(story, onFirstPage=self._draw_footer, onLaterPages=self._draw_footer)

    # ── Footer (canvas-level) ─────────────────────────────────────────────────

    def _draw_footer(self, canvas, doc):
        canvas.saveState()
        y_line = 20 * mm
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(0.6)
        canvas.line(20 * mm, y_line, PAGE_W - 20 * mm, y_line)

        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MID_GRAY)
        ts = datetime.now().strftime("%d-%m-%Y  %H:%M:%S")
        canvas.drawString(20 * mm, 13 * mm, f"Generated: {ts}")
        canvas.drawCentredString(PAGE_W / 2, 13 * mm, "TIPL — Thermal Camera NETD Analysis Report")
        canvas.drawRightString(PAGE_W - 20 * mm, 13 * mm, f"Page {doc.page}")
        canvas.restoreState()

    # ── Story builder ─────────────────────────────────────────────────────────

    def _build_story(self):
        story = []

        story += self._header_block()
        story.append(HRFlowable(width="100%", thickness=1.5, color=NAVY, spaceAfter=10))
        story += self._title_block()
        story.append(Spacer(1, 10))
        story.append(self._netd_result_box())
        story.append(Spacer(1, 14))
        story.append(self._metadata_table())

        if self.image_path and os.path.exists(self.image_path):
            story.append(Spacer(1, 14))
            story.append(self._thermal_image_block())

        story.append(Spacer(1, 14))
        story.append(self._verified_by_block())

        return story

    # ── Sections ──────────────────────────────────────────────────────────────

    def _header_block(self):
        """Logo left, company right."""
        left_cell = ""
        if os.path.exists(LOGO_PATH):
            left_cell = Image(LOGO_PATH, width=38 * mm, height=15 * mm, kind="proportional")

        company_style = ParagraphStyle(
            "Company", fontSize=13, textColor=NAVY,
            fontName="Helvetica-Bold", alignment=TA_RIGHT,
        )
        tagline_style = ParagraphStyle(
            "Tagline", fontSize=8, textColor=MID_GRAY,
            fontName="Helvetica", alignment=TA_RIGHT,
        )
        right_cell = [
            Paragraph("TIPL", company_style),
            Paragraph("Thermal Imaging &amp; Precision Labs", tagline_style),
        ]

        header_data = [[left_cell, right_cell]]
        t = Table(header_data, colWidths=[CONTENT_W * 0.45, CONTENT_W * 0.55])
        t.setStyle(TableStyle([
            ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
            ("ALIGN",   (0, 0), (0, 0),   "LEFT"),
            ("ALIGN",   (1, 0), (1, 0),   "RIGHT"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return [t]

    def _title_block(self):
        title_style = ParagraphStyle(
            "RTitle", fontSize=17, textColor=NAVY,
            fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=3,
        )
        sub_style = ParagraphStyle(
            "RSub", fontSize=10, textColor=MID_GRAY,
            fontName="Helvetica", alignment=TA_CENTER,
        )
        return [
            Paragraph("NETD Analysis Report", title_style),
            Paragraph("Thermal Camera — Noise Equivalent Temperature Difference", sub_style),
        ]

    def _netd_result_box(self):
        label_style = ParagraphStyle(
            "NL", fontSize=10, textColor=colors.HexColor("#B8C8E8"),
            fontName="Helvetica", alignment=TA_CENTER,
        )
        value_style = ParagraphStyle(
            "NV", fontSize=34, textColor=WHITE,
            fontName="Helvetica-Bold", alignment=TA_CENTER,
        )
        unit_style = ParagraphStyle(
            "NU", fontSize=11, textColor=colors.HexColor("#B8C8E8"),
            fontName="Helvetica", alignment=TA_CENTER,
        )

        data = [
            [Paragraph("NETD Result", label_style)],
            [Paragraph(f"{self.result.netd_mk}", value_style)],
            [Paragraph("mK  (Millikelvin)", unit_style)],
        ]
        t = Table(data, colWidths=[CONTENT_W])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 16),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ]))
        return t

    def _metadata_table(self):
        header_style = ParagraphStyle(
            "TH", fontSize=9, textColor=WHITE, fontName="Helvetica-Bold",
        )
        key_style = ParagraphStyle(
            "TK", fontSize=9, textColor=DARK_GRAY, fontName="Helvetica-Bold",
        )
        val_style = ParagraphStyle(
            "TV", fontSize=9, textColor=BLACK, fontName="Helvetica",
        )

        rows = [
            ("Model Name",          self.metadata.get("model_name", "N/A")),
            ("Serial Number",       self.metadata.get("serial_number", "N/A")),
            ("Emissivity",          str(self.metadata.get("emissivity", "N/A"))),
            ("Date & Time",         self.metadata.get("datetime", "N/A")),
            ("ROI Size (pixels)",   self.result.roi_size),
            ("Total Samples (N)",   str(self.result.N)),
            ("Mean Temperature",    f"{self.result.mean:.4f} °C"),
            ("Std Deviation (σ)",   f"{self.result.sigma:.6f} °C"),
        ]

        data = [
            [Paragraph("Parameter", header_style), Paragraph("Value", header_style)],
        ] + [
            [Paragraph(k, key_style), Paragraph(v, val_style)] for k, v in rows
        ]

        col_w = [CONTENT_W * 0.38, CONTENT_W * 0.62]
        t = Table(data, colWidths=col_w)

        style = [
            ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#C8C8D4")),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]
        # Alternating row colours for data rows
        for i in range(1, len(data)):
            bg = WHITE if i % 2 == 1 else LIGHT_BLUE
            style.append(("BACKGROUND", (0, i), (-1, i), bg))

        t.setStyle(TableStyle(style))
        return t

    def _thermal_image_block(self):
        heading_style = ParagraphStyle(
            "ImgH", fontSize=11, textColor=NAVY,
            fontName="Helvetica-Bold", spaceAfter=6,
        )
        img = Image(self.image_path, width=110 * mm, height=80 * mm, kind="proportional")
        img.hAlign = "CENTER"
        return KeepTogether([
            Paragraph("Thermal Reference Image", heading_style),
            img,
        ])

    def _verified_by_block(self):
        key_style = ParagraphStyle(
            "VK", fontSize=9, textColor=DARK_GRAY, fontName="Helvetica-Bold",
        )
        val_style = ParagraphStyle(
            "VV", fontSize=9, textColor=BLACK, fontName="Helvetica",
        )
        line_style = ParagraphStyle(
            "VL", fontSize=9, textColor=MID_GRAY, fontName="Helvetica",
        )

        verified_by = self.metadata.get("verified_by", "N/A")
        data = [
            [Paragraph("Verified By", key_style),  Paragraph(verified_by, val_style)],
            [Paragraph("Signature",   key_style),  Paragraph("_" * 35, line_style)],
        ]
        col_w = [CONTENT_W * 0.28, CONTENT_W * 0.72]
        t = Table(data, colWidths=col_w)
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BLUE),
            ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#C8C8D4")),
            ("TOPPADDING",    (0, 0), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ("LEFTPADDING",   (0, 0), (-1, -1), 10),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 10),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return t
