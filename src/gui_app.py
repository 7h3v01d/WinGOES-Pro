# gui_app.py  —  WinGOES Pro 2.1
# Professional retail GUI — PyQt6
from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from models_and_utils import (
    ALL_MODES,
    MODE_CLEAN,
    MODE_CUSTOM,
    MODE_SAME,
    Toggles,
    ensure_dir,
    is_admin,
    is_windows,
    relaunch_as_admin,
)
from orchestrator_core import op_apply, op_capture, op_verify
from license_manager import (
    APP_NAME,
    APP_VERSION,
    EDITION_NAME,
    LicenseInfo,
    check_license,
    deactivate_license,
    save_license,
    validate_key,
    generate_key,
)

APP_TITLE = f"{APP_NAME} {APP_VERSION}"

# ── Stylesheet ─────────────────────────────────────────────────────────────────

THEME_STYLE = """
/* ══════════════════════════════════════════════════════
   WinGOES Pro 2.1  —  Dark Industrial Theme
   Signature palette (7h3v01d):
     Base:       #0b0f14  (obsidian)
     Surface:    #10151c  (panel)
     Surface2:   #141a22  (raised)
     Surface3:   #171e27  (input bg)
     Hairline:   #232b35  (steel, 1px)
     HairlineHi: #3a4655  (active)
     Accent:     #2fd6c3  (teal)
     AccentDim:  #1fa896
     Success:    #4be08a  (phosphor)
     Warning:    #ffb454  (amber)
     Danger:     #ff5c66  (red)
     Text:       #d7e0ea  (primary)
     TextMuted:  #7d8a99  (secondary)
     TextDim:    #46525f  (disabled)
   Rules: flat, zero-radius, monospace, 1px steel hairlines.
   ══════════════════════════════════════════════════════ */

QWidget {
    background-color: #10151c;
    color: #d7e0ea;
    font-family: "JetBrains Mono", "Cascadia Mono", "Consolas", monospace;
    font-size: 13px;
}
QMainWindow { background-color: #0b0f14; }

/* ── Sidebar (left panel) ── */
#sidebar {
    background-color: #10151c;
    border-right: 1px solid #232b35;
}

/* ── Brand header inside sidebar ── */
#brandBlock {
    background-color: #0b0f14;
    padding: 20px 16px 16px 16px;
    border-bottom: 1px solid #232b35;
}
#brandTitle {
    color: #d7e0ea;
    font-size: 18px;
    font-weight: bold;
    letter-spacing: 2px;
}
#brandSub {
    color: #7d8a99;
    font-size: 10px;
    letter-spacing: 3px;
}
#brandVersion {
    color: #2fd6c3;
    font-size: 10px;
    font-weight: 600;
    padding: 1px 7px;
    border: 1px solid #1fa896;
    border-radius: 0px;
    background: #0c1a18;
}

/* ── Sidebar section labels ── */
#sideLabel {
    color: #46525f;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 2px;
    padding: 14px 16px 5px 16px;
}

/* ── Sidebar checkboxes ── */
#sidebar QCheckBox {
    color: #b7c2ce;
    font-size: 12px;
    spacing: 8px;
    padding: 4px 16px;
}
#sidebar QCheckBox:disabled { color: #232b35; }
#sidebar QCheckBox::indicator {
    width: 14px; height: 14px;
    border: 1px solid #3a4655;
    border-radius: 0px;
    background: #0b0f14;
}
#sidebar QCheckBox::indicator:checked {
    background: #2fd6c3;
    border-color: #2fd6c3;
}
#sidebar QCheckBox::indicator:disabled {
    background: #10151c;
    border-color: #232b35;
}

/* ── Info labels inside sidebar ── */
#sideInfo {
    color: #ffb454;
    font-size: 11px;
    padding: 3px 16px;
    font-style: italic;
}

/* ── Main content area ── */
#mainArea {
    background-color: #0b0f14;
}

/* ── Top toolbar strip ── */
#toolbar {
    background-color: #10151c;
    border-bottom: 1px solid #232b35;
    min-height: 56px;
    max-height: 56px;
}

/* ── Bundle path row ── */
#bundleRow {
    background: #171e27;
    border: 1px solid #232b35;
    border-radius: 0px;
    padding: 4px 8px;
    color: #d7e0ea;
}

/* ── Arrow labels ── */
#wfArrow { color: #232b35; font-size: 16px; padding: 0 2px; }

/* ── Generic QPushButton — must come BEFORE named overrides ── */
QPushButton {
    background-color: #141a22;
    color: #b7c2ce;
    border: 1px solid #232b35;
    border-radius: 0px;
    padding: 7px 16px;
    font-weight: 500;
}
QPushButton:hover {
    background-color: #1a222c;
    border-color: #3a4655;
    color: #d7e0ea;
}
QPushButton:pressed { background-color: #0b0f14; border-color: #3a4655; }
QPushButton:disabled { color: #46525f; border-color: #141a22; background: #10151c; }

/* ── Primary action buttons — after generic so they override ── */
QPushButton#btnCapture {
    background-color: #2fd6c3;
    color: #0b0f14;
    border: 1px solid #2fd6c3;
    border-radius: 0px;
    font-weight: 700;
    font-size: 13px;
    padding: 10px 28px;
}
QPushButton#btnCapture:hover {
    background-color: #5ce4d4;
    border-color: #5ce4d4;
    color: #0b0f14;
}
QPushButton#btnCapture:pressed { background-color: #1fa896; color: #0b0f14; }
QPushButton#btnCapture:disabled { background-color: #141a22; color: #46525f; border-color: #141a22; }

QPushButton#btnApply {
    background-color: #4be08a;
    color: #0b0f14;
    border: 1px solid #4be08a;
    border-radius: 0px;
    font-weight: 700;
    font-size: 13px;
    padding: 10px 28px;
}
QPushButton#btnApply:hover { background-color: #71e8a3; border-color: #71e8a3; color: #0b0f14; }
QPushButton#btnApply:pressed { background-color: #35b06c; color: #0b0f14; }
QPushButton#btnApply:disabled { background-color: #141a22; color: #46525f; border-color: #141a22; }

QPushButton#btnVerify {
    background-color: #ffb454;
    color: #0b0f14;
    border: 1px solid #ffb454;
    border-radius: 0px;
    font-weight: 700;
    font-size: 13px;
    padding: 10px 28px;
}
QPushButton#btnVerify:hover { background-color: #ffc678; border-color: #ffc678; color: #0b0f14; }
QPushButton#btnVerify:pressed { background-color: #d99539; color: #0b0f14; }
QPushButton#btnVerify:disabled { background-color: #141a22; color: #46525f; border-color: #141a22; }

/* ── Workflow step buttons — after generic ── */
QPushButton#wfBtn {
    background: transparent;
    color: #7d8a99;
    border: none;
    border-bottom: 2px solid transparent;
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 0.4px;
    padding: 0px 20px;
    min-height: 52px;
    border-radius: 0px;
}
QPushButton#wfBtn:hover {
    color: #d7e0ea;
    background: #141a22;
    border: none;
    border-bottom: 2px solid #3a4655;
}
QPushButton#wfBtn[active="true"] {
    color: #2fd6c3;
    border: none;
    border-bottom: 2px solid #2fd6c3;
    background: #0c1a18;
}
QPushButton#wfBtn[completed="true"] {
    color: #4be08a;
    border: none;
    border-bottom: 2px solid #4be08a;
    background: transparent;
}

/* ── Line Edit ── */
QLineEdit {
    background: #0b0f14;
    border: 1px solid #232b35;
    border-radius: 0px;
    padding: 6px 10px;
    color: #d7e0ea;
    selection-background-color: #17453f;
}
QLineEdit:focus { border-color: #2fd6c3; }
QLineEdit:disabled { background: #10151c; color: #46525f; }

/* ── ComboBox ── */
QComboBox {
    background: #141a22;
    border: 1px solid #232b35;
    border-radius: 0px;
    padding: 6px 12px;
    color: #d7e0ea;
    min-width: 190px;
}
QComboBox:hover { border-color: #3a4655; }
QComboBox:focus { border-color: #2fd6c3; }
QComboBox::drop-down { border: none; padding-right: 8px; }
QComboBox QAbstractItemView {
    background: #10151c;
    border: 1px solid #232b35;
    selection-background-color: #17453f;
    color: #d7e0ea;
}

/* ── Tab widget ── */
QTabWidget::pane {
    border: 1px solid #232b35;
    border-top: none;
    background: #0b0f14;
}
QTabBar::tab {
    background: #10151c;
    color: #7d8a99;
    border: 1px solid #232b35;
    border-bottom: none;
    padding: 7px 22px;
    margin-right: 2px;
    font-weight: 500;
    border-radius: 0px;
}
QTabBar::tab:selected {
    background: #0b0f14;
    color: #d7e0ea;
    font-weight: 700;
    border-top: 2px solid #2fd6c3;
}
QTabBar::tab:hover:!selected { background: #141a22; color: #b7c2ce; }

/* ── Text output areas ── */
QTextEdit {
    background: #0b0f14;
    border: none;
    color: #b7c2ce;
    font-family: "JetBrains Mono", "Cascadia Mono", "Consolas", monospace;
    font-size: 13px;
    padding: 12px;
    selection-background-color: #17453f;
}
QPlainTextEdit {
    background: #0b0f14;
    border: none;
    color: #7d8a99;
    font-family: "JetBrains Mono", "Cascadia Mono", "Consolas", monospace;
    font-size: 12px;
    padding: 10px;
    selection-background-color: #17453f;
}

/* ── Results Table ── */
QTableView {
    background: #0b0f14;
    border: none;
    gridline-color: #141a22;
    color: #b7c2ce;
    font-size: 12px;
    selection-background-color: #17453f;
    alternate-background-color: #10151c;
}
QTableView::item:selected { background: #17453f; color: #d7e0ea; }
QHeaderView::section {
    background: #10151c;
    border: none;
    border-right: 1px solid #141a22;
    border-bottom: 1px solid #232b35;
    color: #7d8a99;
    font-size: 11px;
    font-weight: 700;
    letter-spacing: 1px;
    padding: 7px 10px;
}

/* ── Status bar ── */
QStatusBar {
    background: #10151c;
    border-top: 1px solid #232b35;
    color: #7d8a99;
    font-size: 11px;
}
QStatusBar::item { border: none; }

/* ── Menu bar ── */
QMenuBar {
    background: #10151c;
    border-bottom: 1px solid #232b35;
    color: #b7c2ce;
    padding: 2px;
}
QMenuBar::item:selected { background: #141a22; color: #2fd6c3; border-radius: 0px; }
QMenu {
    background: #10151c;
    border: 1px solid #232b35;
    color: #b7c2ce;
}
QMenu::item:selected { background: #141a22; color: #2fd6c3; }
QMenu::separator { height: 1px; background: #232b35; margin: 4px 0; }

/* ── Dialogs ── */
QDialog { background: #10151c; }
QDialogButtonBox QPushButton { min-width: 80px; }

/* ── Scroll bars ── */
QScrollBar:vertical {
    background: #0b0f14; width: 8px; border: none;
}
QScrollBar::handle:vertical {
    background: #232b35; border-radius: 0px; min-height: 20px;
}
QScrollBar::handle:vertical:hover { background: #3a4655; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar:horizontal {
    background: #0b0f14; height: 8px; border: none;
}
QScrollBar::handle:horizontal {
    background: #232b35; border-radius: 0px; min-width: 20px;
}
QScrollBar::handle:horizontal:hover { background: #3a4655; }
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal { width: 0; }

/* ── License badge ── */
#licBadge {
    color: #7d8a99; font-size: 11px; font-weight: 600;
    padding: 3px 10px; border: 1px solid #232b35;
    border-radius: 0px; background: #141a22;
}
#licBadge[licensed="true"] {
    color: #4be08a; border-color: #35b06c;
    background: #0c1f14; font-weight: 700;
}
#licBadge[trial="true"] {
    color: #ffb454; border-color: #a86f2a;
    background: #1f1608; font-weight: 600;
}

/* ── Admin badge ── */
#adminOk  { color: #4be08a; font-size: 11px; font-weight: 600; padding: 2px 8px; border: 1px solid #35b06c; border-radius: 0px; background: #0c1f14; }
#adminOff { color: #ffb454; font-size: 11px; padding: 2px 8px; border: 1px solid #a86f2a; border-radius: 0px; background: #1f1608; }

/* ── Dry-run checkbox ── */
QCheckBox#dryRunChk { color: #ffb454; font-weight: 700; font-size: 12px; }
QCheckBox#dryRunChk::indicator { width:14px; height:14px; border:1px solid #a86f2a; border-radius:0px; background:#1f1608; }
QCheckBox#dryRunChk::indicator:checked { background: #ffb454; border-color: #ffc678; }

/* ── Chips / inline badges ── */
#chipWarn    { color: #ffb454; background: #1f1608; border: 1px solid #a86f2a; border-radius: 0px; padding: 4px 8px; font-size: 11px; }
#chipInfo    { color: #2fd6c3; background: #0c1a18; border: 1px solid #1fa896; border-radius: 0px; padding: 4px 8px; font-size: 11px; }
#chipSuccess { color: #4be08a; background: #0c1f14; border: 1px solid #35b06c; border-radius: 0px; padding: 4px 8px; font-size: 11px; }

/* ── License key input ── */
#keyInput {
    font-family: "JetBrains Mono", "Cascadia Mono", "Consolas", monospace;
    font-size: 15px; letter-spacing: 2px;
    color: #2fd6c3; background: #0c1a18;
    border: 1px solid #1fa896; border-radius: 0px;
    padding: 10px 14px;
}
#keyInput:focus { border-color: #2fd6c3; background: #0b0f14; }

/* ── Splitter ── */
QSplitter::handle { background: #232b35; width: 1px; height: 1px; }

/* ── Frame separators ── */
QFrame[frameShape="4"] { color: #232b35; }
QFrame[frameShape="5"] { color: #232b35; }
"""


