#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import html
import json
import mimetypes
from pathlib import Path
from typing import Any


DEFAULT_THREE_URL = "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js"
DEFAULT_THREE_MODULE_PATH = Path(__file__).resolve().parents[1] / "assets" / "three.module.js"


def read_report(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def image_data_url(path: str) -> str | None:
    if not path:
        return None
    image_path = Path(path)
    if not image_path.exists() or not image_path.is_file():
        return None
    mime = mimetypes.guess_type(str(image_path))[0] or "image/png"
    data = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{data}"


def prepared_report(report: dict[str, Any]) -> dict[str, Any]:
    copied = json.loads(json.dumps(report))
    for view in copied.get("views", []):
        view["data_url"] = image_data_url(view.get("path", ""))
    return copied


def browser_safe_report(report: dict[str, Any]) -> dict[str, Any]:
    """Return only fields needed by the offline HTML runtime, without local paths."""
    copied = json.loads(json.dumps(report))
    copied.pop("input", None)
    copied.pop("execution", None)
    for view in copied.get("views", []):
        view.pop("path", None)
    return copied


def table_rows(rows: list[list[Any]]) -> str:
    return "\n".join(
        "<tr>" + "".join(f"<td>{html.escape(str(value))}</td>" for value in row) + "</tr>"
        for row in rows
    )


def three_loader_script(three_source: str | None, three_url: str) -> str:
    if three_source:
        return "\n".join(
            [
                f"    const THREE_SOURCE = {json.dumps(three_source)};",
                "    const THREE_BLOB_URL = URL.createObjectURL(new Blob([THREE_SOURCE], { type: \"text/javascript\" }));",
                "    const THREE = await import(THREE_BLOB_URL);",
            ]
        )
    return f'    import * as THREE from "{three_url}";'


def build_html(report: dict[str, Any], title: str, three_url: str, three_source: str | None) -> str:
    structure = report["structure"]
    cell = structure["cell"]
    nearest = structure["nearest_distances"]
    symmetry = structure["symmetry_attempt"]
    coordinates = structure["coordinates"]
    views = report.get("views", [])
    element_counts = ", ".join(f"{key}: {value}" for key, value in structure["element_counts"].items())
    limitations = report.get("limitations") or ["none"]
    not_assessed = report.get("not_assessed") or []

    fact_rows = table_rows(
        [
            ["Formula", structure["formula"]],
            ["Atom count", structure["atom_count"]],
            ["Elements", element_counts],
            ["Cell", f'a={cell["a"]} Ang, b={cell["b"]} Ang, c={cell["c"]} Ang'],
            ["Angles", f'alpha={cell["alpha"]} deg, beta={cell["beta"]} deg, gamma={cell["gamma"]} deg'],
            ["Volume", f'{structure["volume_ang3"]} Ang^3'],
            ["Density", f'{structure["density_g_cm3"]} g/cm^3'],
            ["Nearest distance", f'{nearest["min_distance_ang"]} Ang'],
            ["Symmetry attempt", f'{symmetry.get("international", "")} #{symmetry.get("number", "")} ({symmetry.get("status", "")})'],
        ]
    )
    coord_rows = table_rows(
        [
            [
                item["index"],
                item["symbol"],
                item["cartesian_ang"],
                item["fractional"],
            ]
            for item in coordinates["coordinate_sample"]
        ]
    )
    pair_rows = table_rows(
        [
            [
                f'{item["i"]}-{item["j"]}',
                "-".join(item["symbols"]),
                item["distance_ang"],
            ]
            for item in nearest.get("nearest_pairs_sample", [])[:12]
        ]
    )
    gap_rows = table_rows(
        [
            [
                item["axis"],
                item.get("largest_gap_ang"),
                item.get("occupied_span_estimate_ang"),
            ]
            for item in structure.get("axis_gap_estimates", [])
        ]
    )
    view_cards = "\n".join(
        f"""
        <figure class="view-card">
          <img src="{html.escape(view.get('data_url') or view.get('path', ''))}" alt="view along {html.escape(view.get('axis', ''))}">
          <figcaption>along {html.escape(view.get('axis', ''))}: {html.escape(view.get('x_axis', ''))}-{html.escape(view.get('y_axis', ''))}</figcaption>
        </figure>
        """
        for view in views
    )
    limit_items = "\n".join(f"<li>{html.escape(str(item))}</li>" for item in limitations)
    not_assessed_items = "\n".join(f"<li>{html.escape(str(item))}</li>" for item in not_assessed)
    report_json = json.dumps(browser_safe_report(report), ensure_ascii=False)
    escaped_title = html.escape(title)

    three_loader = three_loader_script(three_source, three_url)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <style>
    :root {{
      color-scheme: light;
      --bg: #f3f5f8;
      --ink: #18202a;
      --muted: #5d6876;
      --line: #d7dce4;
      --panel: #ffffff;
      --accent: #1f6feb;
      --accent-2: #0f766e;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      background: var(--bg);
      color: var(--ink);
      overflow: hidden;
    }}
    .deck {{
      width: 100vw;
      height: 100vh;
      display: grid;
      place-items: center;
      padding: 3vh 4vw 8vh;
    }}
    .slide {{
      display: none;
      width: min(1500px, 94vw);
      aspect-ratio: 16 / 9;
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      box-shadow: 0 18px 50px rgba(20, 31, 45, 0.14);
      padding: 42px;
      overflow: hidden;
    }}
    .slide.active {{ display: block; }}
    h1, h2, h3 {{ margin: 0; letter-spacing: 0; }}
    h1 {{ font-size: 48px; line-height: 1.05; max-width: 1050px; }}
    h2 {{ font-size: 34px; margin-bottom: 20px; }}
    h3 {{ font-size: 19px; margin-bottom: 10px; }}
    p {{ font-size: 20px; color: var(--muted); line-height: 1.45; }}
    .subtitle {{ margin-top: 18px; max-width: 1000px; }}
    .grid-2 {{
      display: grid;
      grid-template-columns: 1.05fr 0.95fr;
      gap: 28px;
      height: calc(100% - 64px);
      min-height: 0;
    }}
    .grid-3 {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 18px;
      height: calc(100% - 72px);
      min-height: 0;
    }}
    .metric-row {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 16px;
      margin-top: 44px;
    }}
    .metric {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      background: #fbfcfe;
      min-height: 112px;
    }}
    .metric b {{ display: block; font-size: 30px; margin-top: 12px; }}
    .metric span {{ color: var(--muted); font-size: 15px; }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 15px;
    }}
    th, td {{
      border-bottom: 1px solid var(--line);
      text-align: left;
      padding: 8px 10px;
      vertical-align: top;
    }}
    th {{ color: #2c3440; background: #f7f9fc; }}
    .table-wrap {{
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: auto;
      height: 100%;
    }}
    .three-panel {{
      display: grid;
      grid-template-columns: minmax(0, 1fr) 310px;
      gap: 22px;
      height: calc(100% - 64px);
      min-height: 0;
    }}
    #three-stage {{
      position: relative;
      border: 1px solid var(--line);
      border-radius: 8px;
      overflow: hidden;
      background: #f8fafc;
      min-height: 0;
    }}
    #three-canvas {{ width: 100%; height: 100%; display: block; }}
    .hint {{
      position: absolute;
      left: 14px;
      bottom: 14px;
      padding: 8px 10px;
      border-radius: 6px;
      background: rgba(255,255,255,0.88);
      border: 1px solid var(--line);
      color: var(--muted);
      font-size: 13px;
    }}
    .side-panel {{
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      overflow: auto;
      background: #fbfcfe;
    }}
    .legend-item {{
      display: flex;
      align-items: center;
      gap: 10px;
      margin: 10px 0;
      font-size: 16px;
    }}
    .dot {{
      width: 18px;
      height: 18px;
      border-radius: 50%;
      border: 1px solid rgba(0,0,0,0.35);
      display: inline-block;
    }}
    .view-card {{
      margin: 0;
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 12px;
      background: #fbfcfe;
      display: flex;
      flex-direction: column;
      min-width: 0;
      min-height: 0;
    }}
    .view-card img {{
      max-width: 100%;
      height: 100%;
      min-height: 0;
      object-fit: contain;
    }}
    .view-card figcaption {{
      color: var(--muted);
      font-size: 14px;
      text-align: center;
      margin-top: 8px;
    }}
    .footer {{
      position: fixed;
      left: 4vw;
      right: 4vw;
      bottom: 2vh;
      display: flex;
      justify-content: space-between;
      align-items: center;
      color: var(--muted);
      font-size: 14px;
    }}
    .nav button {{
      border: 1px solid var(--line);
      background: var(--panel);
      border-radius: 6px;
      padding: 8px 12px;
      margin-left: 8px;
      color: var(--ink);
      cursor: pointer;
    }}
    .nav button:hover {{ border-color: var(--accent); color: var(--accent); }}
    ul {{ font-size: 17px; line-height: 1.5; color: var(--muted); padding-left: 22px; }}
    code {{ font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace; font-size: 0.9em; }}
  </style>
