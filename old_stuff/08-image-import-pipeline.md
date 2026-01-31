# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## Image Import & Multi-Layer Generation

### Overview

When a user uploads an image, the backend automatically generates **multiple layers** to help with pattern creation:

1. **Original Image Layer** (read-only) - Unmodified reference
2. **Processed Image Layer** (editable) - Color-quantized, grid-aligned
3. **Lines/Edges Layer** (editable) - Detected edges to make image "pop"
4. User can draw on all layers except the original

This multi-layer approach gives users flexibility to work from reference while creating patterns.

### Image Processing Pipeline

**`blueprints/images/services.py` orchestrates the pipeline:**

```python
from .processors import ImageQuantizer, EdgeDetector, LayerGenerator

class ImageImportService:
    @staticmethod
    def process_uploaded_image(user_id: str, project_id: str, image_file, max_colors: int = 50):
        """
        Process uploaded image and generate multiple layers

        Returns: Updated project with 3 new layers
        """
        # 1. Load and preprocess image
        img = cv2.imdecode(np.frombuffer(image_file.read(), np.uint8), cv2.IMREAD_COLOR)
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # 2. Get project dimensions
        project = ProjectService.get_project(project_id)
        target_width = project.width
        target_height = project.height

        # 3. Resize to match project grid (preserve aspect ratio)
        resized = ImageQuantizer.resize_to_grid(img_rgb, target_width, target_height)

        # 4. Generate layers
        layers = []

        # Layer 1: Original Image (read-only reference)
        original_layer = LayerGenerator.create_image_layer(
            name="Original Image (reference)",
            image=resized,
            opacity=0.5,
            editable=False  # Read-only
        )
        layers.append(original_layer)

        # Layer 2: Processed/Quantized Image (editable)
        quantized, palette = ImageQuantizer.quantize(resized, max_colors=max_colors)
        processed_layer = LayerGenerator.create_raster_layer_from_image(
            name="Processed Image",
            quantized_image=quantized,
            palette=palette,
            project_width=target_width,
            project_height=target_height
        )
        layers.append(processed_layer)

        # Layer 3: Lines/Edges (makes image pop)
        edges = EdgeDetector.detect_edges(resized)
        lines_layer = LayerGenerator.create_lines_layer(
            name="Lines (edges)",
            edges=edges,
            project_width=target_width,
            project_height=target_height
        )
        layers.append(lines_layer)

        # 5. Update project with new layers and palette
        ProjectService.add_layers(project_id, layers)
        ProjectService.update_palette(project_id, palette)

        return ProjectService.get_project(project_id)
```

### Image Processor Modules

**`processors/quantizer.py` - Color Quantization:**
```python
import cv2
import numpy as np
from sklearn.cluster import KMeans

class ImageQuantizer:
    @staticmethod
    def resize_to_grid(image, grid_width, grid_height):
        """Resize image to match grid dimensions"""
        # Preserve aspect ratio, fit within grid
        h, w = image.shape[:2]
        aspect = w / h

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

        # Pad to exact grid dimensions if needed
        if new_w < grid_width or new_h < grid_height:
            padded = np.full((grid_height, grid_width, 3), 255, dtype=np.uint8)
            y_offset = (grid_height - new_h) // 2
            x_offset = (grid_width - new_w) // 2
            padded[y_offset:y_offset+new_h, x_offset:x_offset+new_w] = resized
            return padded

        return resized

    @staticmethod
    def quantize(image, max_colors=50):
        """
        Quantize image to max_colors using k-means clustering

        Returns: (quantized_image, palette)
        """
        # Reshape for k-means (pixels as rows)
        pixels = image.reshape(-1, 3).astype(np.float32)

        # K-means clustering
        kmeans = KMeans(n_clusters=max_colors, random_state=42, n_init=10)
        labels = kmeans.fit_predict(pixels)
        centers = kmeans.cluster_centers_.astype(np.uint8)

        # Create quantized image
        quantized = centers[labels].reshape(image.shape)

        # Build palette
        palette = [
            {
                'id': str(uuid.uuid4()),
                'rgbHex': f'#{r:02x}{g:02x}{b:02x}',
                'symbol': get_next_symbol(i),  # A-Z, 0-9, then ANSI
                'sortIndex': i
            }
            for i, (r, g, b) in enumerate(centers)
        ]

        return quantized, palette
```

**`processors/edge_detector.py` - Edge Detection:**
```python
import cv2
import numpy as np

class EdgeDetector:
    @staticmethod
    def detect_edges(image, method='canny'):
        """
        Detect edges to create lines layer

        Uses Canny edge detection for clean lines
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

        return edges  # Binary image (0 or 255)
```

