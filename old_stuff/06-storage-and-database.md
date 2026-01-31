# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## File Storage Structure

**No database for images - filesystem only:**

```
uploads/
├── <user_id_1>/
│   ├── originals/           # Original uploaded images
│   │   ├── img_20250101_120000.jpg
│   │   ├── img_20250101_130000.png
│   │   └── ...
│   ├── thumbnails/          # Auto-generated thumbnails (150x150)
│   │   ├── img_20250101_120000_thumb.jpg
│   │   └── ...
│   └── cache/               # Cached processed images (regenerated on-demand)
│       ├── <prepared_id>_quantized.png
│       ├── <prepared_id>_edges.png
│       └── ...
│
├── <user_id_2>/
│   └── ...
```

### Image Identification Scheme

**Original Images (no database):**
- Identified by: **filename** (generated on upload)
- Example: `img_20250101_120000_abc123.jpg`
- Stored in: `/uploads/<user_id>/originals/<filename>`
- Routes use filename: `/images/prepare/<filename>`

**Prepared Images (database record):**
- Identified by: **UUID** (database primary key)
- Database stores: config JSONB + reference to original filename
- Routes use UUID: `/projects/import/<prepared_image_id>`

### How Image Gallery Works (No Database)

**Listing images for `/images` route:**
```python
import os
from pathlib import Path

def get_user_images(user_id):
    """Get all original images for user, sorted by creation time"""
    originals_dir = Path(f"uploads/{user_id}/originals")

    if not originals_dir.exists():
        return []

    images = []
    for img_path in originals_dir.glob("*"):
        if img_path.suffix.lower() in ['.jpg', '.jpeg', '.png', '.gif']:
            stat = img_path.stat()
            images.append({
                'filename': img_path.name,
                'path': str(img_path),
                'thumbnail': f"uploads/{user_id}/thumbnails/{img_path.stem}_thumb.jpg",
                'size': stat.st_size,
                'uploaded_at': stat.st_ctime,  # Creation time
                'url': f"/uploads/{user_id}/originals/{img_path.name}"
            })

    # Sort by creation time (newest first)
    images.sort(key=lambda x: x['uploaded_at'], reverse=True)
    return images
```

**Upload handling:**
```python
from werkzeug.utils import secure_filename
import uuid
from PIL import Image

def upload_image(user_id, file):
    """Upload image - save original + generate thumbnail"""
    # Create directories
    originals_dir = Path(f"uploads/{user_id}/originals")
    thumbnails_dir = Path(f"uploads/{user_id}/thumbnails")
    originals_dir.mkdir(parents=True, exist_ok=True)
    thumbnails_dir.mkdir(parents=True, exist_ok=True)

    # Generate unique filename
    ext = Path(secure_filename(file.filename)).suffix
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"img_{timestamp}_{uuid.uuid4().hex[:8]}{ext}"

    # Save original
    original_path = originals_dir / filename
    file.save(original_path)

    # Generate thumbnail
    thumb_path = thumbnails_dir / f"{Path(filename).stem}_thumb.jpg"
    img = Image.open(original_path)
    img.thumbnail((150, 150))
    img.save(thumb_path, "JPEG")

    return filename
```

### Prepared Image Regeneration

**Prepared images are NOT stored - regenerated on-demand:**