</head>
<body>
  <main class="deck">
    <section class="slide active">
      <h1>{escaped_title}</h1>
      <p class="subtitle">Interactive CIF structure deck generated from code-backed structure facts. Use arrow keys or the navigation buttons to move between slides.</p>
      <div class="metric-row">
        <div class="metric"><span>Formula</span><b>{html.escape(str(structure["formula"]))}</b></div>
        <div class="metric"><span>Atoms</span><b>{html.escape(str(structure["atom_count"]))}</b></div>
        <div class="metric"><span>Cell c</span><b>{html.escape(str(cell["c"]))} Ang</b></div>
        <div class="metric"><span>Min distance</span><b>{html.escape(str(nearest["min_distance_ang"]))} Ang</b></div>
      </div>
      <p class="subtitle"><code>{html.escape(report["input"]["path"])}</code></p>
    </section>

    <section class="slide">
      <h2>Rotatable 3D Structure</h2>
      <div class="three-panel">
        <div id="three-stage">
          <canvas id="three-canvas"></canvas>
          <div class="hint">Drag to rotate. Scroll to zoom. Double-click to reset. Use arrow keys for slides.</div>
        </div>
        <aside class="side-panel">
          <h3>Composition</h3>
          <div id="legend"></div>
          <h3 style="margin-top: 24px;">Cell</h3>
          <table><tbody>{fact_rows}</tbody></table>
        </aside>
      </div>
    </section>

    <section class="slide">
      <h2>a / b / c Views</h2>
      <div class="grid-3">
        {view_cards}
      </div>
    </section>

    <section class="slide">
      <h2>Structure Tables</h2>
      <div class="grid-2">
        <div class="table-wrap">
          <table>
            <thead><tr><th>Index</th><th>Element</th><th>Cartesian Ang</th><th>Fractional</th></tr></thead>
            <tbody>{coord_rows}</tbody>
          </table>
        </div>
        <div class="table-wrap">
          <table>
            <thead><tr><th>Pair</th><th>Symbols</th><th>Distance Ang</th></tr></thead>
            <tbody>{pair_rows}</tbody>
          </table>
        </div>
      </div>
    </section>

    <section class="slide">
      <h2>Review Notes</h2>
      <div class="grid-2">
        <div>
          <h3>Axis Gap Estimates</h3>
          <div class="table-wrap" style="height: 220px;">
            <table><thead><tr><th>Axis</th><th>Largest gap Ang</th><th>Occupied span Ang</th></tr></thead><tbody>{gap_rows}</tbody></table>
          </div>
          <h3 style="margin-top: 28px;">Limitations</h3>
          <ul>{limit_items}</ul>
        </div>
        <div>
          <h3>Not Assessed</h3>
          <ul>{not_assessed_items}</ul>
          <p>This deck reports structure facts only. It does not provide DFT setup advice or physics credibility judgments.</p>
        </div>
      </div>
    </section>
  </main>

  <div class="footer">
    <span id="counter">1 / 5</span>
    <span>Use arrow keys. 3D slide supports mouse drag and wheel zoom.</span>
    <span class="nav"><button id="prev">Previous</button><button id="next">Next</button></span>
  </div>

  <script type="module">
{three_loader}
    const REPORT = {report_json};
    const ELEMENT_COLORS = {{ Hf: 0x6a5acd, Br: 0x8b4513, Ti: 0x7f7f7f, Se: 0xff7f0e, Na: 0x1f77b4, Cl: 0x2ca02c }};
    const ELEMENT_RADII = {{ Hf: 0.34, Br: 0.24, Ti: 0.28, Se: 0.27, Na: 0.22, Cl: 0.22 }};

    const slides = Array.from(document.querySelectorAll(".slide"));
    const counter = document.getElementById("counter");
    let currentSlide = 0;
    function showSlide(index) {{
      currentSlide = (index + slides.length) % slides.length;
      slides.forEach((slide, i) => slide.classList.toggle("active", i === currentSlide));
      counter.textContent = `${{currentSlide + 1}} / ${{slides.length}}`;
      setTimeout(resizeRenderer, 0);
    }}
    document.getElementById("prev").addEventListener("click", () => showSlide(currentSlide - 1));
    document.getElementById("next").addEventListener("click", () => showSlide(currentSlide + 1));
    window.addEventListener("keydown", (event) => {{
      if (event.key === "ArrowRight" || event.key === "PageDown") showSlide(currentSlide + 1);
      if (event.key === "ArrowLeft" || event.key === "PageUp") showSlide(currentSlide - 1);
    }});

    function degToRad(value) {{ return value * Math.PI / 180; }}
    function cellVectors(cell) {{
      const a = cell.a, b = cell.b, c = cell.c;
      const alpha = degToRad(cell.alpha), beta = degToRad(cell.beta), gamma = degToRad(cell.gamma);
      const avec = new THREE.Vector3(a, 0, 0);
      const bvec = new THREE.Vector3(b * Math.cos(gamma), b * Math.sin(gamma), 0);
      const cx = c * Math.cos(beta);
      const cy = c * (Math.cos(alpha) - Math.cos(beta) * Math.cos(gamma)) / Math.sin(gamma);
      const cz = Math.sqrt(Math.max(c * c - cx * cx - cy * cy, 0));
      return [avec, bvec, new THREE.Vector3(cx, cy, cz)];
    }}
    function fromFractional(frac, vectors) {{
      return new THREE.Vector3()
        .addScaledVector(vectors[0], frac[0])
        .addScaledVector(vectors[1], frac[1])
        .addScaledVector(vectors[2], frac[2]);
    }}

    const canvas = document.getElementById("three-canvas");
    const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true }});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0xf8fafc, 1);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(38, 1, 0.1, 1000);
    const group = new THREE.Group();
    scene.add(group);
    scene.add(new THREE.AmbientLight(0xffffff, 0.62));
    const light = new THREE.DirectionalLight(0xffffff, 1.15);
    light.position.set(6, -10, 12);
    scene.add(light);
    const fill = new THREE.DirectionalLight(0xabc6ff, 0.4);
    fill.position.set(-8, 4, 8);
    scene.add(fill);

    const vectors = cellVectors(REPORT.structure.cell);
    const corners = [
      [0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,0],
      [0,0,1],[1,0,1],[1,1,1],[0,1,1],[0,0,1],
      [1,0,0],[1,0,1],[1,1,1],[1,1,0],[0,1,0],[0,1,1]
    ].map(frac => fromFractional(frac, vectors));
    const cellGeometry = new THREE.BufferGeometry().setFromPoints(corners);
    group.add(new THREE.Line(cellGeometry, new THREE.LineBasicMaterial({{ color: 0x29313d }})));

    const atoms = REPORT.structure.coordinates.coordinate_sample.map(item => ({{
      index: item.index,
      symbol: item.symbol,
      position: fromFractional(item.fractional, vectors)
    }}));
    const allPoints = corners.concat(atoms.map(atom => atom.position));
    const box = new THREE.Box3().setFromPoints(allPoints);
    const center = new THREE.Vector3();
    box.getCenter(center);
    group.position.copy(center).multiplyScalar(-1);
    const size = new THREE.Vector3();
    box.getSize(size);
    const maxDim = Math.max(size.x, size.y, size.z, 1);
    camera.position.set(maxDim * 0.9, -maxDim * 1.25, maxDim * 0.85);
    camera.lookAt(0, 0, 0);

    atoms.forEach(atom => {{
      const color = ELEMENT_COLORS[atom.symbol] ?? 0xd62728;
      const radius = ELEMENT_RADII[atom.symbol] ?? 0.24;
      const sphere = new THREE.Mesh(
        new THREE.SphereGeometry(radius, 48, 32),
        new THREE.MeshStandardMaterial({{ color, roughness: 0.36, metalness: 0.08 }})
      );
      sphere.position.copy(atom.position);
      group.add(sphere);
    }});

    const legend = document.getElementById("legend");
    Object.entries(REPORT.structure.element_counts).forEach(([symbol, count]) => {{
      const row = document.createElement("div");
      row.className = "legend-item";
      const color = (ELEMENT_COLORS[symbol] ?? 0xd62728).toString(16).padStart(6, "0");
      row.innerHTML = `<span class="dot" style="background:#${{color}}"></span><span>${{symbol}} × ${{count}}</span>`;
      legend.appendChild(row);
    }});

    let dragging = false;
    let lastX = 0;
    let lastY = 0;
    canvas.addEventListener("pointerdown", event => {{
      dragging = true;
      lastX = event.clientX;
      lastY = event.clientY;
      canvas.setPointerCapture(event.pointerId);
    }});
    canvas.addEventListener("pointermove", event => {{
      if (!dragging) return;
      const dx = event.clientX - lastX;
      const dy = event.clientY - lastY;
      group.rotation.y += dx * 0.01;
      group.rotation.x += dy * 0.01;
      lastX = event.clientX;
      lastY = event.clientY;
    }});
    canvas.addEventListener("pointerup", () => dragging = false);
    canvas.addEventListener("wheel", event => {{
      event.preventDefault();
      const factor = event.deltaY > 0 ? 1.08 : 0.92;
      camera.position.multiplyScalar(factor);
    }}, {{ passive: false }});
    canvas.addEventListener("dblclick", () => {{
      group.rotation.set(0, 0, 0);
      camera.position.set(maxDim * 0.9, -maxDim * 1.25, maxDim * 0.85);
      camera.lookAt(0, 0, 0);
    }});

    function resizeRenderer() {{
      const stage = document.getElementById("three-stage");
      if (!stage) return;
      const rect = stage.getBoundingClientRect();
      if (rect.width < 10 || rect.height < 10) return;
      renderer.setSize(rect.width, rect.height, false);
      camera.aspect = rect.width / rect.height;
      camera.updateProjectionMatrix();
    }}
    window.addEventListener("resize", resizeRenderer);
    resizeRenderer();
    function animate() {{
      requestAnimationFrame(animate);
      renderer.render(scene, camera);
    }}
    animate();
    const querySlide = Number(new URLSearchParams(location.search).get("slide"));
    const querySlide = Number(new URLSearchParams(location.search).get("slide"));
    showSlide(Number.isFinite(querySlide) ? querySlide : 0);
  </script>
