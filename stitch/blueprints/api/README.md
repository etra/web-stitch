# API Blueprint

JSON API endpoints consumed by frontend JavaScript. For architecture rules and how to add new resources, see [claude/api.md](../../../claude/api.md).

## URL Prefix

`/api`

## Resources

| Resource | Description |
|----------|-------------|
| [color](color/README.md) | Thread and bead color catalogs |
| [stitch](stitch/README.md) | Stitch type definitions |
| [project](project/README.md) | Project data and layers |
| tag | Tag autocomplete (`GET /api/tags?q=...`) |
| [vote](vote/) | Project voting (`POST/DELETE /api/projects/<id>/vote`) |