```python
def get_prepared_image_layers(prepared_image_id):
    """
    Regenerate processed image from config + original
    Uses caching to avoid reprocessing
    """
    # 1. Load config from database
    prep = db.session.query(PreparedImage).get(prepared_image_id)
    config = prep.config  # JSONB field
    user_id = prep.user_id
    original_filename = prep.original_filename

    # 2. Check cache
    cache_dir = Path(f"uploads/{user_id}/cache")
    cache_quantized = cache_dir / f"{prepared_image_id}_quantized.png"
    cache_edges = cache_dir / f"{prepared_image_id}_edges.png"

    if cache_quantized.exists() and cache_edges.exists():
        # Return cached versions
        return {
            'quantized': str(cache_quantized),
            'edges': str(cache_edges)
        }

    # 3. Load original image
    original_path = Path(f"uploads/{user_id}/originals/{original_filename}")
    img = cv2.imread(str(original_path))

    # 4. Apply processing from config
    resized = ImageQuantizer.resize_to_grid(
        img,
        config['width'],
        config['height']
    )

    quantized, palette = ImageQuantizer.quantize(
        resized,
        max_colors=config['maxColors']
    )

    edges = EdgeDetector.detect_edges(
        resized,
        threshold=config.get('edgeThreshold', 100)
    )

    # 5. Cache results
    cache_dir.mkdir(parents=True, exist_ok=True)
    cv2.imwrite(str(cache_quantized), quantized)
    cv2.imwrite(str(cache_edges), edges)

    return {
        'quantized': str(cache_quantized),
        'edges': str(cache_edges),
        'palette': palette
    }
```

**Benefits of this approach:**
- ✅ No large processed images in database
- ✅ Can change processing algorithm and regenerate all images
- ✅ Configuration is tiny (just JSON)
- ✅ Cached for performance, regenerated if cache missing
- ✅ Original images preserved

---

## Database Schema

### Database Design Philosophy

**⚠️ IMPORTANT: No Foreign Key Constraints**

This application **does not use database-level foreign key constraints**. Instead, referential integrity is managed at the application level using SQLAlchemy relationships.

**Why no foreign keys:**
- **Portability**: Not all database systems support foreign keys equally (especially SQLite in certain modes)
- **Flexibility**: Easier to handle soft deletes, archiving, and data migrations
- **Performance**: No FK constraint checking overhead on writes
- **Application control**: Business logic handles referential integrity explicitly

**How relationships work:**
- Database columns are simple integers/strings with indexes
- SQLAlchemy `db.relationship()` defines logical connections
- Application code enforces referential integrity
- Comments in code document relationships

### Core Tables

