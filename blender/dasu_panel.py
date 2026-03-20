"""
dasu_panel.py  —  Blender / Bonsai BIM N-panel: Send to Dasu
=============================================================
Run in Blender Text Editor (click Run Script), or install as an addon.

Adds a "Dasu" panel to the N-panel (press N in the 3D viewport, look for
the "Dasu" tab).

Workflow:
  1. In Bonsai BIM, set up your drawing as normal (activate drawing, etc.)
  2. In the Dasu panel, press "Send Active Drawing to Dasu"
  3. Bonsai generates the SVG via bim.create_drawing
  4. This script reads the SVG file + EPset_Drawing metadata
  5. POSTs everything to the Dasu bridge server on localhost:7821
  6. Dasu picks it up automatically and places it on the active sheet
"""

bl_info = {
    "name": "Dasu Bridge",
    "author": "4nigel",
    "version": (0, 1, 0),
    "blender": (4, 0, 0),
    "location": "View3D > N-Panel > Dasu",
    "description": "Send Bonsai BIM drawings to the Dasu sheet layout tool",
    "category": "Import-Export",
}

import bpy
import json
import os
import math
import urllib.request
import urllib.error
from bpy.props import IntProperty, StringProperty, BoolProperty


# ── Settings ──────────────────────────────────────────────────────────────────
BRIDGE_URL = 'http://localhost:7821/receive'


# ── Helpers ───────────────────────────────────────────────────────────────────
def _get_ifc():
    """Return the loaded IFC file, or None."""
    try:
        import bonsai.bim.ifc as ifc_store
        ifc = ifc_store.IfcStore.get_file()
        # Attach path if missing — try BIM properties and blend file location
        if ifc and not getattr(ifc, 'path', None):
            # Try BIM document properties
            try:
                path = bpy.context.scene.BIMProperties.ifc_file
                if path and os.path.isfile(bpy.path.abspath(path)):
                    ifc.path = bpy.path.abspath(path)
            except Exception:
                pass
            # Try blend file directory as last resort
            if not getattr(ifc, 'path', None) and bpy.data.filepath:
                ifc.path = os.path.dirname(bpy.path.abspath(bpy.data.filepath))
        return ifc
    except Exception:
        return None


def _clean_camera_name(camera_obj):
    """
    Return candidate SVG base names from the camera object.
    Bonsai camera names are like 'IfcAnnotation/0_GRDFLOOR PLAN'.
    The SVG is usually named after the part after the last '/'.
    """
    names = []
    if not camera_obj:
        return names
    raw = camera_obj.name
    # Part after last slash — most common: 'IfcAnnotation/DrawingName' → 'DrawingName'
    if '/' in raw:
        names.append(raw.split('/')[-1])
    # Full name with slash replaced
    names.append(raw.replace('/', '_').replace('\\', '_'))
    # Full name as-is (in case OS allows it)
    names.append(raw)
    # Also strip common IFC class prefixes
    for prefix in ('IfcAnnotation', 'IfcBuildingElement', 'Ifc'):
        clean = raw.replace(prefix + '/', '').replace(prefix, '').strip('_ ')
        if clean and clean not in names:
            names.append(clean)
    return names


def _get_drawing_tool():
    for attempt in [
        lambda: __import__('bonsai.bim.tool', fromlist=['Drawing']).Drawing,
        lambda: __import__('bonsai.bim', fromlist=['tool']).tool.Drawing,
        lambda: __import__('blenderbim.bim.tool', fromlist=['Drawing']).Drawing,
    ]:
        try:
            t = attempt()
            if t:
                return t
        except Exception:
            pass
    return None


def _get_ifcopenshell():
    try:
        import ifcopenshell
        import ifcopenshell.util.element
        import ifcopenshell.util.unit
        return ifcopenshell
    except Exception:
        return None


def _get_active_drawing_camera():
    """Return the active drawing camera object, or None."""
    return bpy.context.scene.camera


def _get_drawing_entity(camera_obj):
    """Get the IfcAnnotation entity for a camera object."""
    if not camera_obj:
        return None
    for attempt in [
        lambda: __import__('bonsai.bim.tool', fromlist=['Ifc']).Ifc.get_entity(camera_obj),
        lambda: __import__('bonsai.bim', fromlist=['tool']).tool.Ifc.get_entity(camera_obj),
        lambda: __import__('blenderbim.bim.tool', fromlist=['Ifc']).Ifc.get_entity(camera_obj),
    ]:
        try:
            e = attempt()
            if e:
                return e
        except Exception:
            pass
    return None


