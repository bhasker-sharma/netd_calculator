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

from core.logger import AppLogger
from core.netd_calculator import NETDResult

log = AppLogger.get(__name__)

# ── Colours ──────────────────────────────────────────────────────────────────
NAVY      = colors.HexColor("#1A3A6E")
DARK_GRAY = colors.HexColor("#333355")
MID_GRAY  = colors.HexColor("#888899")
BLACK     = colors.black

# ── Asset path ────────────────────────────────────────────────────────────────
_ASSETS   = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
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
        log.info("Building PDF report: %s", output_path)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=15 * mm,
            bottomMargin=42 * mm,          # extra space for verified-by drawn on canvas
            title="NETD Analysis Report — TIPL",
            author="TIPL",
        )
        story = self._build_story()
        doc.build(story, onFirstPage=self._draw_footer, onLaterPages=self._draw_footer)
        log.info("PDF report written successfully")

    # ── Footer (canvas-level) ─────────────────────────────────────────────────

    def _draw_footer(self, canvas, doc):
        canvas.saveState()

        # ── Verified by — pinned above the divider line ───────────────────────
        verified_by = self.metadata.get("verified_by", "N/A")

        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(DARK_GRAY)
        canvas.drawString(20 * mm, 37 * mm, "Verified By:")
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(BLACK)
        canvas.drawString(52 * mm, 37 * mm, verified_by)

        canvas.setFont("Helvetica-Bold", 9)
        canvas.setFillColor(DARK_GRAY)
        canvas.drawString(20 * mm, 30 * mm, "Signature:")
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(MID_GRAY)
        canvas.drawString(52 * mm, 30 * mm, "_" * 38)

        # ── Divider ───────────────────────────────────────────────────────────
        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(0.6)
        canvas.line(20 * mm, 24 * mm, PAGE_W - 20 * mm, 24 * mm)

        # ── Footer text ───────────────────────────────────────────────────────
        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MID_GRAY)
        ts = datetime.now().strftime("%d-%m-%Y  %H:%M:%S")
        canvas.drawString(20 * mm, 17 * mm, f"Generated: {ts}")
        canvas.drawCentredString(PAGE_W / 2, 17 * mm, "TIPL — Thermal Camera NETD Analysis Report")
        canvas.drawRightString(PAGE_W - 20 * mm, 17 * mm, f"Page {doc.page}")

        canvas.restoreState()

    # ── Story builder ─────────────────────────────────────────────────────────

    def _build_story(self):
        story = []

        story += self._header_block()
        story.append(HRFlowable(width="100%", thickness=1.2, color=NAVY, spaceAfter=8))
        story += self._title_block()
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY, spaceAfter=8))
        story += self._netd_result_block()
        story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY, spaceBefore=8, spaceAfter=8))
        story += self._section_label("Test Parameters")
        story.append(self._metadata_table())

        if self.image_path and os.path.exists(self.image_path):
            story.append(Spacer(1, 10))
            story.append(self._thermal_image_block())

        return story

    # ── Sections ──────────────────────────────────────────────────────────────

    def _header_block(self):
        """Logo left, company name right — invisible layout table."""
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

        t = Table([[left_cell, right_cell]], colWidths=[CONTENT_W * 0.45, CONTENT_W * 0.55])
        t.setStyle(TableStyle([
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        return [t]

    def _title_block(self):
        title_style = ParagraphStyle(
            "RTitle", fontSize=17, textColor=NAVY,
            fontName="Helvetica-Bold", alignment=TA_CENTER,
            spaceAfter=8,
        )
        sub_style = ParagraphStyle(
            "RSub", fontSize=10, textColor=MID_GRAY,
            fontName="Helvetica", alignment=TA_CENTER,
            spaceBefore=0,
        )
        return [
            Paragraph("NETD Analysis Report", title_style),
            Paragraph("Thermal Camera \u2014 Noise Equivalent Temperature Difference", sub_style),
        ]

    def _netd_result_block(self):
        # Everything on one line: label — value unit
        style = ParagraphStyle(
            "NResult",
            fontName="Helvetica",
            fontSize=11,
            textColor=MID_GRAY,
            alignment=TA_CENTER,
            leading=30,        # tall enough for the 22pt bold value
        )
        markup = (
            '<font name="Helvetica" size="11" color="#888899">NETD Result &#8212; </font>'
            f'<font name="Helvetica-Bold" size="22" color="#1A3A6E">{self.result.netd_mk}</font>'
            '<font name="Helvetica" size="12" color="#888899">  mK  (Millikelvin)</font>'
        )
        return [Paragraph(markup, style)]

    def _section_label(self, text: str):
        style = ParagraphStyle(
            "SecLabel", fontSize=9, textColor=MID_GRAY,
            fontName="Helvetica-Bold", spaceAfter=4,
        )
        return [Paragraph(text.upper(), style)]

    def _metadata_table(self):
        key_style = ParagraphStyle(
            "TK", fontSize=9, textColor=DARK_GRAY, fontName="Helvetica-Bold",
        )
        val_style = ParagraphStyle(
            "TV", fontSize=9, textColor=BLACK, fontName="Helvetica",
        )

        rows = [
            ("Model Name",        self.metadata.get("model_name", "N/A")),
            ("Serial Number",     self.metadata.get("serial_number", "N/A")),
            ("Emissivity",        str(self.metadata.get("emissivity", "N/A"))),
            ("Date & Time",       self.metadata.get("datetime", "N/A")),
            ("ROI Size (pixels)", self.result.roi_size),
            ("Total Samples (N)", str(self.result.N)),
            ("Mean Temperature",  f"{self.result.mean:.4f} \u00b0C"),
            ("Std Deviation (\u03c3)", f"{self.result.sigma:.6f} \u00b0C"),
        ]

        data = [[Paragraph(k, key_style), Paragraph(v, val_style)] for k, v in rows]
        t = Table(data, colWidths=[CONTENT_W * 0.38, CONTENT_W * 0.62])
        t.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 2),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            # thin bottom border on each row as a light separator
            ("LINEBELOW", (0, 0), (-1, -2), 0.3, colors.HexColor("#DDDDDD")),
        ]))
        return t

    def _thermal_image_block(self):
        heading_style = ParagraphStyle(
            "ImgH", fontSize=9, textColor=MID_GRAY,
            fontName="Helvetica-Bold", spaceAfter=4,
        )
        img = Image(self.image_path, width=90 * mm, height=65 * mm, kind="proportional")
        img.hAlign = "CENTER"
        return KeepTogether([
            Paragraph("THERMAL REFERENCE IMAGE", heading_style),
            img,
        ])
