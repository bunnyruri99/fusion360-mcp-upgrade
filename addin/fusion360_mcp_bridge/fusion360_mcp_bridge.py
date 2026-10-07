"""Fusion 360 MCP Bridge add-in.

Architecture:
  TCP server (worker thread, port 9876)
    → fires CustomEvent to main thread
    → Fusion API runs on main thread (thread-safety requirement)
    → result returned to worker thread via threading.Event
    → TCP response sent back to MCP server

Critical invariants:
  1. All adsk.fusion API calls MUST happen on the Fusion main thread.
  2. _handlers list prevents CustomEventHandler from being garbage-collected.
  3. Fusion internal unit is centimeters — convert mm args here, not in the caller.
"""

from __future__ import annotations

import json
import logging
import math
from pathlib import Path
import socket
import threading
import traceback
import uuid

import adsk.core
import adsk.fusion

logger = logging.getLogger(__name__)

HOST = "127.0.0.1"
PORT = 9876
TIMEOUT = 30.0
MAX_PAYLOAD_BYTES = 64 * 1024  # 64 KB limit to prevent unbounded memory DoS
MAX_PENDING_REQUESTS = 100
CUSTOM_EVENT_ID = "fusion_mcp_bridge_execute"

app: adsk.core.Application | None = None
ui: adsk.core.UserInterface | None = None

_handlers: list = []          # GC protection for event handlers
_pending: dict[str, dict] = {}  # request_id → {event, result}
_stop_flag = threading.Event()
_server_thread: threading.Thread | None = None


# ---------------------------------------------------------------------------
# Unit conversion
# ---------------------------------------------------------------------------

def mm(value: float) -> float:
    """Convert millimeters to centimeters (Fusion internal unit)."""
    return value * 0.1


# ---------------------------------------------------------------------------
# Tool dispatch — add new tools here
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Tool dispatch handlers
# ---------------------------------------------------------------------------

def _tool_create_sketch(design: adsk.fusion.Design, args: dict) -> dict:
    root = design.rootComponent
    plane_map = {
        "XY": root.xYConstructionPlane,
        "XZ": root.xZConstructionPlane,
        "YZ": root.yZConstructionPlane,
    }
    plane_name = args.get("plane", "XY")
    if plane_name not in plane_map:
        return {"success": False, "error": f"Unknown plane: {plane_name}"}
    sketch = root.sketches.add(plane_map[plane_name])
    return {"success": True, "message": f"Sketch '{sketch.name}' created on {plane_name}"}


def _tool_draw_rectangle(design: adsk.fusion.Design, args: dict) -> dict:
    root = design.rootComponent
    sketch = root.sketches.item(root.sketches.count - 1)
    lines = sketch.sketchCurves.sketchLines
    p0 = adsk.core.Point3D.create(0, 0, 0)
    p1 = adsk.core.Point3D.create(mm(args["width_mm"]), mm(args["height_mm"]), 0)
    lines.addTwoPointRectangle(p0, p1)
    return {
        "success": True,
        "message": f"Rectangle {args['width_mm']}×{args['height_mm']} mm drawn",
    }


def _tool_draw_circle(design: adsk.fusion.Design, args: dict) -> dict:
    root = design.rootComponent
    sketch = root.sketches.item(root.sketches.count - 1)
    center = adsk.core.Point3D.create(0, 0, 0)
    sketch.sketchCurves.sketchCircles.addByCenterRadius(center, mm(args["diameter_mm"] / 2))
    return {"success": True, "message": f"Circle ⌀{args['diameter_mm']} mm drawn"}


