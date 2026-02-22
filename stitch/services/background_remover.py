"""Background removal service using U2Net via ONNX Runtime.

Downloads the U2Net model on first use (~44MB, cached in the instance
directory) and runs inference to produce a foreground mask.  The mask is
applied as an alpha channel so existing pipeline steps (remove_alpha →
white background → skip near-white pixels) work without changes.
"""
import logging
import urllib.request
from pathlib import Path

import cv2
import numpy as np

logger = logging.getLogger(__name__)

# U2Net model hosted by the rembg project (same model, just direct download)
_MODEL_URL = (
    'https://github.com/danielgatis/rembg/releases/download/v0.0.0/u2net.onnx'
)
_MODEL_FILENAME = 'u2net.onnx'


class BackgroundRemover:
    """Remove image backgrounds using the U2Net segmentation model."""

    _session = None  # lazily initialised ONNX inference session

    @classmethod
    def _get_model_path(cls) -> Path:
        """Return the cached model path, downloading if needed."""
        from flask import current_app

        cache_dir = Path(current_app.instance_path) / 'models'
        cache_dir.mkdir(parents=True, exist_ok=True)
        model_path = cache_dir / _MODEL_FILENAME

        if not model_path.exists():
            logger.info('Downloading U2Net model (~44 MB) …')
            urllib.request.urlretrieve(_MODEL_URL, str(model_path))
            logger.info('U2Net model saved to %s', model_path)

        return model_path

    @classmethod
    def _get_session(cls):
        """Lazy-load the ONNX Runtime inference session."""
        if cls._session is None:
            import onnxruntime as ort

            model_path = cls._get_model_path()
            cls._session = ort.InferenceSession(
                str(model_path),
                providers=['CPUExecutionProvider'],
            )
        return cls._session

    @classmethod
    def remove_background(cls, image: np.ndarray) -> np.ndarray:
        """Remove the background from an RGB image.

        Args:
            image: RGB uint8 array (H, W, 3).

        Returns:
            RGBA uint8 array (H, W, 4) with background made transparent.
        """
        orig_h, orig_w = image.shape[:2]
        input_size = 320  # U2Net expects 320×320

        # --- preprocess ------------------------------------------------
        img = cv2.resize(image, (input_size, input_size),
                         interpolation=cv2.INTER_LANCZOS4).astype(np.float32)
        img /= 255.0
        # ImageNet-style normalisation (same as rembg / U2Net training)
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img = (img - mean) / std
        # NCHW layout
        img = img.transpose(2, 0, 1)[np.newaxis, ...]

        # --- inference --------------------------------------------------
        session = cls._get_session()
        input_name = session.get_inputs()[0].name
        outputs = session.run(None, {input_name: img})

        # First output is the main prediction mask (320×320)
        mask = outputs[0][0, 0]  # (320, 320)

        # Normalise to 0-1
        mask_min, mask_max = mask.min(), mask.max()
        if mask_max - mask_min > 1e-6:
            mask = (mask - mask_min) / (mask_max - mask_min)
        else:
            mask = np.ones_like(mask)

        # --- resize mask to original dimensions -------------------------
        mask_uint8 = (mask * 255).astype(np.uint8)
        alpha = cv2.resize(mask_uint8, (orig_w, orig_h),
                           interpolation=cv2.INTER_LANCZOS4)

        # --- apply as alpha channel ------------------------------------
        rgba = np.dstack([image, alpha])
        return rgba

    @classmethod
    def is_available(cls) -> bool:
        """Check whether onnxruntime is installed."""
        try:
            import onnxruntime  # noqa: F401
            return True
        except ImportError:
            return False
