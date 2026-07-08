"""
modulo2_procesamiento.py
------------------------
MÓDULO #2: PROCESAMIENTO Y ANÁLISIS VISUAL

Entrada:  Imágenes originales completas + recortes de objetos del Módulo 1.
Proceso:  - Manipulación de canales de color (RGB/HSV/LAB) para color dominante
          - Evaluación de gradientes/GLCM para textura
          - Operadores matriciales para bordes y binarización
Salida:   4 insumos visuales: bordes crudos, bordes filtrados (sin ruido),
          máscaras binarias y objetos segmentados.

RF-03, RF-04, RF-05, RNF-04.
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
    """
    Determina el color dominante de una imagen aplicando K-Means sobre los
    píxeles en el espacio de color configurado (RF-05).
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
    n_clusters = min(k, max(1, len(pixeles)))

    kmeans = KMeans(n_clusters=n_clusters, n_init=4, random_state=42)
    kmeans.fit(pixeles)

    _, conteos = np.unique(kmeans.labels_, return_counts=True)
    color_predominante = kmeans.cluster_centers_[np.argmax(conteos)]
    return tuple(int(c) for c in color_predominante)


def _textura_glcm(imagen_gris: np.ndarray) -> tuple:
    """
    Calcula descriptores de textura (energía y contraste) mediante la matriz
    de co-ocurrencia de niveles de gris (GLCM).
    """
    try:
        from skimage.feature import graycomatrix, graycoprops
    except ImportError:
        # Fallback simple basado en gradientes si scikit-image no está disponible
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
    Aplica el pipeline completo de PDI sobre una imagen (o recorte de objeto):

      1. Bordes crudos:   Canny directo sobre la imagen en escala de grises.
      2. Bordes filtrados: Filtro Gaussiano (remueve ruido, RNF-04) + Canny.
      3. Máscara binaria:  Umbralización (Otsu) o máscara de segmentación
                            provista externamente (p. ej. por YOLO/SAM).
      4. Objeto segmentado: Aplicación de la máscara sobre fondo neutro.

    Retorna (InsumosVisuales, Metadatos).
    """
    gris = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2GRAY)

    # 1) Bordes crudos
    bordes_crudos = cv2.Canny(gris, config.CANNY_THRESHOLD_1, config.CANNY_THRESHOLD_2)

    # 2) Bordes filtrados (Gaussiano -> Canny)
    gris_suavizado = cv2.GaussianBlur(gris, config.GAUSSIAN_KERNEL, 0)
    bordes_filtrados = cv2.Canny(gris_suavizado, config.CANNY_THRESHOLD_1, config.CANNY_THRESHOLD_2)

    # 3) Máscara binaria
    if mascara_objeto is not None:
        mascara_binaria = mascara_objeto
        fondo_neutro = np.full_like(imagen_bgr, 128)
        mascara_3c = cv2.cvtColor(mascara_binaria, cv2.COLOR_GRAY2BGR) / 255.0
        objeto_segmentado = (imagen_bgr * mascara_3c + fondo_neutro * (1 - mascara_3c)).astype(np.uint8)
    else:
        # Opción 1: El objeto segmentado es exactamente el recorte intacto
        mascara_binaria = np.full(imagen_bgr.shape[:2], 255, dtype=np.uint8)
        objeto_segmentado = imagen_bgr.copy()

    insumos = InsumosVisuales(
        bordes_crudos=bordes_crudos,
        bordes_filtrados=bordes_filtrados,
        mascara_binaria=mascara_binaria,
        objeto_segmentado=objeto_segmentado,
    )

    color_rgb = _color_dominante(imagen_bgr)
    densidad_bordes = float(np.count_nonzero(bordes_filtrados)) / bordes_filtrados.size
    energia, contraste = _textura_glcm(gris)

    metadatos = Metadatos(
        color_dominante_rgb=color_rgb,
        densidad_bordes=round(densidad_bordes, 4),
        energia_textura=round(energia, 4),
        contraste_textura=round(contraste, 4),
    )

    return insumos, metadatos