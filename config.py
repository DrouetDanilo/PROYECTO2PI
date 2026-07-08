"""
config.py
---------
Configuración global del Clasificador y Organizador Automático de Fotografías.

Centraliza rutas, parámetros de los algoritmos y el mapeo de clases YOLO/COCO
hacia las categorías de escena que el sistema es capaz de generar:
Paisajes, Personas, Animales, Comidas y Eventos.
"""

from pathlib import Path

# ---------------------------------------------------------------------------
# Rutas por defecto (pueden ser sobreescritas por línea de comandos, ver main.py)
# ---------------------------------------------------------------------------
DEFAULT_INPUT_DIR = "./entrada"
DEFAULT_OUTPUT_DIR = "./Datasets/Resultados_DIP"

# Subcarpetas que se crean dentro de la carpeta de salida (RF-06)
SUBFOLDERS = {
    "originales": "originales",
    "bordes_crudos": "bordes_crudos",
    "bordes_procesados": "bordes_procesados",
    "mascaras": "mascaras",
    "recortes": "recortes",
}

# Extensiones de imagen soportadas (Entrada General)
VALID_EXTENSIONS = {".jpg", ".jpeg", ".png"}

# ---------------------------------------------------------------------------
# Parámetros del Módulo 1: Detección (YOLO - Ultralytics)
# ---------------------------------------------------------------------------
YOLO_MODEL_NAME = "yolov8m-seg.pt"   # modelo de segmentación medio (COCO, más inteligente)
YOLO_CONF_THRESHOLD = 0.35

# ---------------------------------------------------------------------------
# Parámetros del Módulo 2: Procesamiento y Análisis Visual (OpenCV)
# ---------------------------------------------------------------------------
GAUSSIAN_KERNEL = (5, 5)          # RNF-04: remoción de ruido de alta frecuencia
CANNY_THRESHOLD_1 = 50
CANNY_THRESHOLD_2 = 150
KMEANS_N_CLUSTERS = 3             # color dominante (RF-05)
COLOR_SPACE_FOR_DOMINANT = "RGB"  # RGB, HSV o LAB

# ---------------------------------------------------------------------------
# Mapeo de clases COCO (detectadas por YOLO) -> Categorías de escena (Módulo 3)
# ---------------------------------------------------------------------------
# Clases COCO relevantes agrupadas semánticamente. Si una imagen no contiene
# ninguna de estas clases se clasifica como "Paisajes" (ausencia de objetos
# de primer plano). Si contiene varias clases de distintos grupos a la vez,
# se prioriza según SCENE_PRIORITY (de mayor a menor especificidad).

SCENE_CATEGORY_MAP = {
    "Personas": {"person"},
    "Animales": {
        "bird", "cat", "dog", "horse", "sheep", "cow", "elephant",
        "bear", "zebra", "giraffe"
    },
    "Comidas": {
        "banana", "apple", "sandwich", "orange", "broccoli", "carrot",
        "hot dog", "pizza", "donut", "cake", "bowl", "dining table"
    },
    "Eventos": {
        "wine glass", "cup", "fork", "knife", "spoon", "cake",
        "sports ball", "frisbee", "kite", "surfboard", "tie", "balloon"
    },
}

# Orden de prioridad cuando una imagen matchea más de una categoría
SCENE_PRIORITY = ["Personas", "Animales", "Comidas", "Eventos"]

# Categoría por defecto cuando no se detecta ningún objeto de interés
DEFAULT_SCENE_CATEGORY = "Paisajes"

ALL_CATEGORIES = ["Paisajes", "Personas", "Animales", "Comidas", "Eventos"]

# ---------------------------------------------------------------------------
# Reporte final (RF-07)
# ---------------------------------------------------------------------------
REPORT_FORMATS = ("txt", "json", "pdf")
DEFAULT_REPORT_FORMAT = "json"
REPORT_FILENAME_BASE = "reporte_final"


def ensure_dir(path: str) -> Path:
    """Crea (si no existe) y retorna un Path absoluto."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p