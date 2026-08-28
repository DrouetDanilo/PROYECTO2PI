"""
modulo2_procesamiento.py
------------------------
MÓDULO #2: PROCESAMIENTO Y ANÁLISIS VISUAL
"""

import colorsys
from dataclasses import dataclass, field
from typing import Optional

import cv2
import numpy as np
from sklearn.cluster import KMeans

import config


@dataclass
class InsumosVisuales:
    """Los 4 tipos de insumos visuales generados por el Módulo 2."""
    bordes_crudos: np.ndarray = field(repr=False)
    bordes_filtrados: np.ndarray = field(repr=False)
    mascara_binaria: np.ndarray = field(repr=False)
    objeto_segmentado: np.ndarray = field(repr=False)


@dataclass
class Metadatos:
    """Atributos extraídos de cada insumo (RF-05)."""
    color_dominante_rgb: tuple
    nombre_color_dominante: str  # <--- NUEVO: Nombre aproximado del color
    densidad_bordes: float
    energia_textura: float
    contraste_textura: float


def aproximar_nombre_color(rgb: tuple) -> str:
    """
    Aproxima la tupla (R, G, B) a un nombre de color clasificando en el
    espacio HSV en lugar de distancia euclidiana en RGB.

    Motivo del cambio: en RGB, colores desaturados o de brillo medio caían
    de forma sesgada hacia el ancla más cercana (típicamente "Gris"), y la
    paleta de anclas RGB estaba distribuida de forma desigual (mayoría
    saturadas al máximo). En HSV separamos primero brillo/saturación
    (Negro/Blanco/Gris/Marrón) y luego clasificamos el matiz (H) por
    bandas angulares, que es el criterio estándar y más robusto para
    "naming" de color en visión por computador.
    """
    r, g, b = (max(0, min(255, c)) for c in rgb)
    h, s, v = colorsys.rgb_to_hsv(r / 255.0, g / 255.0, b / 255.0)
    h_deg = h * 360.0

    # 1. Acromáticos: decididos por brillo (V) y saturación (S), no por matiz
    if v < 0.18:
        return "Negro"
    if s < 0.15:
        return "Blanco" if v > 0.85 else "Gris"

    # 2. Marrón: tonos naranja/rojizo con brillo medio-bajo (antes de evaluar bandas)
    if 10.0 <= h_deg < 45.0 and v < 0.65 and s > 0.35:
        return "Marron"

    # 3. Clasificación cromática por banda de matiz (grados, 0-360)
    bandas = [
        (0.0, 10.0, "Rojo"),
        (10.0, 45.0, "Naranja"),
        (45.0, 65.0, "Amarillo"),
        (65.0, 170.0, "Verde"),
        (170.0, 200.0, "Cian"),
        (200.0, 255.0, "Azul"),
        (255.0, 290.0, "Violeta"),
        (290.0, 320.0, "Magenta"),
        (320.0, 345.0, "Rosa"),
        (345.0, 360.0, "Rojo"),
    ]
    for inicio, fin, nombre in bandas:
        if inicio <= h_deg < fin:
            # Celeste: azul con saturación baja y brillo alto (cielo, jeans claros, etc.)
            if nombre == "Azul" and s < 0.4 and v > 0.6:
                return "Celeste"
            return nombre

    return "Gris"  # fallback teórico; no debería alcanzarse


def _color_dominante(imagen_bgr: np.ndarray, mascara: Optional[np.ndarray] = None,
                     k: int = config.KMEANS_N_CLUSTERS) -> tuple:
    """
    Calcula el color dominante vía KMeans.

    Si se provee `mascara` (binaria, mismo alto/ancho que imagen_bgr,
    255=objeto / 0=fondo), el clustering se restringe a los píxeles del
    objeto. Esto evita el sesgo de incluir fondo dentro del bounding box
    rectangular (frecuente en objetos no rectangulares), que antes podía
    hacer que el "color dominante del objeto" fuera en realidad el color
    del fondo.
    """
    if imagen_bgr.size == 0:
        return (0, 0, 0)

    if config.COLOR_SPACE_FOR_DOMINANT == "HSV":
        img = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2HSV)
    elif config.COLOR_SPACE_FOR_DOMINANT == "LAB":
        img = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2LAB)
    else:
        img = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)

    pixeles = img.reshape(-1, 3).astype(np.float32)

    if mascara is not None and mascara.size > 0 and mascara.shape[:2] == imagen_bgr.shape[:2]:
        mascara_flat = mascara.reshape(-1) > 0
        pixeles_objeto = pixeles[mascara_flat]
        # Si la máscara no dejó píxeles válidos (p.ej. vacía), se hace fallback
        # a la imagen completa en vez de fallar.
        if len(pixeles_objeto) > 0:
            pixeles = pixeles_objeto

    n_clusters = min(k, max(1, len(pixeles)))

    kmeans = KMeans(n_clusters=n_clusters, n_init=4, random_state=42)
    kmeans.fit(pixeles)

    _, conteos = np.unique(kmeans.labels_, return_counts=True)
    color_predominante = kmeans.cluster_centers_[np.argmax(conteos)]
    return tuple(int(c) for c in color_predominante)