def _read_epset_drawing(ifc, camera_entity):
    """
    Read EPset_Drawing pset from the camera entity.
    Returns dict with: Scale, HumanScale, TargetView, HasAnnotations, etc.
    """
    ifcos = _get_ifcopenshell()
    if not ifcos or not camera_entity:
        return {}
    try:
        pset = ifcos.util.element.get_pset(camera_entity, 'EPset_Drawing')
        return pset or {}
    except Exception:
        return {}


def _get_bonsai_drawings_dir():
    """
    Read the Default Drawings Directory from Bonsai preferences.
    Returns absolute path, or None.
    """
    try:
        prefs = bpy.context.preferences.addons.get('bonsai')
        if not prefs:
            prefs = bpy.context.preferences.addons.get('blenderbim')
        if not prefs:
            return None
        bprefs = prefs.preferences
        # The pref is stored as a relative path like 'drawings\'
        # We need to resolve it relative to the IFC file
        drawings_rel = getattr(bprefs, 'drawings_dir',
                       getattr(bprefs, 'default_drawings_dir', None))
        if drawings_rel is None:
            # Try BIM document props
            try:
                doc_props = bpy.context.scene.DocProperties
                drawings_rel = getattr(doc_props, 'drawings_dir', None)
            except Exception:
                pass
        if drawings_rel:
            ifc = _get_ifc()
            if ifc and hasattr(ifc, 'path') and ifc.path:
                ifc_dir = os.path.dirname(os.path.abspath(ifc.path))
                return os.path.normpath(os.path.join(ifc_dir, drawings_rel))
    except Exception:
        pass
    return None


