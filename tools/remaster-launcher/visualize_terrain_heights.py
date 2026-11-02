"""Visual inspection and interactive 3D review tooling for terrain height maps.

Generates self-contained HTML5/WebGL interactive inspection reports and PNG contact
sheets comparing colour albedo, authored normals, reconstructed height fields,
re-derived normals, and angular error heatmaps. Zero external imaging dependencies.
"""

from __future__ import annotations

import base64
import html
import io
import json
import math
from pathlib import Path
import struct
import zlib

try:
    import numpy as np
except ImportError:
    np = None


def encode_png(width: int, height: int, rgba: bytes) -> bytes:
    """Encode raw 8-bit RGBA pixels into standard PNG byte stream without external libraries."""
    if width <= 0 or height <= 0:
        raise ValueError("Invalid image dimensions for PNG encoding")
    expected_bytes = width * height * 4
    if len(rgba) < expected_bytes:
        raise ValueError(f"Incomplete RGBA payload: got {len(rgba)}, expected {expected_bytes}")

    raw_scanlines = bytearray()
    stride = width * 4
    for y in range(height):
        raw_scanlines.append(0)  # Filter type 0 (None)
        raw_scanlines.extend(rgba[y * stride : (y + 1) * stride])

    compressed = zlib.compress(bytes(raw_scanlines), level=6)

    def make_chunk(tag: bytes, data: bytes) -> bytes:
        crc = zlib.crc32(tag + data) & 0xFFFFFFFF
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", crc)

    ihdr = struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + make_chunk(b"IHDR", ihdr)
        + make_chunk(b"IDAT", compressed)
        + make_chunk(b"IEND", b"")
    )


def compute_angular_error_heatmap(
    authored_normals_rgba: bytes,
    reconstructed_height_rgba: bytes,
    width: int,
    height: int,
) -> tuple[bytes, float, float]:
    """Calculate per-pixel angular error and render an RGBA heatmap.

    Returns:
        (heatmap_rgba_bytes, median_angular_error_deg, normal_correlation)
    """
    if np is None:
        # Fallback dummy heatmap if numpy is not installed
        dummy = bytearray()
        for _ in range(width * height):
            dummy.extend((0, 200, 0, 255))
        return bytes(dummy), 0.0, 1.0

    # Unpack authored normals: RGB in [0, 255] -> [-1, 1]
    raw_auth = np.frombuffer(authored_normals_rgba[: width * height * 4], dtype=np.uint8).reshape(height, width, 4)
    nx = raw_auth[:, :, 0].astype(np.float32) / 127.5 - 1.0
    ny = raw_auth[:, :, 1].astype(np.float32) / 127.5 - 1.0
    nz = np.clip(raw_auth[:, :, 2].astype(np.float32) / 127.5 - 1.0, 0.01, 1.0)
    len_auth = np.sqrt(nx * nx + ny * ny + nz * nz)
    nx /= len_auth
    ny /= len_auth
    nz /= len_auth

    # Derive normals from height map
    raw_h = np.frombuffer(reconstructed_height_rgba[: width * height * 4], dtype=np.uint8).reshape(height, width, 4)
    h_field = raw_h[:, :, 0].astype(np.float32) / 255.0

    # Central difference slopes (periodic boundary)
    p = (np.roll(h_field, -1, axis=1) - np.roll(h_field, 1, axis=1)) * 0.5 * 10.0
    q = (np.roll(h_field, -1, axis=0) - np.roll(h_field, 1, axis=0)) * 0.5 * 10.0
    rnz = 1.0 / np.sqrt(p * p + q * q + 1.0)
    rnx = -p * rnz
    rny = -q * rnz

    # Dot product -> angular error in degrees
    dot = np.clip(nx * rnx + ny * rny + nz * rnz, -1.0, 1.0)
    ang_err = np.degrees(np.arccos(dot))
    median_err = float(np.median(ang_err))

    # Correlation
    var_auth = float(np.var(nx) + np.var(ny))
    var_re = float(np.var(rnx) + np.var(rny))
    if var_auth > 1e-6 and var_re > 1e-6:
        cov = float(np.mean((nx - np.mean(nx)) * (rnx - np.mean(rnx)) + (ny - np.mean(ny)) * (rny - np.mean(rny))))
        corr = cov / math.sqrt(var_auth * var_re)
    else:
        corr = 1.0

    # Colorize heatmap:
    # 0 deg: Green (0, 220, 80)
    # 15 deg: Yellow (240, 210, 0)
    # 30 deg: Orange (255, 120, 0)
    # >= 45 deg: Red (230, 30, 30)
    err_norm = np.clip(ang_err / 40.0, 0.0, 1.0)
    heat_r = np.clip(err_norm * 2.0 * 255.0, 0, 255).astype(np.uint8)
    heat_g = np.clip((1.0 - np.maximum(0.0, err_norm - 0.4) * 1.6) * 255.0, 0, 255).astype(np.uint8)
    heat_b = np.full_like(heat_r, 30)
    heat_a = np.full_like(heat_r, 255)

    heatmap_rgba = np.dstack((heat_r, heat_g, heat_b, heat_a)).tobytes()
    return heatmap_rgba, median_err, corr


