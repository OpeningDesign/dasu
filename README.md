# Dasu.print — Sheet Layout Tool

**出す** *(dasu)* — Japanese: *to output / to print*

A free, open-source browser-based sheet layout tool built for the [Bonsai BIM](https://bonsaibim.org) / [IfcOpenShell](https://ifcopenshell.org) ecosystem — and anyone else who needs to compose print-ready drawing sheets without proprietary software.

> Developed independently for the benefit of the OSArch and Bonsai communities and everyone else.
> Not affiliated with, endorsed by, or a product of either community but would like to be that cool.

---

## What is it?

Dasu is a **single HTML file** that runs entirely in your browser. No install. No subscription. No cloud. No vendor lock-in. Open it in Chrome or Edge (other browsers have not been tested) and it works — on a home PC, a locked-down government machine, a borrowed laptop or your phone.

---

## Quick Start

1. Download `dasu.html`
2. Open in Edge or Chrome — **directly as a local file** (`Ctrl+O`)
3. Choose a template from the Start dialog
4. Drag SVG, PNG, JPG, or PDF files onto the sheet

For DXF import and Bonsai BIM live connection, also run the bridge server:
```
python bridge/dasu_bridge.py
```
## Terminology 
- Elements: external stuff that has been placed on drawing sheets. Elements can be SVG, PNG, JPG, PDF, DXF (work in progress)
- Objects: internal things like Annotations, lines, circles, polygons, text and dimensions 
---

## Features

### Sheet Canvas
- A4 · A3 · A2 · A1 · Letter, portrait/landscape
- Configurable grid (1–25 mm), zoom/pan, fit-to-sheet
- Sheet background permanently locked
- Elements cannot be placed behind sheet background

### Import Sources
- **SVG** — drag-drop or file picker (Inkscape SVGs fully supported)
- **PNG / JPG** — drag-drop or file picker
- **PDF** — page picker with 1×–4× render resolution
- **DXF** — converted via bridge server (ezdxf, work in progress)
- **Bonsai BIM** — live push from Blender N-panel via bridge (work in progress)

### Bonsai SVG Intelligence
- Auto-reads `data-scale` — scale field pre-populated on import
- Detects `xmlns:ifc=` namespace
- **Style Manager** — edit CSS classes (IfcWall, PredefinedType-LINEWORK etc.) per drawing. Presets:Regional Drawing Standard, Greyscale Print, Colour by Class. Preserve white fills option keeps text/marker backgrounds intact.

### Element Panel
- Position, size (mm), **scale label drives resize** (centre-anchored, reversible, 10× warning)
- Order, align, mirror, crop, lock
- Colour Override — Original / Black / Greyscale / Single colour
- Bonsai BIM Drawing section with Style Manager access
- DXF Layers section

### Snap Engine
- Grid snap, sheet edges/centres, element edges/centres, equal spacing
- Smart guides, ortho lock (Ctrl), angle snap (Shift)
- Arrow key nudge

### Annotation Tools (not trying to be a CAD app)
- Line, Polyline/Polygon, Rectangle, Circle/Ellipse, Arrow/Leader
- **Dimension** — three-click workflow, H/V/A modes, live rubber-band, scale-aware
- Text — formatting, background box, revision cloud border
- All annotate tools suspend element selection

### Canvas UX
- **☰ Elements panel** — list all elements, toggle hide/show and lock per element
- **Lock icon on hover only** — clean canvas, icon appears only on mouse-over
- **Shift+rotate** — snaps to lineAngleSnap increment
- Copy (Ctrl+C) / Paste internal (Ctrl+Shift+V) / Paste OS (Ctrl+V)
- Duplicate (Ctrl+D), Select all (Ctrl+A), Order (Ctrl+[/])
- Space to pan, G to toggle grid, S to toggle snap

### Sheets
- **Duplicate sheet** — Shift+click `+` or right-click tab
- **Delete sheet** — right-click tab
- **Rename sheet** — double-click tab or right-click tab

### File System
- `.bprint` format — Portable or Referenced
- Save As with OS native folder picker
- Auto-save to IndexedDB, recent files, templates, start dialog

### Export
- PDF (jsPDF), SVG, browser Print
- Outputs panel pinned to left sidebar bottom

---

## Bonsai BIM Bridge

```bash
python bridge/dasu_bridge.py
```

Listens on `localhost:7821`. Handles:
- Live drawing push from Blender N-panel
- DXF→SVG conversion via ezdxf (`pip install ezdxf Pillow`)
- In-app ezdxf install button (no terminal needed)

### One-click startup (Windows)
```batch
@echo off
start "" python C:\dasu\bridge\dasu_bridge.py
timeout /t 2
start msedge "file:///C:/dasu/dasu.html"
```

---

## Tech Stack

| Library | Licence | Purpose |
|---------|---------|---------|
| Fabric.js 5.3.1 | MIT | Canvas |
| jsPDF 2.5.1 | MIT | PDF export |
| PDF.js 3.11 | Apache 2.0 | PDF import |
| ezdxf *(bridge)* | MIT | DXF→SVG |

---

## Project Structure

```
dasu/
├── dasu.html
├── bridge/dasu_bridge.py
├── blender/dasu_panel.py
├── docs/
│   ├── dasu-onepager.docx
│   └── dasu-kb-shortcuts.xlsx
├── README.md
├── CHANGELOG.md
└── .gitignore
```

---

## Licence

MIT

---

*Dasu.print v0.4.0-alpha · 出す · github.com/4nigel/dasu*
