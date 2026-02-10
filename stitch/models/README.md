# Models

This folder contains **database models** and **static/reference data** used by the app.

Rules for model writing and documentation: see `database-models.md`.

---

## Database Models

| Model                 | File                       | Purpose                                                                                                                    |
| --------------------- | -------------------------- | -------------------------------------------------------------------------------------------------------------------------- |
| `User`                | `user.py`                  | User record for MVP email-only authentication. Owns projects via `User.projects`.                 |
| `Project`             | `project.py`               | A cross-stitch pattern project. State is normalized into `ProjectLayer` and `ProjectColor`. References `User` via `user_id` (no DB FK). Has `colors` and `layers` relationship properties. |
| `ProjectLayer`        | `project_layer.py`         | Normalized layer storage. Each row is one layer in a project's stack, ordered by `sort_order`. Types: `raster`, `reference`. |
| `ProjectLayerCells`   | `project_layer_cells.py`   | Cell data for a layer, stored separately from layer metadata. One row per layer, keyed by `layer_id`. |
| `ProjectLayerPaths`   | `project_layer_paths.py`   | Path/backstitch data for a layer, stored separately from layer metadata. One row per layer, keyed by `layer_id`. |
| `ProjectLayerImage`   | `project_layer_image.py`   | Base64 reference image for a layer, stored separately from layer metadata. One row per layer, keyed by `layer_id`. |
| `ProjectColor`        | `project_color.py`         | Links a project to a catalog color (`colors.id`) with a chart symbol and sort order. Ordered by `sort_order`. |
| `Color`               | `color.py`                 | Vendor color catalog entry (e.g., DMC floss, Hama beads). Seeded from JSON/static data via `scripts/seed_colors.py`. |
| `Tag`                 | `tag.py`                   | Tag for categorizing projects. Unique by normalized name, shared across all projects. |
| `ProjectTag`          | `project_tag.py`           | Junction table linking projects to tags (many-to-many). Composite PK (project_id, tag_id), no DB foreign keys. |
| `ProjectVote`         | `project_vote.py`          | Stores a user's vote on a project (+1 or -1). Unique constraint on (project_id, user_id). No DB foreign keys. |

**Note:** `Project` has a denormalized `vote_score` column (integer, default 0) caching the sum of votes for efficient sorting. Updated by `VoteService`.

## Enums

| Enum              | File         | Values | Purpose |
| ----------------- | ------------ | ------ | ------- |
| `ProjectStatus`   | `project.py` | DELETED (-1), DEFAULT (0), PUBLIC (1), PRIVATE (2) | Project visibility/soft-delete status |
| `DifficultyLevel` | `project.py` | BEGINNER (1), INTERMEDIATE (2), ADVANCED (3) | Project difficulty level (optional) |
| `ColorVendor`     | `color.py`   | DMC, HAMA, ARTKAL, NABBI | Supported color vendors with display metadata (full_name, description, vendor_type) |

---

## Static / Reference Data

| Component          | File             | Purpose                                                                                                                                          |
| ------------------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Stitch` + types   | `stitch.py`      | Stitch type definitions. `STITCH_TYPES` dict, `Stitch` dataclass, `get_stitches()` helper. |
| DMC palette data   | `dmc.json`       | Source data for DMC colors (code/name/hex/default). Used by `scripts/seed_colors.py` to seed the `colors` table.            |

---

## Update Rule

If you add, remove, rename, or repurpose a model/module in this folder, **update this README in the same commit**.
