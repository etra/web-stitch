"""Image processing service for preparing images for cross-stitch patterns"""
import cv2
import numpy as np
from pathlib import Path
from typing import Tuple, List, Dict, Optional
import base64


class ImageProcessor:
    """Process images for cross-stitch pattern creation using OpenCV"""

    @staticmethod
    def load_image(file_path: Path) -> np.ndarray:
        """
        Load image from file using OpenCV

        Args:
            file_path: Path to image file

        Returns:
            RGB numpy array (H, W, 3)
        """
        # Load image (OpenCV loads as BGR)
        img = cv2.imread(str(file_path), cv2.IMREAD_COLOR)

        if img is None:
            raise ValueError(f"Could not load image: {file_path}")

        # Convert BGR to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        return img_rgb

    @staticmethod
    def remove_alpha(image: np.ndarray) -> np.ndarray:
        """
        Remove alpha channel if present

        Args:
            image: numpy array (H, W, 3 or 4)

        Returns:
            RGB image (H, W, 3)
        """
        if image.shape[2] == 4:  # Has alpha channel
            # Create white background
            background = np.full((image.shape[0], image.shape[1], 3), 255, dtype=np.uint8)

            # Extract alpha channel
            alpha = image[:, :, 3] / 255.0

            # Blend with white background
            for c in range(3):
                background[:, :, c] = (
                    alpha * image[:, :, c] + (1 - alpha) * 255
                ).astype(np.uint8)

            return background

        return image

    @staticmethod
    def resize_to_grid(image: np.ndarray, grid_width: int, grid_height: int) -> np.ndarray:
        """
        Resize image to match grid dimensions (preserve aspect ratio)

        Args:
            image: RGB numpy array (H, W, 3)
            grid_width: Target width in cells/stitches
            grid_height: Target height in cells/stitches

        Returns:
            Resized and padded image matching grid dimensions
        """
        h, w = image.shape[:2]
        aspect = w / h

        # Calculate new dimensions maintaining aspect ratio
        if grid_width / grid_height > aspect:
            # Height-limited
            new_h = grid_height
            new_w = int(grid_height * aspect)
        else:
            # Width-limited
            new_w = grid_width
            new_h = int(grid_width / aspect)

        # Resize using area interpolation (best for downscaling)
        resized = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)

        # Pad to exact grid dimensions with white background
        if new_w < grid_width or new_h < grid_height:
            padded = np.full((grid_height, grid_width, 3), 255, dtype=np.uint8)
            y_offset = (grid_height - new_h) // 2
            x_offset = (grid_width - new_w) // 2
            padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
            return padded

        return resized

    @staticmethod
    def quantize_colors(image: np.ndarray, max_colors: int) -> Tuple[np.ndarray, List[Dict]]:
        """
        Quantize image to max_colors using OpenCV K-means (much faster than sklearn)

        Args:
            image: RGB numpy array (H, W, 3)
            max_colors: Number of colors to reduce to (2-256)

        Returns:
            Tuple of (quantized image, palette list of dicts)
        """
        # Reshape for k-means (pixels as rows)
        h, w = image.shape[:2]
        pixels = image.reshape(-1, 3).astype(np.float32)

        # K-means using OpenCV (much faster than sklearn)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 100, 0.2)
        _, labels, centers = cv2.kmeans(
            pixels,
            max_colors,
            None,
            criteria,
            attempts=3,
            flags=cv2.KMEANS_PP_CENTERS
        )

        # Convert centers to uint8
        centers = centers.astype(np.uint8)

        # Create quantized image
        quantized = centers[labels.flatten()].reshape(image.shape)

        # Build palette with color info
        palette = []
        for i, (r, g, b) in enumerate(centers):
            palette.append({
                'id': f'c{i}',
                'rgbHex': f'#{r:02x}{g:02x}{b:02x}',
                'rgb': (int(r), int(g), int(b)),
                'vendor': None,
                'code': None,
                'name': f'Color {i + 1}',
                'symbol': ImageProcessor._get_symbol(i),
                'sortIndex': i
            })

        return quantized, palette

    @staticmethod
    def _get_symbol(index: int) -> str:
        """Get symbol for palette color (A-Z, then a-z, then 0-9)"""
        if index < 26:
            return chr(65 + index)  # A-Z
        elif index < 52:
            return chr(97 + index - 26)  # a-z
        elif index < 62:
            return chr(48 + index - 52)  # 0-9
        else:
            return '•'  # Fallback

    @staticmethod
    def detect_edges(image: np.ndarray) -> np.ndarray:
        """
        Detect edges using Canny edge detection

        Args:
            image: RGB numpy array (H, W, 3)

        Returns:
            Binary edge image (H, W)
        """
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_RGB2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 1.4)

        # Canny edge detection
        edges = cv2.Canny(blurred, threshold1=50, threshold2=150)

        # Optional: Dilate edges slightly for visibility
        kernel = np.ones((2, 2), np.uint8)
        edges = cv2.dilate(edges, kernel, iterations=1)

        return edges

    @staticmethod
    def process_for_pattern(image_path: Path, target_width: int, target_height: int,
                           num_colors: int) -> Dict:
        """
        Complete processing pipeline for cross-stitch pattern

        Args:
            image_path: Path to source image file
            target_width: Target width in stitches
            target_height: Target height in stitches
            num_colors: Number of colors for palette

        Returns:
            Dict with processed image data, palette, and layers
        """
        # Step 1: Load image
        image = ImageProcessor.load_image(image_path)
        original_size = (image.shape[1], image.shape[0])  # (width, height)

        # Step 2: Remove alpha if present
        image_rgb = ImageProcessor.remove_alpha(image)

        # Step 3: Resize to grid dimensions
        resized = ImageProcessor.resize_to_grid(image_rgb, target_width, target_height)

        # Step 4: Quantize colors using K-means
        quantized, palette = ImageProcessor.quantize_colors(resized, num_colors)

        # Step 5: Detect edges
        edges = ImageProcessor.detect_edges(resized)

        # Calculate actual color usage
        pixels = quantized.reshape(-1, 3)
        unique_colors, counts = np.unique(pixels, axis=0, return_counts=True)

        used_palette = []
        for color, count in zip(unique_colors, counts):
            hex_color = f'#{color[0]:02x}{color[1]:02x}{color[2]:02x}'
            # Find in palette
            palette_entry = next((p for p in palette if p['rgbHex'] == hex_color), None)
            if palette_entry:
                used_palette.append({
                    **palette_entry,
                    'count': int(count)
                })

        # Sort by usage
        used_palette.sort(key=lambda x: x['count'], reverse=True)

        return {
            'width': target_width,
            'height': target_height,
            'quantized_image': quantized,
            'edges': edges,
            'palette': palette,
            'used_palette': used_palette,
            'original_size': original_size,
            'num_colors': len(used_palette)
        }

    @staticmethod
    def image_to_base64(image: np.ndarray) -> str:
        """
        Convert numpy image to base64 PNG data URI

        Args:
            image: RGB numpy array (H, W, 3)

        Returns:
            Base64 encoded image string with data URI prefix
        """
        # Convert RGB to BGR for OpenCV
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Encode as PNG
        _, buffer = cv2.imencode('.png', image_bgr)

        # Convert to base64
        img_str = base64.b64encode(buffer).decode()
        return f'data:image/png;base64,{img_str}'

    @staticmethod
    def save_processed_image(image: np.ndarray, output_path: Path) -> None:
        """
        Save processed image to file

        Args:
            image: RGB numpy array (H, W, 3)
            output_path: Path to save file
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Convert RGB to BGR for OpenCV
        image_bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Save as PNG
        cv2.imwrite(str(output_path), image_bgr)

    @staticmethod
    def image_to_layer_cells(image: np.ndarray, palette: List[Dict], width: int,
                            stitch_type: str = 'full') -> Dict[str, Dict]:
        """
        Convert quantized image to layer cells format

        Args:
            image: RGB numpy array (H, W, 3) - quantized image
            palette: Color palette with rgbHex or rgb values
            width: Grid width (for calculating cell keys)
            stitch_type: Default stitch type (default: 'full')

        Returns:
            Dict of cells in format {key: {paletteIndex, stitchType}}
        """
        cells = {}
        height, img_width = image.shape[:2]

        # Build palette RGB values for matching
        palette_colors = []
        for p in palette:
            if 'rgb' in p:
                palette_colors.append(p['rgb'])
            elif 'rgbHex' in p:
                # Convert hex to RGB tuple
                hex_color = p['rgbHex'].lstrip('#')
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                palette_colors.append(rgb)
            else:
                palette_colors.append((0, 0, 0))  # Fallback

        # Convert each pixel to a cell (skip background/white pixels)
        for y in range(height):
            for x in range(img_width):
                # Get pixel color
                pixel = image[y, x]
                pixel_rgb = (int(pixel[0]), int(pixel[1]), int(pixel[2]))

                # Skip white/background pixels (pixels close to white)
                # This allows the cloth to show through
                if pixel_rgb[0] > 250 and pixel_rgb[1] > 250 and pixel_rgb[2] > 250:
                    continue  # Don't create a stitch for background

                # Find closest palette color (exact match or nearest)
                min_distance = float('inf')
                palette_index = 0

                for i, pal_rgb in enumerate(palette_colors):
                    # Calculate simple Euclidean distance
                    distance = sum((a - b) ** 2 for a, b in zip(pixel_rgb, pal_rgb))
                    if distance < min_distance:
                        min_distance = distance
                        palette_index = i

                    # If exact match, stop searching
                    if distance == 0:
                        break

                # Calculate cell key: y * width + x
                key = str(y * width + x)
                cells[key] = {
                    'paletteIndex': palette_index,
                    'stitchType': stitch_type
                }

        return cells

    @staticmethod
    def image_to_reference_cells(image: np.ndarray, width: int) -> Dict[str, Dict]:
        """
        Convert image to reference layer cells with direct RGB colors

        Args:
            image: RGB numpy array (H, W, 3) - original image
            width: Grid width (for calculating cell keys)

        Returns:
            Dict of cells in format {key: {color: '#rrggbb'}}
        """
        cells = {}
        height, img_width = image.shape[:2]

        # Convert each pixel to a reference cell with direct color
        for y in range(height):
            for x in range(img_width):
                # Get pixel color
                pixel = image[y, x]
                hex_color = f'#{pixel[0]:02x}{pixel[1]:02x}{pixel[2]:02x}'

                # Calculate cell key: y * width + x
                key = str(y * width + x)
                cells[key] = {
                    'color': hex_color
                }

        return cells

    @staticmethod
    def edges_to_layer_cells(edges: np.ndarray, width: int, palette_index: int = 0,
                            stitch_type: str = 'full') -> Dict[str, Dict]:
        """
        Convert edge detection result to layer cells format

        Args:
            edges: Binary edge image (H, W) - non-zero values are edges
            width: Grid width (for calculating cell keys)
            palette_index: Palette index for edge color (default: 0)
            stitch_type: Stitch type for edges (default: 'full')

        Returns:
            Dict of cells in format {key: {paletteIndex, stitchType}}
        """
        cells = {}
        height, img_width = edges.shape[:2] if len(edges.shape) > 1 else (edges.shape[0], width)

        # Convert each edge pixel to a cell
        for y in range(height):
            for x in range(img_width):
                if edges[y, x] > 0:  # Edge pixel
                    # Calculate cell key: y * width + x
                    key = str(y * width + x)
                    cells[key] = {
                        'paletteIndex': palette_index,
                        'stitchType': stitch_type
                    }

        return cells

    @staticmethod
    def edges_with_image_colors(edges: np.ndarray, quantized_image: np.ndarray,
                                palette: List[Dict], width: int,
                                stitch_type: str = 'full') -> Dict[str, Dict]:
        """
        Convert edges to layer cells using colors from the underlying quantized image

        Args:
            edges: Binary edge image (H, W) - non-zero values are edges
            quantized_image: RGB numpy array (H, W, 3) - quantized image
            palette: Color palette with rgbHex or rgb values
            width: Grid width (for calculating cell keys)
            stitch_type: Stitch type for edges (default: 'full')

        Returns:
            Dict of cells in format {key: {paletteIndex, stitchType}}
        """
        cells = {}
        height = edges.shape[0]
        img_width = edges.shape[1] if len(edges.shape) > 1 else width

        # Build palette RGB values for matching
        palette_colors = []
        for p in palette:
            if 'rgb' in p:
                palette_colors.append(p['rgb'])
            elif 'rgbHex' in p:
                hex_color = p['rgbHex'].lstrip('#')
                rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                palette_colors.append(rgb)
            else:
                palette_colors.append((0, 0, 0))

        # Convert each edge pixel to a cell with the underlying image color
        for y in range(height):
            for x in range(img_width):
                if edges[y, x] > 0:  # Edge pixel
                    # Get the color from the quantized image at this position
                    pixel = quantized_image[y, x]
                    pixel_rgb = (int(pixel[0]), int(pixel[1]), int(pixel[2]))

                    # Find closest palette color
                    min_distance = float('inf')
                    palette_index = 0

                    for i, pal_rgb in enumerate(palette_colors):
                        distance = sum((a - b) ** 2 for a, b in zip(pixel_rgb, pal_rgb))
                        if distance < min_distance:
                            min_distance = distance
                            palette_index = i
                        if distance == 0:
                            break

                    # Calculate cell key: y * width + x
                    key = str(y * width + x)
                    cells[key] = {
                        'paletteIndex': palette_index,
                        'stitchType': stitch_type
                    }

        return cells