def _textura_glcm(imagen_gris: np.ndarray) -> tuple:
    try:
        from skimage.feature import graycomatrix, graycoprops
    except ImportError:
        gx = cv2.Sobel(imagen_gris, cv2.CV_64F, 1, 0, ksize=3)
        gy = cv2.Sobel(imagen_gris, cv2.CV_64F, 0, 1, ksize=3)
        magnitud = np.sqrt(gx ** 2 + gy ** 2)
        return float(np.std(magnitud)), float(np.mean(magnitud))

    glcm = graycomatrix(
        imagen_gris, distances=[1], angles=[0], levels=256,
        symmetric=True, normed=True
    )
    energia = float(graycoprops(glcm, "energy")[0, 0])
    contraste = float(graycoprops(glcm, "contrast")[0, 0])
    return energia, contraste


def procesar_imagen(imagen_bgr: np.ndarray,
                    mascara_objeto: Optional[np.ndarray] = None) -> tuple:
    """
    Aplica el pipeline de PDI sobre la imagen o el recorte directo del objeto.
    """
    h, w = imagen_bgr.shape[:2]
    gris = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2GRAY)

    # 1) Bordes crudos
    bordes_crudos = cv2.Canny(gris, config.CANNY_THRESHOLD_1, config.CANNY_THRESHOLD_2)

    # 2) Bordes filtrados (Filtro Gaussiano para eliminar ruido - RNF-04)
    gris_suavizado = cv2.GaussianBlur(gris, config.GAUSSIAN_KERNEL, 0)
    bordes_filtrados = cv2.Canny(gris_suavizado, config.CANNY_THRESHOLD_1, config.CANNY_THRESHOLD_2)

    # 3) Mascara binaria
    if mascara_objeto is not None and mascara_objeto.size > 0:
        if mascara_objeto.shape[:2] != (h, w):
            mascara_binaria = cv2.resize(mascara_objeto, (w, h), interpolation=cv2.INTER_NEAREST)
        else:
            mascara_binaria = mascara_objeto.copy()
            
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        mascara_binaria = cv2.morphologyEx(mascara_binaria, cv2.MORPH_CLOSE, kernel)
    else:
        # Fallback con Otsu
        _, mascara_binaria = cv2.threshold(gris_suavizado, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

    # 4) Recorte / Segmento limpio
    objeto_segmentado = cv2.bitwise_and(imagen_bgr, imagen_bgr, mask=mascara_binaria)

    insumos = InsumosVisuales(
        bordes_crudos=bordes_crudos,
        bordes_filtrados=bordes_filtrados,
        mascara_binaria=mascara_binaria,
        objeto_segmentado=objeto_segmentado,
    )

    color_rgb = _color_dominante(imagen_bgr, mascara_binaria)
    nombre_color = aproximar_nombre_color(color_rgb) # <--- Llamada a la aproximación
    densidad_bordes = float(np.count_nonzero(bordes_filtrados)) / (h * w) if (h * w) > 0 else 0.0
    energia, contraste = _textura_glcm(gris)

    metadatos = Metadatos(
        color_dominante_rgb=color_rgb,
        nombre_color_dominante=nombre_color, # <--- Se asigna el nombre
        densidad_bordes=round(densidad_bordes, 4),
        energia_textura=round(energia, 4),
        contraste_textura=round(contraste, 4),
    )

    return insumos, metadatos