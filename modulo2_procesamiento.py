"""
modulo2_procesamiento.py
------------------------
MÓDULO #2: PROCESAMIENTO Y ANÁLISIS VISUAL (CORREGIDO)
"""

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
    densidad_bordes: float
    energia_textura: float
    contraste_textura: float


def _color_dominante(imagen_bgr: np.ndarray, k: int = config.KMEANS_N_CLUSTERS) -> tuple:
    if imagen_bgr.size == 0:
        return (0, 0, 0)

    if config.COLOR_SPACE_FOR_DOMINANT == "HSV":
        img = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2HSV)
    elif config.COLOR_SPACE_FOR_DOMINANT == "LAB":
        img = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2LAB)
    else:
        img = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)

    pixeles = img.reshape(-1, 3).astype(np.float32)
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

    # 3) Máscara binaria (Para el requerimiento de insumos de PDI)
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

    # 4) RECORTE / SEGMENTO LIMPIO (Estilo Tortuga: Mantiene la imagen BGR pura sin alteración)
    objeto_segmentado = imagen_bgr.copy()

    insumos = InsumosVisuales(
        bordes_crudos=bordes_crudos,
        bordes_filtrados=bordes_filtrados,
        mascara_binaria=mascara_binaria,
        objeto_segmentado=objeto_segmentado,
    )

    color_rgb = _color_dominante(imagen_bgr)
    densidad_bordes = float(np.count_nonzero(bordes_filtrados)) / (h * w) if (h * w) > 0 else 0.0
    energia, contraste = _textura_glcm(gris)

    metadatos = Metadatos(
        color_dominante_rgb=color_rgb,
        densidad_bordes=round(densidad_bordes, 4),
        energia_textura=round(energia, 4),
        contraste_textura=round(contraste, 4),
    )

    return insumos, metadatos