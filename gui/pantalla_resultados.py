import json
from pathlib import Path
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QSplitter, QListWidget, QListWidgetItem, QTabWidget, QMessageBox,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QPixmap, QIcon, QColor
from gui.widgets import CardWidget

# Importamos la función de aproximación por si el JSON cargado aún no tenía el nombre guardado
try:
    from modulo2_procesamiento import aproximar_nombre_color
except ImportError:
    def aproximar_nombre_color(rgb):
        return ""


class PantallaResultados(QWidget):
    nueva_clasificacion = Signal()
    abrir_carpeta_resultados = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.report_data = {}
        self.output_dir = Path(".")
        self.current_category = ""
        self.current_det = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # -------------------------------------------------------------
        # 1. Barra superior de navegación / acciones
        # -------------------------------------------------------------
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
                color: #0f172a;
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

        # -------------------------------------------------------------
        # 2. Tarjetas de estadísticas superiores
        # -------------------------------------------------------------
        stats_layout = QHBoxLayout()
        self.card_total = CardWidget("Fotos Procesadas", "0", parent=self)
        self.card_cats = CardWidget("Categorías", "0", parent=self)
        self.card_time = CardWidget("Tiempo Total", "0 s", parent=self)
        stats_layout.addWidget(self.card_total)
        stats_layout.addWidget(self.card_cats)
        stats_layout.addWidget(self.card_time)
        main_layout.addLayout(stats_layout)

        # -------------------------------------------------------------
        # 3. Contenido Principal con Splitters
        # -------------------------------------------------------------
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

        # Derecha: Splitter vertical (Galería arriba, Insumos abajo)
        right_splitter = QSplitter(Qt.Vertical, self)

        # Galería de miniaturas (Corregido texto oscuro visible)
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
                color: #0f172a; /* <-- TEXTO VISIBLE DE MINIATURA */
                font-weight: 500;
                font-size: 11px;
                padding: 4px;
            }
            QListWidget::item:selected {
                border: 2px solid #3b82f6;
                color: #1d4ed8;
                background-color: #eff6ff;
            }
        """)
        self.gallery_list.itemClicked.connect(self.on_image_selected)
        gallery_layout.addWidget(self.gallery_list)
        right_splitter.addWidget(gallery_container)

        # Vista Detallada (Insumos + Detalles)
        detail_container = QFrame(self)
        detail_container.setStyleSheet("background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px;")
        detail_layout = QHBoxLayout(detail_container)
        detail_layout.setContentsMargins(12, 12, 12, 12)
        detail_layout.setSpacing(12)

        # Panel de Objetos/Contornos detectados en la imagen seleccionada
        self.objects_panel = QFrame(self)
        self.objects_panel.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px;")
        objects_panel_layout = QVBoxLayout(self.objects_panel)
        objects_panel_layout.setContentsMargins(10, 10, 10, 10)
        objects_panel_layout.setSpacing(6)

        self.lbl_objects_title = QLabel("Objetos / Contornos detectados", self)
        self.lbl_objects_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_objects_title.setStyleSheet("color: #0f172a; border: none;")
        objects_panel_layout.addWidget(self.lbl_objects_title)

        self.objects_list = QListWidget(self)
        self.objects_list.setStyleSheet("""
            QListWidget {
                background-color: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 6px;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f1f5f9;
                color: #334155;
                font-size: 11px;
            }
            QListWidget::item:selected {
                background-color: #eff6ff;
                color: #2563eb;
                font-weight: bold;
            }
        """)
        self.objects_list.itemClicked.connect(self.on_object_selected)
        objects_panel_layout.addWidget(self.objects_list)

        detail_layout.addWidget(self.objects_panel, 2)

        # Tabs de visualización (Corregidos colores de pestañas inactivas y activas)
        self.tabs_insumos = QTabWidget(self)
        self.tabs_insumos.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid #cbd5e1;
                border-radius: 6px;
                background-color: #ffffff;
            }
            QTabBar::tab {
                background-color: #f1f5f9;
                color: #334155;                 /* <-- TEXTO OSCURO PESTAÑAS NO SELECCIONADAS */
                padding: 6px 14px;
                margin-right: 4px;
                border: 1px solid #cbd5e1;
                border-bottom: none;
                border-top-left-radius: 4px;
                border-top-right-radius: 4px;
                font-weight: 600;
                font-size: 11px;
            }
            QTabBar::tab:selected {
                background-color: #64748b;     /* Pestaña seleccionada activa */
                color: #ffffff;                 /* Texto blanco contrastado */
                border-color: #64748b;
            }
            QTabBar::tab:hover:!selected {
                background-color: #e2e8f0;
                color: #0f172a;
            }
        """)

        self.tab_original = QLabel(self)
        self.tab_original.setAlignment(Qt.AlignCenter)
        self.tab_segmentada = QLabel(self)
        self.tab_segmentada.setAlignment(Qt.AlignCenter)
        self.tab_crudos = QLabel(self)
        self.tab_crudos.setAlignment(Qt.AlignCenter)
        self.tab_procesados = QLabel(self)
        self.tab_procesados.setAlignment(Qt.AlignCenter)
        self.tab_mascara = QLabel(self)
        self.tab_mascara.setAlignment(Qt.AlignCenter)
        self.tab_recorte = QLabel(self)
        self.tab_recorte.setAlignment(Qt.AlignCenter)

        for tab_lbl in [self.tab_original, self.tab_segmentada, self.tab_crudos, self.tab_procesados, self.tab_mascara, self.tab_recorte]:
            tab_lbl.setStyleSheet("color: #64748b; font-size: 12px; border: none;")

        self.tabs_insumos.addTab(self.tab_original, "Original")
        self.tabs_insumos.addTab(self.tab_segmentada, "Segmentada")
        self.tabs_insumos.addTab(self.tab_crudos, "Bordes Crudos")
        self.tabs_insumos.addTab(self.tab_procesados, "Bordes Procesados")
        self.tabs_insumos.addTab(self.tab_mascara, "Máscara")
        self.tabs_insumos.addTab(self.tab_recorte, "Recorte")

        detail_layout.addWidget(self.tabs_insumos, 5)

        # -------------------------------------------------------------
        # 4. Panel lateral derecho: Métricas + Leyenda
        # -------------------------------------------------------------
        self.info_panel = QFrame(self)
        self.info_panel.setStyleSheet("background-color: #f8fafc; border: 1px solid #cbd5e1; border-radius: 6px;")
        self.info_panel_layout = QVBoxLayout(self.info_panel)
        self.info_panel_layout.setContentsMargins(12, 12, 12, 12)
        self.info_panel_layout.setSpacing(6)

        self.lbl_det_title = QLabel("Detalles del Análisis", self)
        self.lbl_det_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_det_title.setStyleSheet("color: #0f172a; border: none;")
        self.info_panel_layout.addWidget(self.lbl_det_title)

        self.lbl_det_cat = QLabel("Categoría: -", self)
        self.lbl_det_objs = QLabel("Objetos detectados: -", self)
        self.lbl_det_obj_actual = QLabel("Objeto seleccionado: -", self)
        self.lbl_det_color = QLabel("Color dominante: -", self)
        self.lbl_det_density = QLabel("Densidad de bordes: -", self)
        self.lbl_det_contrast = QLabel("Contraste de textura: -", self)

        for lbl in [self.lbl_det_cat, self.lbl_det_objs, self.lbl_det_obj_actual, self.lbl_det_color, self.lbl_det_density, self.lbl_det_contrast]:
            lbl.setStyleSheet("color: #1e293b; font-size: 11px; border: none;")
            self.info_panel_layout.addWidget(lbl)

        # --- LEYENDA / CRITERIOS PDI ---
        self.lbl_ref_title = QLabel("Leyenda / Criterios PDI", self)
        self.lbl_ref_title.setFont(QFont("Segoe UI", 10, QFont.Bold))
        self.lbl_ref_title.setStyleSheet("color: #0f172a; margin-top: 6px; border: none;")
        self.info_panel_layout.addWidget(self.lbl_ref_title)

        self.table_ref = QTableWidget(self)
        self.table_ref.setColumnCount(3)
        self.table_ref.setRowCount(4)
        self.table_ref.setHorizontalHeaderLabels(["Métrica", "Rango", "Interpretación"])
        self.table_ref.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table_ref.verticalHeader().setVisible(False)
        self.table_ref.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table_ref.setSelectionMode(QTableWidget.NoSelection)
        self.table_ref.setStyleSheet("""
            QTableWidget {
                background-color: #ffffff;
                color: #0f172a;                 /* <-- TEXTO NEGRO VISIBLE DENTRO DE LA TABLA */
                font-size: 10px;
                border: 1px solid #cbd5e1;
                border-radius: 4px;
                gridline-color: #e2e8f0;
            }
            QTableWidget::item {
                color: #0f172a;                 /* <-- FORZADO POR CELDA */
                padding: 3px;
                background-color: #ffffff;
            }
            QHeaderView::section {
                background-color: #f1f5f9;
                color: #334155;                 /* <-- TEXTO VISIBLE DE CABECERA */
                font-weight: bold;
                font-size: 10px;
                border: 1px solid #cbd5e1;
                padding: 4px;
            }
        """)

        criterios = [
            ("Densidad", "> 0.08", "Alta (Complejo / Bordes)"),
            ("Densidad", "≤ 0.08", "Baja (Plano / Suave)"),
            ("Contraste", "> 150", "Rugosa / Transiciones"),
            ("Contraste", "≤ 150", "Homogénea / Suave"),
        ]

        for row, (met, rng, interp) in enumerate(criterios):
            it_m = QTableWidgetItem(met)
            it_r = QTableWidgetItem(rng)
            it_i = QTableWidgetItem(interp)
            
            for item in (it_m, it_r, it_i):
                item.setForeground(QColor("#0f172a"))
                item.setTextAlignment(Qt.AlignCenter)
                
            self.table_ref.setItem(row, 0, it_m)
            self.table_ref.setItem(row, 1, it_r)
            self.table_ref.setItem(row, 2, it_i)

        self.info_panel_layout.addWidget(self.table_ref)

        detail_layout.addWidget(self.info_panel, 3)
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

        self.card_total.set_value(str(self.report_data.get("total_imagenes_procesadas", 0)))
        self.card_cats.set_value(str(self.report_data.get("categorias_generadas", 0)))
        self.card_time.set_value(f"{self.report_data.get('tiempo_total_segundos', 0)} s")

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

        detalles = self.report_data.get("detalle", [])
        for det in detalles:
            if det.get("categoria") == cat:
                rel_path = det.get("rutas_generadas", {}).get("original", "")
                full_path = self.output_dir / rel_path

                if full_path.exists():
                    g_item = QListWidgetItem(det.get("nombre_original"))
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
        self.current_det = det
        rutas = det.get("rutas_generadas", {})

        self.update_tab_image(self.tab_original, self.output_dir / rutas.get("original", ""))
        self.update_tab_image(self.tab_segmentada, self.output_dir / rutas.get("segmentada_general", ""))

        self.lbl_det_cat.setText(f"Categoría: {det.get('categoria', '-')}")
        self.lbl_det_objs.setText(f"Objetos detectados: {det.get('num_objetos_detectados', 0)}")

        # Poblar la lista de objetos/contornos de ESTA imagen (antes solo se
        # mostraba el objeto en índice 0, ignorando el resto de detecciones).
        self.objects_list.clear()
        objs_proc = det.get("objetos_procesados", [])
        for i, p_obj in enumerate(objs_proc):
            clase = p_obj.get("clase", "objeto")
            o_item = QListWidgetItem(f"Objeto {i + 1} — {clase}")
            o_item.setData(Qt.UserRole, i)
            self.objects_list.addItem(o_item)

        if self.objects_list.count() > 0:
            self.objects_list.setCurrentRow(0)
            self.on_object_selected(self.objects_list.item(0))
        else:
            self.tab_crudos.clear()
            self.tab_procesados.clear()
            self.tab_mascara.clear()
            self.tab_recorte.clear()
            self.lbl_det_obj_actual.setText("Objeto seleccionado: -")
            self.lbl_det_color.setText("Color dominante: -")
            self.lbl_det_density.setText("Densidad de bordes: -")
            self.lbl_det_contrast.setText("Contraste de textura: -")

    def on_object_selected(self, item):
        """Actualiza pestañas de insumos y panel de detalles según el
        objeto/contorno seleccionado en self.objects_list (no siempre el 0)."""
        if not self.current_det:
            return

        idx = item.data(Qt.UserRole)
        rutas = self.current_det.get("rutas_generadas", {})
        objs = rutas.get("objetos", [])

        if 0 <= idx < len(objs):
            obj = objs[idx]
            self.update_tab_image(self.tab_crudos, self.output_dir / obj.get("bordes_crudos", ""))
            self.update_tab_image(self.tab_procesados, self.output_dir / obj.get("bordes_filtrados", ""))
            self.update_tab_image(self.tab_mascara, self.output_dir / obj.get("mascara", ""))
            self.update_tab_image(self.tab_recorte, self.output_dir / obj.get("objeto_segmentado", ""))
        else:
            self.tab_crudos.clear()
            self.tab_procesados.clear()
            self.tab_mascara.clear()
            self.tab_recorte.clear()

        objs_proc = self.current_det.get("objetos_procesados", [])
        if 0 <= idx < len(objs_proc):
            p_obj = objs_proc[idx]
            self.lbl_det_obj_actual.setText(f"Objeto seleccionado: {idx + 1} ({p_obj.get('clase', '-')})")

            rgb = p_obj.get("color_dominante_rgb")
            nombre_color = p_obj.get("nombre_color_dominante")

            # Si el JSON no tiene el nombre, lo aproximamos en tiempo real
            if not nombre_color and isinstance(rgb, (list, tuple)) and len(rgb) == 3:
                nombre_color = aproximar_nombre_color(tuple(rgb))

            if nombre_color:
                self.lbl_det_color.setText(f"Color dominante: {nombre_color} (RGB: {rgb})")
            else:
                self.lbl_det_color.setText(f"Color dominante RGB: {rgb}")

            self.lbl_det_density.setText(f"Densidad de bordes: {p_obj.get('densidad_bordes', '-')}")
            self.lbl_det_contrast.setText(f"Contraste de textura: {p_obj.get('contraste_textura', '-')}")
        else:
            self.lbl_det_obj_actual.setText("Objeto seleccionado: -")
            self.lbl_det_color.setText("Color dominante: -")
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
        report_file = self.output_dir / "reporte_final.json"
        pdf_file = self.output_dir / "reporte_final.pdf"

        if not report_file.exists():
            QMessageBox.warning(self, "Error", "El archivo de reporte no existe.")
            return

        try:
            # Asegurarse de que los datos del reporte estén cargados
            if not self.report_data:
                with open(report_file, "r", encoding="utf-8") as f:
                    self.report_data = json.load(f)

            # Generar el archivo PDF
            from modulo3_organizacion import _generar_reporte_pdf
            _generar_reporte_pdf(self.report_data, pdf_file)

            # Abrir el PDF si fue creado exitosamente
            if pdf_file.exists():
                os.startfile(str(pdf_file.resolve()))

            # Abrir el JSON original
            os.startfile(str(report_file.resolve()))

            QMessageBox.information(
                self,
                "Reporte Exportado",
                "El reporte se ha exportado correctamente a PDF y JSON.\n\n"
                f"Archivos guardados en:\n{self.output_dir.resolve()}"
            )
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error al exportar",
                f"No se pudo generar o abrir el reporte PDF:\n{str(e)}"
            )

    def on_open_folder_clicked(self):
        self.abrir_carpeta_resultados.emit()

    def on_new_clicked(self):
        self.nueva_clasificacion.emit()