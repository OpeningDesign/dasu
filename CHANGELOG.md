# Changelog

All notable changes to Dasu.print are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.4.0-alpha] — 2026-03

### Added

**Bonsai SVG**
- Auto-read `data-scale` attribute on SVG import — scale field pre-populated automatically
- Bonsai SVG detection via `xmlns:ifc=` and `data-scale=` attributes — element panel shows Bonsai BIM Drawing section
- **Style Manager** — parses embedded CSS `<style>` block, lists all classes (IfcWall, PredefinedType-LINEWORK etc.) with colour/lineweight/visibility controls
- Four presets: NZ Drawing Standard, Greyscale Print, Colour by Class, Reset to Original
- Fill options: Preserve White Fills (default on — keeps knockout fills behind text/markers white), Recolour All Fills with custom colour and hatch lineweight
- CSS override uses append strategy with `!important` — original SVG never modified, always reloadable
- Redraw safety — original drawing preserved on canvas if reload fails

**Sheet management**
- **Duplicate sheet** — Shift+click `+` button, or right-click tab → Duplicate
- **Delete sheet** — right-click tab → Delete (with confirmation, disabled when only one sheet)
- **Rename sheet** — double-click tab for inline rename, or right-click → Rename
- Right-click context menu on all sheet tabs

**Element panel**
- **Scale label drives resize** — changing scale from 1:50 to 1:100 halves the element on the sheet, anchored at centre point. Reversible (non-destructive transform). Warning dialog if change is 10× or more.
- **Bonsai BIM Drawing section** — shows when Bonsai SVG selected, displays scale and filename
- **DXF Layers section** — shows when DXF import selected

**Canvas UX**
- **Lock icon on hover only** — lock icon now only appears when mouse is over a locked element, or when it is selected. Canvas no longer cluttered with amber icons on busy sheets.
- **Element list panel** — ☰ Elements button in toolbar opens a panel listing all elements on the current sheet. Each row: icon, name, hide/show toggle (👁/🙈), lock/unlock toggle (🔒/🔓). Click row to select element. Auto-refreshes when objects change.
- **Shift+rotate snap** — hold Shift while rotating an element to snap to `lineAngleSnap` increments (default 15°)

**Preferences**
- Preferences panel now uses wide modal (640px) — no more horizontal scrollbar

### Fixed
- Console errors: `_guides` and `_bonsaiMeta` declared before use (moved to top of state variables)
- Element list `canvas.on` registration moved inside `_hookAutosave` to avoid canvas-before-init error
- Sheet context menu `_hideSheetCtxMenu` null-checked to prevent TypeError on every click
- Delete sheet menu item index corrected (separator not counted as `.dd-item`)
- Style manager redraw: `canvas.remove()` only called after successful reload (drawing no longer disappears on failed redraw)
- CSS style override switched from fragile regex rewrite to append strategy

---

## [0.3.0-alpha] — 2026-03

### Added
- Dimension tool — three-click workflow (pt1 → pt2 → offset), H/V/A modes, live rubber-band preview, scale-aware, Ctrl=ortho
- Clipboard OS paste — Ctrl+V images/screenshots and text from OS clipboard
- Clipboard internal copy/paste — Ctrl+C / Ctrl+Shift+V, persists across sheet switches
- Duplicate — Ctrl+D
- Keyboard shortcuts — G grid, S snap, Space pan, Ctrl+A select all, Ctrl+[/] order
- Colour Override — Original/Black/Greyscale/Single colour, works on vector and images
- Annotate UX — draw tools suspend element selection, cursor crosshair
- Outputs panel moved to left sidebar bottom
- Force refresh — ↺ button and R key

### Fixed
- Crop display after apply — added canvas.renderAll() + setCoords()
- Sheet background locked — cannot be selected or moved
- Elements cannot be placed behind sheet background

---

## [0.2.0-alpha] — 2026-03

### Added
- PDF import — PDF.js, page picker, 1×–4× resolution
- DXF import — bridge /convert-dxf, sidebar panel, Install ezdxf button
- Multi-sheet Add Sheet fix
- DXF background rect strip
- KB shortcuts xlsx reference matrix

---

## [0.1.0-alpha] — 2026-03

### Added
- Sheet canvas A4–A1, grid, zoom/pan, snap engine
- SVG/PNG/JPG import, drag-drop
- Annotation tools — line, rect, ellipse, polyline, arrow, dimension, text
- Fill — solid, hatch, gradient
- Title block, north point, scale bar
- Multi-page tabs
- `.bprint` file format — Portable and Referenced
- Save As, auto-save, recent files, templates, start dialog
- Export PDF, SVG, Print
- Bonsai BIM bridge — local HTTP server + Blender N-panel

---

## Upcoming — [0.5.0]

- Crop tool fix for Bonsai BIM SVGs
- DXF layer manager — confirm ezdxf SVG group format, per-layer colour/lineweight/visibility
- ifc: namespace metadata display — click element to see IFC properties
- Bridge end-to-end SVG send confirmation
- Inkscape SVG symbol library — NZ standard title blocks, north points, symbols
- Associated dimensions — element-linked, updates on move/rescale
- Undo / Redo