# ── GUI Main ───────────────────────────────────────────────────────────────────


def gui_main() -> int:
    from PyQt6.QtCore import (
        Qt, QThread, pyqtSignal, QObject,
        QAbstractTableModel, QModelIndex, QTimer,
    )
    from PyQt6.QtGui import QAction, QDesktopServices, QIcon, QColor
    from PyQt6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
        QLabel, QPushButton, QComboBox, QCheckBox, QFileDialog, QLineEdit,
        QGroupBox, QTextEdit, QPlainTextEdit, QMessageBox,
        QTableView, QHeaderView, QAbstractItemView, QDialog, QDialogButtonBox,
        QTextBrowser, QStatusBar, QFrame, QTabWidget,
    )
    from PyQt6.QtCore import QUrl

    # ── License Dialog ────────────────────────────────────────────────────────

    def show_license_dialog(parent, current_lic: LicenseInfo) -> LicenseInfo:
        dlg = QDialog(parent)
        dlg.setWindowTitle(f"License — {APP_TITLE}")
        dlg.setModal(True)
        dlg.setFixedWidth(540)
        dlg.setStyleSheet(THEME_STYLE)
        layout = QVBoxLayout(dlg)
        layout.setSpacing(14)
        layout.setContentsMargins(24, 24, 24, 24)

        title_lbl = QLabel(f"Activate {APP_NAME}")
        title_lbl.setStyleSheet("font-size:18px; font-weight:bold; color:#d7e0ea; letter-spacing:1px;")
        layout.addWidget(title_lbl)

        status_lbl = QLabel(current_lic.display_status())
        status_lbl.setWordWrap(True)
        status_lbl.setObjectName("chipSuccess" if current_lic.is_pro() else "chipWarn")
        layout.addWidget(status_lbl)

        result_holder = [current_lic]

        if current_lic.is_pro():
            _seat = current_lic.seat_name or "(unnamed)"
            _activated = current_lic.activated_date[:10]
            info = QLabel(
                f"<b>Key:</b> {current_lic.key[:14]}\u2026<br>"
                f"<b>Seat:</b> {_seat}<br>"
                f"<b>Activated:</b> {_activated}"
            )
            info.setStyleSheet("color:#7d8a99; font-size:12px; line-height:1.7;")
            layout.addWidget(info)
            deact_btn = QPushButton("Deactivate License")
            deact_btn.setStyleSheet("color:#ff5c66; border-color:#7a2c31; background:#1a0d0e;")
            layout.addWidget(deact_btn)
            close_btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
            close_btns.rejected.connect(dlg.reject)
            layout.addWidget(close_btns)
            def do_deactivate():
                if QMessageBox.question(dlg, "Confirm", "Remove this license?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                ) == QMessageBox.StandardButton.Yes:
                    deactivate_license()
                    result_holder[0] = check_license()
                    dlg.accept()
            deact_btn.clicked.connect(do_deactivate)
            dlg.exec()
            return result_holder[0]

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color:#232b35;")
        layout.addWidget(sep)
        layout.addWidget(QLabel("Enter your license key:"))

        key_input = QLineEdit()
        key_input.setObjectName("keyInput")
        key_input.setPlaceholderText("WGPRO-XXXXX-XXXXX-XXXXX-XXXXX-XXXXX")
        key_input.setMaxLength(36)
        layout.addWidget(key_input)

        seat_lbl = QLabel("Seat name (optional):")
        seat_lbl.setStyleSheet("color:#7d8a99; font-size:12px;")
        layout.addWidget(seat_lbl)
        seat_input = QLineEdit()
        seat_input.setPlaceholderText("e.g. Main Dev PC")
        layout.addWidget(seat_input)

        err_lbl = QLabel("")
        err_lbl.setObjectName("chipWarn")
        err_lbl.setVisible(False)
        err_lbl.setWordWrap(True)
        layout.addWidget(err_lbl)

        btn_row = QHBoxLayout()
        act_btn = QPushButton("Activate")
        act_btn.setObjectName("btnCapture")
        trial_btn = QPushButton("Continue Trial")
        trial_btn.setStyleSheet("color:#7d8a99;")
        cancel_btn = QPushButton("Cancel")
        btn_row.addWidget(act_btn)
        btn_row.addWidget(trial_btn)
        btn_row.addStretch()
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        purchase_lbl = QLabel(
            '<a href="https://example.com/wingoes-pro" style="color:#2fd6c3;">Purchase a license →</a>'
        )
        purchase_lbl.setOpenExternalLinks(True)
        purchase_lbl.setStyleSheet("font-size:12px;")
        layout.addWidget(purchase_lbl)

        def do_activate():
            raw = key_input.text().strip()
            if not raw:
                err_lbl.setText("Please enter a license key.")
                err_lbl.setVisible(True)
                return
            ok, edition, err = validate_key(raw)
            if not ok:
                err_lbl.setText(f"Invalid key: {err}")
                err_lbl.setVisible(True)
                return
            save_license(raw, edition, seat_input.text().strip())
            result_holder[0] = check_license()
            dlg.accept()

        act_btn.clicked.connect(do_activate)
        trial_btn.clicked.connect(dlg.reject)
        cancel_btn.clicked.connect(dlg.reject)
        key_input.returnPressed.connect(do_activate)
        dlg.exec()
        return result_holder[0]

    # ── HTML Dialog ───────────────────────────────────────────────────────────

    HELP_HTML = """<style>
    body{font-family:'JetBrains Mono','Cascadia Mono',Consolas,monospace;color:#d7e0ea;background:#0b0f14;}
    h2{color:#2fd6c3;border-bottom:1px solid #232b35;padding-bottom:8px;letter-spacing:1px;}
    h3{color:#7d8a99;margin-top:20px;letter-spacing:1px;} h4{color:#ffb454;}
    p,li{color:#b7c2ce;line-height:1.7;}
    blockquote{border-left:2px solid #2fd6c3;margin-left:0;padding-left:16px;color:#7d8a99;}
    code{background:#10151c;border:1px solid #232b35;padding:2px 6px;color:#2fd6c3;font-family:'JetBrains Mono',Consolas,monospace;}
    hr{border:none;border-top:1px solid #232b35;}
    </style>
    <h2>How to Use WinGOES Pro</h2>
    <h3>The Three-Step Workflow</h3>
    <h4>1) CAPTURE — Before Reinstalling Windows</h4>
    <ul><li>Run on your <b>current</b> installation</li>
    <li>Records apps, configs, hardware fingerprint</li>
    <li><b>Does not modify your system</b></li>
    <li>Copy the bundle folder to external storage</li></ul>
    <h4>2) APPLY — After a Fresh Windows Install</h4>
    <ul><li>Run on your new clean installation</li>
    <li>Hardware compatibility checked automatically</li>
    <li>Enable <b>Dry Run</b> to preview without changes</li></ul>
    <h4>3) VERIFY — Final Check</h4>
    <ul><li>Confirms tools are installed and working</li>
    <li>Flags missing drivers — never modifies the system</li></ul>
    <hr/>
    <h3>Modes</h3>
    <h4>✅ CLEAN REBUILD</h4><p>Default. Safest. Recommended for most cases.</p>
    <h4>⚠️ SAME-HARDWARE TRANSFER</h4><p>Reinstalling on the same physical machine. Hardware verified automatically.</p>
    <h4>🧪 CUSTOM</h4><p>Expert control. Safety gates still apply.</p>
    <hr/>
    <h3>Log Messages</h3>
    <p>Most log entries are <b>informational</b>. Only entries marked <code>fatal</code> indicate a real failure.</p>"""

    ABOUT_HTML = """<style>
    body{font-family:'JetBrains Mono','Cascadia Mono',Consolas,monospace;color:#d7e0ea;background:#0b0f14;}
    h2{color:#2fd6c3;letter-spacing:1px;} h3{color:#7d8a99;margin-top:20px;letter-spacing:1px;}
    p,li{color:#b7c2ce;line-height:1.7;}
    hr{border:none;border-top:1px solid #232b35;}
    </style>
    <h2>About WinGOES Pro 2.1</h2>
    <p><i>"Rebuild Windows cleanly. Restore only what matters."</i></p>
    <p><b>WinGOES Pro</b> captures your essential setup, lets you install Windows fresh,
    then restores only what's safe — leaving old problems behind.</p>
    <hr/>
    <h3>Design Principles</h3>
    <ul>
    <li><b>Clean by Default</b> — A fresh install stays fresh.</li>
    <li><b>Explicit</b> — Every action appears in the log.</li>
    <li><b>Safe</b> — Risky operations are blocked by design.</li>
    <li><b>Honest</b> — Dry Run shows you exactly what will happen.</li>
    </ul>
    <h3>What WinGOES Pro Will Never Do</h3>
    <ul>
    <li>Import raw registry blobs</li>
    <li>Copy drivers blindly across hardware</li>
    <li>Migrate browser passwords</li>
    <li>Download files silently</li>
    </ul>
    <hr/>
    <p><b>WinGOES Pro 2.1 — Professional Edition</b><br/>
    Windows 10 Pro &bull; Python 3.11+ &bull; PyQt6</p>"""

    def show_html_dialog(parent, title: str, html: str) -> None:
        dlg = QDialog(parent)
        dlg.setWindowTitle(title)
        dlg.setModal(True)
        dlg.resize(760, 560)
        dlg.setStyleSheet(THEME_STYLE)
        layout = QVBoxLayout(dlg)
        view = QTextBrowser()
        view.setOpenExternalLinks(True)
        view.setReadOnly(True)
        view.setHtml(html)
        btns = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        btns.rejected.connect(dlg.reject)
        btns.clicked.connect(lambda _=None: dlg.close())
        layout.addWidget(view, 1)
        layout.addWidget(btns, 0)
        dlg.exec()

    # ── Table Model ───────────────────────────────────────────────────────────

    class ResultsTableModel(QAbstractTableModel):
        COLS = ["Step", "Item", "Status", "Message"]

        def __init__(self):
            super().__init__()
            self.rows: List[Dict[str, str]] = []

        def rowCount(self, parent=QModelIndex()): return len(self.rows)
        def columnCount(self, parent=QModelIndex()): return len(self.COLS)

        def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
            if role != Qt.ItemDataRole.DisplayRole: return None
            if orientation == Qt.Orientation.Horizontal: return self.COLS[section]
            return str(section + 1)

        def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
            if not index.isValid(): return None
            r = self.rows[index.row()]
            col = index.column()
            if role == Qt.ItemDataRole.DisplayRole:
                return [r.get("step",""), r.get("item",""), r.get("status",""), r.get("message","")][col]
            if role == Qt.ItemDataRole.ForegroundRole and col == 2:
                s = r.get("status","")
                if s == "OK": return QColor("#4be08a")
                if s == "FAIL": return QColor("#ff5c66")
                return QColor("#7d8a99")
            return None

        def add_row(self, step, item, status, message):
            self.beginInsertRows(QModelIndex(), len(self.rows), len(self.rows))
            self.rows.append({"step": step, "item": item, "status": status, "message": message})
            self.endInsertRows()

        def clear(self):
            self.beginResetModel()
            self.rows = []
            self.endResetModel()

    # ── Worker ────────────────────────────────────────────────────────────────

    class WorkerSignals(QObject):
        log_line = pyqtSignal(str)
        row      = pyqtSignal(str, str, str, str)
        summary  = pyqtSignal(str)
        finished = pyqtSignal(bool, str, str)

    class OpWorker(QThread):
        def __init__(self, op_name, bundle_dir, mode, dry_run, toggles):
            super().__init__()
            self.op_name = op_name; self.bundle_dir = bundle_dir
            self.mode = mode; self.dry_run = dry_run; self.toggles = toggles
            self.sig = WorkerSignals()

        def run(self):
            def cb(line): self.sig.log_line.emit(line)
            try:
                if self.op_name == "CAPTURE":
                    ctx, report = op_capture(self.bundle_dir, self.mode, self.dry_run, self.toggles, stream_cb=cb)
                elif self.op_name == "APPLY":
                    ctx, report = op_apply(self.bundle_dir, self.mode, self.dry_run, self.toggles, stream_cb=cb)
                elif self.op_name == "VERIFY":
                    ctx, report, checklist = op_verify(self.bundle_dir, self.mode, self.dry_run, self.toggles, stream_cb=cb)
                    if checklist:
                        self.sig.summary.emit("\nChecklist:\n- " + "\n- ".join(checklist))
                else:
                    self.sig.finished.emit(False, "", ""); return

                ok = all(s.get("ok") for s in report.get("steps", []))
                self.sig.summary.emit(f"{self.op_name} complete. ok={ok}")
                for step in report.get("steps", []):
                    for it in step.get("items", []):
                        st = "OK" if it.get("ok") else "FAIL"
                        self.sig.row.emit(step.get("name",""), it.get("description", it.get("id","")), st, it.get("message",""))
                self.sig.finished.emit(bool(ok), str(ctx.report_path), str(ctx.summary_path))
            except Exception as e:
                self.sig.summary.emit(f"ERROR: {e}")
                self.sig.finished.emit(False, "", "")

    # ── Main Window ───────────────────────────────────────────────────────────

    class MainWindow(QMainWindow):
        def __init__(self, license_info: LicenseInfo):
            super().__init__()
            self.license_info = license_info
            self.worker: Optional[OpWorker] = None
            self.last_report_path: Optional[str] = None
            self.last_summary_path: Optional[str] = None

            self.setWindowTitle(APP_TITLE)
            self.resize(1360, 860)
            self.setMinimumSize(1100, 700)
            self._build_ui()
            self._build_menus()
            self.on_mode_changed(self.mode_combo.currentText())
            self._update_license_badge()
            self._set_workflow("none")

        # ── UI Build ──────────────────────────────────────────────────────────

        def _build_ui(self):
            outer = QWidget()
            outer_l = QVBoxLayout(outer)
            outer_l.setContentsMargins(0, 0, 0, 0)
            outer_l.setSpacing(0)

            # ── Top toolbar ──────────────────────────────────────────────────
            toolbar = QWidget(); toolbar.setObjectName("toolbar")
            tb_l = QHBoxLayout(toolbar)
            tb_l.setContentsMargins(12, 0, 16, 0); tb_l.setSpacing(0)

            # Workflow step buttons
            self.step_btns: Dict[str, QPushButton] = {}
            for i, (lbl, key) in enumerate([
                ("① Capture", "CAPTURE"), ("② Apply", "APPLY"), ("③ Verify", "VERIFY")
            ]):
                btn = QPushButton(lbl); btn.setObjectName("wfBtn")
                btn.setProperty("active", "false"); btn.setProperty("completed", "false")
                self.step_btns[key] = btn; tb_l.addWidget(btn)
                if i < 2:
                    arr = QLabel("›"); arr.setObjectName("wfArrow"); tb_l.addWidget(arr)

            tb_l.addStretch()

            # Bundle folder (compact in toolbar)
            self.bundle_edit = QLineEdit()
            self.bundle_edit.setPlaceholderText("Bundle folder…")
            self.bundle_edit.setMinimumWidth(280)
            self.bundle_edit.setObjectName("bundleRow")
            browse_btn = QPushButton("Browse…")
            browse_btn.clicked.connect(self.browse_bundle)
            browse_btn.setFixedHeight(30)

            tb_l.addSpacing(12)
            tb_l.addWidget(QLabel("Bundle:"))
            tb_l.addSpacing(6)
            tb_l.addWidget(self.bundle_edit)
            tb_l.addSpacing(4)
            tb_l.addWidget(browse_btn)
            tb_l.addSpacing(16)

            self.mode_combo = QComboBox()
            self.mode_combo.addItems(ALL_MODES)
            self.mode_combo.setCurrentText(MODE_CLEAN)
            self.mode_combo.currentTextChanged.connect(self.on_mode_changed)
            self.mode_combo.setFixedWidth(190)
            tb_l.addWidget(self.mode_combo)
            tb_l.addSpacing(12)

            self.dryrun_chk = QCheckBox("Dry Run")
            self.dryrun_chk.setObjectName("dryRunChk")
            self.dryrun_chk.setChecked(True)
            self.dryrun_chk.setToolTip("Preview all actions without making changes (recommended)")
            tb_l.addWidget(self.dryrun_chk)

            outer_l.addWidget(toolbar)

            # ── Body: sidebar + main ──────────────────────────────────────────
            body = QWidget()
            body_l = QHBoxLayout(body)
            body_l.setContentsMargins(0, 0, 0, 0)
            body_l.setSpacing(0)

            # ── Sidebar ───────────────────────────────────────────────────────
            sidebar = QWidget(); sidebar.setObjectName("sidebar")
            sidebar.setFixedWidth(260)
            side_l = QVBoxLayout(sidebar)
            side_l.setContentsMargins(0, 0, 0, 0)
            side_l.setSpacing(0)

            # Brand block
            brand_block = QWidget(); brand_block.setObjectName("brandBlock")
            brand_lay = QVBoxLayout(brand_block)
            brand_lay.setContentsMargins(16, 18, 16, 14)
            brand_lay.setSpacing(3)
            t_row = QHBoxLayout(); t_row.setSpacing(8)
            title_lbl = QLabel("WinGOES"); title_lbl.setObjectName("brandTitle")
            ver_lbl = QLabel("Pro 2.1"); ver_lbl.setObjectName("brandVersion")
            t_row.addWidget(title_lbl); t_row.addWidget(ver_lbl); t_row.addStretch()
            sub_lbl = QLabel("REBUILD ASSISTANT"); sub_lbl.setObjectName("brandSub")
            brand_lay.addLayout(t_row)
            brand_lay.addWidget(sub_lbl)
            side_l.addWidget(brand_block)

            # License + admin row
            lic_row = QWidget()
            lic_row.setObjectName("licRow")
            lic_row.setStyleSheet("#licRow { background: #0b0f14; padding: 6px 16px; }")
            lic_row_l = QHBoxLayout(lic_row)
            lic_row_l.setContentsMargins(0, 0, 0, 0); lic_row_l.setSpacing(6)
            self.lic_badge = QLabel("…"); self.lic_badge.setObjectName("licBadge")
            self.admin_badge = QLabel("✓ Admin" if is_admin() else "⚠ Admin")
            self.admin_badge.setObjectName("adminOk" if is_admin() else "adminOff")
            lic_row_l.addWidget(self.lic_badge); lic_row_l.addStretch(); lic_row_l.addWidget(self.admin_badge)
            side_l.addWidget(lic_row)

            # Scrollable controls area
            from PyQt6.QtWidgets import QScrollArea
            scroll = QScrollArea(); scroll.setWidgetResizable(True)
            scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
            scroll.setStyleSheet("QScrollArea { border: none; background: #10151c; }")
            ctrl_widget = QWidget(); ctrl_widget.setObjectName("sidebar")
            ctrl_l = QVBoxLayout(ctrl_widget)
            ctrl_l.setContentsMargins(0, 8, 0, 16)
            ctrl_l.setSpacing(0)

            def side_label(text):
                l = QLabel(text); l.setObjectName("sideLabel"); return l

            def side_info(text):
                l = QLabel(text); l.setObjectName("sideInfo")
                l.setWordWrap(True); return l

            # Package managers
            ctrl_l.addWidget(side_label("Package Managers"))
            self.chk_winget = QCheckBox("Winget  (recommended)"); self.chk_winget.setChecked(True)
            self.chk_choco  = QCheckBox("Chocolatey")
            self.chk_scoop  = QCheckBox("Scoop")
            for w in (self.chk_winget, self.chk_choco, self.chk_scoop): ctrl_l.addWidget(w)

            # Dev configs
            ctrl_l.addWidget(side_label("Developer Configs"))
            self.chk_git       = QCheckBox("Git global config");      self.chk_git.setChecked(True)
            self.chk_gitconfig = QCheckBox(".gitconfig file");         self.chk_gitconfig.setChecked(True)
            self.chk_ssh       = QCheckBox("SSH keys  (~/.ssh)");     self.chk_ssh.setChecked(True)
            self.chk_vscode    = QCheckBox("VS Code  (settings + ext)"); self.chk_vscode.setChecked(True)
            self.chk_terminal  = QCheckBox("Windows Terminal");        self.chk_terminal.setChecked(True)
            for w in (self.chk_git, self.chk_gitconfig, self.chk_ssh, self.chk_vscode, self.chk_terminal):
                ctrl_l.addWidget(w)

            # Windows settings
            ctrl_l.addWidget(side_label("Windows Settings"))
            self.chk_tz    = QCheckBox("Timezone / Region"); self.chk_tz.setChecked(False)
            self.chk_power = QCheckBox("Power plan");        self.chk_power.setChecked(False)
            ctrl_l.addWidget(self.chk_tz); ctrl_l.addWidget(self.chk_power)
            self.lbl_ws_help = QLabel("")
            self.lbl_ws_help.setObjectName("sideInfo")
            self.lbl_ws_help.setWordWrap(True)
            self.lbl_ws_help.setVisible(False)
            ctrl_l.addWidget(self.lbl_ws_help)

            # Drivers
            ctrl_l.addWidget(side_label("Drivers"))
            self.chk_drv_inv      = QCheckBox("Driver inventory  (safe)");      self.chk_drv_inv.setChecked(True)
            self.chk_drv_check    = QCheckBox("Post-install checklist  (safe)"); self.chk_drv_check.setChecked(True)
            self.chk_drv_transfer = QCheckBox("Driver transfer  ⚠ advanced");   self.chk_drv_transfer.setChecked(False)
            ctrl_l.addWidget(self.chk_drv_inv); ctrl_l.addWidget(self.chk_drv_check)
            ctrl_l.addWidget(self.chk_drv_transfer)
            self.lbl_drv_help = QLabel("")
            self.lbl_drv_help.setObjectName("sideInfo")
            self.lbl_drv_help.setWordWrap(True)
            self.lbl_drv_help.setVisible(False)
            ctrl_l.addWidget(self.lbl_drv_help)

            ctrl_l.addStretch()

            # Manage license button at bottom of sidebar
            lic_btn = QPushButton("Manage License…")
            lic_btn.setStyleSheet(
                "QPushButton { background: #2fd6c3; color: #0b0f14; border: none; "
                "border-radius: 0px; padding: 8px 16px; font-weight: 700; margin: 12px 16px 4px 16px; }"
                "QPushButton:hover { background: #5ce4d4; }"
            )
            lic_btn.clicked.connect(self.open_license_dialog)
            ctrl_l.addWidget(lic_btn)

            scroll.setWidget(ctrl_widget)
            side_l.addWidget(scroll, 1)
            body_l.addWidget(sidebar, 0)

            # ── Main right area ───────────────────────────────────────────────
            main_area = QWidget(); main_area.setObjectName("mainArea")
            main_l = QVBoxLayout(main_area)
            main_l.setContentsMargins(0, 0, 0, 0)
            main_l.setSpacing(0)

            # Output tabs
            self.output_tabs = QTabWidget()
            self.output_tabs.setDocumentMode(True)

            # Summary tab
            self.summary = QTextEdit(); self.summary.setReadOnly(True)
            self.summary.setPlaceholderText(
                "Ready.\n\n"
                "Select a bundle folder, choose a mode, then:\n\n"
                "  (1) CAPTURE  - run on your existing Windows installation\n"
                "  (2) APPLY   - run after a fresh Windows install\n"
                "  (3) VERIFY  - confirm the restore is complete\n\n"
                "Enable Dry Run to preview before making any changes."
            )
            self.output_tabs.addTab(self.summary, "  Summary  ")

            # Results table tab
            table_wrap = QWidget()
            tw_l = QVBoxLayout(table_wrap); tw_l.setContentsMargins(0, 0, 0, 0)
            self.table_model = ResultsTableModel()
            self.table = QTableView(); self.table.setModel(self.table_model)
            self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
            self.table.setAlternatingRowColors(True)
            self.table.setShowGrid(False)
            hdr = self.table.horizontalHeader()
            hdr.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
            hdr.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
            hdr.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
            hdr.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
            self.table.verticalHeader().setVisible(False)
            self.table.setFrameShape(QFrame.Shape.NoFrame)
            tw_l.addWidget(self.table)
            self.output_tabs.addTab(table_wrap, "  Step Results  ")

            # Live log tab
            self.log = QPlainTextEdit(); self.log.setReadOnly(True); self.log.setMaximumBlockCount(8000)
            self.output_tabs.addTab(self.log, "  Live Log  ")

            main_l.addWidget(self.output_tabs, 1)

            # ── Action bar ────────────────────────────────────────────────────
            action_bar = QWidget()
            action_bar.setObjectName("actionBar")
            action_bar.setStyleSheet(
                "#actionBar { background: #10151c; border-top: 1px solid #232b35; padding: 0px; }"
            )
            ab_l = QHBoxLayout(action_bar)
            ab_l.setContentsMargins(16, 10, 16, 10); ab_l.setSpacing(10)

            self.btn_capture = QPushButton("▶  Capture"); self.btn_capture.setObjectName("btnCapture")
            self.btn_apply   = QPushButton("▶  Apply");   self.btn_apply.setObjectName("btnApply")
            self.btn_verify  = QPushButton("▶  Verify");  self.btn_verify.setObjectName("btnVerify")
            self.btn_capture.setMinimumHeight(38)
            self.btn_apply.setMinimumHeight(38)
            self.btn_verify.setMinimumHeight(38)

            self.btn_capture.clicked.connect(lambda: self.start_op("CAPTURE"))
            self.btn_apply.clicked.connect(lambda: self.start_op("APPLY"))
            self.btn_verify.clicked.connect(lambda: self.start_op("VERIFY"))

            ab_l.addWidget(self.btn_capture)
            ab_l.addWidget(self.btn_apply)
            ab_l.addWidget(self.btn_verify)
            ab_l.addStretch()

            self.btn_open_report = QPushButton("Open Report")
            self.btn_copy_diag   = QPushButton("Copy Diagnostics")
            self.btn_open_report.clicked.connect(self.open_last_report)
            self.btn_copy_diag.clicked.connect(self.copy_diagnostics)
            ab_l.addWidget(self.btn_open_report)
            ab_l.addWidget(self.btn_copy_diag)

            main_l.addWidget(action_bar, 0)
            body_l.addWidget(main_area, 1)
            outer_l.addWidget(body, 1)
            self.setCentralWidget(outer)

            # Status bar
            self.status_bar = QStatusBar(); self.setStatusBar(self.status_bar)
            self.status_bar.showMessage("Ready")
            self._progress_lbl = QLabel(""); self.status_bar.addPermanentWidget(self._progress_lbl)


        def _build_menus(self):
            from PyQt6.QtGui import QAction
            fm = self.menuBar().addMenu("File")
            a = QAction("Select Bundle Folder…", self); a.triggered.connect(self.browse_bundle); fm.addAction(a)
            b = QAction("Open Last Report", self); b.triggered.connect(self.open_last_report); fm.addAction(b)
            fm.addSeparator()
            q = QAction("Exit", self); q.triggered.connect(self.close); fm.addAction(q)

            lm = self.menuBar().addMenu("License")
            la = QAction("Manage License…", self); la.triggered.connect(self.open_license_dialog); lm.addAction(la)

            hm = self.menuBar().addMenu("Help")
            ha = QAction("How to Use", self); ha.triggered.connect(lambda: show_html_dialog(self,"Help",HELP_HTML)); hm.addAction(ha)
            hm.addSeparator()
            ab = QAction("About WinGOES Pro", self); ab.triggered.connect(lambda: show_html_dialog(self,"About",ABOUT_HTML)); hm.addAction(ab)

        # ── License ───────────────────────────────────────────────────────────

        def _update_license_badge(self):
            lic = self.license_info
            if lic.is_pro():
                self.lic_badge.setText(f"✓ Licensed  •  {self.license_info.edition or EDITION_NAME}")
                self.lic_badge.setProperty("licensed","true"); self.lic_badge.setProperty("trial","false")
            elif lic.trial and lic.valid:
                self.lic_badge.setText(f"Trial  •  {lic.trial_days_remaining}d left")
                self.lic_badge.setProperty("licensed","false"); self.lic_badge.setProperty("trial","true")
            else:
                self.lic_badge.setText("Unlicensed")
                self.lic_badge.setProperty("licensed","false"); self.lic_badge.setProperty("trial","false")
            self.lic_badge.style().unpolish(self.lic_badge); self.lic_badge.style().polish(self.lic_badge)

        def open_license_dialog(self):
            updated = show_license_dialog(self, self.license_info)
            if updated is not None:
                self.license_info = updated
                self._update_license_badge()

        # ── Workflow ─────────────────────────────────────────────────────────

        def _set_workflow(self, active: str):
            for key, btn in self.step_btns.items():
                btn.setProperty("active", "true" if key == active else "false")
                btn.style().unpolish(btn); btn.style().polish(btn)

        # ── Mode Gating ───────────────────────────────────────────────────────

        def on_mode_changed(self, mode: str):
            mode = (mode or "").strip()
            if mode == MODE_CLEAN:
                self.chk_tz.setChecked(False);    self.chk_tz.setEnabled(False)
                self.chk_power.setChecked(False);  self.chk_power.setEnabled(False)
                self.chk_drv_transfer.setChecked(False); self.chk_drv_transfer.setEnabled(False)
                self.lbl_ws_help.setText("Disabled in CLEAN REBUILD mode"); self.lbl_ws_help.setVisible(True)
                self.lbl_drv_help.setVisible(False)
            elif mode == MODE_SAME:
                self.chk_tz.setEnabled(True); self.chk_power.setEnabled(True)
                self.chk_drv_transfer.setEnabled(True); self.chk_drv_transfer.setChecked(False)
                self.lbl_ws_help.setVisible(False)
                self.lbl_drv_help.setText("⚠ Driver transfer gated by hardware fingerprint match"); self.lbl_drv_help.setVisible(True)
            else:
                self.chk_tz.setEnabled(True); self.chk_power.setEnabled(True)
                self.chk_drv_transfer.setEnabled(True); self.chk_drv_transfer.setChecked(False)
                self.lbl_ws_help.setVisible(False)
                self.lbl_drv_help.setText("⚠ Driver transfer still gated by hardware match"); self.lbl_drv_help.setVisible(True)

        # ── Bundle ────────────────────────────────────────────────────────────

        def browse_bundle(self):
            d = QFileDialog.getExistingDirectory(self, "Select bundle folder", str(Path.home()))
            if d: self.bundle_edit.setText(d)

        def current_bundle(self) -> Optional[Path]:
            s = self.bundle_edit.text().strip()
            if not s: return None
            p = Path(s)
            try: ensure_dir(p)
            except Exception: return None
            return p

        def build_toggles(self) -> Toggles:
            return Toggles(
                use_winget=self.chk_winget.isChecked(), use_choco=self.chk_choco.isChecked(),
                use_scoop=self.chk_scoop.isChecked(), cfg_git=self.chk_git.isChecked(),
                cfg_gitconfig_file=self.chk_gitconfig.isChecked(), cfg_ssh=self.chk_ssh.isChecked(),
                cfg_vscode=self.chk_vscode.isChecked(), cfg_windows_terminal=self.chk_terminal.isChecked(),
                win_tz_region=self.chk_tz.isChecked(), win_power_plan=self.chk_power.isChecked(),
                drv_inventory=self.chk_drv_inv.isChecked(), drv_checklist=self.chk_drv_check.isChecked(),
                drv_export_driverstore=self.chk_drv_transfer.isChecked(),
                drv_restore_driverstore=self.chk_drv_transfer.isChecked(),
            )

        # ── Operations ────────────────────────────────────────────────────────

        def set_busy(self, busy: bool, op: str = ""):
            for w in (self.btn_capture, self.btn_apply, self.btn_verify, self.mode_combo, self.dryrun_chk):
                w.setEnabled(not busy)
            if busy:
                self._progress_lbl.setText(f"Running {op}…")
                self.status_bar.showMessage(f"{op} in progress — please wait…")
            else:
                self._progress_lbl.setText(""); self.status_bar.showMessage("Ready")

        def confirm_apply(self) -> bool:
            if self.dryrun_chk.isChecked(): return True
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Icon.Warning)
            msg.setWindowTitle("Confirm Apply")
            msg.setText("<b>Dry Run is OFF.</b><br>This will make real changes to the system.<br>Proceed?")
            msg.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            msg.setDefaultButton(QMessageBox.StandardButton.No)
            return msg.exec() == QMessageBox.StandardButton.Yes

        def start_op(self, op_name: str):
            if not self.license_info.valid:
                QMessageBox.warning(self, "License Required",
                    f"{APP_NAME} requires a valid license or active trial.\n\nUse License → Manage License to activate.")
                return
            bundle = self.current_bundle()
            if not bundle:
                QMessageBox.warning(self, "Bundle Folder Required", "Please select a bundle folder first.")
                return
            mode = self.mode_combo.currentText().strip()
            if mode not in ALL_MODES:
                QMessageBox.warning(self, "Mode Error", "Invalid mode."); return
            if op_name == "APPLY" and not self.confirm_apply(): return

            self.table_model.clear(); self.log.clear(); self.summary.clear()
            dry_label = "Yes" if self.dryrun_chk.isChecked() else '<b style="color:#ff5c66">No</b>'
            self.summary.append(
                f"<b>{APP_TITLE}</b>  |  {op_name}  |  Mode: {mode}  |  "
                f"Dry-run: {dry_label}"
                f"<br>Bundle: {bundle}<br><br>"
            )
            self.output_tabs.setCurrentIndex(0)
            self._set_workflow(op_name)

            t = self.build_toggles()
            self.worker = OpWorker(op_name, bundle, mode, self.dryrun_chk.isChecked(), t)
            self.worker.sig.log_line.connect(self.on_log_line)
            self.worker.sig.row.connect(self.on_row)
            self.worker.sig.summary.connect(self.on_summary)
            self.worker.sig.finished.connect(lambda ok, rp, sp: self.on_finished(ok, rp, sp, op_name))
            self.set_busy(True, op_name)
            self.worker.start()

        def on_log_line(self, line): self.log.appendPlainText(line)
        def on_row(self, step, item, status, message): self.table_model.add_row(step, item, status, message)
        def on_summary(self, text): self.summary.append(text)

        def on_finished(self, ok: bool, report_path: str, summary_path: str, op_name: str):
            self.set_busy(False)
            self.last_report_path = report_path or None
            self.last_summary_path = summary_path or None
            badge = ('<span style="color:#4be08a;font-weight:bold;">✓ COMPLETED</span>' if ok else
                     '<span style="color:#ff5c66;font-weight:bold;">⚠ COMPLETED WITH ISSUES</span>')
            self.summary.append(f"<br>{badge}<br>")
            if report_path:
                self.summary.append(f'Report: <a href="file:///{report_path}" style="color:#2fd6c3">{report_path}</a>')
            _result_word = "succeeded" if ok else "completed with issues"
            _report_label = report_path or "no report"
            self.status_bar.showMessage(
                f"{op_name} {_result_word}  —  {_report_label}"
            )
            if not ok: self.output_tabs.setCurrentIndex(1)

        def open_last_report(self):
            if not self.last_report_path:
                QMessageBox.information(self, "No Report", "No report generated yet."); return
            p = Path(self.last_report_path)
            if not p.exists():
                QMessageBox.warning(self, "Not Found", f"Not found:\n{p}"); return
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))

        def copy_diagnostics(self):
            parts = []
            if self.last_report_path:  parts.append(f"report={self.last_report_path}")
            if self.last_summary_path: parts.append(f"summary={self.last_summary_path}")
            txt = "\n".join(parts) if parts else "No diagnostics available yet."
            QApplication.clipboard().setText(txt)
            QMessageBox.information(self, "Diagnostics Copied", txt)

    # ── Bootstrap ─────────────────────────────────────────────────────────────

    def _set_wid(app_id):
        try:
            import ctypes; ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
        except Exception: pass

    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(THEME_STYLE)
    _set_wid("WinGOES.Pro.2.1")

    icon_path = Path(__file__).resolve().parent / "assets" / "wingoes.ico"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    lic = check_license()
    w = MainWindow(lic)
    if icon_path.exists():
        w.setWindowIcon(QIcon(str(icon_path)))
    w.show()

    # On first run with no valid license, prompt activation
    if not lic.valid:
        QTimer.singleShot(500, lambda: w.open_license_dialog())

    return app.exec()


