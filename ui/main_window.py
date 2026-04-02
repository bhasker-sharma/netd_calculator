import os
from datetime import datetime

from PyQt5.QtCore import Qt, QDateTime
from PyQt5.QtGui import QFont, QIcon, QPixmap
from PyQt5.QtWidgets import (
    QDateTimeEdit,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from core.netd_calculator import NETDCalculator, NETDResult
from reports.report_generator import ReportGenerator

_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._excel_path: str = ""
        self._image_path: str = ""
        self._result: NETDResult | None = None

        self._setup_window()
        self._build_ui()
        self._apply_stylesheet()

    # ── Window setup ──────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("NETD Calculator — TIPL")
        ico = os.path.join(_ASSETS, "logo.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))
        self.setMinimumSize(720, 660)
        self.resize(820, 720)

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(10)
        root.setContentsMargins(20, 14, 20, 14)

        root.addWidget(self._build_header())
        root.addWidget(self._build_file_group())
        root.addWidget(self._build_metadata_group())
        root.addLayout(self._build_action_row())
        root.addWidget(self._build_results_group())

    def _build_header(self) -> QFrame:
        frame = QFrame()
        frame.setObjectName("headerFrame")
        layout = QHBoxLayout(frame)
        layout.setContentsMargins(0, 0, 0, 6)
        layout.setSpacing(14)

        logo_lbl = QLabel()
        logo_path = os.path.join(_ASSETS, "logo.png")
        if os.path.exists(logo_path):
            pix = QPixmap(logo_path).scaledToHeight(48, Qt.SmoothTransformation)
            logo_lbl.setPixmap(pix)
        layout.addWidget(logo_lbl, alignment=Qt.AlignVCenter)

        text_col = QVBoxLayout()
        text_col.setSpacing(2)
        title = QLabel("NETD Calculator")
        title.setObjectName("appTitle")
        sub = QLabel("Thermal Camera — Noise Equivalent Temperature Difference Analysis")
        sub.setObjectName("appSubtitle")
        text_col.addWidget(title)
        text_col.addWidget(sub)
        layout.addLayout(text_col)
        layout.addStretch()

        return frame

    def _build_file_group(self) -> QGroupBox:
        group = QGroupBox("Input Files")
        grid = QGridLayout(group)
        grid.setColumnStretch(1, 1)
        grid.setSpacing(10)
        grid.setContentsMargins(14, 14, 14, 14)

        # Excel
        grid.addWidget(QLabel("Temperature Matrix (.xlsx):"), 0, 0)
        self.excel_edit = QLineEdit()
        self.excel_edit.setPlaceholderText("Select Excel file containing temperature data...")
        self.excel_edit.setReadOnly(True)
        grid.addWidget(self.excel_edit, 0, 1)
        btn_xl = QPushButton("Browse")
        btn_xl.setObjectName("browseBtn")
        btn_xl.clicked.connect(self._browse_excel)
        grid.addWidget(btn_xl, 0, 2)

        # Image
        grid.addWidget(QLabel("Thermal Reference Image (.jpg):"), 1, 0)
        self.image_edit = QLineEdit()
        self.image_edit.setPlaceholderText("Select thermal image for report (optional)...")
        self.image_edit.setReadOnly(True)
        grid.addWidget(self.image_edit, 1, 1)
        btn_img = QPushButton("Browse")
        btn_img.setObjectName("browseBtn")
        btn_img.clicked.connect(self._browse_image)
        grid.addWidget(btn_img, 1, 2)

        return group

    def _build_metadata_group(self) -> QGroupBox:
        group = QGroupBox("Device & Test Parameters")
        grid = QGridLayout(group)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.setSpacing(10)
        grid.setContentsMargins(14, 14, 14, 14)

        # Row 0 — Model Name | Serial Number
        grid.addWidget(QLabel("Model Name:"), 0, 0)
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("e.g. TIPL-TC320")
        grid.addWidget(self.model_edit, 0, 1)

        grid.addWidget(QLabel("Serial Number:"), 0, 2)
        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("e.g. SN-2024-001")
        grid.addWidget(self.serial_edit, 0, 3)

        # Row 1 — Emissivity | Date & Time
        grid.addWidget(QLabel("Emissivity:"), 1, 0)
        self.emissivity_spin = QDoubleSpinBox()
        self.emissivity_spin.setRange(0.01, 1.0)
        self.emissivity_spin.setSingleStep(0.01)
        self.emissivity_spin.setDecimals(2)
        self.emissivity_spin.setValue(1.0)
        grid.addWidget(self.emissivity_spin, 1, 1)

        grid.addWidget(QLabel("Date & Time:"), 1, 2)
        self.datetime_edit = QDateTimeEdit(QDateTime.currentDateTime())
        self.datetime_edit.setDisplayFormat("dd-MM-yyyy  HH:mm")
        self.datetime_edit.setCalendarPopup(True)
        grid.addWidget(self.datetime_edit, 1, 3)

        # Row 2 — Verified By (spans full width)
        grid.addWidget(QLabel("Verified By:"), 2, 0)
        self.verified_edit = QLineEdit()
        self.verified_edit.setPlaceholderText("Engineer name or approver")
        grid.addWidget(self.verified_edit, 2, 1, 1, 3)

        return group

    def _build_action_row(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        layout.setSpacing(12)

        self.calc_btn = QPushButton("  Calculate NETD  ")
        self.calc_btn.setObjectName("calcBtn")
        self.calc_btn.setMinimumHeight(42)
        self.calc_btn.setCursor(Qt.PointingHandCursor)
        self.calc_btn.clicked.connect(self._run_calculation)

        self.report_btn = QPushButton("  Generate PDF Report  ")
        self.report_btn.setObjectName("reportBtn")
        self.report_btn.setMinimumHeight(42)
        self.report_btn.setCursor(Qt.PointingHandCursor)
        self.report_btn.setEnabled(False)
        self.report_btn.clicked.connect(self._generate_report)

        layout.addStretch()
        layout.addWidget(self.calc_btn)
        layout.addWidget(self.report_btn)
        layout.addStretch()

        return layout

    def _build_results_group(self) -> QGroupBox:
        self.results_group = QGroupBox("Results")
        outer = QHBoxLayout(self.results_group)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(20)

        # ── Left: large NETD value display ───────────────────────────────────
        left = QVBoxLayout()
        left.setSpacing(4)
        self.netd_value_lbl = QLabel("—")
        self.netd_value_lbl.setObjectName("netdValue")
        self.netd_value_lbl.setAlignment(Qt.AlignCenter)
        self.netd_unit_lbl = QLabel("mK  (NETD)")
        self.netd_unit_lbl.setObjectName("netdUnit")
        self.netd_unit_lbl.setAlignment(Qt.AlignCenter)
        left.addStretch()
        left.addWidget(self.netd_value_lbl)
        left.addWidget(self.netd_unit_lbl)
        left.addStretch()

        # ── Vertical divider ─────────────────────────────────────────────────
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setObjectName("divider")

        # ── Right: stats ──────────────────────────────────────────────────────
        right = QVBoxLayout()
        right.setSpacing(10)
        self._stat_labels: dict = {}
        stats = [
            ("Total Pixels (N)",       "N"),
            ("Mean Temperature (°C)",  "mean"),
            ("Std Deviation (σ)",       "sigma"),
            ("ROI Size",               "roi"),
        ]
        for label_text, key in stats:
            row = QHBoxLayout()
            key_lbl = QLabel(f"{label_text}")
            key_lbl.setObjectName("statKey")
            val_lbl = QLabel("—")
            val_lbl.setObjectName("statVal")
            val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
            row.addWidget(key_lbl)
            row.addStretch()
            row.addWidget(val_lbl)
            right.addLayout(row)
            self._stat_labels[key] = val_lbl
            if key != "roi":
                right.addWidget(self._thin_line())

        right.addStretch()

        outer.addLayout(left, 2)
        outer.addWidget(divider)
        outer.addLayout(right, 3)

        return self.results_group

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _thin_line() -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Plain)
        line.setObjectName("thinLine")
        return line

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _browse_excel(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Temperature Matrix", "",
            "Excel Files (*.xlsx *.xls)",
        )
        if path:
            self._excel_path = path
            self.excel_edit.setText(path)

    def _browse_image(self):
        path, _ = QFileDialog.getOpenFileName(
            self, "Select Thermal Image", "",
            "Images (*.jpg *.jpeg *.png *.bmp)",
        )
        if path:
            self._image_path = path
            self.image_edit.setText(path)

    def _run_calculation(self):
        if not self._excel_path:
            QMessageBox.warning(self, "Missing Input",
                                "Please select a temperature matrix Excel file.")
            return

        try:
            calc = NETDCalculator(self._excel_path)
            calc.load_excel()
            self._result = calc.calculate()
            self._display_result(self._result)
            self.report_btn.setEnabled(True)

        except Exception as exc:
            QMessageBox.critical(self, "Calculation Error", str(exc))

    def _display_result(self, result: NETDResult):
        self.netd_value_lbl.setText(str(result.netd_mk))
        self._stat_labels["N"].setText(f"{result.N:,}")
        self._stat_labels["mean"].setText(f"{result.mean:.4f} °C")
        self._stat_labels["sigma"].setText(f"{result.sigma:.6f} °C")
        self._stat_labels["roi"].setText(result.roi_size)

    def _generate_report(self):
        if not self._result:
            return

        default_name = f"NETD_Report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
        path, _ = QFileDialog.getSaveFileName(
            self, "Save PDF Report", default_name,
            "PDF Files (*.pdf)",
        )
        if not path:
            return

        metadata = {
            "model_name":    self.model_edit.text().strip()   or "N/A",
            "serial_number": self.serial_edit.text().strip()  or "N/A",
            "emissivity":    self.emissivity_spin.value(),
            "datetime":      self.datetime_edit.dateTime().toString("dd-MM-yyyy  HH:mm"),
            "verified_by":   self.verified_edit.text().strip() or "N/A",
        }

        try:
            gen = ReportGenerator(
                self._result,
                metadata,
                self._image_path or None,
            )
            gen.generate(path)
            QMessageBox.information(
                self, "Report Saved",
                f"PDF report saved successfully:\n\n{path}",
            )
        except Exception as exc:
            QMessageBox.critical(self, "Report Error", str(exc))

    # ── Stylesheet ────────────────────────────────────────────────────────────

    def _apply_stylesheet(self):
        self.setStyleSheet("""
            /* ── Base ─────────────────────────────────────────────────── */
            QMainWindow, QWidget {
                background-color: #F2F3F7;
                font-family: "Segoe UI", Arial, sans-serif;
                font-size: 13px;
                color: #1A1A2E;
            }

            /* ── Header ───────────────────────────────────────────────── */
            QFrame#headerFrame {
                background-color: transparent;
            }
            QLabel#appTitle {
                font-size: 20px;
                font-weight: bold;
                color: #1A3A6E;
            }
            QLabel#appSubtitle {
                font-size: 10px;
                color: #888899;
            }

            /* ── Group boxes ──────────────────────────────────────────── */
            QGroupBox {
                font-weight: bold;
                font-size: 12px;
                border: 1px solid #C8CADA;
                border-radius: 6px;
                margin-top: 10px;
                padding-top: 6px;
                background-color: #FFFFFF;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 2px 8px;
                color: #1A3A6E;
                background-color: #F2F3F7;
            }

            /* ── Inputs ───────────────────────────────────────────────── */
            QLineEdit, QDoubleSpinBox, QDateTimeEdit {
                border: 1px solid #C8CADA;
                border-radius: 4px;
                padding: 5px 8px;
                background: #FFFFFF;
                min-height: 28px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus, QDateTimeEdit:focus {
                border: 1.5px solid #1A3A6E;
            }
            QLineEdit[readOnly="true"] {
                background: #EBEBF3;
                color: #555566;
            }

            /* ── Buttons ──────────────────────────────────────────────── */
            QPushButton#browseBtn {
                border: 1px solid #C8CADA;
                border-radius: 4px;
                padding: 6px 14px;
                background-color: #EAEAF0;
                min-width: 72px;
            }
            QPushButton#browseBtn:hover  { background-color: #D5D5E5; }
            QPushButton#browseBtn:pressed { background-color: #C5C5D8; }

            QPushButton#calcBtn {
                background-color: #1A3A6E;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 5px;
                padding: 8px 28px;
            }
            QPushButton#calcBtn:hover  { background-color: #254F96; }
            QPushButton#calcBtn:pressed { background-color: #102850; }

            QPushButton#reportBtn {
                background-color: #1E6B31;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 13px;
                border: none;
                border-radius: 5px;
                padding: 8px 28px;
            }
            QPushButton#reportBtn:hover   { background-color: #278A3E; }
            QPushButton#reportBtn:pressed { background-color: #145224; }
            QPushButton#reportBtn:disabled {
                background-color: #A5C8A7;
                color: #FFFFFF;
            }

            /* ── Results panel ────────────────────────────────────────── */
            QLabel#netdValue {
                font-size: 56px;
                font-weight: bold;
                color: #1A3A6E;
                letter-spacing: 2px;
            }
            QLabel#netdUnit {
                font-size: 13px;
                color: #888899;
            }
            QLabel#statKey {
                font-size: 12px;
                color: #555566;
            }
            QLabel#statVal {
                font-size: 12px;
                font-weight: bold;
                color: #1A1A2E;
            }
            QFrame#divider {
                color: #C8CADA;
            }
            QFrame#thinLine {
                color: #E0E0EA;
                max-height: 1px;
            }

            /* ── Calendar popup ───────────────────────────────────────── */
            QCalendarWidget {
                background-color: #FFFFFF;
            }
        """)
