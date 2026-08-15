import json
from pathlib import Path
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QScrollArea, QSplitter, QListWidget, QListWidgetItem, QTabWidget, QMessageBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon
from gui.widgets import CardWidget

class PantallaResultados(QWidget):
    nueva_clasificacion = Signal()
    abrir_carpeta_resultados = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data = {}
        self.output_dir = Path(".")
        self.current_category = ""
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Barra superior de navegación / acciones
        top_bar = QHBoxLayout()
        self.title_lbl = QLabel("Resultados de la Clasificación", self)
        self.title_lbl.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title_lbl.setStyleSheet("color: #0f172a;")

        self.btn_open_folder = QPushButton("Abrir Carpeta", self)
        self.btn_open_folder.setCursor(Qt.PointingHandCursor)
        self.btn_open_folder.setStyleSheet("""
            QPushButton {
                background-color: #f1f5f9;
                color: #334155;
                padding: 8px 16px;
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e2e8f0;
            }
        """)
        self.btn_open_folder.clicked.connect(self.on_open_folder_clicked)

        self.btn_export = QPushButton("Exportar Reporte", self)
        self.btn_export.setCursor(Qt.PointingHandCursor)
        self.btn_export.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: #ffffff;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        self.btn_export.clicked.connect(self.on_export_clicked)

        self.btn_new = QPushButton("Nueva Clasificación", self)
        self.btn_new.setCursor(Qt.PointingHandCursor)
        self.btn_new.setStyleSheet("""
            QPushButton {
                background-color: #3b82f6;
                color: #ffffff;
                padding: 8px 16px;
                border: none;
                border-radius: 6px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2563eb;
            }
        """)
        self.btn_new.clicked.connect(self.on_new_clicked)

        top_bar.addWidget(self.title_lbl)
        top_bar.addStretch()
        top_bar.addWidget(self.btn_open_folder)
        top_bar.addWidget(self.btn_export)
        top_bar.addWidget(self.btn_new)
        main_layout.addLayout(top_bar)

        # Tarjetas de estadísticas superiores
        stats_layout = QHBoxLayout()
        self.card_total = CardWidget("Fotos Procesadas", "0", parent=self)
        self.card_cats = CardWidget("Categorías", "0", parent=self)
        self.card_time = CardWidget("Tiempo Total", "0 s", parent=self)
        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_cats)
        stats_layout.addWidget(self.card_time)
        main_layout.addLayout(stats_layout)

        # Contenido Principal: Categorías a la izquierda, Galería/Detalle a la derecha
        main_splitter = QSplitter(Qt.Horizontal, self)

        # Izquierda: Lista de Categorías
        self.categories_list = QListWidget(self)
        self.categories_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 12px;
                border-bottom: 1px solid #f1f5f9;
                border-radius: 4px;
                color: #334155;
                font-weight: bold;
            }
            QListWidget::item:selected {
                background-color: #eff6ff;
                color: #2563eb;
            }
        """)
        self.categories_list.itemClicked.connect(self.on_category_selected)
        main_splitter.addWidget(self.categories_list)

        # Derecha: Splitter para la Galería (superior) y Vista Detallada (inferior)
        right_splitter = QSplitter(Qt.Vertical, self)

        # Galería de miniaturas
        gallery_container = QFrame(self)
        gallery_container.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;")
        gallery_layout = QVBoxLayout(gallery_container)
        gallery_layout.setContentsMargins(12, 12, 12, 12)
        
        self.gallery_title = QLabel("Seleccione una categoría para ver sus fotografías", self)
        self.gallery_title.setFont(QFont("Segoe UI", 11, QFont.Bold))
        self.gallery_title.setStyleSheet("color: #0f172a; border: none;")
        gallery_layout.addWidget(self.gallery_title)

        self.gallery_list = QListWidget(self)
        self.gallery_list.setViewMode(QListWidget.IconMode)
        self.gallery_list.setIconSize(QSize(100, 100))
        self.gallery_list.setResizeMode(QListWidget.Adjust)
        self.gallery_list.setSpacing(12)
        self.gallery_list.setStyleSheet("""
            QListWidget {
                background-color: #f8fafc;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            QListWidget::item {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QListWidget::item:selected {
                border: 2px solid #3b82f6;
            }
        """)
        self.gallery_list.itemClicked.connect(self.on_image_selected)
        gallery_layout.addWidget(self.gallery_list)
        right_splitter.addWidget(gallery_container)

        # Vista Detallada (PDI Insumos)
        detail_container = QFrame(self)
        detail_container.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;")
        detail_layout = QHBoxLayout(detail_container)
        detail_layout.setContentsMargins(12, 12, 12, 12)

        # Tabs de visualización de imágenes procesadas
        self.tabs_insumos = QTabWidget(self)
        self.tab_original = QLabel(self)
        self.tab_original.setAlignment(Qt.AlignCenter)
        self.tab_crudos = QLabel(self)
        self.tab_crudos.setAlignment(Qt.AlignCenter)
        self.tab_procesados = QLabel(self)
        self.tab_procesados.setAlignment(Qt.AlignCenter)
        self.tab_mascara = QLabel(self)
        self.tab_mascara.setAlignment(Qt.AlignCenter)
        self.tab_recorte = QLabel(self)
        self.tab_recorte.setAlignment(Qt.AlignCenter)

        self.tabs_insumos.addTab(self.tab_original, "Original")
        self.tabs_insumos.addTab(self.tab_crudos, "Bordes Crudos")
        self.tabs_insumos.addTab(self.tab_procesados, "Bordes Procesados")
        self.tabs_insumos.addTab(self.tab_mascara, "Máscara")
        self.tabs_insumos.addTab(self.tab_recorte, "Recorte")
        
        detail_layout.addWidget(self.tabs_insumos, 3)

        # Panel derecho con detalles numéricos / GLCM
        self.info_panel = QFrame(self)
        self.info_panel.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px;")
        self.info_panel_layout = QVBoxLayout(self.info_panel)
        self.info_panel_layout.setSpacing(8)

        self.lbl_det_title = QLabel("Detalles del Análisis", self)
        self.lbl_det_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_det_title.setStyleSheet("color: #0f172a; border: none;")
        self.info_panel_layout.addWidget(self.lbl_det_title)

        self.lbl_det_cat = QLabel("Categoría: -", self)
        self.lbl_det_objs = QLabel("Objetos detectados: -", self)
        self.lbl_det_color = QLabel("Color dominante RGB: -", self)
        self.lbl_det_density = QLabel("Densidad de bordes: -", self)
        self.lbl_det_contrast = QLabel("Contraste de textura: -", self)
        
        for lbl in [self.lbl_det_cat, self.lbl_det_objs, self.lbl_det_color, self.lbl_det_density, self.lbl_det_contrast]:
            lbl.setStyleSheet("color: #334155; font-size: 11px; border: none;")
            self.info_panel_layout.addWidget(lbl)

        self.info_panel_layout.addStretch()
        detail_layout.addWidget(self.info_panel, 1)

        right_splitter.addWidget(detail_container)
        
        right_splitter.setStretchFactor(0, 3)
        right_splitter.setStretchFactor(1, 4)

        main_splitter.addWidget(right_splitter)
        
        main_splitter.setStretchFactor(0, 1)
        main_splitter.setStretchFactor(1, 4)
        main_layout.addWidget(main_splitter)

    def load_report(self, report_path: str, output_dir: str):
        self.output_dir = Path(output_dir)
        try:
            with open(report_path, "r", encoding="utf-8") as f:
                self.report_data = json.load(f)
        except Exception as e:
            QMessageBox.critical(self, "Error", f"No se pudo leer el reporte final:\n{str(e)}")
            return

        # Actualizar Tarjetas superiores
        self.card_total.set_value(str(self.report_data.get("total_imagenes_procesadas", 0)))
        self.card_cats.set_value(str(self.report_data.get("categorias_generadas", 0)))
        self.card_time.set_value(f"{self.report_data.get('tiempo_total_segundos', 0)} s")

        # Cargar lista de categorías
        self.categories_list.clear()
        conteo = self.report_data.get("conteo_por_categoria", {})
        for cat, count in conteo.items():
            if count > 0:
                item = QListWidgetItem(f"{cat} ({count} fotos)")
                item.setData(Qt.UserRole, cat)
                self.categories_list.addItem(item)

        if self.categories_list.count() > 0:
            self.categories_list.setCurrentRow(0)
            self.on_category_selected(self.categories_list.item(0))

    def on_category_selected(self, item):
        cat = item.data(Qt.UserRole)
        self.current_category = cat
        self.gallery_title.setText(f"{cat.upper()} — Fotografías reales")
        self.gallery_list.clear()

        # Filtrar imágenes del reporte en esta categoría
        detalles = self.report_data.get("detalle", [])
        for det in detalles:
            if det.get("categoria") == cat:
                # Ruta de la imagen original guardada
                rel_path = det.get("rutas_generadas", {}).get("original", "")
                full_path = self.output_dir / rel_path
                
                if full_path.exists():
                    g_item = QListWidgetItem(det.get("nombre_original"))
                    # Establecer icono con pixmap para la miniatura
                    pixmap = QPixmap(str(full_path))
                    if not pixmap.isNull():
                        g_item.setIcon(QIcon(pixmap.scaled(100, 100, Qt.KeepAspectRatio)))
                    g_item.setData(Qt.UserRole, det)
                    self.gallery_list.addItem(g_item)

        if self.gallery_list.count() > 0:
            self.gallery_list.setCurrentRow(0)
            self.on_image_selected(self.gallery_list.item(0))

    def on_image_selected(self, item):
        det = item.data(Qt.UserRole)
        rutas = det.get("rutas_generadas", {})
        
        # Mostrar transformaciones visuales en los Tabs
        self.update_tab_image(self.tab_original, self.output_dir / rutas.get("original", ""))
        
        # Insumos de objetos (usamos el primero por defecto si tiene)
        objs = rutas.get("objetos", [])
        if objs:
            obj = objs[0]
            self.update_tab_image(self.tab_crudos, self.output_dir / obj.get("bordes_crudos", ""))
            self.update_tab_image(self.tab_procesados, self.output_dir / obj.get("bordes_filtrados", ""))
            self.update_tab_image(self.tab_mascara, self.output_dir / obj.get("mascara", ""))
            self.update_tab_image(self.tab_recorte, self.output_dir / obj.get("objeto_segmentado", ""))
        else:
            self.tab_crudos.clear()
            self.tab_procesados.clear()
            self.tab_mascara.clear()
            self.tab_recorte.clear()

        # Actualizar panel de detalles
        self.lbl_det_cat.setText(f"Categoría: {det.get('categoria')}")
        self.lbl_det_objs.setText(f"Objetos detectados: {det.get('num_objetos_detectados')}")
        
        objs_proc = det.get("objetos_procesados", [])
        if objs_proc:
            p_obj = objs_proc[0]
            self.lbl_det_color.setText(f"Color dominante RGB: {p_obj.get('color_dominante_rgb')}")
            self.lbl_det_density.setText(f"Densidad de bordes: {p_obj.get('densidad_bordes')}")
            self.lbl_det_contrast.setText(f"Contraste de textura: {p_obj.get('contraste_textura')}")
        else:
            self.lbl_det_color.setText("Color dominante RGB: -")
            self.lbl_det_density.setText("Densidad de bordes: -")
            self.lbl_det_contrast.setText("Contraste de textura: -")

    def update_tab_image(self, label: QLabel, path: Path):
        if not path or not path.exists():
            label.setText("Insumo no disponible")
            return
        pixmap = QPixmap(str(path))
        if not pixmap.isNull():
            label.setPixmap(pixmap.scaled(360, 270, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    def on_export_clicked(self):
        # Abre el archivo del reporte JSON directamente en el visor predeterminado del sistema
        report_file = self.output_dir / "reporte_final.json"
        if report_file.exists():
            os.startfile(str(report_file.resolve()))
        else:
            QMessageBox.warning(self, "Error", "El archivo de reporte no existe.")

    def on_open_folder_clicked(self):
        self.abrir_carpeta_resultados.emit()

    def on_new_clicked(self):
        self.nueva_clasificacion.emit()
