import os
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.logger import AppLogger
from core.netd_calculator import MultiFrameResult

log = AppLogger.get(__name__)

# ── Colours ───────────────────────────────────────────────────────────────────
NAVY      = colors.HexColor("#1A3A6E")
DARK_GRAY = colors.HexColor("#333355")
MID_GRAY  = colors.HexColor("#888899")
LIGHT_BG  = colors.HexColor("#F5F6FA")
BLACK     = colors.black

# ── Asset path ────────────────────────────────────────────────────────────────
_ASSETS   = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
LOGO_PATH = os.path.join(_ASSETS, "logo.png")

# ── Page dimensions ───────────────────────────────────────────────────────────
PAGE_W, PAGE_H = A4
CONTENT_W = PAGE_W - 40 * mm

# ── Applicable standards ──────────────────────────────────────────────────────
_STANDARDS = [
    "VDI/VDE 5585 Part 1 (2018)",
    "ASTM E1543-14 (2022)",
    "ISO 18554:2017",
    "ISO/IEC 17025:2017",
]


class ReportGenerator:
    """Builds the Multi-Frame Thermal Sensitivity (NETD) Analysis PDF report."""

    def __init__(self, result: MultiFrameResult, metadata: dict):
        self.result = result
        self.metadata = metadata

    # ── Public ────────────────────────────────────────────────────────────────

    def generate(self, output_path: str) -> None:
        log.info("Building PDF report: %s", output_path)
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20 * mm,
            leftMargin=20 * mm,
            topMargin=15 * mm,
            bottomMargin=30 * mm,
            title="Multi-Frame Thermal Sensitivity (NETD) Analysis Report — TIPL",
            author="TIPL",
        )
        story = self._build_story()
        doc.build(story, onFirstPage=self._draw_footer, onLaterPages=self._draw_footer)
        log.info("PDF report written successfully")

    # ── Footer (canvas-level) ─────────────────────────────────────────────────

    def _draw_footer(self, canvas, doc):
        canvas.saveState()

        canvas.setStrokeColor(NAVY)
        canvas.setLineWidth(0.6)
        canvas.line(20 * mm, 24 * mm, PAGE_W - 20 * mm, 24 * mm)

        # Standards alignment note — small text between rule and footer line
        canvas.setFont("Helvetica-Bold", 5.8)
        canvas.setFillColor(MID_GRAY)
        canvas.drawCentredString(
            PAGE_W / 2, 22 * mm,
            "Standards Alignment: The methodology is aligned with internationally recognized standards and best practices.",
        )
        canvas.setFont("Helvetica", 5.8)
        canvas.drawCentredString(
            PAGE_W / 2, 19.8 * mm,
            "Primary Standards (Infrared Imaging Performance): ASTM E1543-14 (2022)  \u00b7  VDI/VDE 5585 Part 1 (2018)  \u00b7  ISO 18554:2017 (general guidance reference)",
        )
        canvas.drawCentredString(
            PAGE_W / 2, 17.8 * mm,
            "Supporting Standards (Noise Characterization): ISO 15739  \u00b7  EMVA 1288    \u2502    Quality & Laboratory Compliance: ISO/IEC 17025:2017",
        )

        canvas.setFont("Helvetica", 7.5)
        canvas.setFillColor(MID_GRAY)
        ts = datetime.now().strftime("%d-%m-%Y  %H:%M:%S")
        canvas.drawString(20 * mm, 14 * mm, f"Generated: {ts}")
        canvas.drawCentredString(
            PAGE_W / 2, 14 * mm,
            "TIPL \u2014 Multi-Frame Thermal Sensitivity (NETD) Analysis Report",
        )
        canvas.drawRightString(PAGE_W - 20 * mm, 14 * mm, f"Page {doc.page}")

        canvas.restoreState()

    # ── Story builder ─────────────────────────────────────────────────────────

    def _build_story(self):
        story = []

        story += self._header_block()
        story.append(HRFlowable(width="100%", thickness=1.2, color=NAVY, spaceAfter=8))
        story += self._title_block()
        story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY,
                                spaceBefore=6, spaceAfter=8))
        story += self._section_label("Test Parameters")
        story.append(self._parameters_table())
        story.append(Spacer(1, 8))
        story.append(HRFlowable(width="100%", thickness=0.5, color=MID_GRAY, spaceAfter=8))
        story += self._section_label("Calculation — Frame Analysis")
        story.append(self._frames_table())
        story.append(Spacer(1, 6))
        story += self._summary_block()
        story.append(Spacer(1, 12))
        story += self._signature_block()

        return story

    # ── Sections ──────────────────────────────────────────────────────────────

    def _header_block(self):
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
            fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=6,
        )
        sub_style = ParagraphStyle(
            "RSub", fontSize=10, textColor=MID_GRAY,
            fontName="Helvetica", alignment=TA_CENTER,
        )
        return [
            Paragraph("Multi-Frame Thermal Sensitivity (NETD) Analysis Report", title_style),
            Paragraph(
                "Thermal Camera &#8212; Noise Equivalent Temperature Difference",
                sub_style,
            ),
        ]

    def _parameters_table(self):
        key_style = ParagraphStyle(
            "TK", fontSize=9, textColor=DARK_GRAY, fontName="Helvetica-Bold",
        )
        val_style = ParagraphStyle(
            "TV", fontSize=9, textColor=BLACK, fontName="Helvetica",
        )
        m = self.metadata
        rows = [
            ("Thermal Imager Model",    m.get("model", "N/A")),
            ("Serial Number",           m.get("serial_number", "N/A")),
            ("Condition",               m.get("condition", "Satisfactory")),
            ("Thermal Imager Make",     m.get("make", "TIPL")),
            ("Black Body Name",         m.get("blackbody_name", "N/A")),
            ("Black Body Emissivity",   str(m.get("blackbody_emissivity", "N/A"))),
            ("Relative Humidity",       f"{m.get('relative_humidity', 'N/A')} %"),
            ("Ambient Temperature",     f"{m.get('ambient_temp', 'N/A')} \u00b0C"),
            ("Stabilisation Time",      m.get("stabilisation_time", "30 minutes")),
            ("Airflow Disturbance",     m.get("airflow_disturbance", "Negligible")),
            ("Confidence Level",        "High"),
        ]
        data = [[Paragraph(k, key_style), Paragraph(v, val_style)] for k, v in rows]
        t = Table(data, colWidths=[CONTENT_W * 0.38, CONTENT_W * 0.62])
        t.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 2),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LINEBELOW",     (0, 0), (-1, -2), 0.3, colors.HexColor("#DDDDDD")),
        ]))
        return t

    def _standards_block(self):
        heading_style = ParagraphStyle(
            "StdH", fontSize=9, textColor=MID_GRAY,
            fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=3,
        )
        item_style = ParagraphStyle(
            "StdI", fontSize=9, textColor=DARK_GRAY,
            fontName="Helvetica", alignment=TA_LEFT, spaceBefore=2,
        )
        items = [Paragraph("APPLICABLE STANDARDS", heading_style)]
        for std in _STANDARDS:
            items.append(Paragraph(f"\u2022  {std}", item_style))
        return items

    def _frames_table(self):
        hdr_style = ParagraphStyle(
            "FH", fontSize=9, textColor=colors.white,
            fontName="Helvetica-Bold", alignment=TA_CENTER,
        )
        num_style = ParagraphStyle(
            "FNum", fontSize=9, textColor=DARK_GRAY,
            fontName="Helvetica", alignment=TA_CENTER,
        )
        name_style = ParagraphStyle(
            "FName", fontSize=9, textColor=DARK_GRAY,
            fontName="Helvetica", alignment=TA_LEFT,
        )

        header_row = [
            Paragraph("Sr. No.", hdr_style),
            Paragraph("File Name", hdr_style),
            Paragraph("Avg. Temp (\u00b0C)", hdr_style),
            Paragraph("NETD (mK)", hdr_style),
        ]
        data = [header_row]

        for i, frame in enumerate(self.result.frames, start=1):
            data.append([
                Paragraph(str(i), num_style),
                Paragraph(frame.filename, name_style),
                Paragraph(f"{frame.tbar:.4f}", num_style),
                Paragraph(f"{frame.netd_mk:.1f}", num_style),
            ])

        col_widths = [CONTENT_W * w for w in (0.08, 0.50, 0.21, 0.21)]
        t = Table(data, colWidths=col_widths)
        t.setStyle(TableStyle([
            ("BACKGROUND",     (0, 0), (-1, 0),  NAVY),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, LIGHT_BG]),
            ("TOPPADDING",     (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
            ("LEFTPADDING",    (0, 0), (-1, -1), 6),
            ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
            ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",           (0, 0), (-1, -1), 0.3, colors.HexColor("#CCCCCC")),
            ("LINEBELOW",      (0, 0), (-1, 0),  1.0, NAVY),
        ]))
        return t

    def _summary_block(self):
        key_style = ParagraphStyle(
            "SumK", fontSize=10, textColor=DARK_GRAY,
            fontName="Helvetica-Bold",
        )
        val_style = ParagraphStyle(
            "SumV", fontSize=10, textColor=NAVY,
            fontName="Helvetica-Bold",
        )
        netd_style = ParagraphStyle(
            "SumN", fontSize=12, textColor=NAVY,
            fontName="Helvetica-Bold",
        )

        data = [
            [
                Paragraph("Thermal Sensitivity (NETD)", key_style),
                Paragraph(f"{self.result.netd_mk:.1f} mK", netd_style),
            ],
        ]
        t = Table(data, colWidths=[CONTENT_W * 0.55, CONTENT_W * 0.45])
        t.setStyle(TableStyle([
            ("BACKGROUND",    (0, 0), (-1, -1), LIGHT_BG),
            ("TOPPADDING",    (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ("LEFTPADDING",   (0, 0), (-1, -1), 8),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 8),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
            ("LINEABOVE",     (0, 0), (-1,  0), 0.8, NAVY),
            ("LINEBELOW",     (0, -1), (-1, -1), 0.8, NAVY),
        ]))
        return [t]

    def _signature_block(self):
        from reportlab.platypus import KeepTogether
        key_style = ParagraphStyle(
            "SigK", fontSize=9, textColor=DARK_GRAY, fontName="Helvetica-Bold",
        )
        val_style = ParagraphStyle(
            "SigV", fontSize=9, textColor=BLACK, fontName="Helvetica",
        )
        line_style = ParagraphStyle(
            "SigL", fontSize=9, textColor=MID_GRAY, fontName="Helvetica",
        )
        verified_by = self.metadata.get("verified_by", "N/A")
        data = [
            [Paragraph("Verified By:", key_style), Paragraph(verified_by, val_style)],
            [Paragraph("Signature:", key_style),   Paragraph("_" * 38, line_style)],
        ]
        t = Table(data, colWidths=[CONTENT_W * 0.20, CONTENT_W * 0.80])
        t.setStyle(TableStyle([
            ("TOPPADDING",    (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ("LEFTPADDING",   (0, 0), (-1, -1), 2),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
            ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ]))
        return [KeepTogether([t])]

    def _section_label(self, text: str):
        style = ParagraphStyle(
            "SecLabel", fontSize=9, textColor=MID_GRAY,
            fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4,
        )
        return [Paragraph(text.upper(), style)]

