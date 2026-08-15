from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QProgressBar, QFrame, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QPixmap
from gui.widgets import CardWidget, LogConsole

class PantallaProceso(QWidget):
    cancelar_procesamiento = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Barra superior con Título de monitoreo
        top_bar = QHBoxLayout()
        self.title_lbl = QLabel("Monitoreo en Tiempo Real", self)
        self.title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title_lbl.setStyleSheet("color: #0f172a;")
        
        self.btn_cancel = QPushButton("Cancelar Procesamiento", self)
        self.btn_cancel.setCursor(Qt.PointingHandCursor)
        self.btn_cancel.setStyleSheet("""
            QPushButton {
                background-color: #ef4444;
                color: #ffffff;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #dc2626;
            }
        """)
        self.btn_cancel.clicked.connect(self.on_cancel_clicked)
        top_bar.addWidget(self.title_lbl)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_cancel)
        main_layout.addLayout(top_bar)

        # Seccion Central - Splitter para separar tarjetas/consola del preview
        splitter = QSplitter(Qt.Horizontal, self)
        
        # Lado izquierdo: Tarjetas de módulos y consola de logs
        left_widget = QWidget(self)
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(16)

        # Tarjetas de los módulos
        modules_layout = QHBoxLayout()
        self.card_m1 = CardWidget("Módulo 1", "Detección", "○ En espera", parent=self)
        self.card_m2 = CardWidget("Módulo 2", "Procesamiento", "○ En espera", parent=self)
        self.card_m3 = CardWidget("Módulo 3", "Organización", "○ En espera", parent=self)
        modules_layout.addWidget(self.card_m1)
        modules_layout.addWidget(self.card_m2)
        modules_layout.addWidget(self.card_m3)
        left_layout.addLayout(modules_layout)

        # Consola de logs
        self.console = LogConsole(self)
        left_layout.addWidget(self.console)
        splitter.addWidget(left_widget)

        # Lado derecho: Tarjeta de Vista Previa y Características PDI
        right_widget = QFrame(self)
        right_widget.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
            }
        """)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(16, 16, 16, 16)
        right_layout.setSpacing(12)

        preview_header = QLabel("ÚLTIMA FOTO PROCESADA", self)
        preview_header.setFont(QFont("Segoe UI", 9, QFont.Bold))
        preview_header.setStyleSheet("color: #64748b; letter-spacing: 1px; border: none;")
        right_layout.addWidget(preview_header)

        # Imagen de preview
        self.img_preview = QLabel(self)
        self.img_preview.setAlignment(Qt.AlignCenter)
        self.img_preview.setMinimumSize(320, 240)
        self.img_preview.setStyleSheet("""
            QLabel {
                background-color: #f8fafc;
                border: 1px dashed #cbd5e1;
                border-radius: 8px;
            }
        """)
        right_layout.addWidget(self.img_preview)

        # Metadatos del preview
        self.meta_layout = QVBoxLayout()
        self.meta_layout.setSpacing(6)
        
        self.lbl_objs = QLabel("Objetos detectados: -", self)
        self.lbl_objs.setStyleSheet("color: #334155; font-size: 11px; border: none;")
        self.lbl_cat = QLabel("Categoría asignada: -", self)
        self.lbl_cat.setStyleSheet("color: #334155; font-size: 11px; border: none;")
        self.lbl_color = QLabel("Color dominante (RGB): -", self)
        self.lbl_color.setStyleSheet("color: #334155; font-size: 11px; border: none;")
        self.lbl_edge = QLabel("Densidad de bordes: -", self)
        self.lbl_edge.setStyleSheet("color: #334155; font-size: 11px; border: none;")
        self.lbl_texture = QLabel("Contraste de textura: -", self)
        self.lbl_texture.setStyleSheet("color: #334155; font-size: 11px; border: none;")

        self.meta_layout.addWidget(self.lbl_objs)
        self.meta_layout.addWidget(self.lbl_cat)
        self.meta_layout.addWidget(self.lbl_color)
        self.meta_layout.addWidget(self.lbl_edge)
        self.meta_layout.addWidget(self.lbl_texture)
        right_layout.addLayout(self.meta_layout)
        splitter.addWidget(right_widget)

        # Proporciones del splitter
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)
        main_layout.addWidget(splitter)

        # Sección inferior: Barra de progreso e información de estado
        progress_container = QFrame(self)
        progress_container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
            }
        """)
        p_layout = QVBoxLayout(progress_container)
        p_layout.setContentsMargins(12, 12, 12, 12)
        
        self.status_lbl = QLabel("Preparando ejecución del pipeline...", self)
        self.status_lbl.setFont(QFont("Segoe UI", 10, QFont.Medium))
        self.status_lbl.setStyleSheet("color: #334155; border: none;")
        
        self.progress_bar = QProgressBar(self)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                height: 18px;
                border: 1px solid #cbd5e1;
                border-radius: 9px;
                text-align: center;
                background-color: #f8fafc;
                color: #0f172a;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #10b981;
                border-radius: 9px;
            }
        """)

        p_layout.addWidget(self.status_lbl)
        p_layout.addWidget(self.progress_bar)
        main_layout.addWidget(progress_container)

    def on_cancel_clicked(self):
        self.cancelar_procesamiento.emit()

    def update_module_state(self, mod_id: int, state: str):
        card = None
        if mod_id == 1:
            card = self.card_m1
        elif mod_id == 2:
            card = self.card_m2
        elif mod_id == 3:
            card = self.card_m3

        if not card:
            return

        if state == "waiting":
            card.set_subtitle("○ En espera")
            card.set_active(False)
        elif state == "processing":
            card.set_subtitle("⟳ En proceso")
            card.set_active(False)
            card.setStyleSheet("CardWidget { background-color: #eff6ff; border: 1px solid #3b82f6; border-radius: 12px; }")
        elif state == "completed":
            card.set_subtitle("✓ Completado")
            card.set_active(True)

    def update_preview_image(self, img_path: str, categoria: str, num_objs: int, meta: dict):
        # Cargar pixmap y ajustarlo a las dimensiones del label
        pixmap = QPixmap(img_path)
        if not pixmap.isNull():
            self.img_preview.setPixmap(pixmap.scaled(
                self.img_preview.width(), 
                self.img_preview.height(), 
                Qt.KeepAspectRatio, 
                Qt.SmoothTransformation
            ))
        
        self.lbl_objs.setText(f"Objetos detectados: {num_objs}")
        self.lbl_cat.setText(f"Categoría asignada: {categoria}")
        
        color_rgb = meta.get("color_dominante_rgb", "-")
        self.lbl_color.setText(f"Color dominante (RGB): {color_rgb}")
        
        density = meta.get("densidad_bordes", "-")
        self.lbl_edge.setText(f"Densidad de bordes: {density}")
        
        texture = meta.get("contraste_textura", "-")
        self.lbl_texture.setText(f"Contraste de textura: {texture}")

    def update_status(self, current: int, total: int, elapsed: float, remaining: float):
        self.status_lbl.setText(
            f"Procesando: {current} / {total} | "
            f"Tiempo Transcurrido: {elapsed:.1f}s | "
            f"Restante Estimado: {remaining:.1f}s"
        )
