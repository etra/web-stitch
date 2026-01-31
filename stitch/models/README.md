# Models

This folder contains **database models** and **static/reference data** used by the app.

Rules for model writing and documentation: see `database-models.md`.

---

## Database Models

| Model     | File         | Purpose                                                                                                                    |
| --------- | ------------ | -------------------------------------------------------------------------------------------------------------------------- |
| `User`    | `user.py`    | User record for MVP email-only authentication. Owns projects via `User.projects`.                 |
| `Project` | `project.py` | A cross-stitch pattern project (metadata + `state` JSON). References `User` via `user_id` (no DB FK). |

## Enums

| Enum            | File         | Values | Purpose |
| --------------- | ------------ | ------ | ------- |
| `ProjectStatus` | `project.py` | DELETED (-1), DEFAULT (0), PUBLIC (1), PRIVATE (2) | Project visibility/soft-delete status |

---

## Static / Reference Data

| Component          | File             | Purpose                                                                                                                                          |
| ------------------ | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `Color` + palettes | `static_data.py` | Palette loader + helpers. Includes `Color` dataclass and `DMC_PALETTE` loaded from `dmc.json` (plus placeholder palettes).  |
| DMC palette data   | `dmc.json`       | Source data for DMC colors (code/name/hex/default).                                                                       |

---

## Update Rule

If you add, remove, rename, or repurpose a model/module in this folder, **update this README in the same commit**.
