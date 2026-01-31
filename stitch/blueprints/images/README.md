# Images Blueprint

Handles image uploads, gallery management, and image processing for cross-stitch pattern creation.

## URL Prefix

`/images`

## Routes

| Method | Path | Function | Description |
|--------|------|----------|-------------|
| GET, POST | `/images/` | `gallery` | Image gallery with upload functionality |
| POST | `/images/delete/<filename>` | `delete` | Delete an uploaded image |
| GET | `/images/thumbnail/<filename>` | `thumbnail` | Serve thumbnail image |
| POST | `/images/process-ajax` | `process_ajax` | AJAX endpoint for real-time image processing preview |
| GET, POST | `/images/prepare/<filename>` | `prepare` | Configure image processing parameters |
| GET | `/images/preview` | `preview_processed` | Preview processed image before creating project |
| GET, POST | `/images/match-colors` | `match_colors` | Match quantized colors to DMC thread palette |
| GET | `/images/create-from-processed/<filename>` | `create_from_processed` | Load saved processed image for project creation |
| GET, POST | `/images/create-project` | `create_project_from_image` | Create project from processed image |

## Route Details

### `GET /images/`
Displays the user's image gallery with all uploaded images and their processed versions.

### `POST /images/`
Handles new image uploads. Validates file presence and delegates to `ImageService.upload_image()`.

### `POST /images/delete/<filename>`
Deletes the specified image file and its associated thumbnails/processed versions.

### `GET /images/thumbnail/<filename>`
Serves thumbnail images for gallery display. Falls back to original if thumbnail doesn't exist.

### `POST /images/process-ajax`
Real-time image processing endpoint for live preview. Accepts JSON with:
- `filename`: Source image filename
- `width`: Target width (10-500)
- `height`: Target height (10-500)
- `colors`: Number of colors (2-100)

Returns base64-encoded images for original, processed, and edges.

### `GET /images/prepare/<filename>`
Shows the image processing configuration form with original dimensions.

### `POST /images/prepare/<filename>`
Processes the image with submitted parameters (width, height, colors), saves the result, and redirects to color matching.

### `GET /images/preview`
Shows a preview of the processed image stored in session before project creation.

### `GET /images/match-colors`
Displays color matching interface to map quantized colors to DMC thread colors.

### `POST /images/match-colors`
Processes color selections and creates final palette with DMC mappings.

### `GET /images/create-from-processed/<filename>`
Loads a previously saved processed image's metadata and prepares it for project creation.

### `GET /images/create-project`
Shows project creation form with processed image details.

### `POST /images/create-project`
Creates a new project with:
- Reference layer (original image, semi-transparent, read-only)
- Image layer (quantized/DMC-matched stitches)
- Edges layer (outline stitches, hidden by default)

## Session Keys

| Key | Usage |
|-----|-------|
| `user_id` | Read to identify current user for all operations |
| `processed_image` | Processed image metadata (filename, dimensions, palette) |
| `matched_colors` | Color matching results for form processing |

## Static Assets

None - this blueprint uses global static assets only.

## Services Used

| Service | Methods |
|---------|---------|
| `ImageService` | `upload_image`, `get_user_images`, `delete_image`, `get_processed_versions`, `get_image_dimensions`, `generate_preview`, `process_pattern_image`, `load_processed_metadata`, `get_thumbnail_path` |
| `ColorMatcher` | `match_palette_to_dmc`, `update_selection`, `create_dmc_mapped_palette` |
| `ProjectService` | `create_project_from_image` |
