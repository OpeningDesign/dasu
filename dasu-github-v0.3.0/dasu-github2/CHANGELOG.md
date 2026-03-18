# Changelog

All notable changes to Dasu.print are documented here.  
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [0.3.0-alpha] — 2026-03

### Added
- **Dimension tool** — three-click workflow: click pt1 → click pt2 → click offset position. H/V/A mode keys after first click. Ctrl=ortho lock on second click. Live rubber-band preview with real-time mm label at all stages. Offset direction determined by which side of the measurement line you click. Scale-aware: reads `_drawingScale` from active element so 1:50 drawing shows real-world mm. Esc cancels at any stage. Stores element ref and scaleDenom ready for associated dims later.
- **Clipboard — OS paste** — `Ctrl+V` pastes images (screenshots, copied images) or plain text from the OS clipboard directly onto the canvas
- **Clipboard — internal copy/paste** — `Ctrl+C` copies selected element including all custom properties. `Ctrl+Shift+V` pastes onto current or any other sheet (persists across sheet switches)
- **Duplicate** — `Ctrl+D` duplicates selected element with 10mm offset. Also in Edit menu.
- **Keyboard shortcuts** — `G` toggle grid, `S` toggle snap, `Space` (hold) temporary pan, `Ctrl+A` select all, `Ctrl+[`/`Ctrl+]` order backward/forward, `Ctrl+Shift+[`/`Ctrl+Shift+]` send to back/bring to front
- **Colour Override** — Original / Black / Greyscale / Single colour override on any element. Context-aware labels (images show Greyscale/One Colour, vector shows Black/Single). Recursive tree walk handles nested SVG groups. Restores original colours cleanly.
- **Annotate UX fix** — all annotate tools now suspend selection of underlying elements. First click always starts drawing, never accidentally selects/moves an element. Cursor changes to crosshair. Restored to select on tool switch or Esc.
- **Outputs panel** — moved to bottom of left sidebar, pinned with margin-top:auto
- **Sheet background locked** — `_isSheetRect` objects re-enforced non-selectable after every loadFromJSON. `onDown` discards any accidental selection. Elements can never be placed behind the sheet background via order operations.
- **Safe order operations** — `safeOrderOp()` wrapper ensures `sheetRect` is always re-pinned to bottom after any reorder. `object:added` event also re-pins automatically.
- **Force refresh** — `↺ Refresh` button in toolbar and `R` key shortcut

### Fixed
- Crop display — `canvas.renderAll()` + `setCoords()` called synchronously after applying clipPath in `_applyCropToObj`, `clearCrop`, and `exitCropMode`
- `_setBridgeStatus` no longer crashes when bridge-btn element is absent from sidebar

### Bridge (dasu_bridge.py)
- `/install-package` endpoint — runs `pip install` for whitelisted packages (ezdxf, Pillow) from within Dasu UI, no terminal needed
- Startup message updated to "Ready — waiting for connections from Dasu"
- `/convert-dxf` — added dark background rect stripping from ezdxf SVG output

---

## [0.2.0-alpha] — 2026-03

### Added
- PDF import — PDF.js 3.11, page picker, 1×–4× resolution
- DXF import — bridge /convert-dxf endpoint, sidebar panel, Install ezdxf button
- Multi-sheet fix — Add Sheet creates independent blank sheets
- Sheet background locked
- Force refresh button (R key)
- Crop display fix
- Source panel cleanup — SVG rename, Bonsai BIM button removed from source
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

## Upcoming — [0.4.0]

- DXF layer manager — lineweight/colour/linetype mapping, NZ Drawing Standard preset
- DXF lineweight scaling fix in element panel
- Associated dimensions (element-linked, updates on move/scale)
- Inkscape SVG symbol library — title blocks, north points, NZ standard symbols
- Colour override greyscale for SVG groups containing embedded images
- Undo / Redo
