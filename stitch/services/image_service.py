"""Image service for upload, storage, and retrieval"""
from pathlib import Path
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app
import uuid


class ImageService:
    """Service for managing image uploads and storage"""

    # Allowed file extensions
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif'}

    # Thumbnail size
    THUMBNAIL_SIZE = (150, 150)

    @staticmethod
    def get_upload_dir(user_id):
        """Get base upload directory for user"""
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'uploads')
        return Path(upload_folder) / str(user_id)

    @staticmethod
    def allowed_file(filename):
        """Check if file extension is allowed"""
        ext = Path(filename).suffix.lower()
        return ext in ImageService.ALLOWED_EXTENSIONS

    @staticmethod
    def upload_image(user_id, file):
        """
        Upload image - save original + generate thumbnail

        Args:
            user_id: User's ID
            file: Werkzeug FileStorage object

        Returns:
            str: Generated filename

        Raises:
            ValueError: If file type not allowed
        """
        if not ImageService.allowed_file(file.filename):
            raise ValueError('File type not allowed. Use JPG, PNG, or GIF.')

        # Create directories
        originals_dir = ImageService.get_upload_dir(user_id) / 'originals'
        thumbnails_dir = ImageService.get_upload_dir(user_id) / 'thumbnails'
        originals_dir.mkdir(parents=True, exist_ok=True)
        thumbnails_dir.mkdir(parents=True, exist_ok=True)

        # Generate unique filename
        ext = Path(secure_filename(file.filename)).suffix
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"img_{timestamp}_{uuid.uuid4().hex[:8]}{ext}"

        # Save original
        original_path = originals_dir / filename
        file.save(str(original_path))

        # Generate thumbnail
        thumb_path = thumbnails_dir / f"{Path(filename).stem}_thumb.jpg"
        try:
            img = Image.open(original_path)
            # Convert RGBA to RGB if needed (for PNG with transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            img.thumbnail(ImageService.THUMBNAIL_SIZE)
            img.save(str(thumb_path), "JPEG", quality=85)
        except Exception as e:
            # If thumbnail generation fails, delete original and raise
            original_path.unlink(missing_ok=True)
            raise ValueError(f'Failed to process image: {str(e)}')

        return filename

    @staticmethod
    def get_user_images(user_id):
        """
        Get all original images for user, sorted by creation time

        Args:
            user_id: User's ID

        Returns:
            list: List of image metadata dicts
        """
        originals_dir = ImageService.get_upload_dir(user_id) / 'originals'

        if not originals_dir.exists():
            return []

        images = []
        for img_path in originals_dir.glob("*"):
            if img_path.suffix.lower() in ImageService.ALLOWED_EXTENSIONS:
                stat = img_path.stat()
                images.append({
                    'filename': img_path.name,
                    'path': str(img_path),
                    'thumbnail': f"resource/{user_id}/thumbnails/{img_path.stem}_thumb.jpg",
                    'size': stat.st_size,
                    'size_mb': round(stat.st_size / (1024 * 1024), 2),
                    'uploaded_at': stat.st_ctime,
                    'uploaded_at_formatted': datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M'),
                    'url': f"resource/{user_id}/originals/{img_path.name}"
                })

        # Sort by creation time (newest first)
        images.sort(key=lambda x: x['uploaded_at'], reverse=True)
        return images

    @staticmethod
    def delete_image(user_id, filename):
        """
        Delete an image and its thumbnail

        Args:
            user_id: User's ID
            filename: Image filename

        Returns:
            bool: True if deleted successfully
        """
        # Security: ensure filename doesn't contain path traversal
        filename = Path(filename).name

        original_path = ImageService.get_upload_dir(user_id) / 'originals' / filename
        thumb_path = ImageService.get_upload_dir(user_id) / 'thumbnails' / f"{Path(filename).stem}_thumb.jpg"

        deleted = False
        if original_path.exists():
            original_path.unlink()
            deleted = True

        if thumb_path.exists():
            thumb_path.unlink()

        return deleted

    @staticmethod
    def process_pattern_image(user_id, source_filename: str, width: int, height: int, num_colors: int) -> dict:
        """
        Process an image for pattern creation (resize, quantize, save).

        Args:
            user_id: User's ID
            source_filename: Original image filename
            width: Target width in stitches
            height: Target height in stitches
            num_colors: Number of colors for quantization

        Returns:
            dict with keys:
                - processed_filename: Name of saved processed image
                - metadata: Processing metadata dict
                - used_palette: List of colors from quantization

        Side effects:
            - Saves processed image to user's processed/ directory
            - Saves metadata JSON file

        Raises:
            FileNotFoundError: If source image doesn't exist
            ValueError: If processing fails
        """
        import json
        import time
        import cv2
        from stitch.services.image_processor import ImageProcessor

        upload_dir = ImageService.get_upload_dir(user_id)
        source_path = upload_dir / 'originals' / source_filename

        if not source_path.exists():
            raise FileNotFoundError(f'Source image not found: {source_filename}')

        # Process image
        processor = ImageProcessor()
        result = processor.process_for_pattern(
            str(source_path),
            target_width=width,
            target_height=height,
            num_colors=num_colors
        )

        # Save processed image
        timestamp = int(time.time())
        processed_filename = f"processed_{width}x{height}_{num_colors}c_{timestamp}_{source_filename}"
        processed_dir = upload_dir / 'processed'
        processed_dir.mkdir(parents=True, exist_ok=True)
        processed_path = processed_dir / processed_filename

        cv2.imwrite(str(processed_path), cv2.cvtColor(result['quantized_image'], cv2.COLOR_RGB2BGR))

        # Save metadata
        metadata = {
            'original_filename': source_filename,
            'width': width,
            'height': height,
            'num_colors': num_colors,
            'palette': result['used_palette'],
            'processing_params': {
                'width': width,
                'height': height,
                'colors': num_colors
            },
            'created_at': timestamp
        }

        metadata_path = processed_dir / f"{processed_filename}.json"
        with open(metadata_path, 'w') as f:
            json.dump(metadata, f, indent=2)

        return {
            'processed_filename': processed_filename,
            'metadata': metadata,
            'used_palette': result['used_palette']
        }

    @staticmethod
    def get_processed_versions(user_id, original_filename):
        """
        Get all processed versions of an original image

        Args:
            user_id: User's ID
            original_filename: Original image filename

        Returns:
            list: List of processed version metadata dicts
        """
        import json
        processed_dir = ImageService.get_upload_dir(user_id) / 'processed'

        if not processed_dir.exists():
            return []

        processed_versions = []

        # Find all processed images and their metadata
        for img_path in processed_dir.glob("*.png"):
            metadata_path = processed_dir / f"{img_path.name}.json"

            # Load metadata if exists
            if metadata_path.exists():
                try:
                    with open(metadata_path, 'r') as f:
                        metadata = json.load(f)

                    # Only include if it matches the original filename
                    if metadata.get('original_filename') == original_filename:
                        stat = img_path.stat()
                        processed_versions.append({
                            'filename': img_path.name,
                            'original_filename': metadata.get('original_filename'),
                            'width': metadata.get('width'),
                            'height': metadata.get('height'),
                            'num_colors': metadata.get('num_colors'),
                            'processing_params': metadata.get('processing_params', {}),
                            'created_at': metadata.get('created_at'),
                            'created_at_formatted': datetime.fromtimestamp(
                                metadata.get('created_at', stat.st_ctime)
                            ).strftime('%Y-%m-%d %H:%M'),
                            'size_mb': round(stat.st_size / (1024 * 1024), 2),
                            'url': f"resource/{user_id}/processed/{img_path.name}"
                        })
                except Exception:
                    # Skip if metadata is corrupt
                    continue

        # Sort by creation time (newest first)
        processed_versions.sort(key=lambda x: x.get('created_at', 0), reverse=True)
        return processed_versions

    @staticmethod
    def get_image_dimensions(user_id, filename: str) -> dict:
        """
        Get dimensions of an original image.

        Args:
            user_id: User's ID
            filename: Image filename

        Returns:
            dict with width, height

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If image can't be loaded
        """
        import cv2

        image_path = ImageService.get_upload_dir(user_id) / 'originals' / filename

        if not image_path.exists():
            raise FileNotFoundError(f'Image not found: {filename}')

        img = cv2.imread(str(image_path))
        if img is None:
            raise ValueError(f'Could not load image: {filename}')

        height, width = img.shape[:2]
        return {'width': width, 'height': height}

    @staticmethod
    def generate_preview(user_id, filename: str, width: int, height: int, num_colors: int) -> dict:
        """
        Generate preview data for image processing (AJAX endpoint).

        Args:
            user_id: User's ID
            filename: Original image filename
            width: Target width in stitches
            height: Target height in stitches
            num_colors: Number of colors for quantization

        Returns:
            dict with preview images (base64) and metadata

        Raises:
            FileNotFoundError: If image doesn't exist
            ValueError: If processing fails
        """
        import numpy as np
        from stitch.services.image_processor import ImageProcessor

        image_path = ImageService.get_upload_dir(user_id) / 'originals' / filename

        if not image_path.exists():
            raise FileNotFoundError(f'Image not found: {filename}')

        # Process image
        result = ImageProcessor.process_for_pattern(
            image_path,
            width,
            height,
            num_colors
        )

        # Load original for comparison
        original_img = ImageProcessor.load_image(image_path)
        original_resized = ImageProcessor.resize_to_grid(original_img, width, height)

        # Create edges visualization
        edges_rgb = np.zeros_like(result['quantized_image'])
        edges_rgb[result['edges'] > 0] = [0, 0, 0]
        edges_rgb[result['edges'] == 0] = [255, 255, 255]

        return {
            'width': result['width'],
            'height': result['height'],
            'num_colors': result['num_colors'],
            'original': ImageProcessor.image_to_base64(original_resized),
            'processed': ImageProcessor.image_to_base64(result['quantized_image']),
            'edges': ImageProcessor.image_to_base64(edges_rgb),
            'palette': result['used_palette'][:20]  # First 20 colors for preview
        }

    @staticmethod
    def load_processed_metadata(user_id, filename: str) -> dict:
        """
        Load metadata for a previously processed image.

        Args:
            user_id: User's ID
            filename: Processed image filename

        Returns:
            dict with processed image metadata

        Raises:
            FileNotFoundError: If metadata doesn't exist
        """
        import json

        processed_dir = ImageService.get_upload_dir(user_id) / 'processed'
        metadata_path = processed_dir / f"{filename}.json"

        if not metadata_path.exists():
            raise FileNotFoundError(f'Processed image metadata not found: {filename}')

        with open(metadata_path, 'r') as f:
            metadata = json.load(f)

        return {
            'filename': filename,
            'original_filename': metadata.get('original_filename'),
            'width': metadata.get('width'),
            'height': metadata.get('height'),
            'palette': metadata.get('palette'),
            'num_colors': metadata.get('num_colors'),
            'processing_params': metadata.get('processing_params')
        }

    @staticmethod
    def get_thumbnail_path(user_id, filename: str) -> Path:
        """
        Get path to thumbnail for an image.

        Args:
            user_id: User's ID
            filename: Original image filename

        Returns:
            Path to thumbnail file, or None if not found
        """
        upload_dir = ImageService.get_upload_dir(user_id)
        thumb_filename = f"{Path(filename).stem}_thumb.jpg"
        thumb_path = upload_dir / 'thumbnails' / thumb_filename

        if thumb_path.exists():
            return thumb_path

        # Fallback to original
        original_path = upload_dir / 'originals' / filename
        if original_path.exists():
            return original_path

        return None