def _get_svg_path(drawing_tool, camera_entity):
    """
    Find the SVG output path for the active drawing.
    Tries every known Bonsai API and filesystem strategy.
    Returns the path string if found and file exists, else None.
    """
    ifc = _get_ifc()
    candidates = []

    # ── Strategy 00: Manual drawings directory set in the Dasu panel ──────────
    manual_dir = getattr(bpy.context.scene, 'dasu_drawings_dir', '').strip()
    if manual_dir and os.path.isdir(manual_dir):
        cam_obj    = bpy.context.scene.camera
        cam_names  = _clean_camera_name(cam_obj)

        # Try each cleaned name as an SVG filename
        for name in cam_names:
            candidates.append(os.path.join(manual_dir, name + '.svg'))

        # Also try entity name/description if available
        if camera_entity:
            for attr in ('Name', 'Description'):
                val = getattr(camera_entity, attr, None)
                if val:
                    candidates.append(os.path.join(manual_dir, val + '.svg'))
            guid = getattr(camera_entity, 'GlobalId', None)
            if guid:
                candidates.append(os.path.join(manual_dir, guid + '.svg'))

        # Scan the folder — pick any SVG that contains any of our name candidates
        try:
            for f in sorted(os.listdir(manual_dir)):
                if not f.lower().endswith('.svg'):
                    continue
                fbase = f[:-4].lower()
                for name in cam_names:
                    if name.lower() in fbase or fbase in name.lower():
                        candidates.append(os.path.join(manual_dir, f))
                        break
        except Exception:
            pass
    # This is the most reliable — reads exactly what Bonsai is configured to use
    bonsai_drawings_dir = _get_bonsai_drawings_dir()
    if bonsai_drawings_dir and os.path.isdir(bonsai_drawings_dir) and camera_entity:
        for attr in ('Name', 'Description'):
            val = getattr(camera_entity, attr, None)
            if val:
                p = os.path.join(bonsai_drawings_dir, val + '.svg')
                candidates.append(p)
        # Also try GlobalId — Bonsai sometimes uses GUID as filename
        guid = getattr(camera_entity, 'GlobalId', None)
        if guid:
            candidates.append(os.path.join(bonsai_drawings_dir, guid + '.svg'))
        # Scan the directory for any SVG matching the camera name
        cam_obj = bpy.context.scene.camera
        if cam_obj:
            for f in os.listdir(bonsai_drawings_dir):
                if f.lower().endswith('.svg') and cam_obj.name.lower() in f.lower():
                    candidates.append(os.path.join(bonsai_drawings_dir, f))

    # ── Strategy 1: Bonsai drawing tool API (varies by version) ──────────────
    if drawing_tool and camera_entity:
        for method_args in [
            ('get_document_uri', (camera_entity, 'LAYOUT')),
            ('get_document_uri', (camera_entity,)),
            ('get_svg_uri',      (camera_entity,)),
        ]:
            try:
                fn = getattr(drawing_tool, method_args[0], None)
                if fn:
                    p = fn(*method_args[1])
                    if p:
                        candidates.append(str(p))
            except Exception:
                pass

    # ── Strategy 2: IfcDocumentReference linked to the camera entity ──────────
    # Bonsai links the SVG path via an IfcRelAssociatesDocument relationship.
    if ifc and camera_entity:
        try:
            ifcos = _get_ifcopenshell()
            if ifcos:
                import ifcopenshell.util.element as ifc_el
                # Walk relationships looking for document references
                for rel in getattr(camera_entity, 'HasAssociations', []):
                    if rel.is_a('IfcRelAssociatesDocument'):
                        doc = rel.RelatingDocument
                        if doc.is_a('IfcDocumentReference'):
                            loc = getattr(doc, 'Location', None) or getattr(doc, 'Identification', None)
                            if loc and str(loc).lower().endswith('.svg'):
                                candidates.append(str(loc))
        except Exception:
            pass

    # ── Strategy 3: filesystem search in expected locations ───────────────────
    if ifc and hasattr(ifc, 'path') and ifc.path:
        ifc_dir  = os.path.dirname(os.path.abspath(ifc.path))
        ifc_name = os.path.splitext(os.path.basename(ifc.path))[0]

        # Drawing name candidates
        draw_names = []
        if camera_entity:
            if hasattr(camera_entity, 'Name') and camera_entity.Name:
                draw_names.append(camera_entity.Name)
            if hasattr(camera_entity, 'Description') and camera_entity.Description:
                draw_names.append(camera_entity.Description)

        # Also try the active camera object name
        cam_obj = bpy.context.scene.camera
        if cam_obj:
            draw_names.append(cam_obj.name)

        # Common Bonsai output folder structures
        search_dirs = [
            os.path.join(ifc_dir, 'drawings'),
            os.path.join(ifc_dir, ifc_name + '-drawings'),
            os.path.join(ifc_dir, ifc_name, 'drawings'),
            os.path.join(ifc_dir, 'output', 'drawings'),
            ifc_dir,
        ]

        for d in search_dirs:
            if not os.path.isdir(d):
                continue
            for name in draw_names:
                p = os.path.join(d, name + '.svg')
                if os.path.isfile(p):
                    candidates.append(p)
            # Also scan the folder for any SVG that matches camera name
            try:
                for f in os.listdir(d):
                    if f.lower().endswith('.svg'):
                        for name in draw_names:
                            if name.lower() in f.lower():
                                candidates.append(os.path.join(d, f))
            except Exception:
                pass

    # ── Pick the first candidate that actually exists on disk ─────────────────
    for c in candidates:
        if c and os.path.isfile(c):
            return c

    # ── Last resort: return the most likely path even if not yet created ───────
    # (create_drawing may not have run yet; caller will check)
    if candidates:
        return candidates[0]   # caller will report it doesn't exist yet

    return None


def _unit_scale_to_mm(ifc):
    """Return scale factor from IFC internal units to mm."""
    ifcos = _get_ifcopenshell()
    if not ifcos or not ifc:
        return 1000.0   # assume metres
    try:
        scale = ifcos.util.unit.calculate_unit_scale(ifc)
        # scale is multiplier to metres; to mm multiply by 1000
        return scale * 1000.0
    except Exception:
        return 1000.0


def _parse_scale(human_scale):
    """
    Parse a human scale string like '1:50' or '1/50' into denominator int.
    Returns int denominator, e.g. 50.
    """
    if not human_scale:
        return 100
    s = str(human_scale).strip()
    for sep in [':', '/']:
        if sep in s:
            parts = s.split(sep)
            try:
                return int(float(parts[1].strip()))
            except Exception:
                pass
    return 100


