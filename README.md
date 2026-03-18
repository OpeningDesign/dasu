# Dasu.print — Sheet Layout Tool

**出す** *(dasu)* — Japanese: *to output / to print*

A free, open-source browser-based sheet layout tool built for the [Bonsai BIM](https://bonsaibim.org) / [IfcOpenShell](https://ifcopenshell.org) ecosystem — and anyone else who needs to compose print-ready drawing sheets without proprietary software.

> Developed independently for the benefit of the OSArch and Bonsai communities and anyone else who believes in FOSS.  
> This is not affiliated with, endorsed by, or a product of either community.

---

## What is it?

Dasu is a **single HTML file** that runs entirely in your browser. No install. No subscription. No cloud. No vendor lock-in. Open it in Chrome or Edge and it works — on a home PC, a locked-down government machine, a borrowed laptop.

The goal is to bridge the gap between IFC-based BIM authoring in Blender/Bonsai BIM and the production of print-ready drawing sheets. Drawings from Bonsai BIM, DXF files from any source, PDFs from Revit or anywhere else — composed on sheets, annotated, and exported as PDF or SVG, entirely within the browser.

---

## Quick Start

1. Download `dasu.html`
2. Open it in Chrome or Edge — **directly as a local file** (`Ctrl+O`)
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
- Sheet background locked — cannot be accidentally moved

### Import Sources
- **SVG** — drag-drop or file picker
- **PNG / JPG** — drag-drop or file picker
- **PDF** — page picker with 1×–4× render resolution (via PDF.js)
- **DXF** — converted to SVG via bridge server (ezdxf)
- **Bonsai BIM** — live push from Blender N-panel via bridge server

### Element Panel
- Position (mm), size (mm), scale label, angle
- Order (forward/back), align to sheet
- Mirror X/Y, crop with drag handles, lock

### Snap Engine
- Grid snap, sheet edges/centres, element edges/centres, equal spacing
- Smart guide lines, ortho lock (Ctrl), angle snap (Shift)
- Arrow key nudge, large nudge with Shift/Ctrl

### Annotation Tools
- Line (with Alt→polyline continuation)
- Polyline / Polygon
- Rectangle, Circle / Ellipse
- Arrow / Leader
- Dimension (basic)
- Text — full formatting, background box, revision cloud border

### Fill & Stroke
- Solid colour, hatch patterns (5 styles), linear gradient
- Stroke width uniform across scale

### File System
- `.bprint` format — Portable (embedded) or Referenced mode
- Save As with OS native folder picker
- Auto-save to IndexedDB (3s debounce)
- Recent files, built-in and user templates
- Start dialog — New / Templates / Recent

### Export
- PDF (jsPDF), SVG, browser Print

### Multi-page
- Tab-based sheets, per-sheet paper settings
- Add sheets, switch preserves state

---

## Bonsai BIM Bridge

The bridge connects Dasu to Blender/Bonsai BIM for live drawing push, and handles DXF→SVG conversion for any DXF file.

### Requirements
- Python 3.6+ (bridge server — stdlib only, no pip needed for basic operation)
- `pip install ezdxf Pillow` for DXF conversion
- Blender 4.x / 5.x with Bonsai BIM for live drawing push

### Setup

```bash
# Terminal 1 — start the bridge
python bridge/dasu_bridge.py

# Blender Text Editor — open and run:
blender/dasu_panel.py
# Then: N-panel → Dasu tab → set drawings folder → Send to Dasu ↗
```

The bridge listens on `localhost:7821`. Open `http://localhost:7821` for a status page.

### DXF Import (no Bonsai needed)
1. Run `dasu_bridge.py`
2. In Dasu sidebar: DXF Import → Browse DXF → Convert & Import
3. Works with any DXF from any source

### One-click startup (Windows)
Create `start-dasu.bat`:
```batch
@echo off
start "" C:\Users\nigel\AppData\Local\Programs\Python\Python311\python.exe C:\dasu\bridge\dasu_bridge.py
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

## File Format — `.bprint`

Plain JSON. Two save modes:
- **Portable** — all assets embedded as base64 (self-contained)
- **Referenced** — asset paths only (smaller, assets must stay in place)

Auto-save runs every 3 seconds to browser IndexedDB in referenced mode.

---

## Keyboard Shortcuts

See `docs/dasu-kb-shortcuts.xlsx` for the full reference matrix.

**Key shortcuts:**

| Key | Action |
|-----|--------|
| `F` | Fit sheet |
| `R` | Force refresh |
| `Del` | Delete selected |
| `Esc` | Cancel / deselect |
| `Ctrl+S` | Save |
| `Ctrl+Shift+S` | Save As |
| `Ctrl+N` | New |
| `Ctrl+O` | Open |
| `Ctrl+P` | Print |
| `Ctrl+Shift+E` | Export PDF |
| `Alt+drag` | Pan canvas |
| `Ctrl+drag` | Ortho lock |
| `Shift+drag` | Snaps active |
| Arrow keys | Nudge element |

---

## Roadmap

| Phase | Status | Description |
|-------|--------|-------------|
| 1 | ✅ Done | Canvas, snap, element panel, text, file system, templates, multi-page |
| 2 | ✅ Done | PDF import, DXF import via bridge, Bonsai BIM bridge, sheets fix |
| 3 | 🔵 Active | Clipboard paste, copy/paste across sheets, DXF layer manager, dimension tool, keyboard shortcuts |
| 4 | 🟡 Planned | Editable title block fields, rulers, undo/redo |
| 5 | ⚪ Future | Associated dimensions, TAKT planning integration |

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

*Dasu.print v0.2.0-alpha · 出す · Built for the OSArch / Bonsai BIM community · github.com/4nigel/dasu*