```sql
-- Users (email-only authentication for MVP)
CREATE TABLE users (
  id VARCHAR(36) PRIMARY KEY,  -- UUID as string
  email VARCHAR(255) UNIQUE NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_users_email ON users(email);

-- Prepared image configurations (NOT the actual images)
-- Original images are stored in filesystem: /uploads/<user_id>/originals/<filename>
-- Processed images are regenerated on-demand from config + original
CREATE TABLE prepared_images (
  id VARCHAR(36) PRIMARY KEY,  -- UUID as string
  user_id VARCHAR(36) NOT NULL,  -- Reference to users.id (no FK constraint)
  name TEXT NOT NULL,
  original_filename TEXT NOT NULL,
  config JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_prepared_images_user ON prepared_images(user_id, created_at DESC);

-- Config structure (stored in prepared_images.config):
-- {
--   "width": 100,              // Target dimensions in stitches
--   "height": 100,
--   "maxColors": 50,           // Color reduction count
--   "useDmcPalette": true,     // Map to DMC colors
--   "edgeDetection": true,     // Generate lines/edges layer
--   "edgeThreshold": 100,      // Canny edge detection threshold
--   "resizeMethod": "area"     // OpenCV resize interpolation method
-- }
--
-- Processed images are regenerated on-demand by:
-- 1. Loading original from /uploads/<user_id>/originals/<original_filename>
-- 2. Applying config settings (resize, quantize, edge detect)
-- 3. Caching result (optional) in /uploads/<user_id>/cache/<prepared_id>_*.png

-- Projects (stores full current state with layers)
CREATE TABLE projects (
  id VARCHAR(36) PRIMARY KEY,  -- UUID as string
  user_id VARCHAR(36) NOT NULL,  -- Reference to users.id (no FK constraint)
  name TEXT NOT NULL,
  width INT NOT NULL CHECK (width > 0),
  height INT NOT NULL CHECK (height > 0),
  cloth_color VARCHAR(7) DEFAULT '#ffffff',
  state JSONB NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_projects_user ON projects(user_id, created_at DESC);

-- Full project state structure (stored as JSONB in projects.state):
-- {
--   palette: [
--     {
--       id: "uuid",
--       vendor: "DMC",           -- "DMC", "Anchor", or null
--       code: "310",             -- vendor color code
--       name: "Black",
--       rgbHex: "#000000",
--       symbol: "A",             -- single ANSI unicode character
--       sortIndex: 0             -- display order
--     },
--     ...
--   ],
--   layers: [
--     {
--       id: "uuid",
--       type: "image",           -- "image" or "raster" or "backstitch"
--       name: "Background",
--       visible: true,           -- Show/hide in editor
--       activeForExport: false,  -- Include in PDF export
--       editable: true,          -- Can user edit this layer
--       opacity: 0.5,            -- for image layers (0.0-1.0)
--       imageData: "data:..."    -- for image layers (base64)
--     },
--     {
--       id: "uuid",
--       type: "raster",
--       name: "Main stitches",
--       visible: true,
--       activeForExport: true,   -- This layer WILL be exported
--       editable: true,
--       cells: [                 -- array of (width * height) cells
--         null,                  -- empty cell
--         {
--           paletteIndex: 1,
--           stitchType: "full-stitch"  -- See stitch types list below
--         },
--         ...
--       ]
--     },
--     {
--       id: "uuid",
--       type: "backstitch",      -- Vector lines layer
--       name: "Outlines",
--       visible: true,
--       activeForExport: true,
--       editable: true,
--       lines: [
--         {
--           paletteIndex: 0,
--           strands: 2,           -- 1, 2, or 3
--           x1: 5.5, y1: 3.0,
--           x2: 7.5, y2: 3.0
--         }
--       ]
--     }
--   ],
--   activeLayerId: "uuid",
--   properties: {
--     majorGridInterval: 10,
--     showGridNumbers: false,
--     defaultStitchType: "full"
--   }
-- }

-- Version history snapshots (kept for 7 days)
CREATE TABLE project_snapshots (
  id VARCHAR(36) PRIMARY KEY,  -- UUID as string
  project_id VARCHAR(36) NOT NULL,  -- Reference to projects.id (no FK constraint)
  state JSONB NOT NULL,
  diff JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_snapshots_project_time ON project_snapshots(project_id, created_at DESC);

-- Cleanup old snapshots (run daily)
-- DELETE FROM project_snapshots WHERE created_at < NOW() - INTERVAL '7 days';
```

### SQLAlchemy Model Pattern (No Foreign Keys)

**Example: User model with relationships**
```python
from stitch.database import db
from datetime import datetime
import uuid

class User(db.Model):
    """User model with email-only authentication."""
    __tablename__ = 'users'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships (no database FK constraints)
    projects = db.relationship('Project',
                              primaryjoin='User.id==Project.user_id',
                              foreign_keys='[Project.user_id]',
                              back_populates='user',
                              lazy='dynamic')

    def __repr__(self):
        return f'<User {self.email}>'
```

**Example: Project model with user reference**
```python
class Project(db.Model):
    """Project model storing cross-stitch patterns."""
    __tablename__ = 'projects'

    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), nullable=False, index=True)  # Reference (no FK)
    name = db.Column(db.String(255), nullable=False)
    width = db.Column(db.Integer, nullable=False)
    height = db.Column(db.Integer, nullable=False)
    cloth_color = db.Column(db.String(7), default='#ffffff')
    state = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to user (no database FK constraint)
    user = db.relationship('User',
                          primaryjoin='Project.user_id==User.id',
                          foreign_keys='[Project.user_id]',
                          back_populates='projects')

    def __repr__(self):
        return f'<Project {self.name}>'
```

**Key points:**
- Column definitions use simple types (String, Integer) with indexes
- No `db.ForeignKey()` anywhere
- Use `db.relationship()` with explicit `primaryjoin` and `foreign_keys`
- Comments document what each reference column points to
- Application code ensures data integrity