def derive_normal_map_rgba(reconstructed_height_rgba: bytes, width: int, height: int) -> bytes:
    """Compute re-derived normal map from height field as an RGBA byte buffer."""
    if np is None:
        return reconstructed_height_rgba
    raw_h = np.frombuffer(reconstructed_height_rgba[: width * height * 4], dtype=np.uint8).reshape(height, width, 4)
    h_field = raw_h[:, :, 0].astype(np.float32) / 255.0

    p = (np.roll(h_field, -1, axis=1) - np.roll(h_field, 1, axis=1)) * 0.5 * 10.0
    q = (np.roll(h_field, -1, axis=0) - np.roll(h_field, 1, axis=0)) * 0.5 * 10.0
    nz = 1.0 / np.sqrt(p * p + q * q + 1.0)
    nx = -p * nz
    ny = -q * nz

    out_r = np.clip((nx * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    out_g = np.clip((ny * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    out_b = np.clip((nz * 0.5 + 0.5) * 255.0, 0, 255).astype(np.uint8)
    out_a = np.full_like(out_r, 255)
    return np.dstack((out_r, out_g, out_b, out_a)).tobytes()


def generate_contact_sheet_png(
    color_rgba: bytes,
    normal_rgba: bytes,
    height_rgba: bytes,
    renorm_rgba: bytes,
    heatmap_rgba: bytes,
    width: int,
    height: int,
) -> bytes:
    """Create a 5-panel side-by-side contact sheet PNG: [Colour | Normal | Height | Re-normal | Error Heatmap]."""
    total_width = width * 5
    out = bytearray(total_width * height * 4)

    panels = [color_rgba, normal_rgba, height_rgba, renorm_rgba, heatmap_rgba]
    for y in range(height):
        for p_idx, panel in enumerate(panels):
            src_offset = (y * width) * 4
            dst_offset = ((y * total_width) + (p_idx * width)) * 4
            chunk_len = width * 4
            out[dst_offset : dst_offset + chunk_len] = panel[src_offset : src_offset + chunk_len]

    return encode_png(total_width, height, bytes(out))


HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>__TITLE__ - __REGION__</title>
  <style>
    :root {
      --bg: #121316;
      --card-bg: #1a1c23;
      --border: #2c303c;
      --accent: #4daafc;
      --text: #e1e4ea;
      --text-muted: #8a91a0;
      --success: #22c55e;
      --warning: #f59e0b;
      --danger: #ef4444;
    }
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      display: flex;
      flex-direction: column;
      height: 100vh;
      overflow: hidden;
    }
    header {
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }
    header h1 { font-size: 1.15rem; font-weight: 600; display: flex; align-items: center; gap: 8px; }
    header .badge { background: var(--accent); color: #000; font-size: 0.75rem; font-weight: 700; padding: 2px 8px; border-radius: 4px; text-transform: uppercase; }
    .workspace { display: flex; flex: 1; overflow: hidden; }
    .sidebar {
      width: 340px;
      background: var(--card-bg);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      flex-shrink: 0;
    }
    .search-box { padding: 12px; border-bottom: 1px solid var(--border); }
    .search-box input, .search-box select {
      width: 100%;
      background: var(--bg);
      border: 1px solid var(--border);
      color: var(--text);
      padding: 8px 10px;
      border-radius: 4px;
      font-size: 0.85rem;
      margin-bottom: 6px;
    }
    .item-list { flex: 1; overflow-y: auto; list-style: none; }
    .item-entry {
      padding: 10px 14px;
      border-bottom: 1px solid var(--border);
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: background 0.15s;
    }
    .item-entry:hover { background: #232630; }
    .item-entry.active { background: #2a3142; border-left: 3px solid var(--accent); }
    .item-name { font-weight: 500; font-size: 0.85rem; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; max-width: 190px; }
    .item-family { font-size: 0.75rem; color: var(--text-muted); }
    .stat-pill { font-size: 0.75rem; padding: 2px 6px; border-radius: 3px; font-weight: 600; font-family: monospace; }
    .pill-pass { background: rgba(34, 197, 94, 0.15); color: var(--success); }
    .pill-warn { background: rgba(245, 158, 11, 0.15); color: var(--warning); }
    .pill-fail { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
    .main-view { flex: 1; display: flex; flex-direction: column; overflow: hidden; }
    .viewport-container {
      flex: 1;
      display: flex;
      gap: 16px;
      padding: 16px;
      overflow-y: auto;
    }
    .preview-panel {
      flex: 1;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      min-width: 400px;
    }
    .panel-header {
      padding: 10px 16px;
      border-bottom: 1px solid var(--border);
      font-size: 0.85rem;
      font-weight: 600;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .panel-body {
      flex: 1;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;
      background: #0d0e12;
      min-height: 380px;
    }
    canvas#glCanvas { width: 100%; height: 100%; display: block; }
    .controls-overlay {
      position: absolute;
      bottom: 12px;
      left: 12px;
      right: 12px;
      background: rgba(18, 19, 22, 0.85);
      backdrop-filter: blur(4px);
      padding: 10px 14px;
      border-radius: 6px;
      border: 1px solid var(--border);
      display: flex;
      gap: 16px;
      align-items: center;
      font-size: 0.8rem;
    }
    .control-group { display: flex; align-items: center; gap: 8px; }
    .control-group label { color: var(--text-muted); font-size: 0.75rem; }
    .control-group input[type="range"] { width: 90px; accent-color: var(--accent); }
    .channels-panel {
      width: 440px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      display: flex;
      flex-direction: column;
      overflow-y: auto;
      padding: 14px;
      gap: 14px;
    }
    .channel-card { background: var(--bg); border: 1px solid var(--border); border-radius: 4px; padding: 8px; }
    .channel-header { font-size: 0.75rem; font-weight: 600; color: var(--text-muted); margin-bottom: 6px; display: flex; justify-content: space-between; }
    .channel-img { width: 100%; height: auto; border-radius: 3px; display: block; image-rendering: pixelated; }
    .metric-row { display: flex; justify-content: space-between; font-size: 0.8rem; padding: 4px 0; border-bottom: 1px solid #232733; }
    .metric-label { color: var(--text-muted); }
    .metric-val { font-family: monospace; font-weight: 600; }
  </style>
</head>
<body>
  <header>
    <h1>MW3 Remaster Terrain Surface Inspector <span class="badge">__REGION__</span></h1>
    <div style="font-size: 0.85rem; color: var(--text-muted);">
      Drag in 3D viewport to steer directional light | Scroll to zoom
    </div>
  </header>

  <div class="workspace">
    <div class="sidebar">
      <div class="search-box">
        <input type="text" id="searchInput" placeholder="Search texture name...">
        <select id="familyFilter">
          <option value="">All Families</option>
          <option value="cliff">Cliff</option>
          <option value="rock">Rock</option>
          <option value="road">Road</option>
          <option value="asphalt">Asphalt</option>
          <option value="sand">Sand</option>
          <option value="beach">Beach</option>
          <option value="terrain">Terrain</option>
          <option value="default">Default</option>
        </select>
      </div>
      <ul class="item-list" id="itemList"></ul>
    </div>

    <div class="main-view">
      <div class="viewport-container">
        <!-- Interactive 3D WebGL Relief Viewport -->
        <div class="preview-panel">
          <div class="panel-header">
            <span id="activeTitle">Select Texture</span>
            <div style="display: flex; gap: 8px;">
              <label style="font-size:0.75rem;"><input type="checkbox" id="togglePOM" checked> POM Active</label>
              <label style="font-size:0.75rem;"><input type="checkbox" id="toggleColor" checked> Albedo</label>
            </div>
          </div>
          <div class="panel-body">
            <canvas id="glCanvas"></canvas>
            <div class="controls-overlay">
              <div class="control-group">
                <label>Amplitude</label>
                <input type="range" id="paramAmp" min="0" max="100" value="35">
              </div>
              <div class="control-group">
                <label>Roughness</label>
                <input type="range" id="paramRough" min="0" max="100" value="75">
              </div>
              <div class="control-group">
                <label>Reflectivity</label>
                <input type="range" id="paramRefl" min="0" max="20" value="4">
              </div>
              <div class="control-group">
                <label>Light Angle</label>
                <input type="range" id="paramLight" min="0" max="360" value="45">
              </div>
            </div>
          </div>
        </div>

        <!-- Channel Inspection Strip -->
        <div class="channels-panel">
          <h3 style="font-size: 0.9rem; font-weight: 600;">Quality & Material Profile</h3>
          <div id="metricsCard" style="margin-bottom: 8px;"></div>

          <div class="channel-card">
            <div class="channel-header"><span>COLOUR (ALBEDO)</span><span id="dimLabel"></span></div>
            <img id="imgColor" class="channel-img" alt="Albedo">
          </div>

          <div class="channel-card">
            <div class="channel-header"><span>AUTHORED NORMAL</span><span>TANGENT RGB</span></div>
            <img id="imgNormal" class="channel-img" alt="Normal">
          </div>

          <div class="channel-card">
            <div class="channel-header"><span>DERIVED HEIGHT</span><span>FRANKOT-CHELLAPPA</span></div>
            <img id="imgHeight" class="channel-img" alt="Height">
          </div>

          <div class="channel-card">
            <div class="channel-header"><span>RE-DERIVED NORMAL</span><span>CENTRAL DIFF</span></div>
            <img id="imgRenorm" class="channel-img" alt="Re-derived Normal">
          </div>

          <div class="channel-card">
            <div class="channel-header"><span>ANGULAR ERROR HEATMAP</span><span>GREEN: &lt;5° | RED: &gt;35°</span></div>
            <img id="imgHeatmap" class="channel-img" alt="Error Heatmap">
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const DATA = __JSON_DATA__;
    let currentIdx = 0;

    const itemList = document.getElementById("itemList");
    const searchInput = document.getElementById("searchInput");
    const familyFilter = document.getElementById("familyFilter");

    function renderList() {
      const q = searchInput.value.toLowerCase();
      const fam = familyFilter.value;
      itemList.innerHTML = "";
      DATA.forEach((item, idx) => {
        if (q && !item.name.toLowerCase().includes(q)) return;
        if (fam && item.family !== fam) return;

        const li = document.createElement("li");
        li.className = "item-entry" + (idx === currentIdx ? " active" : "");
        const err = item.median_error_deg;
        const pillClass = err < 8 ? "pill-pass" : err < 15 ? "pill-warn" : "pill-fail";

        li.innerHTML = `
          <div>
            <div class="item-name">${item.name}</div>
            <div class="item-family">${item.family} · ${item.width}x${item.height}</div>
          </div>
          <div class="stat-pill ${pillClass}">${err.toFixed(1)}°</div>
        `;
        li.onclick = () => selectItem(idx);
        itemList.appendChild(li);
      });
    }

    function selectItem(idx) {
      currentIdx = idx;
      renderList();
      const item = DATA[idx];
      if (!item) return;

      document.getElementById("activeTitle").innerText = item.name + " (" + item.family + ")";
      document.getElementById("dimLabel").innerText = item.width + "x" + item.height;

      document.getElementById("imgColor").src = item.color_data || item.normal_data;
      document.getElementById("imgNormal").src = item.normal_data;
      document.getElementById("imgHeight").src = item.height_data;
      document.getElementById("imgRenorm").src = item.renorm_data;
      document.getElementById("imgHeatmap").src = item.heatmap_data;

      const card = document.getElementById("metricsCard");
      card.innerHTML = `
        <div class="metric-row"><span class="metric-label">Median Angular Error</span><span class="metric-val">${item.median_error_deg.toFixed(2)}°</span></div>
        <div class="metric-row"><span class="metric-label">Normal Correlation</span><span class="metric-val">${item.correlation.toFixed(4)}</span></div>
        <div class="metric-row"><span class="metric-label">Height Amplitude</span><span class="metric-val">${item.height_amplitude.toFixed(2)}</span></div>
        <div class="metric-row"><span class="metric-label">Roughness / Reflectivity</span><span class="metric-val">${item.roughness.toFixed(2)} / ${item.reflectivity.toFixed(2)}</span></div>
      `;

      document.getElementById("paramAmp").value = Math.round(item.height_amplitude * 100);
      document.getElementById("paramRough").value = Math.round(item.roughness * 100);
      document.getElementById("paramRefl").value = Math.round(item.reflectivity * 100);

      updateTextures(item);
    }

    searchInput.oninput = renderList;
    familyFilter.onchange = renderList;

    const canvas = document.getElementById("glCanvas");
    const gl = canvas.getContext("webgl");

    const vsSource = `
      attribute vec2 aPos;
      attribute vec2 aUV;
      varying vec2 vUV;
      void main() {
        vUV = aUV;
        gl_Position = vec4(aPos, 0.0, 1.0);
      }
    `;

    const fsSource = `
      precision mediump float;
      varying vec2 vUV;
      uniform sampler2D uColor;
      uniform sampler2D uNormal;
      uniform sampler2D uHeight;
      uniform bool uEnablePOM;
      uniform bool uEnableColor;
      uniform float uHeightScale;
      uniform float uRoughness;
      uniform float uReflectivity;
      uniform vec3 uLightDir;
      uniform vec3 uViewDir;

      void main() {
        vec2 uv = vUV;

        if (uEnablePOM) {
          float numSteps = 32.0;
          float stepSize = 1.0 / numSteps;
          vec2 p = uViewDir.xy * (uHeightScale * 0.08);
          vec2 deltaUV = p / numSteps;

          float currLayerDepth = 0.0;
          vec2 currUV = uv;
          float currHeight = 1.0 - texture2D(uHeight, currUV).r;

          for (int i = 0; i < 32; i++) {
            if (currLayerDepth >= currHeight) break;
            currUV -= deltaUV;
            currHeight = 1.0 - texture2D(uHeight, currUV).r;
            currLayerDepth += stepSize;
          }

          vec2 prevUV = currUV + deltaUV;
          float nextWeight = currLayerDepth - currHeight;
          float prevWeight = (1.0 - texture2D(uHeight, prevUV).r) - (currLayerDepth - stepSize);
          float weight = nextWeight / (nextWeight + prevWeight + 0.0001);
          uv = prevUV * weight + currUV * (1.0 - weight);
        }

        vec3 N = normalize(texture2D(uNormal, uv).rgb * 2.0 - 1.0);
        vec3 L = normalize(uLightDir);
        vec3 V = normalize(uViewDir);
        vec3 H = normalize(L + V);

        float NdotL = max(dot(N, L), 0.0);
        float NdotH = max(dot(N, H), 0.0);

        vec3 albedo = uEnableColor ? texture2D(uColor, uv).rgb : vec3(0.7);
        vec3 diffuse = albedo * NdotL;

        float specPower = mix(128.0, 4.0, uRoughness);
        float spec = pow(NdotH, specPower) * uReflectivity * 5.0 * NdotL;

        vec3 ambient = albedo * 0.15;
        gl_FragColor = vec4(ambient + diffuse + vec3(spec), 1.0);
      }
    `;

    function compileShader(type, src) {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      return s;
    }

    const program = gl.createProgram();
    gl.attachShader(program, compileShader(gl.VERTEX_SHADER, vsSource));
    gl.attachShader(program, compileShader(gl.FRAGMENT_SHADER, fsSource));
    gl.linkProgram(program);
    gl.useProgram(program);

    const buf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
      -1, -1,  0, 1,
       1, -1,  1, 1,
      -1,  1,  0, 0,
      -1,  1,  0, 0,
       1, -1,  1, 1,
       1,  1,  1, 0,
    ]), gl.STATIC_DRAW);

    const aPos = gl.getAttribLocation(program, "aPos");
    const aUV = gl.getAttribLocation(program, "aUV");
    gl.enableVertexAttribArray(aPos);
    gl.vertexAttribPointer(aPos, 2, gl.FLOAT, false, 16, 0);
    gl.enableVertexAttribArray(aUV);
    gl.vertexAttribPointer(aUV, 2, gl.FLOAT, false, 16, 8);

    const texColor = gl.createTexture();
    const texNormal = gl.createTexture();
    const texHeight = gl.createTexture();

    function initTex(tex, unit) {
      gl.activeTexture(gl.TEXTURE0 + unit);
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);
    }
    initTex(texColor, 0);
    initTex(texNormal, 1);
    initTex(texHeight, 2);

    gl.uniform1i(gl.getUniformLocation(program, "uColor"), 0);
    gl.uniform1i(gl.getUniformLocation(program, "uNormal"), 1);
    gl.uniform1i(gl.getUniformLocation(program, "uHeight"), 2);

    function updateTextures(item) {
      function load(tex, unit, src) {
        const img = new Image();
        img.onload = () => {
          gl.activeTexture(gl.TEXTURE0 + unit);
          gl.bindTexture(gl.TEXTURE_2D, tex);
          gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
          draw();
        };
        img.src = src;
      }
      load(texColor, 0, item.color_data || item.normal_data);
      load(texNormal, 1, item.normal_data);
      load(texHeight, 2, item.height_data);
    }

    let lightAngle = 45;
    let viewDir = [0.0, -0.4, 0.9];

    function draw() {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
      gl.viewport(0, 0, canvas.width, canvas.height);

      gl.uniform1i(gl.getUniformLocation(program, "uEnablePOM"), document.getElementById("togglePOM").checked ? 1 : 0);
      gl.uniform1i(gl.getUniformLocation(program, "uEnableColor"), document.getElementById("toggleColor").checked ? 1 : 0);
      gl.uniform1f(gl.getUniformLocation(program, "uHeightScale"), parseFloat(document.getElementById("paramAmp").value) / 100.0);
      gl.uniform1f(gl.getUniformLocation(program, "uRoughness"), parseFloat(document.getElementById("paramRough").value) / 100.0);
      gl.uniform1f(gl.getUniformLocation(program, "uReflectivity"), parseFloat(document.getElementById("paramRefl").value) / 100.0);

      const rad = lightAngle * Math.PI / 180.0;
      gl.uniform3f(gl.getUniformLocation(program, "uLightDir"), Math.cos(rad), Math.sin(rad), 0.7);
      gl.uniform3f(gl.getUniformLocation(program, "uViewDir"), viewDir[0], viewDir[1], viewDir[2]);

      gl.drawArrays(gl.TRIANGLES, 0, 6);
    }

    let isDragging = false;
    let lastX = 0, lastY = 0;
    canvas.onmousedown = (e) => { isDragging = true; lastX = e.clientX; lastY = e.clientY; };
    window.onmouseup = () => { isDragging = false; };
    canvas.onmousemove = (e) => {
      if (!isDragging) return;
      const dx = (e.clientX - lastX) * 0.005;
      const dy = (e.clientY - lastY) * 0.005;
      viewDir[0] = Math.max(-1.0, Math.min(1.0, viewDir[0] + dx));
      viewDir[1] = Math.max(-1.0, Math.min(1.0, viewDir[1] - dy));
      lastX = e.clientX;
      lastY = e.clientY;
      draw();
    };

    document.querySelectorAll("input").forEach(el => el.oninput = () => {
      lightAngle = parseFloat(document.getElementById("paramLight").value);
      draw();
    });

    if (DATA.length > 0) {
      renderList();
      selectItem(0);
    }
  </script>
</body>
</html>
"""


def generate_html_inspection_report(
    region: str,
    entries: list[dict],
    output_path: Path,
    title: str = "Terrain Surface Material & Height Map Inspector",
) -> None:
    """Generate a self-contained interactive HTML5/WebGL visual inspector report."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json_payload = json.dumps(entries)
    rendered = (
        HTML_TEMPLATE.replace("__TITLE__", html.escape(title))
        .replace("__REGION__", html.escape(region))
        .replace("__JSON_DATA__", json_payload)
    )
    output_path.write_text(rendered, encoding="utf-8")
