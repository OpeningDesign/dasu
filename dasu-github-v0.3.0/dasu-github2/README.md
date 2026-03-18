# Dasu.print — Sheet Layout Tool

**出す** *(dasu)* — Japanese: *to output / to print*

A free, open-source browser-based sheet layout tool built for the [Bonsai BIM](https://bonsaibim.org) / [IfcOpenShell](https://ifcopenshell.org) ecosystem — and anyone else who needs to compose print-ready drawing sheets without proprietary software.

> Developed independently for the benefit of the OSArch and Bonsai communities.  
> Not affiliated with, endorsed by, or a product of either community.

---

## What is it?

Dasu is a **single HTML file** that runs entirely in your browser. No install. No subscription. No cloud. No vendor lock-in. Open it in Chrome or Edge and it works — on a home PC, a locked-down government machine, a borrowed laptop.

The goal is to bridge the gap between IFC-based BIM authoring in Blender/Bonsai BIM and the production of print-ready drawing sheets. Drawings from Bonsai BIM, DXF files from any source, PDFs from Revit or anywhere else — composed on sheets, annotated, dimensioned, and exported as PDF or SVG, entirely within the browser.

---

## Quick Start

1. Download `dasu.html`
2. Open in Chrome or Edge — **directly as a local file** (`Ctrl+O`)
3. Choose a template from the Start dialog
4. Drag SVG, PNG, JPG, or PDF files onto the sheet

For DXF import and Bonsai BIM live connection, also run the bridge server:
```
python bridge/dasu_bridge.py
```

---

## Features

### Sheet Canvas
- A4 · A3 · A2 · A1 · Letter, portrait/landscape
- Configurable grid (1–25 mm), zoom/pan, fit-to-sheet
- Sheet background permanently locked — cannot be accidentally moved or selected
- Elements cannot be placed behind the sheet background

### Import Sources
- **SVG** — drag-drop or file picker (Inkscape SVGs fully supported)
- **PNG / JPG** — drag-drop or file picker
- **PDF** — page picker with 1×–4× render resolution (via PDF.js)
- **DXF** — converted to SVG via bridge server (ezdxf) — sidebar panel, no Bonsai needed
- **Bonsai BIM** — live push from Blender N-panel via bridge server

### Element Panel
- Position (mm), size (mm), scale label, angle
- Order (forward/back/front/back — always above sheet), align to sheet
- Mirror X/Y, crop with drag handles, lock
- **Colour Override** — Original / Black / Greyscale / Single colour — works on vector, images, and mixed SVG groups

### Snap Engine
- Grid snap, sheet edges/centres, element edges/centres, equal spacing
- Smart guide lines, ortho lock (Ctrl), angle snap (Shift)
- Arrow key nudge, large nudge with Shift/Ctrl

### Annotation Tools
- Line (with Alt→polyline continuation)
- Polyline / Polygon
- Rectangle, Circle / Ellipse
- Arrow / Leader
- **Dimension** — three-click workflow (pt1 → pt2 → offset), H/V/A modes, live rubber-band with real-time mm label, scale-aware, Ctrl=ortho
- Text — full formatting, background box, revision cloud border
- All annotate tools suspend underlying element selection — no accidental moves while drawing

### Clipboard
- `Ctrl+C` — copy element to internal clipboard
- `Ctrl+Shift+V` — paste internal clipboard (works across sheets)
- `Ctrl+V` — paste from OS clipboard (screenshots, images, text)

### Keyboard Shortcuts
| Key | Action |
|-----|--------|
| `F` | Fit sheet |
| `R` | Force refresh |
| `G` | Toggle grid |
| `S` | Toggle snap |
| `Space` (hold) | Temporary pan |
| `Ctrl+D` | Duplicate |
| `Ctrl+A` | Select all |
| `Ctrl+C` | Copy element |
| `Ctrl+Shift+V` | Paste element |
| `Ctrl+V` | Paste from OS clipboard |
| `Ctrl+[` / `Ctrl+]` | Order backward/forward |
| `Ctrl+Shift+[` / `Ctrl+Shift+]` | Send to back / bring to front |
| `Ctrl+S` | Save |
| `Ctrl+Shift+S` | Save As |
| `Ctrl+Shift+E` | Export PDF |
| `Alt+drag` | Pan canvas |

See `docs/dasu-kb-shortcuts.xlsx` for the full reference matrix.

### File System
- `.bprint` format — Portable (embedded) or Referenced mode
- Save As with OS native folder picker
- Auto-save to IndexedDB (3s debounce)
- Recent files, built-in and user templates
- Start dialog — New / Templates / Recent

### Export
- PDF (jsPDF), SVG, browser Print
- Outputs panel pinned to bottom of left sidebar

### Multi-page
- Tab-based sheets, per-sheet paper settings
- Copy/paste elements across sheets

---

## Bonsai BIM Bridge

The bridge connects Dasu to Blender/Bonsai BIM for live drawing push, and handles DXF→SVG conversion for any DXF file.

### Requirements
- Python 3.6+ (stdlib only for basic operation)
- `pip install ezdxf Pillow` for DXF conversion
- Blender 4.x / 5.x with Bonsai BIM for live drawing push

### Setup

```bash
# Terminal — start the bridge
python bridge/dasu_bridge.py

# Blender Text Editor — open and run:
blender/dasu_panel.py
# Then: N-panel → Dasu tab → set drawings folder → Send to Dasu ↗
```

Bridge listens on `localhost:7821`. Open `http://localhost:7821` for a status page.

### DXF Import (no Bonsai needed)
1. Run `dasu_bridge.py`
2. Dasu sidebar: DXF Import → Install ezdxf (if needed) → Browse DXF → Convert & Import
3. Works with any DXF from any source

### One-click startup (Windows)
Create `start-dasu.bat` in your Dasu folder:
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
| [Fabric.js 5.3.1](https://fabricjs.com) | MIT | Canvas manipulation |
| [jsPDF 2.5.1](https://parall.ax/products/jspdf) | MIT | PDF generation |
| [PDF.js 3.11](https://mozilla.github.io/pdf.js/) | Apache 2.0 | PDF import |
| [ezdxf](https://ezdxf.readthedocs.io) *(bridge)* | MIT | DXF→SVG conversion |

Zero proprietary dependencies. Runs fully local. No cloud. No licence fees.

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Done | Canvas, snap, element panel, text, file system, templates, multi-page |
| 2 | ✅ Done | PDF import, DXF import via bridge, Bonsai BIM bridge, sheets fix |
| 3 | ✅ Done | Clipboard, copy/paste across sheets, dim tool, KB shortcuts, colour override, annotate UX fix |
| 4 | 🔵 Active | DXF layer manager, associated dimensions, Inkscape SVG symbol library |
| 5 | ⚪ Future | Editable title block fields, rulers, undo/redo, TAKT planning integration |

---

## Project Structure

```
dasu/
├── dasu.html              ← the complete app (single file)
├── bridge/
│   └── dasu_bridge.py     ← local HTTP bridge server (Python stdlib)
├── blender/
│   └── dasu_panel.py      ← Blender N-panel script
├── docs/
│   ├── dasu-onepager.docx
│   └── dasu-kb-shortcuts.xlsx
├── README.md
├── CHANGELOG.md
└── .gitignore
```

---

## Contributing

Issues, pull requests, and feedback welcome. Built for the OSArch and Bonsai communities — independently developed.

- [OSArch Community](https://community.osarch.org)
- [Bonsai BIM](https://bonsaibim.org)
- [IfcOpenShell](https://github.com/IfcOpenShell/IfcOpenShell)

---

## Licence

MIT — see [LICENSE](LICENSE)

---

*Dasu.print v0.3.0-alpha · 出す · Built for the OSArch / Bonsai BIM community · github.com/4nigel/dasu*
