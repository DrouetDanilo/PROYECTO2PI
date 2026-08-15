from pathlib import Path
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QFileDialog, QMessageBox, QFrame
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

class PantallaInicio(QWidget):
    iniciar_procesamiento = Signal(str, str) # input_dir, output_dir

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(40, 40, 40, 40)
        main_layout.setSpacing(24)
        main_layout.setAlignment(Qt.AlignCenter)

        # Contenedor central
        container = QFrame(self)
        container.setFixedWidth(640)
        container.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 16px;
            }
        """)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(32, 32, 32, 32)
        container_layout.setSpacing(20)

        # Título y Subtítulo
        title_label = QLabel("Clasificador y Organizador Automático de Fotografías", self)
        title_label.setFont(QFont("Segoe UI", 18, QFont.Bold))
        title_label.setStyleSheet("color: #0f172a; border: none;")
        title_label.setAlignment(Qt.AlignCenter)

        subtitle_label = QLabel("Procesamiento Digital de Imágenes", self)
        subtitle_label.setFont(QFont("Segoe UI", 11, QFont.Medium))
        subtitle_label.setStyleSheet("color: #64748b; border: none;")
        subtitle_label.setAlignment(Qt.AlignCenter)

        container_layout.addWidget(title_label)
        container_layout.addWidget(subtitle_label)

        # Separador
        line = QFrame(self)
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #e2e8f0; border: none;")
        container_layout.addWidget(line)

        # Campos de carpetas
        # Entrada
        input_layout = QVBoxLayout()
        input_label = QLabel("Carpeta de Entrada (Fotografías originales)", self)
        input_label.setStyleSheet("color: #334155; font-weight: bold; border: none;")
        input_layout.addWidget(input_label)

        input_field_layout = QHBoxLayout()
        self.input_edit = QLineEdit(self)
        self.input_edit.setPlaceholderText("Seleccione la carpeta de origen...")
        self.input_edit.setText("./entrada")
        self.input_edit.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background-color: #f8fafc;
                color: #0f172a;
            }
        """)
        self.btn_browse_input = QPushButton("Examinar", self)
        self.btn_browse_input.setCursor(Qt.PointingHandCursor)
        self.btn_browse_input.setStyleSheet("""
            QPushButton {
                padding: 10px 16px;
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                color: #334155;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.btn_browse_input.clicked.connect(self.browse_input)
        input_field_layout.addWidget(self.input_edit)
        input_field_layout.addWidget(self.btn_browse_input)
        input_layout.addLayout(input_field_layout)
        container_layout.addLayout(input_layout)

        # Salida
        output_layout = QVBoxLayout()
        output_label = QLabel("Carpeta de Salida (Resultados y Reportes)", self)
        output_label.setStyleSheet("color: #334155; font-weight: bold; border: none;")
        output_layout.addWidget(output_label)

        output_field_layout = QHBoxLayout()
        self.output_edit = QLineEdit(self)
        self.output_edit.setPlaceholderText("Seleccione la carpeta de destino...")
        self.output_edit.setText("./Datasets/Resultados_DIP")
        self.output_edit.setStyleSheet("""
            QLineEdit {
                padding: 10px;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                background-color: #f8fafc;
                color: #0f172a;
            }
        """)
        self.btn_browse_output = QPushButton("Examinar", self)
        self.btn_browse_output.setCursor(Qt.PointingHandCursor)
        self.btn_browse_output.setStyleSheet("""
            QPushButton {
                padding: 10px 16px;
                background-color: #f1f5f9;
                border: 1px solid #cbd5e1;
                border-radius: 8px;
                color: #334155;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.btn_browse_output.clicked.connect(self.browse_output)
        output_field_layout.addWidget(self.output_edit)
        output_field_layout.addWidget(self.btn_browse_output)
        output_layout.addLayout(output_field_layout)
        container_layout.addLayout(output_layout)

        # Panel de información técnica
        info_panel = QFrame(self)
        info_panel.setStyleSheet("""
            QFrame {
                background-color: #f0fdf4;
                border: 1px solid #bbf7d0;
                border-radius: 8px;
            }
        """)
        info_layout = QVBoxLayout(info_panel)
        info_layout.setContentsMargins(12, 12, 12, 12)
        info_title = QLabel("Tecnologías y Métodos Utilizados:", self)
        info_title.setFont(QFont("Segoe UI", 9, QFont.Bold))
        info_title.setStyleSheet("color: #166534; border: none;")
        info_desc = QLabel("• Módulo 1: Detección y Segmentación Inteligente (YOLOv8m-seg)\n"
                           "• Módulo 2: Suavizado Gaussiano, Bordes (Canny) y Análisis de Texturas (GLCM)\n"
                           "• Módulo 3: Clasificación Dinámica (K-Means), Organización Física e Informes", self)
        info_desc.setFont(QFont("Segoe UI", 9))
        info_desc.setStyleSheet("color: #15803d; border: none;")
        info_layout.addWidget(info_title)
        info_layout.addWidget(info_desc)
        container_layout.addWidget(info_panel)

        # Botón de inicio
        self.btn_start = QPushButton("Iniciar procesamiento", self)
        self.btn_start.setCursor(Qt.PointingHandCursor)
        self.btn_start.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.btn_start.setStyleSheet("""
            QPushButton {
                padding: 12px;
                background-color: #3b82f6;
                color: #ffffff;
                border: none;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.btn_start.clicked.connect(self.on_start_clicked)
        container_layout.addWidget(self.btn_start)

        main_layout.addWidget(container)

    def browse_input(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de entrada", self.input_edit.text())
        if folder:
            self.input_edit.setText(folder)

    def browse_output(self):
        folder = QFileDialog.getExistingDirectory(self, "Seleccionar carpeta de salida", self.output_edit.text())
        if folder:
            self.output_edit.setText(folder)

    def on_start_clicked(self):
        in_path = self.input_edit.text().strip()
        out_path = self.output_edit.text().strip()

        # Validación
        if not in_path:
            QMessageBox.critical(self, "Ruta no seleccionada", "Por favor seleccione la carpeta de entrada.")
            return
        
        in_dir = Path(in_path)
        if not in_dir.exists() or not in_dir.is_dir():
            QMessageBox.critical(self, "Ruta inválida", "La carpeta de entrada no existe o no es válida.")
            return

        out_dir = Path(out_path)
        if not out_dir.exists():
            reply = QMessageBox.question(
                self, "Crear carpeta", 
                f"La carpeta de salida no existe.\n¿Desea crearla automáticamente en:\n{out_path}?",
                QMessageBox.Yes | QMessageBox.No
            )
            if reply == QMessageBox.Yes:
                try:
                    out_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    QMessageBox.critical(self, "Error", f"No se pudo crear la carpeta: {str(e)}")
                    return
            else:
                return

        self.iniciar_procesamiento.emit(in_path, out_path)