# ── CLI ────────────────────────────────────────────────────────────────────────


def parse_cli(argv):
    p = argparse.ArgumentParser(description=APP_TITLE)
    p.add_argument("--cli", action="store_true")
    p.add_argument("op", nargs="?", choices=["capture","apply","verify"])
    p.add_argument("--bundle", type=str, default="")
    p.add_argument("--mode", type=str, default=MODE_CLEAN, choices=ALL_MODES)
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--no-winget", action="store_true")
    p.add_argument("--choco", action="store_true"); p.add_argument("--scoop", action="store_true")
    p.add_argument("--no-git", action="store_true"); p.add_argument("--no-gitconfig", action="store_true")
    p.add_argument("--no-ssh", action="store_true"); p.add_argument("--no-vscode", action="store_true")
    p.add_argument("--no-terminal", action="store_true")
    p.add_argument("--tz-region", action="store_true"); p.add_argument("--power-plan", action="store_true")
    p.add_argument("--no-driver-inventory", action="store_true"); p.add_argument("--no-driver-checklist", action="store_true")
    p.add_argument("--driver-transfer", action="store_true")
    p.add_argument("--genkey", metavar="EDITION", help="Generate license key (dev use)")
    p.add_argument("--validate-key", metavar="KEY", help="Validate a license key")
    return p.parse_args(argv)