**`processors/layer_generator.py` - Layer Creation:**
```python
import uuid
import base64
import cv2

class LayerGenerator:
    @staticmethod
    def create_image_layer(name, image, opacity=0.5, editable=False):
        """Create image layer from numpy array"""
        # Encode image as base64 PNG
        _, buffer = cv2.imencode('.png', cv2.cvtColor(image, cv2.COLOR_RGB2BGR))
        image_data = f"data:image/png;base64,{base64.b64encode(buffer).decode()}"

        return {
            'id': str(uuid.uuid4()),
            'type': 'image',
            'name': name,
            'visible': True,
            'opacity': opacity,
            'imageData': image_data,
            'editable': editable
        }

    @staticmethod
    def create_raster_layer_from_image(name, quantized_image, palette, project_width, project_height):
        """Create raster layer from quantized image"""
        # Map RGB colors to palette indices
        h, w = quantized_image.shape[:2]
        cells = []

        for y in range(project_height):
            for x in range(project_width):
                if y < h and x < w:
                    pixel_rgb = quantized_image[y, x]
                    hex_color = f'#{pixel_rgb[0]:02x}{pixel_rgb[1]:02x}{pixel_rgb[2]:02x}'

                    # Find matching palette index
                    palette_idx = next(
                        (i for i, c in enumerate(palette) if c['rgbHex'] == hex_color),
                        None
                    )

                    if palette_idx is not None:
                        cells.append({
                            'paletteIndex': palette_idx,
                            'stitchType': 'full'  # Default to full stitch
                        })
                    else:
                        cells.append(None)  # Empty cell
                else:
                    cells.append(None)

        return {
            'id': str(uuid.uuid4()),
            'type': 'raster',
            'name': name,
            'visible': True,
            'cells': cells
        }

    @staticmethod
    def create_lines_layer(name, edges, project_width, project_height):
        """Create raster layer from edge detection (black lines on transparent)"""
        h, w = edges.shape
        cells = []

        # Find a black color in palette (or add it)
        black_idx = 0  # Assume first color is black (or background)

        for y in range(project_height):
            for x in range(project_width):
                if y < h and x < w and edges[y, x] > 128:  # Edge detected
                    cells.append({
                        'paletteIndex': black_idx,
                        'stitchType': 'full'
                    })
                else:
                    cells.append(None)  # Transparent

        return {
            'id': str(uuid.uuid4()),
            'type': 'raster',
            'name': name,
            'visible': False,  # Hidden by default, user can toggle
            'cells': cells
        }
```

### Symbol Rendering (OpenCV, not Pillow)

**Why OpenCV?** Pillow has poor support for rendering ANSI unicode symbols on images. OpenCV with custom fonts handles this better.

**`export/renderers/png_renderer.py`:**
```python
import cv2
import numpy as np

class PNGRenderer:
    @staticmethod
    def render_pattern_with_symbols(project, layers_to_export, mode='both'):
        """
        Render pattern to PNG with symbols using OpenCV

        mode: 'stitches' | 'symbols' | 'both'
        """
        # Create canvas
        cell_size = 20  # pixels per cell
        canvas_width = project.width * cell_size
        canvas_height = project.height * cell_size
        canvas = np.full((canvas_height, canvas_width, 3), 255, dtype=np.uint8)

        # Render each layer
        for layer in layers_to_export:
            if layer['type'] == 'raster':
                if mode in ['stitches', 'both']:
                    PNGRenderer._render_stitches(canvas, layer, project.palette, cell_size)
                if mode in ['symbols', 'both']:
                    PNGRenderer._render_symbols(canvas, layer, project.palette, cell_size)

        return canvas

    @staticmethod
    def _render_symbols(canvas, layer, palette, cell_size):
        """Render symbols using OpenCV (handles ANSI unicode)"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.5
        thickness = 1

        for i, cell in enumerate(layer['cells']):
            if cell is None:
                continue

            y = i // layer.width
            x = i % layer.width

            symbol = palette[cell['paletteIndex']]['symbol']
            color = palette[cell['paletteIndex']]['rgbHex']
            rgb = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))

            # Position text in center of cell
            text_x = x * cell_size + cell_size // 4
            text_y = y * cell_size + int(cell_size * 0.7)

            cv2.putText(
                canvas,
                symbol,
                (text_x, text_y),
                font,
                font_scale,
                rgb,
                thickness,
                cv2.LINE_AA
            )
```