def _tool_create_box(design: adsk.fusion.Design, args: dict) -> dict:
    """Create an axis-aligned box at an explicit XYZ origin, dimensions in mm."""
    root = design.rootComponent
    x = mm(float(args.get("x_mm", 0)))
    y = mm(float(args.get("y_mm", 0)))
    z = mm(float(args.get("z_mm", 0)))
    width = mm(float(args["width_mm"]))
    height = mm(float(args["height_mm"]))
    depth = mm(float(args["depth_mm"]))
    if width <= 0 or height <= 0 or depth <= 0:
        return {"success": False, "error": "Box dimensions must be positive."}

    sketch = root.sketches.add(root.xYConstructionPlane)
    lines = sketch.sketchCurves.sketchLines
    lines.addTwoPointRectangle(
        adsk.core.Point3D.create(x, y, 0),
        adsk.core.Point3D.create(x + width, y + height, 0),
    )
    profile = sketch.profiles.item(0)
    ext_input = root.features.extrudeFeatures.createInput(
        profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_input.setDistanceExtent(False, adsk.core.ValueInput.createByReal(depth))
    ext = root.features.extrudeFeatures.add(ext_input)
    body = ext.bodies.item(0)
    if z:
        transform = adsk.core.Matrix3D.create()
        transform.translation = adsk.core.Vector3D.create(0, 0, z)
        entities = adsk.core.ObjectCollection.create()
        entities.add(body)
        move_input = root.features.moveFeatures.createInput2(entities)
        move_input.defineAsFreeMove(transform)
        root.features.moveFeatures.add(move_input)
    body.name = args.get("name", "BracketBox")
    return {"success": True, "message": f"Box '{body.name}' created"}


def _tool_extrude(design: adsk.fusion.Design, args: dict) -> dict:
    root = design.rootComponent
    sketch = root.sketches.item(root.sketches.count - 1)
    if sketch.profiles.count == 0:
        return {
            "success": False,
            "error": "No closed profile in sketch. Draw a closed shape first.",
        }
    profile = sketch.profiles.item(0)
    ext_feats = root.features.extrudeFeatures
    dist = adsk.core.ValueInput.createByReal(mm(args["distance_mm"]))
    ext_input = ext_feats.createInput(
        profile, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    ext_input.setDistanceExtent(False, dist)
    ext_feats.add(ext_input)
    return {"success": True, "message": f"Extruded {args['distance_mm']} mm"}


def _tool_fillet(design: adsk.fusion.Design, args: dict) -> dict:
    root = design.rootComponent
    bodies = root.bRepBodies
    if bodies.count == 0:
        return {"success": False, "error": "No solid body to fillet."}
    body = bodies.item(bodies.count - 1)
    edges = adsk.core.ObjectCollection.create()
    for edge in body.edges:
        edges.add(edge)
    fillet_feats = root.features.filletFeatures
    radius = adsk.core.ValueInput.createByReal(mm(args["radius_mm"]))
    fillet_input = fillet_feats.createInput()
    fillet_input.addConstantRadiusEdgeSet(edges, radius, True)
    fillet_feats.add(fillet_input)
    return {"success": True, "message": f"Fillet R{args['radius_mm']} mm applied"}


def _tool_shell(design: adsk.fusion.Design, args: dict) -> dict:
    root = design.rootComponent
    bodies = root.bRepBodies
    if bodies.count == 0:
        return {"success": False, "error": "No solid body to shell."}
    body = bodies.item(bodies.count - 1)
    # Remove the largest face (top face by area heuristic)
    faces = adsk.core.ObjectCollection.create()
    top_face = max(body.faces, key=lambda f: f.area)
    faces.add(top_face)
    shell_feats = root.features.shellFeatures
    thickness = adsk.core.ValueInput.createByReal(mm(args["thickness_mm"]))
    shell_input = shell_feats.createInput(faces, False)
    shell_input.insideThickness = thickness
    shell_feats.add(shell_input)
    return {"success": True, "message": f"Shell {args['thickness_mm']} mm wall applied"}


def _tool_create_parameter(design: adsk.fusion.Design, args: dict) -> dict:
    if design.userParameters.itemByName(args["name"]) is not None:
        return {"success": False, "error": f"Parameter already exists: {args['name']}"}
    unit = args.get("unit", "mm")
    allowed_units = {"mm", "cm", "m", "in", "ft", "deg", "rad", "%", ""}
    if unit not in allowed_units:
        return {"success": False, "error": f"Unsupported or invalid unit: {unit}"}
    comment = args.get("comment", "")
    value_input = adsk.core.ValueInput.createByString(f"{args['value']} {unit}")
    design.userParameters.add(args["name"], value_input, unit, comment)
    return {
        "success": True,
        "message": f"Parameter created: {args['name']} = {args['value']} {unit}",
    }


def _validate_export_path(filepath: str, allowed_ext: str) -> tuple[bool, str]:
    """Validate export path to prevent directory traversal and dangerous destinations."""
    try:
        p = Path(filepath).resolve()
    except Exception as exc:
        return False, f"Invalid filepath: {exc}"

    if p.suffix.lower() != allowed_ext.lower():
        return False, f"Invalid file extension. Expected '{allowed_ext}', got '{p.suffix}'"

    # Disallow writing directly to system sensitive root directories
    forbidden_prefixes = ("/windows", "/winnt", "/system32", "/etc", "/bin", "/sbin", "/usr", "/root")
    normalized_path = str(p).replace("\\", "/").lower()
    for forbidden in forbidden_prefixes:
        if forbidden in normalized_path:
            return False, f"Export path forbidden for security reasons: {p}"

    try:
        p.parent.mkdir(parents=True, exist_ok=True)
    except Exception as exc:
        return False, f"Cannot create export directory '{p.parent}': {exc}"

    return True, str(p)


def _tool_set_parameter(design: adsk.fusion.Design, args: dict) -> dict:
    param = design.userParameters.itemByName(args["name"])
    if param is None:
        return {"success": False, "error": f"Parameter not found: {args['name']}"}
    unit = args.get("unit", "mm")
    allowed_units = {"mm", "cm", "m", "in", "ft", "deg", "rad", "%", ""}
    if unit not in allowed_units:
        return {"success": False, "error": f"Unsupported or invalid unit: {unit}"}
    param.expression = f"{args['value']} {unit}".strip()
    return {"success": True, "message": f"{args['name']} = {args['value']} {unit}".strip()}


def _tool_list_parameters(design: adsk.fusion.Design, _args: dict) -> dict:
    params = design.userParameters
    data = {
        params.item(i).name: f"{params.item(i).value * 10:.4f} mm"
        for i in range(params.count)
    }
    return {"success": True, "message": f"{params.count} parameters found", "data": data}


def _tool_export_step(design: adsk.fusion.Design, args: dict) -> dict:
    filepath = args.get("filepath", "")
    valid, target_or_err = _validate_export_path(filepath, ".step")
    if not valid:
        return {"success": False, "error": target_or_err}

    export_mgr = design.exportManager
    options = export_mgr.createSTEPExportOptions(target_or_err)
    export_mgr.execute(options)
    return {"success": True, "message": f"STEP exported to {target_or_err}"}


def _tool_revolve(design: adsk.fusion.Design, args: dict) -> dict:
    root = design.rootComponent
    sketch = root.sketches.item(root.sketches.count - 1)
    if sketch.profiles.count == 0:
        return {"success": False, "error": "No closed profile in sketch."}
    profile = sketch.profiles.item(0)
    axis_map = {
        "X": root.xConstructionAxis,
        "Y": root.yConstructionAxis,
    }
    axis_name = args.get("axis", "X")
    axis = axis_map.get(axis_name)
    if axis is None:
        return {"success": False, "error": f"Unknown axis: {axis_name}. Use X or Y."}
    angle_deg = float(args.get("angle_deg", 360))
    revolve_feats = root.features.revolveFeatures
    revolve_input = revolve_feats.createInput(
        profile, axis, adsk.fusion.FeatureOperations.NewBodyFeatureOperation
    )
    angle_val = adsk.core.ValueInput.createByReal(math.radians(angle_deg))
    revolve_input.setAngleExtent(False, angle_val)
    revolve_feats.add(revolve_input)
    return {
        "success": True,
        "message": f"Revolve {angle_deg}° around {axis_name}-axis complete",
    }


def _tool_hole(design: adsk.fusion.Design, args: dict) -> dict:
    root = design.rootComponent
    bodies = root.bRepBodies
    if bodies.count == 0:
        return {
            "success": False,
            "error": "No solid body — run f360_extrude or f360_revolve first.",
        }
    body = bodies.item(bodies.count - 1)
    top_face = max(body.faces, key=lambda f: f.boundingBox.maxPoint.z)
    hole_feats = root.features.holeFeatures
    dia = adsk.core.ValueInput.createByReal(mm(args["diameter_mm"]))
    hole_input = hole_feats.createSimpleInput(dia)
    point = adsk.core.Point3D.create(
        mm(args["x_mm"]),
        mm(args["y_mm"]),
        top_face.boundingBox.maxPoint.z,
    )
    hole_input.setPositionByPoint(top_face, point)
    hole_type = args.get("hole_type", "through")
    if hole_type == "through":
        hole_input.setAllExtent(False)
    else:
        depth_mm = args.get("depth_mm")
        if depth_mm is None:
            return {"success": False, "error": "depth_mm is required for blind holes."}
        hole_input.setDistanceExtent(adsk.core.ValueInput.createByReal(mm(depth_mm)))
    hole_feats.add(hole_input)
    label = f"⌀{args['diameter_mm']}mm {hole_type} hole at ({args['x_mm']}, {args['y_mm']})"
    return {"success": True, "message": label}


def _tool_hole_pattern(design: adsk.fusion.Design, args: dict) -> dict:
    root = design.rootComponent
    bodies = root.bRepBodies
    if bodies.count == 0:
        return {
            "success": False,
            "error": "No solid body — run f360_extrude or f360_revolve first.",
        }
    body = bodies.item(bodies.count - 1)
    top_face = max(body.faces, key=lambda f: f.boundingBox.maxPoint.z)
    hole_feats = root.features.holeFeatures
    dia = adsk.core.ValueInput.createByReal(mm(args["hole_diameter_mm"]))
    bcd_r = mm(args["bolt_circle_dia_mm"] / 2)
    count = int(args["count"])
    hole_type = args.get("hole_type", "through")
    depth_mm = args.get("depth_mm")
    z = top_face.boundingBox.maxPoint.z
    created = 0
    for i in range(count):
        angle = math.radians(i * 360 / count)
        x = bcd_r * math.cos(angle)
        y = bcd_r * math.sin(angle)
        hole_input = hole_feats.createSimpleInput(dia)
        point = adsk.core.Point3D.create(x, y, z)
        hole_input.setPositionByPoint(top_face, point)
        if hole_type == "through":
            hole_input.setAllExtent(False)
        else:
            if depth_mm is None:
                return {"success": False, "error": "depth_mm required for blind hole pattern."}
            hole_input.setDistanceExtent(adsk.core.ValueInput.createByReal(mm(depth_mm)))
        hole_feats.add(hole_input)
        created += 1
    return {
        "success": True,
        "message": (
            f"{created}× ⌀{args['hole_diameter_mm']}mm holes "
            f"on BCD {args['bolt_circle_dia_mm']}mm"
        ),
    }


def _tool_export_stl(design: adsk.fusion.Design, args: dict) -> dict:
    filepath = args.get("filepath", "")
    valid, target_or_err = _validate_export_path(filepath, ".stl")
    if not valid:
        return {"success": False, "error": target_or_err}

    root = design.rootComponent
    mesh_map = {
        "low": adsk.fusion.MeshRefinementSettings.MeshRefinementLow,
        "medium": adsk.fusion.MeshRefinementSettings.MeshRefinementMedium,
        "high": adsk.fusion.MeshRefinementSettings.MeshRefinementHigh,
    }
    export_mgr = design.exportManager
    options = export_mgr.createSTLExportOptions(root)
    options.meshRefinement = mesh_map.get(args.get("mesh_refinement", "medium"))
    options.filename = target_or_err
    export_mgr.execute(options)
    return {"success": True, "message": f"STL exported to {target_or_err}"}


def _tool_ping(_design: adsk.fusion.Design | None, _args: dict) -> dict:
    return {
        "success": True,
        "message": "Fusion 360 MCP bridge is alive and connected",
        "data": {
            "version": "0.1.0",
            "has_active_design": _design is not None,
        }
    }


_TOOL_HANDLERS = {
    "ping": _tool_ping,
    "create_sketch": _tool_create_sketch,
    "draw_rectangle": _tool_draw_rectangle,
    "draw_circle": _tool_draw_circle,
    "extrude": _tool_extrude,
    "create_box": _tool_create_box,
    "fillet": _tool_fillet,
    "shell": _tool_shell,
    "create_parameter": _tool_create_parameter,
    "set_parameter": _tool_set_parameter,
    "list_parameters": _tool_list_parameters,
    "export_step": _tool_export_step,
    "revolve": _tool_revolve,
    "hole": _tool_hole,
    "hole_pattern": _tool_hole_pattern,
    "export_stl": _tool_export_stl,
}


def _tool_pcb_bracket(design: adsk.fusion.Design, args: dict) -> dict:
    import importlib.util
    path = Path(__file__).with_name('bracket_native.py')
    spec = importlib.util.spec_from_file_location('fusion_pcb_bracket_native', path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    result = module.build(design, args)
    return {'success': True, 'message': 'Native PCB bracket action completed', 'data': result}


_TOOL_HANDLERS['pcb_bracket_native'] = _tool_pcb_bracket


def _dispatch(tool: str, args: dict) -> dict:
    if app is None:
        return {"success": False, "error": "Fusion application instance not initialized."}

    handler = _TOOL_HANDLERS.get(tool)
    if handler is None:
        return {"success": False, "error": f"Unknown tool: {tool}"}

    design = adsk.fusion.Design.cast(app.activeProduct)
    if tool == "ping":
        return handler(design, args)

    if design is None:
        return {
            "success": False,
            "error": "No active Fusion design. Open or create a design first.",
        }

    return handler(design, args)


# ---------------------------------------------------------------------------
# Custom event handler (Fusion main thread)
# ---------------------------------------------------------------------------

class _BridgeEventHandler(adsk.core.CustomEventHandler):
    def notify(self, args: adsk.core.CustomEventArgs) -> None:
        req_id: str | None = None  # pre-declare so finally block is always safe
        result: dict = {"success": False, "error": "Unknown error in notify()"}
        try:
            data = json.loads(args.additionalInfo)
            req_id = data["id"]
            result = _dispatch(data["tool"], data["args"])
        except Exception:
            result = {"success": False, "error": traceback.format_exc()}
        finally:
            if req_id and req_id in _pending:
                _pending[req_id]["result"] = result
                _pending[req_id]["event"].set()


# ---------------------------------------------------------------------------
# TCP server (worker thread)
# ---------------------------------------------------------------------------

def _handle_client(conn: socket.socket) -> None:
    try:
        raw = b""
        while not raw.endswith(b"\n"):
            chunk = conn.recv(1024)
            if not chunk:
                break
            raw += chunk
            if len(raw) > MAX_PAYLOAD_BYTES:
                conn.sendall(
                    json.dumps({
                        "success": False,
                        "error": f"Payload exceeded maximum allowed size ({MAX_PAYLOAD_BYTES} bytes)"
                    }).encode() + b"\n"
                )
                return

        if not raw:
            return

        data = json.loads(raw.decode())

        if app is None:
            conn.sendall(
                json.dumps({
                    "success": False,
                    "error": "Fusion application instance not ready or add-in not initialized."
                }).encode() + b"\n"
            )
            return

        if len(_pending) >= MAX_PENDING_REQUESTS:
            conn.sendall(
                json.dumps({
                    "success": False,
                    "error": "Server busy: too many pending requests."
                }).encode() + b"\n"
            )
            return

        req_id = str(uuid.uuid4())
        evt = threading.Event()
        _pending[req_id] = {"event": evt, "result": None}

        # Allow client to pass timeout override per request; clamp to minimum 1.0s for safety
        req_timeout = max(1.0, float(data.get("timeout") or TIMEOUT))

        app.fireCustomEvent(
            CUSTOM_EVENT_ID,
            json.dumps({"id": req_id, "tool": data["tool"], "args": data["args"]}),
        )

        evt.wait(timeout=req_timeout)
        result = _pending.pop(req_id, {}).get("result") or {
            "success": False,
            "error": f"Timeout waiting for Fusion main thread after {req_timeout}s",
        }
        conn.sendall(json.dumps(result).encode() + b"\n")

    except Exception:
        conn.sendall(
            json.dumps({"success": False, "error": traceback.format_exc()}).encode() + b"\n"
        )
    finally:
        conn.close()


def _tcp_server_loop() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind((HOST, PORT))
        srv.listen(5)
        srv.settimeout(1.0)
        logger.info("Fusion MCP bridge listening on %s:%d", HOST, PORT)
        while not _stop_flag.is_set():
            try:
                conn, _ = srv.accept()
                threading.Thread(target=_handle_client, args=(conn,), daemon=True).start()
            except TimeoutError:
                continue
            except OSError as exc:
                if not _stop_flag.is_set():
                    logger.error("TCP server socket error: %s", exc)
                break


# ---------------------------------------------------------------------------
# Add-in lifecycle
# ---------------------------------------------------------------------------

def run(context) -> None:  # noqa: ANN001
    global app, ui, _server_thread
    app = adsk.core.Application.get()
    ui = app.userInterface

    custom_event = app.registerCustomEvent(CUSTOM_EVENT_ID)
    handler = _BridgeEventHandler()
    custom_event.add(handler)
    _handlers.append(handler)  # prevent GC

    _stop_flag.clear()
    _server_thread = threading.Thread(target=_tcp_server_loop, daemon=True)
    _server_thread.start()

    ui.messageBox("Fusion MCP bridge started — listening on port 9876")


def stop(context) -> None:  # noqa: ANN001
    _stop_flag.set()
    app.unregisterCustomEvent(CUSTOM_EVENT_ID)
    if ui:
        ui.messageBox("Fusion MCP bridge stopped")