def cli_main(ns) -> int:
    if ns.genkey:
        key = generate_key(ns.genkey.upper())
        print(f"Generated {ns.genkey.upper()} key: {key}")
        ok, ed, err = validate_key(key)
        print(f"Self-validation: valid={ok} edition={ed}")
        return 0
    if getattr(ns, "validate_key", None):
        ok, ed, err = validate_key(ns.validate_key)
        print(f"valid={ok} edition={ed!r} err={err!r}")
        return 0 if ok else 1
    if not ns.op:
        print("ERROR: CLI mode requires an operation: capture/apply/verify", file=sys.stderr); return 2
    if not ns.bundle:
        print("ERROR: --bundle required in CLI mode", file=sys.stderr); return 2
    bundle = Path(ns.bundle); ensure_dir(bundle)
    toggles = Toggles(
        use_winget=not ns.no_winget, use_choco=bool(ns.choco), use_scoop=bool(ns.scoop),
        cfg_git=not ns.no_git, cfg_gitconfig_file=not ns.no_gitconfig, cfg_ssh=not ns.no_ssh,
        cfg_vscode=not ns.no_vscode, cfg_windows_terminal=not ns.no_terminal,
        win_tz_region=bool(ns.tz_region), win_power_plan=bool(ns.power_plan),
        drv_inventory=not ns.no_driver_inventory, drv_checklist=not ns.no_driver_checklist,
        drv_export_driverstore=bool(ns.driver_transfer),
        drv_restore_driverstore=bool(ns.driver_transfer),
    )
    def cb(line): print(line)
    if ns.op == "capture":
        ctx, report = op_capture(bundle, ns.mode, bool(ns.dry_run), toggles, stream_cb=cb)
        print(f"\nReport: {ctx.report_path}\nSummary: {ctx.summary_path}")
        return 0 if all(s.get("ok") for s in report.get("steps",[])) else 1
    if ns.op == "apply":
        ctx, report = op_apply(bundle, ns.mode, bool(ns.dry_run), toggles, stream_cb=cb)
        return 0 if all(s.get("ok") for s in report.get("steps",[])) else 1
    if ns.op == "verify":
        ctx, report, checklist = op_verify(bundle, ns.mode, bool(ns.dry_run), toggles, stream_cb=cb)
        for c in checklist: print(f"- {c}")
        return 0 if all(s.get("ok") for s in report.get("steps",[])) else 1
    return 2


def main() -> int:
    if not is_windows():
        print("ERROR: WinGOES Pro requires Windows 10 Pro.", file=sys.stderr); return 2
    ns = parse_cli(sys.argv[1:])
    if ns.cli: return cli_main(ns)
    try:
        return gui_main()
    except ImportError as e:
        print("ERROR: PyQt6 required.  pip install PyQt6", file=sys.stderr)
        print(str(e), file=sys.stderr); return 2


if __name__ == "__main__":
    raise SystemExit(main())
