import os
from datetime import datetime

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from core.logger import AppLogger
from core.netd_calculator import MultiFrameCalculator, MultiFrameResult
from reports.report_generator import ReportGenerator

log = AppLogger.get(__name__)

_ASSETS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self._excel_paths: list = []
        self._result: MultiFrameResult | None = None

        self._setup_window()
        self._build_ui()
        self._apply_stylesheet()

    # ── Window setup ──────────────────────────────────────────────────────────

    def _setup_window(self):
        self.setWindowTitle("NETD Calculator — TIPL")
        ico = os.path.join(_ASSETS, "logo.ico")
        if os.path.exists(ico):
            self.setWindowIcon(QIcon(ico))
        self.setMinimumSize(860, 820)
        self.resize(960, 920)

    # ── UI Construction ───────────────────────────────────────────────────────

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setSpacing(10)
        root.setContentsMargins(20, 14, 20, 14)

        root.addWidget(self._build_header())
        root.addWidget(self._build_file_group())
        root.addWidget(self._build_parameters_group())
        root.addLayout(self._build_action_row())
        root.addWidget(self._build_results_group(), stretch=1)

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
        sub = QLabel("Multi-Frame Thermal Sensitivity (NETD) Analysis")
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
        grid.setSpacing(8)
        grid.setContentsMargins(14, 14, 14, 14)

        grid.addWidget(QLabel("Temperature Matrices (.xlsx):"), 0, 0, Qt.AlignTop)

        self.file_list = QListWidget()
        self.file_list.setMinimumHeight(130)
        self.file_list.setSelectionMode(QListWidget.SingleSelection)
        grid.addWidget(self.file_list, 0, 1)

        btn_col = QVBoxLayout()
        btn_col.setSpacing(4)
        btn_add = QPushButton("Add Files")
        btn_add.setObjectName("browseBtn")
        btn_add.clicked.connect(self._add_excel_files)
        btn_remove = QPushButton("Remove")
        btn_remove.setObjectName("browseBtn")
        btn_remove.clicked.connect(self._remove_excel_file)
        btn_clear = QPushButton("Clear All")
        btn_clear.setObjectName("browseBtn")
        btn_clear.clicked.connect(self._clear_excel_files)
        btn_col.addWidget(btn_add)
        btn_col.addWidget(btn_remove)
        btn_col.addWidget(btn_clear)
        btn_col.addStretch()
        grid.addLayout(btn_col, 0, 2)

        return group

    def _build_parameters_group(self) -> QGroupBox:
        group = QGroupBox("Device & Test Parameters")
        grid = QGridLayout(group)
        grid.setColumnStretch(1, 1)
        grid.setColumnStretch(3, 1)
        grid.setSpacing(8)
        grid.setContentsMargins(14, 14, 14, 14)

        # Row 0: Model | Serial Number
        grid.addWidget(QLabel("Thermal Imager Model:"), 0, 0)
        self.model_edit = QLineEdit()
        self.model_edit.setPlaceholderText("e.g. TIPL-TC320")
        grid.addWidget(self.model_edit, 0, 1)
        grid.addWidget(QLabel("Serial Number:"), 0, 2)
        self.serial_edit = QLineEdit()
        self.serial_edit.setPlaceholderText("e.g. SN-2024-001")
        grid.addWidget(self.serial_edit, 0, 3)

        # Row 1: Condition | Make
        grid.addWidget(QLabel("Condition:"), 1, 0)
        self.condition_combo = QComboBox()
        self.condition_combo.addItems(["Satisfactory", "Not Satisfactory"])
        grid.addWidget(self.condition_combo, 1, 1)
        grid.addWidget(QLabel("Thermal Imager Make:"), 1, 2)
        self.make_edit = QLineEdit("TIPL")
        grid.addWidget(self.make_edit, 1, 3)

        # Row 2: Applicable Standards (fixed dropdown — read-only, all 4 always apply)
        grid.addWidget(QLabel("Applicable Standards:"), 2, 0)
        self.standards_combo = QComboBox()
        self.standards_combo.addItems([
            "VDI/VDE 5585 Part 1 (2018) | ASTM E1543-14 (2022) | ISO 18554:2017 | ISO/IEC 17025:2017",
        ])
        self.standards_combo.setEnabled(False)
        grid.addWidget(self.standards_combo, 2, 1, 1, 3)

        # Row 3: Black Body Name | Black Body Emissivity
        grid.addWidget(QLabel("Black Body Name:"), 3, 0)
        self.blackbody_name_edit = QLineEdit()
        self.blackbody_name_edit.setPlaceholderText("e.g. BB-2000")
        grid.addWidget(self.blackbody_name_edit, 3, 1)
        grid.addWidget(QLabel("Black Body Emissivity:"), 3, 2)
        self.emissivity_spin = QDoubleSpinBox()
        self.emissivity_spin.setRange(0.00, 1.00)
        self.emissivity_spin.setSingleStep(0.01)
        self.emissivity_spin.setDecimals(2)
        self.emissivity_spin.setValue(1.00)
        grid.addWidget(self.emissivity_spin, 3, 3)

        # Row 4: Relative Humidity | Ambient Temperature
        grid.addWidget(QLabel("Relative Humidity (%):"), 4, 0)
        self.humidity_spin = QDoubleSpinBox()
        self.humidity_spin.setRange(0.0, 100.0)
        self.humidity_spin.setSingleStep(1.0)
        self.humidity_spin.setDecimals(1)
        self.humidity_spin.setValue(50.0)
        grid.addWidget(self.humidity_spin, 4, 1)
        grid.addWidget(QLabel("Ambient Temperature (\u00b0C):"), 4, 2)
        self.ambient_temp_spin = QDoubleSpinBox()
        self.ambient_temp_spin.setRange(0.0, 100.0)
        self.ambient_temp_spin.setSingleStep(0.5)
        self.ambient_temp_spin.setDecimals(1)
        self.ambient_temp_spin.setValue(25.0)
        grid.addWidget(self.ambient_temp_spin, 4, 3)

        # Row 5: Stabilisation Time | Airflow Disturbance
        grid.addWidget(QLabel("Stabilisation Time:"), 5, 0)
        self.stabilisation_spin = QSpinBox()
        self.stabilisation_spin.setRange(1, 120)
        self.stabilisation_spin.setValue(30)
        self.stabilisation_spin.setSuffix(" minutes")
        grid.addWidget(self.stabilisation_spin, 5, 1)
        grid.addWidget(QLabel("Airflow Disturbance:"), 5, 2)
        self.airflow_combo = QComboBox()
        self.airflow_combo.addItems(["Negligible", "Mild"])
        grid.addWidget(self.airflow_combo, 5, 3)

        # Row 6: Verified By (full width)
        grid.addWidget(QLabel("Verified By:"), 6, 0)
        self.verified_edit = QLineEdit()
        self.verified_edit.setPlaceholderText("Engineer name or approver")
        grid.addWidget(self.verified_edit, 6, 1, 1, 3)

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
        outer = QVBoxLayout(self.results_group)
        outer.setContentsMargins(14, 14, 14, 14)
        outer.setSpacing(10)

        # Per-frame results table
        self.frame_table = QTableWidget(0, 4)
        self.frame_table.setHorizontalHeaderLabels([
            "Sr. No.", "File Name", "Avg. Temp (\u00b0C)", "NETD (mK)",
        ])
        self.frame_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.frame_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.frame_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
        self.frame_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.frame_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.frame_table.setSelectionMode(QTableWidget.NoSelection)
        self.frame_table.setAlternatingRowColors(True)
        self.frame_table.setMinimumHeight(120)
        outer.addWidget(self.frame_table, stretch=1)

        # Summary section: NETD big display (centred)
        summary = QHBoxLayout()
        summary.setSpacing(20)

        self.netd_value_lbl = QLabel("\u2014")
        self.netd_value_lbl.setObjectName("netdValue")
        self.netd_value_lbl.setAlignment(Qt.AlignCenter)
        self.netd_unit_lbl = QLabel("mK  (NETD)")
        self.netd_unit_lbl.setObjectName("netdUnit")
        self.netd_unit_lbl.setAlignment(Qt.AlignCenter)

        netd_col = QVBoxLayout()
        netd_col.setSpacing(4)
        netd_col.addStretch()
        netd_col.addWidget(self.netd_value_lbl)
        netd_col.addWidget(self.netd_unit_lbl)
        netd_col.addStretch()

        summary.addStretch()
        summary.addLayout(netd_col)
        summary.addStretch()

        outer.addLayout(summary)
        return self.results_group

    # ── Slots ─────────────────────────────────────────────────────────────────

    def _add_excel_files(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Temperature Matrix Files", "",
            "Excel Files (*.xlsx *.xls)",
        )
        if not paths:
            return

        added = 0
        for path in paths:
            if path in self._excel_paths:
                continue
            if len(self._excel_paths) >= 50:
                QMessageBox.warning(self, "Limit Reached",
                                    "Maximum 50 files can be selected at once.")
                break
            self._excel_paths.append(path)
            self.file_list.addItem(os.path.basename(path))
            added += 1

        log.info("%d file(s) added (total: %d)", added, len(self._excel_paths))

    def _remove_excel_file(self):
        row = self.file_list.currentRow()
        if row < 0:
            QMessageBox.information(self, "No Selection", "Click a file in the list to select it, then press Remove.")
            return
        self._excel_paths.pop(row)
        self.file_list.takeItem(row)
        log.info("Removed file at index %d (total: %d)", row, len(self._excel_paths))

    def _clear_excel_files(self):
        self._excel_paths.clear()
        self.file_list.clear()
        log.info("Excel file list cleared")

    def _run_calculation(self):
        if not self._excel_paths:
            QMessageBox.warning(self, "Missing Input",
                                "Please add at least one temperature matrix Excel file.")
            return

        log.info("Calculation requested for %d file(s)", len(self._excel_paths))
        try:
            calc = MultiFrameCalculator(self._excel_paths)
            self._result = calc.calculate_all()
            self._display_result(self._result)
            self.report_btn.setEnabled(True)
            log.info("Calculation done — NETD=%.1f mK", self._result.netd_mk)

        except Exception as exc:
            log.exception("Calculation failed")
            QMessageBox.critical(self, "Calculation Error", str(exc))

    def _display_result(self, result: MultiFrameResult):
        self.frame_table.setRowCount(0)
        for i, frame in enumerate(result.frames):
            row = self.frame_table.rowCount()
            self.frame_table.insertRow(row)
            self.frame_table.setItem(row, 0, self._centered_item(str(i + 1)))
            self.frame_table.setItem(row, 1, QTableWidgetItem(frame.filename))
            self.frame_table.setItem(row, 2, self._centered_item(f"{frame.tbar:.4f}"))
            self.frame_table.setItem(row, 3, self._centered_item(f"{frame.netd_mk:.1f}"))

        self.netd_value_lbl.setText(f"{result.netd_mk:.1f}")

    @staticmethod
    def _centered_item(text: str) -> QTableWidgetItem:
        item = QTableWidgetItem(text)
        item.setTextAlignment(Qt.AlignCenter)
        return item

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
            "model":                self.model_edit.text().strip() or "N/A",
            "serial_number":        self.serial_edit.text().strip() or "N/A",
            "condition":            self.condition_combo.currentText(),
            "make":                 self.make_edit.text().strip() or "TIPL",
            "blackbody_name":       self.blackbody_name_edit.text().strip() or "N/A",
            "blackbody_emissivity": f"{self.emissivity_spin.value():.2f}",
            "relative_humidity":    f"{self.humidity_spin.value():.1f}",
            "ambient_temp":         f"{self.ambient_temp_spin.value():.1f}",
            "stabilisation_time":   f"{self.stabilisation_spin.value()} minutes",
            "airflow_disturbance":  self.airflow_combo.currentText(),
            "verified_by":          self.verified_edit.text().strip() or "N/A",
        }

        log.info("Report generation requested — output: %s", path)
        try:
            gen = ReportGenerator(self._result, metadata)
            gen.generate(path)
            log.info("Report saved: %s", path)
            QMessageBox.information(
                self, "Report Saved",
                f"PDF report saved successfully:\n\n{path}",
            )
        except Exception as exc:
            log.exception("Report generation failed")
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
            QLineEdit, QDoubleSpinBox, QSpinBox, QComboBox {
                border: 1px solid #C8CADA;
                border-radius: 4px;
                padding: 5px 8px;
                background: #FFFFFF;
                min-height: 28px;
            }
            QLineEdit:focus, QDoubleSpinBox:focus, QSpinBox:focus, QComboBox:focus {
                border: 1.5px solid #1A3A6E;
            }
            QLineEdit[readOnly="true"] {
                background: #EBEBF3;
                color: #555566;
            }
            QComboBox:disabled {
                background: #EBEBF3;
                color: #333355;
                border: 1px solid #C8CADA;
            }

            /* ── File list ────────────────────────────────────────────── */
            QListWidget {
                border: 1px solid #C8CADA;
                border-radius: 4px;
                background: #FFFFFF;
                font-size: 12px;
            }
            QListWidget::item {
                padding: 3px 6px;
            }
            QListWidget::item:alternate {
                background: #F5F6FA;
            }

            /* ── Buttons ──────────────────────────────────────────────── */
            QPushButton#browseBtn {
                border: 1px solid #C8CADA;
                border-radius: 4px;
                padding: 6px 14px;
                background-color: #EAEAF0;
                min-width: 72px;
            }
            QPushButton#browseBtn:hover   { background-color: #D5D5E5; }
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
            QPushButton#calcBtn:hover   { background-color: #254F96; }
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
            QTableWidget {
                border: 1px solid #C8CADA;
                border-radius: 4px;
                background: #FFFFFF;
                gridline-color: #E0E0EA;
                font-size: 12px;
            }
            QTableWidget::item {
                padding: 4px 8px;
            }
            QHeaderView::section {
                background-color: #1A3A6E;
                color: #FFFFFF;
                font-weight: bold;
                font-size: 12px;
                padding: 6px 8px;
                border: none;
            }
            QTableWidget::item:alternate {
                background: #F5F6FA;
            }
            QLabel#netdValue {
                font-size: 52px;
                font-weight: bold;
                color: #1A3A6E;
                letter-spacing: 2px;
            }
            QLabel#netdUnit {
                font-size: 13px;
                color: #888899;
            }
            QLabel#statVal {
                font-size: 13px;
                font-weight: bold;
                color: #1A3A6E;
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