</body>
</html>
"""


def build_html(report: dict[str, Any], title: str, three_url: str, three_source: str | None) -> str:
    structure = report["structure"]
    cell = structure["cell"]
    nearest = structure["nearest_distances"]
    symmetry = structure["symmetry_attempt"]
    coordinates = structure["coordinates"]
    views = report.get("views", [])
    element_counts = ", ".join(f"{key}: {value}" for key, value in structure["element_counts"].items())
    limitations = report.get("limitations") or ["none"]
    not_assessed = report.get("not_assessed") or []
    report_json = json.dumps(browser_safe_report(report), ensure_ascii=False)
    escaped_title = html.escape(title)
    three_loader = three_loader_script(three_source, three_url)
    report_status = str(report.get("status", "UNKNOWN"))
    status_class = {
        "PASS": "evidence-pass",
        "WARN": "evidence-warn",
        "BLOCK": "evidence-block",
    }.get(report_status.upper(), "evidence-unknown")
    symmetry_label = f'{symmetry.get("international", "")} #{symmetry.get("number", "")} ({symmetry.get("status", "")})'
    not_assessed_text = "; ".join(str(item) for item in not_assessed) or "none"

    fact_rows = table_rows(
        [
            ["Formula", structure["formula"]],
            ["Atoms", structure["atom_count"]],
            ["Elements", element_counts],
            ["Cell", f'a={cell["a"]}, b={cell["b"]}, c={cell["c"]} Ang'],
            ["Angles", f'{cell["alpha"]}, {cell["beta"]}, {cell["gamma"]} deg'],
            ["Volume", f'{structure["volume_ang3"]} Ang^3'],
            ["Density", f'{structure["density_g_cm3"]} g/cm^3'],
            ["Symmetry", symmetry_label],
        ]
    )
    coord_rows = table_rows(
        [
            [item["index"], item["symbol"], item["cartesian_ang"], item["fractional"]]
            for item in coordinates["coordinate_sample"][:8]
        ]
    )
    pair_rows = table_rows(
        [
            [f'{item["i"]}-{item["j"]}', "-".join(item["symbols"]), item["distance_ang"]]
            for item in nearest.get("nearest_pairs_sample", [])[:8]
        ]
    )
    gap_rows = table_rows(
        [
            [item["axis"], item.get("largest_gap_ang"), item.get("occupied_span_estimate_ang")]
            for item in structure.get("axis_gap_estimates", [])
        ]
    )
    view_cards = "\n".join(
        f"""
          <figure class="view-card">
            <figcaption class="view-label">along {html.escape(view.get('axis', ''))} / {html.escape(view.get('x_axis', ''))}-{html.escape(view.get('y_axis', ''))}</figcaption>
            <img src="{html.escape(view.get('data_url') or '')}" alt="view along {html.escape(view.get('axis', ''))}">
          </figure>
        """
        for view in views
    )
    limit_text = "; ".join(str(item) for item in limitations)

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escaped_title}</title>
  <style>
    :root {{
      --bg:#e9edf3;
      --paper:#ffffff;
      --ink:#17202b;
      --muted:#647080;
      --line:#d5dbe5;
      --soft:#f6f8fb;
      --blue:#2458d3;
      --teal:#0f766e;
      --amber:#a16207;
      --red:#b42318;
    }}
    * {{ box-sizing:border-box; }}
    body {{
      margin:0;
      background:var(--bg);
      color:var(--ink);
      font-family:Inter,ui-sans-serif,system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif;
      overflow:hidden;
    }}
    .stage {{ width:100vw; height:100vh; display:grid; place-items:center; padding:16px; }}
    .sheet {{
      width:min(1600px,98vw);
      aspect-ratio:16/9;
      background:var(--paper);
      border:1px solid var(--line);
      border-radius:8px;
      box-shadow:0 18px 44px rgba(16,24,40,.14);
      padding:18px;
      display:grid;
      grid-template-rows:auto 1fr;
      gap:14px;
      overflow:hidden;
    }}
    .brief-header {{
      display:grid;
      grid-template-columns:minmax(0,1fr) auto;
      gap:18px;
      align-items:end;
      border-bottom:1px solid var(--line);
      padding-bottom:12px;
    }}
    h1 {{ margin:0; font-size:30px; line-height:1.08; letter-spacing:0; }}
    h2 {{ margin:0; font-size:14px; line-height:1.2; letter-spacing:0; }}
    .eyebrow {{ color:var(--teal); font-size:12px; font-weight:700; margin-bottom:5px; text-transform:uppercase; }}
    .tag {{ color:var(--muted); font-size:12px; margin-top:5px; line-height:1.35; }}
    .evidence-strip {{ display:grid; grid-template-columns:repeat(4,auto); gap:8px; align-items:stretch; }}
    .evidence-chip {{
      min-width:112px;
      border:1px solid var(--line);
      border-radius:7px;
      background:#fbfcfe;
      padding:8px 10px;
      color:var(--muted);
      font-size:11px;
      line-height:1.2;
    }}
    .evidence-chip b {{ display:block; margin-top:4px; color:var(--ink); font-size:15px; line-height:1.1; white-space:nowrap; }}
    .evidence-pass {{ border-color:rgba(15,118,110,.35); background:#f0fdfa; }}
    .evidence-warn {{ border-color:rgba(161,98,7,.35); background:#fffbeb; }}
    .evidence-block {{ border-color:rgba(180,35,24,.35); background:#fff1f2; }}
    .content {{ min-height:0; display:grid; grid-template-columns:1.16fr .78fr 1fr; gap:12px; }}
    .panel {{ min-height:0; border:1px solid var(--line); border-radius:8px; background:var(--soft); padding:10px; overflow:hidden; }}
    .panel-heading {{ display:flex; align-items:baseline; justify-content:space-between; gap:10px; margin-bottom:8px; }}
    .panel-note {{ color:var(--muted); font-size:10px; line-height:1.25; }}
    .three-panel {{ display:grid; grid-template-rows:auto 1fr; gap:8px; }}
    #three-stage {{
      position:relative;
      min-height:0;
      border:1px solid var(--line);
      border-radius:7px;
      background:
        linear-gradient(rgba(36,88,211,.045) 1px, transparent 1px),
        linear-gradient(90deg, rgba(36,88,211,.045) 1px, transparent 1px),
        #f8fafc;
      background-size:24px 24px;
      overflow:hidden;
    }}
    #three-canvas {{ width:100%; height:100%; display:block; }}
    .view-buttons {{ position:absolute; left:10px; top:10px; display:inline-flex; overflow:hidden; border:1px solid var(--line); border-radius:6px; background:rgba(255,255,255,.94); box-shadow:0 6px 16px rgba(16,24,40,.10); }}
    .view-buttons button {{ min-width:31px; height:28px; padding:0 9px; border:0; border-right:1px solid var(--line); background:transparent; color:var(--muted); font-size:12px; font-weight:700; cursor:pointer; }}
    .view-buttons button:last-child {{ border-right:0; }}
    .view-buttons button.active {{ background:var(--ink); color:#fff; }}
    .measurement-tooltip {{ position:absolute; z-index:5; max-width:220px; padding:7px 9px; border:1px solid var(--line); border-radius:6px; background:rgba(255,255,255,.97); color:var(--ink); font-size:11px; box-shadow:0 10px 24px rgba(16,24,40,.18); pointer-events:none; }}
    .legend {{ position:absolute; right:10px; bottom:10px; display:flex; flex-wrap:wrap; justify-content:flex-end; gap:6px; max-width:62%; }}
    .legend-item {{ display:flex; align-items:center; gap:5px; padding:5px 7px; border:1px solid var(--line); border-radius:999px; background:rgba(255,255,255,.9); color:var(--muted); font-size:11px; }}
    .dot {{ width:12px; height:12px; border-radius:50%; border:1px solid rgba(0,0,0,.35); display:inline-block; }}
    .reference-views {{ display:grid; grid-template-rows:auto repeat(3,minmax(0,1fr)); gap:8px; }}
    .view-card {{ position:relative; margin:0; min-height:0; height:100%; border:1px solid var(--line); border-radius:7px; padding:6px; background:#fff; overflow:hidden; }}
    .view-card img {{ width:100%; height:100%; max-width:100%; max-height:100%; object-fit:contain; min-width:0; min-height:0; display:block; }}
    .view-label {{ position:absolute; left:8px; top:8px; z-index:1; padding:4px 7px; border:1px solid var(--line); border-radius:999px; background:rgba(255,255,255,.93); color:var(--muted); font-size:10px; line-height:1; white-space:nowrap; }}
    .facts-panel {{ display:grid; grid-template-rows:auto auto minmax(0,1fr) minmax(0,1fr) auto; gap:8px; }}
    .facts-grid {{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:6px; }}
    .fact {{ border:1px solid var(--line); border-radius:6px; background:#fff; padding:7px 8px; min-width:0; }}
    .fact span {{ display:block; color:var(--muted); font-size:10px; line-height:1.15; }}
    .fact b {{ display:block; margin-top:3px; color:var(--ink); font-size:13px; line-height:1.15; overflow-wrap:anywhere; }}
    table {{ width:100%; border-collapse:collapse; font-size:11px; background:#fff; }}
    td, th {{ border-bottom:1px solid var(--line); text-align:left; padding:4px 5px; vertical-align:top; }}
    td:last-child, th:last-child {{ text-align:right; }}
    th {{ background:#eef3f8; color:#303b49; }}
    .table-box {{ min-height:0; overflow:auto; border:1px solid var(--line); border-radius:6px; background:#fff; }}
    .axis-gap-note {{ border:1px solid rgba(161,98,7,.30); border-radius:6px; background:#fffbeb; color:#68480d; font-size:10px; line-height:1.3; padding:6px 7px; }}
    .brief {{ color:var(--muted); font-size:10px; line-height:1.35; }}
    .path {{ font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; font-size:10px; color:var(--muted); word-break:break-all; }}
  </style>
</head>
<body>
  <main class="stage">
    <section class="sheet report-brief">
      <header class="brief-header">
        <div>
          <div class="eyebrow">CIF Structure Analysis Brief</div>
          <h1>{escaped_title}</h1>
          <div class="tag">Source of truth: analysis JSON / Markdown. Structure facts only; no DFT setup or physics credibility judgment.</div>
        </div>
        <div class="evidence-strip" aria-label="Evidence summary">
          <span class="evidence-chip {status_class}">Status <b>{html.escape(report_status)}</b></span>
          <span class="evidence-chip">Formula <b>{html.escape(str(structure["formula"]))}</b></span>
          <span class="evidence-chip">Symmetry <b>{html.escape(symmetry_label)}</b></span>
          <span class="evidence-chip">Min d <b>{html.escape(str(nearest["min_distance_ang"]))} Ang</b></span>
        </div>
      </header>
      <div class="content">
        <section class="panel three-panel">
          <div class="panel-heading">
            <h2>Interactive 3D Structure</h2>
            <span class="panel-note">drag rotate / wheel zoom / click bond</span>
          </div>
          <div id="three-stage">
            <canvas id="three-canvas"></canvas>
            <div class="view-buttons" aria-label="3D view controls">
              <button type="button" data-view-axis="a" title="View along a">a</button>
              <button type="button" data-view-axis="b" title="View along b">b</button>
              <button type="button" data-view-axis="c" title="View along c">c</button>
              <button type="button" data-view-axis="reset" title="Reset view">Reset</button>
            </div>
            <div id="legend" class="legend"></div>
            <div id="bond-tooltip" class="measurement-tooltip bond-tooltip" hidden></div>
          </div>
        </section>
        <section class="panel reference-views">
          <div class="panel-heading">
            <h2>Reference Views</h2>
            <span class="panel-note">atom-extent crop</span>
          </div>
          {view_cards}
        </section>
        <section class="panel facts-panel">
          <div class="panel-heading">
            <h2>Structure Facts</h2>
            <span class="panel-note">values from JSON artifact</span>
          </div>
          <div class="facts-grid">
            <div class="fact"><span>Atoms</span><b>{html.escape(str(structure["atom_count"]))}</b></div>
            <div class="fact"><span>Cell c</span><b>{html.escape(str(cell["c"]))} Ang</b></div>
            <div class="fact"><span>Volume</span><b>{html.escape(str(structure["volume_ang3"]))} Ang^3</b></div>
            <div class="fact"><span>Density</span><b>{html.escape(str(structure["density_g_cm3"]))} g/cm^3</b></div>
          </div>
          <div>
            <h2>Coordinates</h2>
            <div class="table-box"><table><thead><tr><th>#</th><th>El.</th><th>Cartesian Ang</th><th>Fractional</th></tr></thead><tbody>{coord_rows}</tbody></table></div>
          </div>
          <div>
            <h2>Nearest Pairs</h2>
            <div class="table-box"><table><thead><tr><th>Pair</th><th>Symbols</th><th>Ang</th></tr></thead><tbody>{pair_rows}</tbody></table></div>
          </div>
          <div class="brief">
            <div class="axis-gap-note"><b>Axis gaps:</b> coordinate-gap estimate, not a physical vacuum conclusion.</div>
            <div class="table-box" style="max-height:74px;"><table><thead><tr><th>Axis</th><th>Gap Ang</th><th>Span Ang</th></tr></thead><tbody>{gap_rows}</tbody></table></div>
            <div style="margin-top:6px;"><b>Limits:</b> {html.escape(limit_text)}. Not assessed: {html.escape(not_assessed_text)}.</div>
            <div class="path">Source artifacts: analysis JSON / Markdown; local file paths are intentionally omitted.</div>
          </div>
        </section>
      </div>
    </section>
  </main>

  <script type="module">
{three_loader}
    const REPORT = {report_json};
    const ELEMENT_COLORS = {{ Hf: 0x6a5acd, Br: 0x8b4513, Ti: 0x7f7f7f, Se: 0xff7f0e, Na: 0x1f77b4, Cl: 0x2ca02c }};
    const ELEMENT_RADII = {{ Hf: 0.34, Br: 0.24, Ti: 0.28, Se: 0.27, Na: 0.22, Cl: 0.22 }};

    function degToRad(value) {{ return value * Math.PI / 180; }}
    function cellVectors(cell) {{
      const a = cell.a, b = cell.b, c = cell.c;
      const alpha = degToRad(cell.alpha), beta = degToRad(cell.beta), gamma = degToRad(cell.gamma);
      const avec = new THREE.Vector3(a, 0, 0);
      const bvec = new THREE.Vector3(b * Math.cos(gamma), b * Math.sin(gamma), 0);
      const cx = c * Math.cos(beta);
      const cy = c * (Math.cos(alpha) - Math.cos(beta) * Math.cos(gamma)) / Math.sin(gamma);
      const cz = Math.sqrt(Math.max(c * c - cx * cx - cy * cy, 0));
      return [avec, bvec, new THREE.Vector3(cx, cy, cz)];
    }}
    function fromFractional(frac, vectors) {{
      return new THREE.Vector3().addScaledVector(vectors[0], frac[0]).addScaledVector(vectors[1], frac[1]).addScaledVector(vectors[2], frac[2]);
    }}

    const canvas = document.getElementById("three-canvas");
    const renderer = new THREE.WebGLRenderer({{ canvas, antialias: true }});
    renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
    renderer.setClearColor(0xf8fafc, 1);
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(34, 1, 0.1, 1000);
    const TARGET = new THREE.Vector3(0, 0, 0);
    const modelRoot = new THREE.Group();
    scene.add(modelRoot);
    scene.add(new THREE.AmbientLight(0xffffff, 0.64));
    const light = new THREE.DirectionalLight(0xffffff, 1.18);
    light.position.set(6, -10, 12);
    scene.add(light);
    const fill = new THREE.DirectionalLight(0xabc6ff, 0.42);
    fill.position.set(-8, 4, 8);
    scene.add(fill);

    const vectors = cellVectors(REPORT.structure.cell);
    const rawCorners = [[0,0,0],[1,0,0],[1,1,0],[0,1,0],[0,0,0],[0,0,1],[1,0,1],[1,1,1],[0,1,1],[0,0,1],[1,0,0],[1,0,1],[1,1,1],[1,1,0],[0,1,0],[0,1,1]].map(frac => fromFractional(frac, vectors));
    const atomsRaw = REPORT.structure.coordinates.coordinate_sample.map(item => ({{ index: item.index, symbol: item.symbol, rawPosition: fromFractional(item.fractional, vectors) }}));
    const allPoints = rawCorners.concat(atomsRaw.map(atom => atom.rawPosition));
    const box = new THREE.Box3().setFromPoints(allPoints);
    const structureCenter = new THREE.Vector3();
    box.getCenter(structureCenter);
    const size = new THREE.Vector3();
    box.getSize(size);
    const maxDim = Math.max(size.x, size.y, size.z, 1);
    const centeredCorners = rawCorners.map(point => point.clone().sub(structureCenter));
    modelRoot.add(new THREE.Line(new THREE.BufferGeometry().setFromPoints(centeredCorners), new THREE.LineBasicMaterial({{ color: 0x29313d }})));
    const atoms = atomsRaw.map(atom => ({{ ...atom, position: atom.rawPosition.clone().sub(structureCenter) }}));
    const atomByIndex = new Map(atoms.map(atom => [atom.index, atom]));
    const BOND_RADIUS = Math.max(maxDim * 0.0025, 0.035);
    const BOND_PICK_RADIUS = Math.max(BOND_RADIUS * 2.8, 0.12);
    const bondMaterial = new THREE.MeshStandardMaterial({{ color: 0x7c8794, roughness: 0.5, metalness: 0.02, transparent: true, opacity: 0.76 }});
    const bondPickMaterial = new THREE.MeshBasicMaterial({{ color: 0xffffff, transparent: true, opacity: 0.0, depthWrite: false }});
    const bondPickTargets = [];

    function createBondMesh(start, end, radius, material) {{
      const direction = end.clone().sub(start);
      const length = direction.length();
      if (length <= 1e-6) return null;
      const geometry = new THREE.CylinderGeometry(radius, radius, length, 16);
      const mesh = new THREE.Mesh(geometry, material);
      mesh.position.copy(start).add(end).multiplyScalar(0.5);
      mesh.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), direction.clone().normalize());
      return mesh;
    }}

    function addBond(pair) {{
      const startAtom = atomByIndex.get(pair.i);
      const endAtom = atomByIndex.get(pair.j);
      if (!startAtom || !endAtom) return;
      const visibleBond = createBondMesh(startAtom.position, endAtom.position, BOND_RADIUS, bondMaterial);
      const pickBond = createBondMesh(startAtom.position, endAtom.position, BOND_PICK_RADIUS, bondPickMaterial);
      if (!visibleBond || !pickBond) return;
      const directLength = startAtom.position.distanceTo(endAtom.position);
      const bondData = {{
        type: "bond",
        i: pair.i,
        j: pair.j,
        symbols: pair.symbols || [startAtom.symbol, endAtom.symbol],
        distance_ang: Number(pair.distance_ang ?? directLength),
      }};
      visibleBond.userData = bondData;
      pickBond.userData = bondData;
      modelRoot.add(visibleBond);
      modelRoot.add(pickBond);
      bondPickTargets.push(pickBond);
    }}

    const bondPairs = REPORT.structure.nearest_distances.nearest_neighbor_bond_pairs
      || REPORT.structure.nearest_distances.nearest_pairs_sample
      || [];
    bondPairs.forEach(addBond);

    atoms.forEach(atom => {{
      const color = ELEMENT_COLORS[atom.symbol] ?? 0xd62728;
      const radius = ELEMENT_RADII[atom.symbol] ?? 0.24;
      const sphere = new THREE.Mesh(new THREE.SphereGeometry(radius, 48, 32), new THREE.MeshStandardMaterial({{ color, roughness: 0.36, metalness: 0.08 }}));
      sphere.position.copy(atom.position);
      modelRoot.add(sphere);
    }});
    const legend = document.getElementById("legend");
    Object.entries(REPORT.structure.element_counts).forEach(([symbol, count]) => {{
      const color = (ELEMENT_COLORS[symbol] ?? 0xd62728).toString(16).padStart(6, "0");
      const row = document.createElement("div");
      row.className = "legend-item";
      row.innerHTML = `<span class="dot" style="background:#${{color}}"></span><span>${{symbol}} × ${{count}}</span>`;
      legend.appendChild(row);
    }});
    const viewButtons = Array.from(document.querySelectorAll("[data-view-axis]"));
    const cameraDistance = Math.max(maxDim * 1.75, 8);
    const minCameraDistance = Math.max(maxDim * 0.55, 2.2);
    const maxCameraDistance = Math.max(maxDim * 5.0, 20);
    camera.near = Math.max(cameraDistance / 150, 0.05);
    camera.far = Math.max(cameraDistance * 12, 1000);
    camera.updateProjectionMatrix();

    function normalizedVector(vector, fallback) {{
      const copy = vector.clone();
      if (copy.lengthSq() <= 1e-9) return fallback.clone().normalize();
      return copy.normalize();
    }}

    function setActiveView(axis) {{
      viewButtons.forEach(button => button.classList.toggle("active", button.dataset.viewAxis === axis));
    }}

    function setCamera(direction, up, distance = cameraDistance) {{
      const safeDirection = normalizedVector(direction, new THREE.Vector3(0.9, -1.25, 0.85));
      const safeUp = normalizedVector(up, vectors[2]);
      const clampedDistance = Math.min(maxCameraDistance, Math.max(minCameraDistance, distance));
      camera.position.copy(safeDirection.multiplyScalar(clampedDistance));
      camera.up.copy(safeUp);
      camera.lookAt(TARGET);
      camera.updateProjectionMatrix();
    }}

    const VIEW_AXES = {{
      a: {{ direction: vectors[0], up: vectors[2] }},
      b: {{ direction: vectors[1], up: vectors[0] }},
      c: {{ direction: vectors[2], up: vectors[1] }},
    }};

    function hideBondTooltip() {{
      document.getElementById("bond-tooltip").hidden = true;
    }}

    function setViewAxis(axis) {{
      const view = VIEW_AXES[axis];
      if (!view) return;
      modelRoot.rotation.set(0, 0, 0);
      setCamera(view.direction, view.up, cameraDistance);
      setActiveView(axis);
      hideBondTooltip();
    }}

    function setDefaultView() {{
      modelRoot.rotation.set(0, 0, 0);
      setCamera(new THREE.Vector3(0.9, -1.25, 0.85), vectors[2], cameraDistance);
      setActiveView(null);
      hideBondTooltip();
    }}

    viewButtons.forEach(button => button.addEventListener("click", () => {{
      const axis = button.dataset.viewAxis;
      if (axis === "reset") setDefaultView();
      else setViewAxis(axis);
    }}));
    setDefaultView();

    const raycaster = new THREE.Raycaster();
    const pointer = new THREE.Vector2();
    const bondTooltip = document.getElementById("bond-tooltip");

    function showBondTooltip(bondData, event) {{
      const rect = document.getElementById("three-stage").getBoundingClientRect();
      const symbols = bondData.symbols || [];
      bondTooltip.textContent = `${{symbols.join("-")}} ${{bondData.i}}-${{bondData.j}} - ${{bondData.distance_ang.toFixed(4)}} Ang`;
      bondTooltip.style.left = `${{Math.min(event.clientX - rect.left + 10, rect.width - 185)}}px`;
      bondTooltip.style.top = `${{Math.min(event.clientY - rect.top + 10, rect.height - 44)}}px`;
      bondTooltip.hidden = false;
    }}

    function pickBond(event) {{
      const rect = canvas.getBoundingClientRect();
      pointer.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      pointer.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;
      raycaster.setFromCamera(pointer, camera);
      const hits = raycaster.intersectObjects(bondPickTargets, false);
      if (hits.length > 0) {{
        showBondTooltip(hits[0].object.userData, event);
      }} else {{
        hideBondTooltip();
      }}
    }}

    function zoomCamera(factor) {{
      const distance = Math.min(maxCameraDistance, Math.max(minCameraDistance, camera.position.length() * factor));
      const direction = normalizedVector(camera.position, new THREE.Vector3(0.9, -1.25, 0.85));
      camera.position.copy(direction.multiplyScalar(distance));
      camera.lookAt(TARGET);
    }}

    let dragging = false, pointerMoved = false, lastX = 0, lastY = 0, startX = 0, startY = 0;
    canvas.addEventListener("pointerdown", event => {{
      dragging = true;
      pointerMoved = false;
      startX = lastX = event.clientX;
      startY = lastY = event.clientY;
      canvas.setPointerCapture(event.pointerId);
    }});
    canvas.addEventListener("pointermove", event => {{
      if (!dragging) return;
      const dx = event.clientX - lastX;
      const dy = event.clientY - lastY;
      if (Math.hypot(event.clientX - startX, event.clientY - startY) > 4) pointerMoved = true;
      if (pointerMoved) {{
        modelRoot.rotation.y += dx * 0.01;
        modelRoot.rotation.x += dy * 0.01;
        setActiveView(null);
        hideBondTooltip();
      }}
      lastX = event.clientX;
      lastY = event.clientY;
    }});
    canvas.addEventListener("pointerup", event => {{
      if (dragging && !pointerMoved) pickBond(event);
      dragging = false;
    }});
    canvas.addEventListener("pointerleave", () => {{ dragging = false; }});
    canvas.addEventListener("wheel", event => {{
      event.preventDefault();
      hideBondTooltip();
      zoomCamera(event.deltaY > 0 ? 1.08 : 0.92);
    }}, {{ passive: false }});
    canvas.addEventListener("dblclick", setDefaultView);
    function resizeRenderer() {{
      const rect = document.getElementById("three-stage").getBoundingClientRect();
      if (rect.width < 10 || rect.height < 10) return;
      renderer.setSize(rect.width, rect.height, false);
      camera.aspect = rect.width / rect.height;
      camera.lookAt(TARGET);
      camera.updateProjectionMatrix();
    }}
    window.addEventListener("resize", resizeRenderer);
    resizeRenderer();
    function animate() {{ requestAnimationFrame(animate); camera.lookAt(TARGET); renderer.render(scene, camera); }}
    animate();
  </script>
</body>
</html>
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build an HTML slide deck from CIF structure analysis JSON.")
    parser.add_argument("--analysis-json", required=True, help="Input analysis JSON from analyze_cif.py.")
    parser.add_argument("--output", required=True, help="Output HTML file.")
    parser.add_argument("--title", default="CIF Structure Analysis Deck", help="Deck title.")
    parser.add_argument("--three-url", default=DEFAULT_THREE_URL, help="Three.js module URL used when no local module is embedded.")
    parser.add_argument("--three-module-path", default=str(DEFAULT_THREE_MODULE_PATH), help="Local Three.js module to embed for offline HTML.")
    parser.add_argument("--no-inline-three", action="store_true", help="Use --three-url instead of embedding the local Three.js module.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    analysis_path = Path(args.analysis_json).expanduser().resolve()
    output_path = Path(args.output).expanduser().resolve()
    report = prepared_report(read_report(analysis_path))
    three_source = None
    if not args.no_inline_three:
        three_path = Path(args.three_module_path).expanduser().resolve()
        if not three_path.exists():
            raise FileNotFoundError(f"Three.js module not found: {three_path}")
        three_source = three_path.read_text(encoding="utf-8")
    html_text = build_html(report, args.title, args.three_url, three_source)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html_text, encoding="utf-8")
    print(f"wrote {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
