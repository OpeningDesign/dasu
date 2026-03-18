# Changelog

All notable changes to Dasu.print are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.2.0-alpha] — 2026-03

### Added
- **PDF import** — PDF.js 3.11, page picker for multi-page PDFs, 1×–4× render resolution, drag-drop support
- **DXF import** — bridge server converts DXF→SVG via ezdxf, sidebar panel with Browse/Convert workflow, Install ezdxf button
- **Multi-sheet fix** — Add Sheet now correctly creates independent blank sheets; switching between sheets preserves state
- **Sheet background locked** — sheet rect cannot be accidentally selected or moved
- **Force refresh button** — toolbar ↺ button and R key shortcut for manual canvas redraw
- **Crop display fix** — added `canvas.renderAll()` + `setCoords()` after applying clipPath to fix stale display
- **Source panel cleanup** — renamed "IFC / SVG" to "SVG", removed "From Bonsai BIM" source button (bridge modal still accessible)
- **DXF background strip** — removes ezdxf dark background rect from converted SVG
- **Keyboard shortcuts xlsx** — full reference matrix with status, category, and clash risk columns
- **Version display** — About dialog now shows v0.2.0-alpha

### Bridge (dasu_bridge.py)
- New `/convert-dxf` endpoint — accepts base64 DXF, converts via ezdxf SVG backend, returns SVG + layer list
- New `/install-package` endpoint — runs pip install for whitelisted packages (ezdxf, Pillow) without needing a terminal
- Improved startup message — "Ready — waiting for connections from Dasu"
- Better error reporting for ezdxf import failures

### Blender Panel (dasu_panel.py)
- Added drawings folder field — persistent per-session, shown in N-panel
- Added SVG path override — manual file picker for when auto-detection fails
- Added Diagnose button — dumps full diagnostic to Blender System Console
- Improved `_get_svg_path` — five-strategy finder including IfcDocumentReference, Bonsai prefs dir, folder scan
- Improved `_clean_camera_name` — handles `IfcAnnotation/DrawingName` prefix stripping
- Suppressed known Bonsai 5.0 decoration.py numpy bug (non-fatal)

### Known Issues
- Crop tool does not display on Bonsai BIM SVGs — render timing under investigation
- DXF lineweight scaling in element panel not working correctly
- Arrow leader vertex editing deferred

---

## [0.1.0-alpha] — 2026-03

### Added
- Sheet canvas with A4–A1 paper sizes, portrait/landscape, configurable grid
- Zoom/pan, fit-to-sheet, viewport transform
- Snap engine — grid snap, sheet edges, element edges/centres, equal spacing, smart guides
- Ortho lock (Ctrl+drag), angle snap (Shift), arrow key nudge
- Element settings panel — position, size (mm), scale label, angle, order, align to sheet
- Mirror X/Y, crop with drag handles, element lock
- Import — SVG, PNG, JPG via drag-drop or file picker
- Annotation tools — line, rectangle, ellipse, polyline/polygon, arrow/leader, dimension, text
- Text — full formatting, background box, revision cloud border
- Fill — solid colour, hatch patterns, linear gradient
- Title block, north point, scale bar
- Multi-page tabs
- `.bprint` file format — Portable and Referenced save modes
- Save As with OS native folder picker (File System Access API)
- Auto-save to IndexedDB, recent files, user templates
- Start dialog — New / Templates / Recent
- Export PDF, SVG, browser Print
- Preferences dialog
- Bonsai BIM bridge — local HTTP server, Blender N-panel

---

## Upcoming — [0.3.0]

- Clipboard paste — Ctrl+V images/text from OS
- Copy + Paste elements within and across sheets (Ctrl+C / Ctrl+V)
- DXF layer manager — lineweight/colour/linetype mapping, NZ Drawing Standard preset
- DXF lineweight scaling fix
- Annotate UX — suspend element selection when annotate tool active
- Dimension tool — dumb first pass (Aligned/H/V, real-world mm, scale-aware)
- Keyboard shortcuts — Ctrl+D, Ctrl+[/], Ctrl+A, G, S, Space
- Undo / Redo
