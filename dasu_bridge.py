"""
dasu_bridge.py  —  Dasu sheet layout tool local bridge server
=============================================================
Run with:  python dasu_bridge.py
Listens on localhost:7821

Endpoints:
  POST /receive   — Blender sends drawing payload (JSON)
  GET  /poll      — Dasu browser app fetches pending drawings
  GET  /status    — health check
  GET  /          — info page

No external dependencies — pure Python 3.6+ stdlib.
"""

import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse

# ── State ─────────────────────────────────────────────────────────────────────
_lock     = threading.Lock()
_drawings = []      # list of drawing dicts, newest last
_max_keep = 20      # keep last N drawings in memory

PORT = 7821
HOST = 'localhost'


# ── Request handler ───────────────────────────────────────────────────────────
class BridgeHandler(BaseHTTPRequestHandler):

    def log_message(self, fmt, *args):
        ts = time.strftime('%H:%M:%S')
        print(f'  [{ts}] {fmt % args}')

    def _cors(self):
        # Allow the Dasu browser app (any localhost origin) to fetch
        self.send_header('Access-Control-Allow-Origin',  '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')

    def do_OPTIONS(self):
        self.send_response(200)
        self._cors()
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == '/poll':
            self._poll()
        elif path == '/status':
            self._status()
        else:
            self._info()

    def do_POST(self):
        path = urlparse(self.path).path
        if path == '/receive':
            self._receive()
        elif path == '/convert-dxf':
            self._convert_dxf()
        else:
            self._json_response(404, {'error': 'Not found'})

    # ── /receive ──────────────────────────────────────────────────────────────
    def _receive(self):
        try:
            length  = int(self.headers.get('Content-Length', 0))
            raw     = self.rfile.read(length)
            payload = json.loads(raw.decode('utf-8'))

            # Required fields
            if 'svg' not in payload:
                self._json_response(400, {'error': 'Missing svg field'})
                return

            drawing = {
                'id':          f'{int(time.time() * 1000)}',
                'receivedAt':  time.strftime('%Y-%m-%dT%H:%M:%S'),
                'name':        payload.get('name',        'Untitled'),
                'drawingName': payload.get('drawingName', ''),
                'scale':       payload.get('scale',       '1:100'),
                'scaleDenom':  payload.get('scaleDenom',  100),
                'paperMm':     payload.get('paperMm',     None),   # {w, h}
                'ifcPath':     payload.get('ifcPath',     ''),
                'projectName': payload.get('projectName', ''),
                'targetView':  payload.get('targetView',  'PLAN_VIEW'),
                'svg':         payload['svg'],
            }

            with _lock:
                _drawings.append(drawing)
                # Keep only the last N
                while len(_drawings) > _max_keep:
                    _drawings.pop(0)

            print(f'\n  ✓  Received: {drawing["name"]}  scale={drawing["scale"]}')
            self._json_response(200, {'ok': True, 'id': drawing['id']})

        except json.JSONDecodeError as e:
            self._json_response(400, {'error': f'Invalid JSON: {e}'})
        except Exception as e:
            self._json_response(500, {'error': str(e)})

    # ── /convert-dxf ──────────────────────────────────────────────────────────
    def _convert_dxf(self):
        """
        Accept a DXF file (multipart or raw bytes), convert to SVG via ezdxf,
        return SVG string as JSON.

        Request body (JSON):
          { "dxf": "<base64-encoded DXF>", "filename": "drawing.dxf" }

        Response:
          { "ok": true, "svg": "<svg...>", "layers": [...] }
        """
        try:
            # Check ezdxf is available
            try:
                import ezdxf
                from ezdxf.addons.drawing import RenderContext, Frontend
                from ezdxf.addons.drawing.svg import SVGBackend
                from ezdxf.addons.drawing.config import Configuration
            except ImportError as ie:
                print(f'\n  ezdxf import error: {ie}')
                import traceback; traceback.print_exc()
                self._json_response(503, {
                    'error': f'ezdxf import failed: {ie}',
                    'install': 'pip install ezdxf'
                })
                return

            import base64, io, tempfile, os

            length  = int(self.headers.get('Content-Length', 0))
            raw     = self.rfile.read(length)
            payload = json.loads(raw.decode('utf-8'))

            dxf_b64  = payload.get('dxf', '')
            filename = payload.get('filename', 'drawing.dxf')
            # Layer overrides: { layerName: { color, lineweight, linetype, visible } }
            layer_map = payload.get('layerMap', {})

            if not dxf_b64:
                self._json_response(400, {'error': 'Missing dxf field'})
                return

            dxf_bytes = base64.b64decode(dxf_b64)

            # Write to temp file — ezdxf reads best from a file path
            with tempfile.NamedTemporaryFile(suffix='.dxf', delete=False) as tmp:
                tmp.write(dxf_bytes)
                tmp_path = tmp.name

            try:
                doc = ezdxf.readfile(tmp_path)
            finally:
                os.unlink(tmp_path)

            # ── Apply layer overrides ─────────────────────────────────────────
            for layer_name, overrides in layer_map.items():
                try:
                    layer = doc.layers.get(layer_name)
                    if not layer:
                        continue
                    if 'color' in overrides and overrides['color'] is not None:
                        # Accept hex string '#RRGGBB' or ACI int
                        col = overrides['color']
                        if isinstance(col, str) and col.startswith('#'):
                            r = int(col[1:3], 16)
                            g = int(col[3:5], 16)
                            b = int(col[5:7], 16)
                            layer.rgb = (r, g, b)
                        elif isinstance(col, int):
                            layer.color = col
                    if 'lineweight' in overrides and overrides['lineweight'] is not None:
                        # lineweight in mm * 100, e.g. 25 = 0.25mm
                        layer.dxf.lineweight = int(overrides['lineweight'])
                    if overrides.get('visible') is False:
                        layer.on = False
                except Exception as e:
                    print(f'  Layer override error ({layer_name}): {e}')

            # ── Convert to SVG (ezdxf 1.4.3) ─────────────────────────────────
            msp = doc.modelspace()
            ctx = RenderContext(doc)

            from ezdxf.addons.drawing.layout import Page, Settings, Units

            page     = Page(0, 0, Units.mm)
            settings = Settings()
            backend  = SVGBackend()
            config   = Configuration.defaults()
            frontend = Frontend(ctx, backend, config=config)
            frontend.draw_layout(msp, finalize=True)
            svg_str  = backend.get_string(page, settings=settings)

            # ── Strip ezdxf background rect (dark canvas colour) ─────────────
            # ezdxf adds a background rect with its default dark theme colour.
            # Remove any rect that is the first child of the root SVG and has
            # a fill matching common ezdxf background colours.
            import re
            # Remove a leading rect with fill="#212830" or rgb(33,40,48) or similar dark fills
            svg_str = re.sub(
                r'<rect[^>]*fill\s*=\s*["\'](?:#(?:1e2428|212830|1a1f24|000000)|rgb\((?:33,\s*40,\s*48|30,\s*36,\s*43|0,\s*0,\s*0)\))["\'][^/]*/?>',
                '',
                svg_str,
                flags=re.IGNORECASE,
            )
            # Also strip any rect with fill that is very dark (catches other ezdxf themes)
            def _is_dark_fill(m):
                style = m.group(0)
                # extract fill value
                fill_match = re.search(r'fill\s*=\s*["\']([^"\']+)["\']', style, re.IGNORECASE)
                if not fill_match:
                    return style
                fill = fill_match.group(1).strip()
                # parse hex
                if fill.startswith('#') and len(fill) in (4, 7):
                    try:
                        if len(fill) == 4:
                            r = int(fill[1]*2, 16); g = int(fill[2]*2, 16); b = int(fill[3]*2, 16)
                        else:
                            r = int(fill[1:3], 16); g = int(fill[3:5], 16); b = int(fill[5:7], 16)
                        if r < 60 and g < 60 and b < 60:
                            return ''   # remove dark rect
                    except Exception:
                        pass
                return style
            svg_str = re.sub(r'<rect[^>]*fill\s*=\s*["\']#[^"\']+["\'][^/]*/?>',
                             _is_dark_fill, svg_str, flags=re.IGNORECASE)

            # ── Extract layer list for the layer manager ──────────────────────
            layers = []
            for layer in doc.layers:
                name = layer.dxf.name
                if name == '0':
                    continue
                try:
                    rgb = layer.rgb
                    col = '#{:02x}{:02x}{:02x}'.format(*rgb) if rgb else None
                except Exception:
                    col = None
                try:
                    lw = int(layer.dxf.lineweight)
                except Exception:
                    lw = 25
                try:
                    on = bool(layer.on)
                except Exception:
                    on = True
                try:
                    fr = bool(layer.is_frozen) if not callable(layer.is_frozen) else bool(layer.is_frozen())
                except Exception:
                    fr = False
                layers.append({
                    'name':       str(name),
                    'color':      col,
                    'lineweight': lw,
                    'on':         on,
                    'frozen':     fr,
                })

            print(f'\n  ✓  DXF converted: {filename}  ({len(layers)} layers)')
            self._json_response(200, {
                'ok':      True,
                'svg':     svg_str,
                'layers':  layers,
                'filename': filename,
            })

        except json.JSONDecodeError as e:
            self._json_response(400, {'error': f'Invalid JSON: {e}'})
        except Exception as e:
            import traceback
            print(f'  DXF conversion error: {e}')
            traceback.print_exc()
            self._json_response(500, {'error': str(e)})


    def _poll(self):
        """
        Returns all drawings received since `since` ms timestamp.
        Query param:  ?since=<unix_ms>   (default 0 = all)
        Dasu passes its last-seen drawing ID and only gets new ones.
        """
        from urllib.parse import parse_qs
        qs    = parse_qs(urlparse(self.path).query)
        since = qs.get('since', [''])[0]

        with _lock:
            if since:
                result = [d for d in _drawings if d['id'] > since]
            else:
                result = list(_drawings)

        self._json_response(200, {
            'drawings': result,
            'count':    len(result),
            'serverTs': int(time.time() * 1000),
        })

    # ── /status ───────────────────────────────────────────────────────────────
    def _status(self):
        with _lock:
            n = len(_drawings)
        self._json_response(200, {
            'status':   'ok',
            'port':     PORT,
            'stored':   n,
            'version':  '0.1.0',
        })

    # ── / info page ───────────────────────────────────────────────────────────
    def _info(self):
        html = f'''<!DOCTYPE html>
<html><head><meta charset="utf-8">
<title>Dasu Bridge</title>
<style>
  body {{ font-family: monospace; background: #1c1c1e; color: #f5f5f7;
         padding: 40px; max-width: 600px; margin: 0 auto; }}
  h1 {{ color: #30d158; }}
  .ep {{ background: #2c2c2e; padding: 10px 14px; border-radius: 6px;
         margin: 8px 0; border-left: 3px solid #30d158; }}
  .method {{ color: #0a84ff; margin-right: 8px; }}
</style></head><body>
<h1>Dasu.print Bridge  v0.1.0</h1>
<p>Local bridge between Bonsai BIM (Blender) and the Dasu sheet layout tool.</p>
<p>Listening on <strong>localhost:{PORT}</strong></p>
<h2>Endpoints</h2>
<div class="ep"><span class="method">POST</span>/receive &mdash; Blender sends drawing payload</div>
<div class="ep"><span class="method">POST</span>/convert-dxf &mdash; Convert DXF to SVG (requires ezdxf)</div>
<div class="ep"><span class="method">GET</span>/poll &mdash; Dasu fetches pending drawings</div>
<div class="ep"><span class="method">GET</span>/status &mdash; Health check</div>
</body></html>'''
        self.send_response(200)
        self.send_header('Content-Type', 'text/html; charset=utf-8')
        self._cors()
        self.end_headers()
        self.wfile.write(html.encode())

    # ── Helper ─────────────────────────────────────────────────────────────────
    def _json_response(self, code, data):
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(code)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self._cors()
        self.end_headers()
        self.wfile.write(body)


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == '__main__':
    server = HTTPServer((HOST, PORT), BridgeHandler)
    print(f'\n  Dasu Bridge  v0.1.0')
    print(f'  Listening on http://{HOST}:{PORT}')
    print(f'  Open http://{HOST}:{PORT} in your browser for info')
    print(f'\n  Ready — waiting for connections from Dasu...')
    print(f'  Press Ctrl+C to stop\n')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n  Bridge stopped.')
        server.server_close()