def _get_camera_extents_mm(camera_obj, unit_scale_to_mm):
    """
    Return (width_mm, height_mm) of what the drawing camera captures.
    Uses the camera's orthographic scale and sensor size.
    """
    cam = camera_obj.data
    if cam.type != 'ORTHO':
        return None, None
    # ortho_scale is the width in Blender units (= IFC metres if scale=1)
    ortho_m = cam.ortho_scale
    # Convert to mm: Blender units = metres for Bonsai default scenes
    ortho_mm = ortho_m * 1000.0   # metres to mm

    # Aspect ratio from sensor
    aspect = cam.sensor_width / cam.sensor_height if cam.sensor_height else 1.0
    # Bonsai drawing cameras: sensor is the paper dimensions in mm at model scale
    # Actually easier: use the viewbox we'll find in the SVG
    return ortho_mm, ortho_mm / aspect


# ── Operator: Send active drawing ─────────────────────────────────────────────
class DASU_OT_send_drawing(bpy.types.Operator):
    bl_idname  = 'dasu.send_drawing'
    bl_label   = 'Send Active Drawing to Dasu'
    bl_options = {'REGISTER'}

    def execute(self, context):
        # ── 1. Get drawing camera ─────────────────────────────────────────────
        camera = _get_active_drawing_camera()
        if not camera or not camera.data or camera.data.type != 'ORTHO':
            self.report({'ERROR'}, 'No active orthographic drawing camera found. '
                        'Activate a Bonsai drawing first (bim.activate_drawing).')
            return {'CANCELLED'}

        ifc            = _get_ifc()
        drawing_tool   = _get_drawing_tool()
        camera_entity  = _get_drawing_entity(camera)
        epset          = _read_epset_drawing(ifc, camera_entity)

        # ── 2. Run bim.create_drawing to regenerate SVG ───────────────────────
        try:
            self.report({'INFO'}, 'Running bim.create_drawing ...')
            bpy.ops.bim.create_drawing()
        except Exception as e:
            err = str(e)
            # Known non-fatal Bonsai bug: numpy shape mismatch in decoration.py
            # The SVG is still written — safe to continue
            if 'shapes' in err and 'not aligned' in err:
                print('  Dasu: ignoring known Bonsai decoration.py numpy bug (non-fatal)')
            else:
                self.report({'WARNING'}, f'create_drawing warning: {err} — will try to send existing SVG.')

        # ── 3. Find the SVG file ──────────────────────────────────────────────
        # Check manual override first
        svg_path = None
        override = getattr(context.scene, 'dasu_svg_override', '')
        if override and os.path.isfile(override):
            svg_path = override
            print(f'  Dasu: using manual SVG override: {svg_path}')
        else:
            if drawing_tool and camera_entity:
                svg_path = _get_svg_path(drawing_tool, camera_entity)

        if not svg_path or not os.path.isfile(svg_path):
            # Print diagnostic info to Blender console
            print('\n  Dasu: SVG not found. Searched:')
            print(f'    Bonsai drawings dir: {_get_bonsai_drawings_dir()}')
            ifc = _get_ifc()
            if ifc and hasattr(ifc, 'path'):
                print(f'    IFC path: {ifc.path}')
                ifc_dir = os.path.dirname(os.path.abspath(ifc.path))
                drawings_dir = os.path.join(ifc_dir, 'drawings')
                print(f'    Drawings dir exists: {os.path.isdir(drawings_dir)}')
                if os.path.isdir(drawings_dir):
                    files = os.listdir(drawings_dir)
                    print(f'    Files in drawings/: {files[:10]}')
            if camera_entity:
                print(f'    Camera entity Name: {getattr(camera_entity, "Name", "?")}')
            print(f'    Resolved path: {svg_path}\n')

            self.report({'ERROR'},
                f'SVG not found at: {svg_path or "None"}\n\n'
                f'Check the Blender System Console (Window → Toggle System Console) '
                f'for a diagnostic listing of what was searched.\n\n'
                f'Make sure bim.create_drawing has completed successfully.')
            return {'CANCELLED'}

        with open(svg_path, 'r', encoding='utf-8') as f:
            svg_content = f.read()

        # ── 4. Extract metadata ───────────────────────────────────────────────
        human_scale   = epset.get('HumanScale', epset.get('Scale', '1:100'))
        scale_denom   = _parse_scale(human_scale)
        target_view   = epset.get('TargetView', 'PLAN_VIEW')
        drawing_name  = camera.name

        # Try to get camera entity name
        if camera_entity and hasattr(camera_entity, 'Name'):
            drawing_name = camera_entity.Name or drawing_name

        # Get IFC project name
        project_name = ''
        if ifc:
            try:
                projects = ifc.by_type('IfcProject')
                if projects:
                    project_name = projects[0].Name or ''
            except Exception:
                pass

        ifc_path = ifc.path if ifc and hasattr(ifc, 'path') else ''

        # Paper extents from camera (best effort)
        unit_scale = _unit_scale_to_mm(ifc)
        w_mm, h_mm = _get_camera_extents_mm(camera, unit_scale)
        paper_mm   = {'w': round(w_mm, 1), 'h': round(h_mm, 1)} if w_mm else None

        # ── 5. Build payload ──────────────────────────────────────────────────
        payload = {
            'name':        drawing_name,
            'drawingName': drawing_name,
            'scale':       str(human_scale) if human_scale else '1:100',
            'scaleDenom':  scale_denom,
            'targetView':  target_view,
            'paperMm':     paper_mm,
            'ifcPath':     ifc_path,
            'projectName': project_name,
            'svgPath':     svg_path,    # for reference only
            'svg':         svg_content,
        }

        # ── 6. POST to bridge ─────────────────────────────────────────────────
        port = context.scene.dasu_bridge_port if hasattr(context.scene, 'dasu_bridge_port') else 7821
        url  = f'http://localhost:{port}/receive'

        try:
            body    = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            req     = urllib.request.Request(
                url,
                data    = body,
                headers = {'Content-Type': 'application/json; charset=utf-8'},
                method  = 'POST',
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                if result.get('ok'):
                    self.report({'INFO'},
                        f'✓ Sent "{drawing_name}" (1:{scale_denom}) to Dasu on port {port}')
                    return {'FINISHED'}
                else:
                    self.report({'ERROR'}, f'Bridge returned error: {result}')
                    return {'CANCELLED'}

        except urllib.error.URLError as e:
            self.report({'ERROR'},
                f'Could not reach Dasu bridge on port {port}.\n'
                f'Make sure dasu_bridge.py is running.\n'
                f'Error: {e.reason}')
            return {'CANCELLED'}
        except Exception as e:
            self.report({'ERROR'}, f'Send failed: {e}')
            return {'CANCELLED'}


# ── Operator: Diagnose — dumps everything to console ─────────────────────────
class DASU_OT_diagnose(bpy.types.Operator):
    bl_idname  = 'dasu.diagnose'
    bl_label   = 'Diagnose (see System Console)'
    bl_options = {'REGISTER'}

    def execute(self, context):
        print('\n' + '='*60)
        print('  DASU DIAGNOSTIC')
        print('='*60)

        # IFC
        ifc = _get_ifc()
        print(f'\n  IFC loaded: {ifc is not None}')
        if ifc:
            print(f'  IFC path:   {getattr(ifc, "path", "no path attr")}')

        # Camera
        camera = bpy.context.scene.camera
        print(f'\n  Scene camera: {camera}')
        if camera:
            print(f'  Camera name: {camera.name}')
            print(f'  Camera type: {camera.data.type if camera.data else "no data"}')

        # Camera entity
        camera_entity = _get_drawing_entity(camera) if camera else None
        print(f'\n  IFC entity: {camera_entity}')
        if camera_entity:
            print(f'  Entity type:       {camera_entity.is_a()}')
            print(f'  Entity Name:       {getattr(camera_entity, "Name", "?")}')
            print(f'  Entity GlobalId:   {getattr(camera_entity, "GlobalId", "?")}')
            print(f'  Entity Description:{getattr(camera_entity, "Description", "?")}')

        # EPset
        epset = _read_epset_drawing(ifc, camera_entity)
        print(f'\n  EPset_Drawing: {epset}')

        # Bonsai drawing tool
        drawing_tool = _get_drawing_tool()
        print(f'\n  Drawing tool available: {drawing_tool is not None}')
        if drawing_tool:
            methods = [m for m in dir(drawing_tool) if 'uri' in m.lower() or 'path' in m.lower() or 'svg' in m.lower()]
            print(f'  Relevant methods: {methods}')

        # Bonsai prefs drawings dir
        bonsai_dir = _get_bonsai_drawings_dir()
        print(f'\n  Bonsai drawings dir: {bonsai_dir}')
        if bonsai_dir and os.path.isdir(bonsai_dir):
            files = sorted(os.listdir(bonsai_dir))
            print(f'  Files in drawings dir ({len(files)}):')
            for f in files[:20]:
                print(f'    {f}')
        elif bonsai_dir:
            print(f'  (directory does not exist)')

        # Bonsai addon prefs - dump all attributes
        try:
            prefs = bpy.context.preferences.addons.get('bonsai') or \
                    bpy.context.preferences.addons.get('blenderbim')
            if prefs:
                bprefs = prefs.preferences
                dir_attrs = [a for a in dir(bprefs) if 'dir' in a.lower() or 'path' in a.lower() or 'drawing' in a.lower()]
                print(f'\n  Bonsai pref attributes with dir/path/drawing:')
                for a in dir_attrs:
                    try:
                        print(f'    {a} = {getattr(bprefs, a)}')
                    except Exception:
                        pass
        except Exception as e:
            print(f'  Prefs error: {e}')

        # IFC file structure near the file
        if ifc and getattr(ifc, 'path', None):
            ifc_dir = os.path.dirname(os.path.abspath(ifc.path))
            print(f'\n  IFC dir contents:')
            try:
                for item in sorted(os.listdir(ifc_dir)):
                    full = os.path.join(ifc_dir, item)
                    marker = '/' if os.path.isdir(full) else ''
                    print(f'    {item}{marker}')
            except Exception as e:
                print(f'    Error: {e}')

        print('\n' + '='*60 + '\n')
        self.report({'INFO'}, 'Diagnostic written to System Console (Window → Toggle System Console)')
        return {'FINISHED'}


# ── Operator: Browse for SVG manually ────────────────────────────────────────
class DASU_OT_browse_svg(bpy.types.Operator):
    bl_idname  = 'dasu.browse_svg'
    bl_label   = 'Browse for SVG…'
    bl_options = {'REGISTER'}

    filepath: bpy.props.StringProperty(subtype='FILE_PATH')
    filter_glob: bpy.props.StringProperty(default='*.svg', options={'HIDDEN'})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        context.scene.dasu_svg_override = self.filepath
        self.report({'INFO'}, f'SVG set to: {self.filepath}')
        return {'FINISHED'}


class DASU_OT_ping(bpy.types.Operator):
    bl_idname  = 'dasu.ping_bridge'
    bl_label   = 'Test Connection'
    bl_options = {'REGISTER'}

    def execute(self, context):
        port = context.scene.dasu_bridge_port if hasattr(context.scene, 'dasu_bridge_port') else 7821
        try:
            url = f'http://localhost:{port}/status'
            with urllib.request.urlopen(url, timeout=3) as resp:
                data = json.loads(resp.read())
                self.report({'INFO'},
                    f'✓ Bridge OK on port {port}  '
                    f'(drawings stored: {data.get("stored", "?")})')
        except Exception as e:
            self.report({'ERROR'}, f'Bridge not reachable on port {port}: {e}')
        return {'FINISHED'}


# ── Scene properties ──────────────────────────────────────────────────────────
def _register_props():
    bpy.types.Scene.dasu_bridge_port = IntProperty(
        name        = 'Bridge Port',
        description = 'Port the Dasu bridge server is listening on',
        default     = 7821,
        min         = 1024,
        max         = 65535,
    )
    bpy.types.Scene.dasu_svg_override = StringProperty(
        name        = 'SVG Override',
        description = 'Manually specify the SVG path (overrides auto-detection)',
        default     = '',
        subtype     = 'FILE_PATH',
    )
    bpy.types.Scene.dasu_drawings_dir = StringProperty(
        name        = 'Drawings Directory',
        description = 'Path to the Bonsai drawings output folder (e.g. C:\\Projects\\house\\drawings)',
        default     = '',
        subtype     = 'DIR_PATH',
    )


def _unregister_props():
    try: del bpy.types.Scene.dasu_bridge_port
    except Exception: pass
    try: del bpy.types.Scene.dasu_svg_override
    except Exception: pass
    try: del bpy.types.Scene.dasu_drawings_dir
    except Exception: pass


# ── N-Panel ───────────────────────────────────────────────────────────────────
class DASU_PT_panel(bpy.types.Panel):
    bl_label       = 'Dasu Bridge'
    bl_idname      = 'DASU_PT_panel'
    bl_space_type  = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category    = 'Dasu'

    def draw(self, context):
        layout = self.layout
        scene  = context.scene

        # ── Status row ────────────────────────────────────────────────────────
        box = layout.box()
        row = box.row()
        row.label(text='Dasu.print Bridge', icon='NETWORK_DRIVE')
        row = box.row()
        row.prop(scene, 'dasu_bridge_port', text='Port')
        row.operator('dasu.ping_bridge', text='', icon='RADIOBUT_ON')

        layout.separator()

        # ── Active drawing info ───────────────────────────────────────────────
        camera = scene.camera
        if camera and camera.data and camera.data.type == 'ORTHO':
            box = layout.box()
            box.label(text='Active Drawing:', icon='CAMERA_DATA')
            box.label(text=camera.name)
            ifc           = _get_ifc()
            camera_entity = _get_drawing_entity(camera)
            epset         = _read_epset_drawing(ifc, camera_entity)
            if epset:
                scale = epset.get('HumanScale', epset.get('Scale', '—'))
                view  = epset.get('TargetView', '—')
                box.label(text=f'Scale:  {scale}')
                box.label(text=f'View:   {view}')
        else:
            box = layout.box()
            box.label(text='No active drawing camera', icon='ERROR')
            box.label(text='Use bim.activate_drawing first')

        layout.separator()

        # ── Drawings directory ────────────────────────────────────────────────
        box = layout.box()
        box.label(text='Bonsai Drawings Folder:', icon='FILE_FOLDER')
        box.prop(scene, 'dasu_drawings_dir', text='')
        if scene.dasu_drawings_dir:
            exists = os.path.isdir(scene.dasu_drawings_dir)
            if exists:
                try:
                    svgs = [f for f in os.listdir(scene.dasu_drawings_dir) if f.endswith('.svg')]
                    box.label(text=f'✓ Found  ({len(svgs)} SVG files)', icon='CHECKMARK')
                except Exception:
                    box.label(text='✓ Folder exists', icon='CHECKMARK')
            else:
                box.label(text='✗ Folder not found', icon='ERROR')
        else:
            box.label(text='Set this to your drawings\\ folder', icon='INFO')

        layout.separator()

        # ── SVG override (specific file) ──────────────────────────────────────
        box = layout.box()
        box.label(text='Single SVG Override (optional):', icon='FILE_IMAGE')
        row = box.row(align=True)
        row.prop(scene, 'dasu_svg_override', text='')
        row.operator('dasu.browse_svg', text='', icon='FILE_FOLDER')
        if scene.dasu_svg_override:
            exists = os.path.isfile(scene.dasu_svg_override)
            box.label(
                text = '✓ File found' if exists else '✗ File not found',
                icon = 'CHECKMARK' if exists else 'ERROR',
            )
        else:
            box.label(text='Leave blank to use folder + drawing name', icon='INFO')

        layout.separator()

        # ── Send button ───────────────────────────────────────────────────────
        col = layout.column()
        col.scale_y = 1.6
        col.operator('dasu.send_drawing', text='Send to Dasu  ↗', icon='EXPORT')

        layout.separator()

        # ── Diagnostic button ─────────────────────────────────────────────────
        layout.operator('dasu.diagnose', text='Diagnose (→ System Console)', icon='CONSOLE')
        layout.label(text='Window → Toggle System Console', icon='INFO')


# ── Registration ───────────────────────────────────────────────────────────────
CLASSES = [
    DASU_OT_send_drawing,
    DASU_OT_ping,
    DASU_OT_diagnose,
    DASU_OT_browse_svg,
    DASU_PT_panel,
]

def register():
    for cls in CLASSES:
        bpy.utils.register_class(cls)
    _register_props()
    print('\n  Dasu panel registered.  Press N in the 3D viewport → Dasu tab.\n')


def unregister():
    for cls in reversed(CLASSES):
        bpy.utils.unregister_class(cls)
    _unregister_props()


if __name__ == '__main__':
    register()
