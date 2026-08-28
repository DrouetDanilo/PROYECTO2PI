from PySide6.QtWidgets import QFrame, QVBoxLayout, QLabel, QHBoxLayout, QTextEdit
from PySide6.QtCore import Qt, QSize, QTime
from PySide6.QtGui import QFont, QColor

class CardWidget(QFrame):
    """Tarjeta moderna e interactiva para métricas y estados."""
    def __init__(self, title: str, value: str, subtitle: str = "", active: bool = False, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setGraphicsEffect(None) # Para evitar recargar la GPU en Qt6 simple
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(6)

        self.title_lbl = QLabel(title.upper())
        self.title_lbl.setFont(QFont("Segoe UI", 9, QFont.Bold))
        self.title_lbl.setStyleSheet("color: #1e293b; letter-spacing: 1px;")

        self.value_lbl = QLabel(value)
        self.value_lbl.setFont(QFont("Segoe UI", 22, QFont.Bold))
        self.value_lbl.setStyleSheet("color: #0f172a;")

        self.subtitle_lbl = QLabel(subtitle)
        self.subtitle_lbl.setFont(QFont("Segoe UI", 9))
        self.subtitle_lbl.setStyleSheet("color: #1e293b;")

        layout.addWidget(self.title_lbl)
        layout.addWidget(self.value_lbl)
        if subtitle:
            layout.addWidget(self.subtitle_lbl)

        self.set_active(active)

    def set_active(self, active: bool):
        if active:
            self.setStyleSheet("""
                CardWidget {
                    background-color: #f0fdf4;
                    border: 2px solid #22c55e;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                CardWidget {
                    background-color: #ffffff;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                }
            """)

    def set_value(self, value: str):
        self.value_lbl.setText(value)

    def set_subtitle(self, subtitle: str):
        self.subtitle_lbl.setText(subtitle)


class LogConsole(QTextEdit):
    """Consola de log estilizada con colores terminal modernos."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setFont(QFont("Courier New", 10))
        self.setStyleSheet("""
            QTextEdit {
                background-color: #0f172a;
                color: #38bdf8;
                border: 1px solid #1e293b;
                border-radius: 8px;
                padding: 10px;
            }
        """)

    def append_log(self, message: str):
        timestamp = time_str = QTime.currentTime().toString("hh:mm:ss")
        self.append(f"<span style='color: #64748b;'>[{timestamp}]</span> {message}")
        # Scroll al final
        self.ensureCursorVisible()
