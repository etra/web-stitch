# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## Decisions Made

✅ **Snapshot retention:** 7 days
✅ **localStorage conflict resolution:** Ask user which to keep
✅ **Image import:** Synchronous (no async job queue)
✅ **Symbol assignment:** ANSI unicode characters
✅ **Grid size limits:** No limits (user decides)
✅ **Authentication:** Email-only for MVP (no password)
✅ **Deployment:** Self-hosted on local server
✅ **Storage:** Local PostgreSQL + file system (no S3)
✅ **Frontend framework:** Bootstrap 5 + Vanilla JavaScript (no React, Vite optional)
✅ **localStorage:** No library needed (native API is sufficient)
✅ **Resize/scale:** Nearest-neighbor scaling for v1
✅ **Markup layer:** Defer to v1.1

## Open Questions (Still TBD)

1. **Export format:** Define JSON export format for portability (OXS-like)?
2. **DMC palette:** Pre-load full DMC color set, or let users build custom palettes?
3. **Grid coordinates:** Show row/column numbers/letters on edges?
4. **Keyboard shortcuts:** Define shortcuts for tools, undo/redo, etc.?

## Future Enhancements

### v1.1
- **Proper authentication** - Password + JWT tokens, OAuth (Google, GitHub)
- **Backstitch layer** - Vector overlay for outlines and details
- **Markup mode** - Track completed stitches for progress
- **PDF export** - With pagination, color key, and symbol legend
- **WebSocket sync** - Real-time updates instead of periodic polling
- **Keyboard shortcuts** - For tools, undo/redo, zoom, etc.
- **Grid coordinates** - Row/column labels on edges

### v2+
- **Multi-user collaboration** - Operational transforms or CRDTs
- **Project sharing** - View-only and edit links
- **DMC palette presets** - Pre-loaded complete DMC color library
- **Pattern marketplace** - Share/sell patterns
- **Mobile/touch interface** - Optimized for tablets
- **Offline mode** - Full PWA with service workers
- **Advanced export** - Multi-page PDFs, print templates
- **Stitch calculator** - Estimate floss requirements
- **Pattern generator** - AI-powered pattern creation from images
