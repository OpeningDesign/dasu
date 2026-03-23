

# Proposal: A Shared Open Project Format for Bonsai and Dasu


The following AI-assisted proposal explores aligning with how Bonsai structures its assets. A parallel path alongside the `.bprint` format that explores a distributed set of files that would be easier to version track with Git — with the aim, basically, of making the workflow as distributed-friendly as possible.

A response from community member Nigel has been incorporated below, which refines the proposal considerably — in particular introducing a three-pathway framework that preserves `.bprint` for standalone use cases rather than retiring it outright.

---

## Background

[Dasu](https://github.com/openingdesign/dasu) is a browser-based drawing sheet layout tool. It lets you compose drawings from Bonsai BIM, DXF, PDF, SVG, and raster images into print-ready sheets — entirely in the browser, with no install or subscription required. It includes a local bridge server that receives live SVG pushes from Blender/Bonsai as you work.

[Bonsai](https://bonsaibim.org) (formerly BlenderBIM) is the Blender-based open-source BIM authoring tool built on IfcOpenShell. Among its many capabilities, it manages drawing sets: it generates SVG drawings from camera views, assembles them into sheet layouts, and stores all of this in the IFC file and on disk.

At present, these two tools work alongside each other but maintain separate, incompatible project structures. This proposal describes a path toward a shared open format that would let both tools — and future tools — read and write the same project folder without conflict.

---

## The Problem

### Dasu's current format

Dasu currently saves everything into a single `.bprint` file: a JSON blob containing Fabric.js canvas state for all sheets, embedded or referenced assets, app preferences, and project metadata. This works for single-user workflows but has real limitations:

- **Not git-friendly.** A single JSON blob means every save produces a large, unreadable diff. Embedded base64 images make it worse.
- **Not interoperable.** No other tool can read or write a `.bprint` file.
- **Duplicates what Bonsai already knows.** Sheet names, drawing scales, IFC paths, and project metadata are all stored in the IFC file by Bonsai. Dasu maintains its own copy, which drifts out of sync.
- **Monolithic.** Adding a dimension on one sheet touches the same file as changing the titleblock on another, making collaborative merges messy.

### Bonsai's existing structure

Bonsai already writes a well-considered folder structure:

```
project-root/
  model.ifc
  drawings/       ← SVG drawings generated from camera views
    assets/       ← per-drawing resources (stylesheets, markers, symbols, patterns)
  layouts/        ← editable sheet layout SVGs (source)
    assets/       ← view title templates, symbols
    titleblocks/  ← titleblock SVG templates
  sheets/         ← compiled output SVGs (built from layouts)
```

The IFC file itself is the manifest: sheets are `IfcDocumentInformation` entities, drawings are `IfcAnnotation` entities, and relationships between them are stored as `IfcDocumentReference` entries. This is already an open, standardised structure.

The question is: can Dasu join this structure rather than sit alongside it?

---

## Design Strategy: Adopt Conventions, Not Assumptions

The guiding principle for this proposal — especially in these early stages — is to adopt Bonsai's conventions as fully as possible, and diverge only when real-world friction makes it necessary.

Bonsai has already solved hard problems through years of actual use: token naming, file structure, IFC entity relationships, asset path conventions, status vocabulary. Adopting these wholesale means Dasu inherits those design decisions without having to justify them from scratch. It also gives Dasu an immediate, credible value proposition for the OSArch community: it works natively with Bonsai projects from day one.

There is also a practical argument against premature abstraction. It is not possible to design a good platform-agnostic standard in the abstract. The right time to generalise is when there is real friction — a second tool that does things differently and needs to interoperate. Building toward an imagined standard before that point usually produces the wrong abstraction.

**The important distinction is between conventions and assumptions:**

- **Conventions** — token names, folder structure, status values, file formats, template schemas. These are safe to adopt wholesale and are shared across all three paths.
- **Assumptions** — that IFC always exists, that the bridge is always running, that Blender is the source of all drawings. These must remain Path 2 concerns, not baked into the core of Dasu.

The three-pathway framework enforces this boundary. For example: `{{Name}}` and `{{Identification}}` are Dasu's token names across *all* paths — but in Path 1 they are populated from Dasu's own sheet metadata, not from an IFC file. The vocabulary is shared; the data source is path-dependent. That is the right level of coupling.

**Where divergence will eventually be needed** — the likely candidates are things Bonsai doesn't need to handle because it lives inside Blender: multi-source sheet composition (DXF, PDF, and rasters alongside IFC drawings), browser-native UX patterns, the crop/viewport concept, and non-IFC projects. These are the areas where Dasu will eventually need its own conventions. By the time those needs arise, there will be real-world experience to design from rather than speculation.

---

## The Three-Pathway Framework

Rather than a single mandatory format, the proposal recognises three distinct usage contexts. The folder-based format is the right long-term direction — but it is not the only format, and `.bprint` is not retired.

| Pathway | Name | Characteristics |
|---|---|---|
| **Path 1** | Standalone / locked-down | No bridge, no IFC, `.bprint` format, any machine |
| **Path 2** | Bonsai-integrated | Bridge required, IFC manifest, folder format, git-friendly |
| **Path 3** | IFC import (read-only) — later phase | Bridge optional, IFC read-only input, `.bprint` output |

**Shared infrastructure across all three paths:**
- SmartText tokens — PascalCase, Bonsai-compatible
- `dasu-overlay` SVG group — Dasu namespace, Bonsai ignores gracefully
- Sidecar concept — `.bprint` is a fat sidecar; `.dasu/` is a thin sidecar
- PDF / SVG / Print output

**Note on `.bprint`:** Path 1 users — including users on locked-down government machines where `window.showDirectoryPicker()` requires explicit IT permissions — depend on the zero-dependency `.bprint` workflow. `.bprint` is a permanent first-class format for Paths 1 and 3, not a stepping stone to be retired. Both formats coexist permanently.

---

## The Proposal (Path 2: Bonsai-integrated)

We propose that Dasu adopt Bonsai's existing folder and file conventions as its Path 2 project format. A Path 2 project is a folder on disk — the same folder as the Bonsai project.

### Folder structure (no changes to Bonsai's conventions)

```
project-root/
  model.ifc                     ← source of truth for sheet/drawing structure

  drawings/                     ← Bonsai writes; Dasu reads
    FLOOR PLAN.svg
    SECTION-A.svg
    assets/                     ← per-drawing resources referenced in EPset_Drawing
      default.css               ← Stylesheet
      markers.svg               ← Markers
      symbols.svg               ← Symbols
      patterns.svg              ← Patterns
      shading-styles.json       ← ShadingStyles

  layouts/                      ← both Bonsai and Dasu read and write
    A-001 - Floor Plan.svg      ← editable layout SVG
    A-002 - Elevations.svg
    assets/
      view-title.svg
    titleblocks/
      A3-LANDSCAPE.svg

  sheets/                       ← compiled output; neither tool edits this directly
    A-001 - Floor Plan.svg      ← built by SheetBuilder from layouts/
    A-002 - Elevations.svg

  images/                       ← raster content placed in Dasu (new)
    logo.png

  .dasu/                        ← thin sidecar for Dasu-specific state (new)
    canvas.json
    prefs.json
```

The only new directories are `images/` and `.dasu/`. Everything else already exists.

### The layout SVG as the shared working file

Bonsai's layout SVGs already use a clean, structured format with `data-type` attributes. The key principle is that each tool owns clearly named groups and never writes into the other tool's groups:

```xml
<svg xmlns="http://www.w3.org/2000/svg">

  <g data-type="titleblock">
    <image xlink:href="titleblocks/A3-LANDSCAPE.svg"
           x="0" y="0" width="420mm" height="297mm"/>
  </g>

  <g data-type="drawing"
     data-id="{reference_id}"
     data-drawing="{IfcAnnotation.GlobalId}">
    <image data-type="foreground"
           xlink:href="../drawings/FLOOR PLAN.svg"
           x="30mm" y="30mm" width="340mm" height="220mm"/>
    <image data-type="view-title"
           xlink:href="assets/view-title.svg"
           x="30mm" y="252mm"/>
  </g>

  <g data-type="dasu-overlay">
    <!-- Dasu-placed annotations, DXF imports, non-IFC content -->
  </g>

</svg>
```

**Ownership rules:**

| SVG group | Ownership rule |
|---|---|
| `data-type="titleblock"` | Bonsai owns — reads and writes |
| `data-type="drawing"` | Bonsai owns — reads and writes |
| `data-type="dasu-overlay"` | Dasu owns — reads and writes. Bonsai preserves but ignores |
| Position of Bonsai drawings | Dasu **never** writes `x`/`y` into Bonsai-owned groups. Position overrides go into `.dasu/canvas.json` only |
| Round-trip safety | `dasu-overlay` is a formally documented, reserved group name — Bonsai preserves it, Inkscape passes it through, other tools ignore it gracefully |

Content that has no IFC equivalent (user-placed annotations, DXF imports, raster images, non-Bonsai SVGs) lives in the `dasu-overlay` group and is invisible to Bonsai.

### The IFC file as manifest

Dasu would read sheet and drawing metadata directly from the IFC, rather than maintaining its own copy:

- **Sheet list, names, paper sizes, revision metadata** → `IfcDocumentInformation` (Scope=SHEET)
- **Drawing properties** → `IfcAnnotation` (ObjectType=DRAWING) + `EPset_Drawing`
- **Which drawings are on which sheet** → `IfcDocumentReference` relationships
- **Project-level paths** → `BBIM_Documentation` property set on `IfcProject`

This means when a Bonsai user renames a sheet or updates a revision, Dasu sees it immediately on next open — no sync required.

**Conflict resolution by path:**

| Path | Rule |
|---|---|
| Path 1 | No IFC — Dasu meta is source of truth |
| Path 2 | IFC wins on conflict with Dasu meta |
| Path 3 | IFC read-only input — no write-back |

#### EPset_Drawing — what Dasu would read

Each drawing carries a property set that describes not just its scale and projection, but also the paths to all the assets used to render it. Dasu would read all of these:

| Property | What it is | How Dasu uses it |
|---|---|---|
| `Scale` | Numeric denominator (e.g. `"100"`) | Scale label, dimension calculations |
| `HumanScale` | Display string (e.g. `"1:100"`) | Title block, view title |
| `TargetView` | Projection type (`PLAN_VIEW`, `SECTION_VIEW`, etc.) | Display hint, filtering |
| `HasLinework` | Boolean | Whether to expect linework in the SVG |
| `HasAnnotation` | Boolean | Whether annotations are embedded in the SVG |
| `HasUnderlay` | Boolean | Whether an underlay layer is present |
| `Include` / `Exclude` | Comma-separated IFC GUIDs | Element filter — which model elements are visible |
| `GlobalReferencing` | Boolean | Whether the drawing uses global coordinates (sections/elevations) |
| `Stylesheet` | Path to `.css` file in `drawings/assets/` | Base visual style applied to the drawing SVG |
| `Markers` | Path to markers SVG in `drawings/assets/` | Arrowheads, endpoint symbols, line terminators |
| `Symbols` | Path to symbols SVG in `drawings/assets/` | Door tags, window tags, section marks, etc. |
| `Patterns` | Path to patterns SVG in `drawings/assets/` | Hatch patterns for materials and fills |
| `ShadingStyles` | Path to shading style definitions in `drawings/assets/` | Library of available shading presets |
| `CurrentShadingStyle` | Name of the active shading preset | Which preset from `ShadingStyles` is currently applied |
| `Metadata` | Comma-separated metadata keys | Custom title block fields |

The asset paths all resolve relative to the IFC file location, and the files themselves live in `drawings/assets/`. Dasu-specific overrides (per-IFC-class colour, lineweight, visibility) layer on top of these base styles and are stored in `.dasu/canvas.json` — only the delta, not a full replacement.

### The `.dasu/canvas.json` sidecar

A small sidecar file stores only what cannot live in either the IFC or the layout SVG. The discipline is keeping it thin: if something can live in the IFC or the layout SVG, it must not also live in the sidecar.

```json
{
  "version": "0.5.0",
  "prefs": {
    "nudgeMm": 1,
    "gridMm": 10,
    "snapEnabled": true,
    "pdfRes": 2
  },
  "objects": {
    "{IfcAnnotation.GlobalId}": {
      "_bonsaiStyleMap": {
        "IfcWall": { "stroke": "#000000", "strokeWidth": 0.5 },
        "IfcSlab": { "stroke": "#000000", "strokeWidth": 0.25 }
      },
      "_dxfLayerMap": {
        "WALLS": { "visible": true, "color": "#000000" }
      },
      "_crop": { "t": 0, "r": 0, "b": 0, "l": 0 }
    }
  }
}
```

**What lives where:**

| Content type | Where it lives |
|---|---|
| Fabric.js display state | Object caching, canvas zoom — sidecar only |
| Per-drawing deltas | Style overrides, DXF layer maps, crop bounds — keyed by `IfcAnnotation.GlobalId` |
| User preferences | Grid, snap, PDF resolution — sidecar only |
| Sheet name / revision / status | IFC (Path 2) or `_blankMeta` (Path 1) — **not** in sidecar |

Sheet names, paper sizes, positions, scales — all absent here because they live in the IFC or the layout SVG. Note the key change for Path 2: Fabric object IDs are replaced by `IfcAnnotation.GlobalId` as the per-drawing key, which is stable across sessions.

**Should `.dasu/canvas.json` be committed to git?** Yes, by default. It contains layout decisions that affect what everyone sees on the sheet — it is not the same as `.vscode/` which is truly personal. Teams can choose to gitignore it if they prefer local-only canvas state.

### Sheets are a build artefact

The `sheets/` directory is the compiled output of `SheetBuilder.build()`. Neither Dasu nor the user edits it directly. It is produced from `layouts/` on demand — either by Bonsai's "Build Sheet" operator, or triggered by Dasu via the bridge server. `sheets/` should go in `.gitignore`, the same way compiled build output does in software projects.

---

## Why this is better for collaboration

### Git-friendly by design

```
git diff layouts/A-001\ -\ Floor\ Plan.svg   ← sheet layout changed
git diff drawings/FLOOR\ PLAN.svg            ← Bonsai regenerated a drawing
git diff .dasu/canvas.json                   ← style overrides or crop changed
git diff model.ifc                           ← sheet structure or metadata changed
```

Each concern diffs independently. Changing a dimension annotation on one sheet touches only that sheet's layout SVG. Adding a drawing to another sheet touches only that sheet's file, plus `model.ifc` for the relationship. No single blob accumulates all changes.

Binary files are isolated in their own directories, making `.gitattributes` rules for [Git LFS](https://git-lfs.com) straightforward:

```
images/* filter=lfs diff=lfs merge=lfs -text
*.pdf   filter=lfs diff=lfs merge=lfs -text
*.ifc   filter=lfs diff=lfs merge=lfs -text
```

Note: `model.ifc` should also go to Git LFS for larger projects — IFC files commonly reach 50–200 MB.

### Decentralised workflow

Because the format is a plain folder of standard files, teams can:

- Use any git host (GitHub, GitLab, Forgejo, Gitea) with no special tooling
- Work on different sheets in parallel branches with clean merges
- Review sheet changes in pull requests by diffing SVG and JSON files
- Roll back to any previous state of any individual sheet
- Have Bonsai users and Dasu users collaborating on the same repo without a shared server

### No proprietary lock-in

The format is: IFC (ISO 16739), SVG (W3C), JSON (ECMA-404), and a folder. Any tool that can read these can participate. The `.dasu/canvas.json` sidecar uses no proprietary encoding — it is plain JSON that any developer can parse.

---

## What would need to change

### What already exists (in Bonsai / IfcOpenShell)

The following are not Dasu work items — they already exist in Bonsai. Dasu's job is to *consume* them, not rebuild them:

| Asset | Where it lives | What Dasu needs to do |
|---|---|---|
| SVG titleblock templates with `{{Token}}` fields | `layouts/titleblocks/` in the Bonsai project | Read and render these rather than generating its own |
| Sheet metadata schema (`IfcDocumentInformation`) | `model.ifc` | Read via bridge |
| Drawing metadata schema (`EPset_Drawing`) | `model.ifc` | Read via bridge |
| Per-drawing assets (`Stylesheet`, `Markers`, `Symbols`, `Patterns`) | `drawings/assets/` | Resolve paths and apply |
| Layout SVG format (`data-type` groups) | `layouts/*.svg` | Parse and write to |

### In Dasu — what needs to be built

The honest sequencing, with no items marked done prematurely:

| Task | Description | Stage |
|---|---|---|
| **Bridge IFC reader** | Read `IfcDocumentInformation` + `EPset_Drawing` from `model.ifc` via bridge — prerequisite for almost everything else in Path 2 | Near term |
| **Token alignment** | Replace Dasu's dot-notation tokens with Bonsai's IFC attribute names outright (see table below). Existing user titleblocks will need updating — no compatibility shim. | Near term |
| **`cmdOpenFolder`** | Add alongside existing `cmdOpen` — opens a Bonsai project folder via bridge or `showDirectoryPicker()` | Near term |
| **`.dasu/` sidecar write** | Once folder open works, write thin JSON sidecar keyed by `IfcAnnotation.GlobalId` rather than Fabric object IDs | Near term |
| **Layout SVG read** | Parse `layouts/*.svg` to reconstruct sheet canvas from Bonsai-placed drawings | Near term |
| **`dasu-overlay` write** | Write Dasu annotations into `<g data-type="dasu-overlay">` group in layout SVG | Near term |
| **`.bprint` migration tool** | Convert existing `.bprint` files to folder format via bridge | Near term |
| **`showDirectoryPicker()`** | Chrome/Edge native directory access without bridge | Medium term |
| **IFC write-back** | Write sheet positions and paper size back to `model.ifc` via bridge | Later |

#### Token mapping — Dasu → Bonsai

Bonsai builds its token data directly from IFC attribute names via `get_info()`. Sheet fields are prefixed with `Sheet`. The full replacement:

| Current Dasu token | Bonsai token | IFC source |
|---|---|---|
| `{{sheet.name}}` | `{{SheetName}}` | `IfcDocumentInformation.Name` |
| `{{sheet.id}}` | `{{SheetIdentification}}` | `IfcDocumentInformation.Identification` |
| `{{description}}` | `{{SheetDescription}}` | `IfcDocumentInformation.Description` |
| `{{revision}}` | `{{SheetRevision}}` | `IfcDocumentInformation.Revision` |
| `{{sheet.status}}` | `{{SheetStatus}}` | `IfcDocumentInformation.Status` |
| `{{issue.date}}` | `{{SheetLastRevisionTime}}` | `IfcDocumentInformation.LastRevisionTime` |
| `{{purpose}}` | `{{SheetPurpose}}` | `IfcDocumentInformation.Purpose` |
| `{{sheet.scale}}` | `{{Scale}}` | `EPset_Drawing.HumanScale` (computed) |
| `{{drawn.by}}` | `{{DrawnBy}}` | Custom pset (no IFC equivalent) |
| `{{checked.by}}` | `{{CheckedBy}}` | Custom pset (no IFC equivalent) |
| `{{discipline}}` | `{{Discipline}}` | Custom pset (no IFC equivalent) |
| `{{project.name}}` | `{{ProjectName}}` | `IfcProject.Name` or `IfcSite.Name` |
| `{{project.address}}` | `{{ProjectAddress}}` | `IfcSite` address (no direct IFC attribute) |
| `{{date}}` | `{{Date}}` | Computed at render time |
| `{{year}}` | `{{Year}}` | Computed at render time |

Tokens with no IFC equivalent (`DrawnBy`, `CheckedBy`, `Discipline`, `ProjectAddress`) would be sourced from a custom property set or from Dasu's own sheet metadata — to be confirmed with the Bonsai team.

#### Further alignments with Bonsai conventions

Beyond token names, this proposal adopts several other Bonsai conventions outright:

**Sheet status values** — Bonsai stores status in `EPset_Status.Status` as a free-text field on `IfcDocumentInformation`. There is no fixed Bonsai enum. Dasu proposes adopting the following common construction industry values (aligned with IFC convention and industry practice) and storing them in the same pset:

| Status | Meaning |
|---|---|
| `DRAFT` | Work in progress |
| `FOR REVIEW` | Issued internally for review |
| `FOR APPROVAL` | Submitted for client/authority approval |
| `FOR CONSTRUCTION` | Issued to contractor |
| `FOR INFORMATION` | Reference only |
| `AS-BUILT` | Reflecting constructed works |
| `SUPERSEDED` | Replaced by a later revision |

**View title template** — Dasu will adopt Bonsai's `view-title.svg` directly from `layouts/assets/` rather than generating its own. The template uses three tokens: `{{Identification}}`, `{{Name}}`, `{{Scale}}`. No Dasu-specific tokens are added to the view title.

**Paper size from titleblock SVG** — Bonsai does not store paper size as a separate IFC property. Sheet dimensions are inferred from the titleblock SVG's `width` and `height` attributes. Dasu will do the same — paper size is a property of the titleblock file, not of the sheet record.

**Target view vocabulary** — Dasu will use Bonsai's `EPset_Drawing.TargetView` values verbatim for labelling and filtering drawings:

| Value | Label |
|---|---|
| `PLAN_VIEW` | Plan |
| `SECTION_VIEW` | Section |
| `ELEVATION_VIEW` | Elevation |
| `REFLECTED_PLAN_VIEW` | RCP |
| `MODEL_VIEW` | Model |

**Titleblock token set** — Bonsai's titleblock templates (A1, A2, A3) use `{{Name}}`, `{{Identification}}`, and `{{Revision}}` as their core tokens, rendered via pystache from `IfcDocumentInformation.get_info()`. Dasu will render these templates using the same data source and the same token names.

### In Bonsai

Potentially nothing, or very little. Bonsai already owns `layouts/`, `drawings/`, `sheets/`, and `model.ifc`. The proposal asks Dasu to conform to Bonsai's conventions, not the other way around.

One possible addition worth raising with the Bonsai team: formally document `data-type="dasu-overlay"` as a reserved-but-ignored group name in the layout SVG schema, so future tools know to preserve it rather than strip it. One line in Bonsai's documentation would suffice.

### Open questions for the community

1. **`data-type="dasu-overlay"` formalisation** — This proposal assumes `dasu-overlay` will be formally documented as a reserved, tool-agnostic group name in the Bonsai layout SVG schema. Is the Bonsai team agreeable to this? A one-line addition to the schema documentation would be sufficient.

2. **Status values** — Since `EPset_Status.Status` is free-text in IFC, there is no canonical list to adopt. The values proposed above reflect common industry practice — are they the right set? Are there values missing or that should be renamed?

3. **IFC read in the browser** — Reading `model.ifc` from a browser requires an IfcOpenShell WASM build or delegating to the bridge. The bridge is the pragmatic path for now. Is there appetite in the community for a lightweight browser-side IFC reader focused on document/sheet metadata only?

4. **The bridge server's role** — In Path 2, the bridge becomes the primary I/O layer (file read/write, IFC parsing, sheet building). Is this the right direction, or should the browser do more directly via the File System Access API for users who have it available?

5. **Path 3 — clarification needed, assumed later phase** — Nigel's response refers to Path 3 as "MoneyBIM IFC import", but this term doesn't correspond to any known tool or product we could identify. Our best reading is that it describes a workflow where a user imports an IFC file to extract drawing/sheet metadata without needing a full Bonsai/Blender setup — using IFC as a read-only data source to populate a `.bprint` project. Parsing IFC independently of the bridge would require either an IfcOpenShell WASM build or a lightweight IFC reader, which is a meaningful technical dependency. Our assumption is that this is a later phase of implementation, tackled after Path 1 and Path 2 are solid. If the community sees it differently — or if it is simpler to implement than we think — please correct us.

---

## Summary

| | Path 1 (current) | Path 2 (proposed) | Path 3 |
|---|---|---|---|
| Primary format | `.bprint` (single JSON blob) | Project folder (IFC + SVGs + sidecar) | `.bprint` output |
| Sheet manifest | Dasu meta | IFC (single source of truth) | IFC read-only |
| Layout files | Fabric.js JSON | Bonsai layout SVG format | n/a |
| Git-friendliness | Poor | Good (per-sheet diffs, LFS for binaries) | Poor |
| Bonsai interop | Bridge only (live push) | Shared folder (continuous) | IFC import |
| Bridge required | No | Yes (filesystem proxy) | Optional |
| Portable sharing | `.bprint` file | Zip the folder, or `git archive` | `.bprint` file |
| New standards required | None | None (IFC, SVG, JSON) | None |

This is not a proposal to build something new. It is a proposal for Dasu to grow a second, Bonsai-native mode — built entirely from standards that already exist — while keeping the standalone `.bprint` workflow intact for users who need it.

Feedback and questions welcome.

---

*Dasu is free and open-source. Source: [github.com/openingdesign/dasu](https://github.com/openingdesign/dasu)*


