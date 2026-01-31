# CLAUDE.md (Split)

These documents are derived from the original CLAUDE.md.
## Frontend Architecture

### Server-Side Rendering with Flask Templates

**Architecture:** Traditional Flask web application with server-side rendering
- **Not a separate frontend:** UI is rendered by Flask using Jinja2 templates
- **Not an API-only backend:** Flask serves HTML pages, not just JSON
- **No build process:** Templates, CSS, and JS served directly

### Technology Stack

**HTML Templates (Jinja2):**
- Server-side rendering with Flask's template engine
- Template inheritance for consistent layout
- Flash messages for user feedback

**Bootstrap 5:**
- CSS framework for responsive UI components
- No custom build process - use CDN
- Ready-to-use components (cards, forms, navbar)

**Vanilla JavaScript:**
- Used only for interactive canvas editor
- No React, Vue, or other frameworks
- ES6 modules for code organization (canvas editor only)

**Why this choice:**
- ✅ **Simpler** - No JSX, no build complexity, no virtual DOM
- ✅ **Faster development** - Bootstrap components + Flask templates
- ✅ **Smaller bundle** - Bootstrap CSS + minimal custom JS
- ✅ **Easy to modify** - Standard HTML/CSS/JS that anyone can read
- ✅ **Perfect for MVP** - Get working prototype faster
- ✅ **SEO-friendly** - Server-rendered HTML

### Application Structure

```
stitch/
├── templates/              # Jinja2 templates
│   ├── base.html          # Base template with navbar, footer
│   ├── index.html         # Home page
│   ├── projects.html      # Projects list
│   ├── images.html        # Image gallery
│   └── auth/
│       └── login.html     # Login page
│
├── static/                # Static assets
│   ├── css/
│   │   └── style.css     # Custom styles
│   └── js/               # JavaScript (canvas editor)
│
├── views.py              # Main page routes
└── blueprints/           # Blueprint routes
    └── auth/
        └── routes.py     # Auth routes
```

### Template Pattern

**Base template (base.html):**
- Bootstrap 5 CSS and JS from CDN
- Navigation bar with user session
- Flash message display
- Footer
- Block system for content injection

**Page templates:**
- Extend base.html
- Override `content` block
- Use Bootstrap components

**UI Components (Bootstrap 5):**
- Navigation: Navbar with user session
- Pages: Bootstrap cards and forms
- Canvas editor (future): Custom canvas with Bootstrap sidebars
  - Left sidebar: Tools card, Stitch type card, Palette card
  - Center: Canvas with toolbar
  - Right sidebar: Layers card


**State management (no library needed):**
```javascript
// Simple reactive state
export const state = { /* ... */ };
const listeners = [];
export function subscribe(callback) { listeners.push(callback); }
export function updateState(updates) {
  Object.assign(state, updates);
  listeners.forEach(cb => cb(state));
}
```

**localStorage (no library needed):**
```javascript
// Simple wrapper
export const Storage = {
  save(key, data) { localStorage.setItem(key, JSON.stringify(data)); },
  load(key) { return JSON.parse(localStorage.getItem(key)); },
  remove(key) { localStorage.removeItem(key); }
};
```

### Vite - Optional Dev Tool
We do not use any development tool for UI.
