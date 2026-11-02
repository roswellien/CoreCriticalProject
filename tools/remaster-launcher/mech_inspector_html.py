"""HTML report generator with real-time 3D WebGL Mech Model viewer and POM raymarching.

Renders full 3D mech models (Bushwacker and MadCat) in hardware-accelerated WebGL with
orbit camera, dynamic lighting, real-time parallax occlusion mapping, multi-material batching,
and 2D channel comparison cards.
"""

from __future__ import annotations

import json
from pathlib import Path


MECH_HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>__TITLE__</title>
  <style>
    :root {
      --bg: #101216;
      --card-bg: #181a22;
      --panel-bg: #14161e;
      --border: #282c3c;
      --accent: #4daafc;
      --accent-hover: #6cb8fc;
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
      user-select: none;
    }
    header {
      background: var(--card-bg);
      border-bottom: 1px solid var(--border);
      padding: 10px 20px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      flex-shrink: 0;
    }
    header h1 {
      font-size: 1.1rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .badge {
      background: var(--accent);
      color: #000;
      font-size: 0.7rem;
      font-weight: 700;
      padding: 2px 7px;
      border-radius: 4px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }
    .view-toggles {
      display: flex;
      background: #0c0d12;
      border: 1px solid var(--border);
      border-radius: 6px;
      overflow: hidden;
    }
    .btn-toggle {
      background: transparent;
      color: var(--text-muted);
      border: none;
      padding: 6px 14px;
      font-size: 0.8rem;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.15s;
    }
    .btn-toggle:hover { color: var(--text); }
    .btn-toggle.active {
      background: var(--accent);
      color: #000;
    }
    .workspace {
      display: flex;
      flex: 1;
      overflow: hidden;
    }
    .sidebar {
      width: 280px;
      background: var(--card-bg);
      border-right: 1px solid var(--border);
      display: flex;
      flex-direction: column;
      overflow: hidden;
      flex-shrink: 0;
    }
    .sidebar-header {
      padding: 12px 16px;
      font-size: 0.75rem;
      font-weight: 700;
      color: var(--text-muted);
      text-transform: uppercase;
      border-bottom: 1px solid var(--border);
      letter-spacing: 0.5px;
    }
    .item-list {
      flex: 1;
      overflow-y: auto;
      list-style: none;
    }
    .item-entry {
      padding: 10px 16px;
      border-bottom: 1px solid var(--border);
      cursor: pointer;
      display: flex;
      justify-content: space-between;
      align-items: center;
      transition: background 0.15s;
    }
    .item-entry:hover { background: #222533; }
    .item-entry.active {
      background: #252b3d;
      border-left: 3px solid var(--accent);
    }
    .item-name { font-weight: 600; font-size: 0.85rem; }
    .item-sub { font-size: 0.75rem; color: var(--text-muted); }
    .stat-pill {
      font-size: 0.75rem;
      padding: 2px 6px;
      border-radius: 3px;
      font-weight: 600;
      font-family: monospace;
    }
    .pill-pass { background: rgba(34, 197, 94, 0.15); color: var(--success); }
    .pill-warn { background: rgba(245, 158, 11, 0.15); color: var(--warning); }
    .pill-fail { background: rgba(239, 68, 68, 0.15); color: var(--danger); }
    .main-view {
      flex: 1;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }
    .viewport-container {
      flex: 1;
      display: flex;
      gap: 16px;
      padding: 16px;
      overflow: hidden;
    }
    .preview-panel {
      flex: 1;
      background: var(--panel-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      display: flex;
      flex-direction: column;
      overflow: hidden;
      position: relative;
    }
    .panel-header {
      padding: 10px 16px;
      border-bottom: 1px solid var(--border);
      font-size: 0.85rem;
      font-weight: 600;
      display: flex;
      justify-content: space-between;
      align-items: center;
      background: var(--card-bg);
      flex-shrink: 0;
    }
    .panel-body {
      flex: 1;
      position: relative;
      background: #090a0d;
      overflow: hidden;
    }
    canvas#glCanvas {
      width: 100%;
      height: 100%;
      display: block;
      cursor: grab;
    }
    canvas#glCanvas:active {
      cursor: grabbing;
    }
    .controls-overlay {
      position: absolute;
      bottom: 12px;
      left: 12px;
      right: 12px;
      background: rgba(18, 20, 26, 0.88);
      backdrop-filter: blur(8px);
      padding: 10px 16px;
      border-radius: 6px;
      border: 1px solid var(--border);
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: center;
      font-size: 0.8rem;
    }
    .control-group { display: flex; align-items: center; gap: 8px; }
    .control-group label { color: var(--text-muted); font-size: 0.75rem; white-space: nowrap; }
    .control-group input[type="range"] { width: 85px; accent-color: var(--accent); }
    .hud-hint {
      position: absolute;
      top: 12px;
      left: 12px;
      background: rgba(16, 18, 24, 0.75);
      border: 1px solid rgba(255, 255, 255, 0.08);
      padding: 6px 12px;
      border-radius: 4px;
      font-size: 0.75rem;
      color: var(--text-muted);
      pointer-events: none;
    }
    .channels-panel {
      width: 410px;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 6px;
      display: flex;
      flex-direction: column;
      overflow-y: auto;
      padding: 14px;
      gap: 12px;
      flex-shrink: 0;
    }
    .channel-card {
      background: var(--panel-bg);
      border: 1px solid var(--border);
      border-radius: 4px;
      overflow: hidden;
    }
    .channel-header {
      padding: 6px 10px;
      font-size: 0.7rem;
      font-weight: 700;
      color: var(--text-muted);
      display: flex;
      justify-content: space-between;
      border-bottom: 1px solid var(--border);
      letter-spacing: 0.5px;
    }
    .channel-img {
      width: 100%;
      height: 180px;
      object-fit: contain;
      background: #050608;
      display: block;
    }
    .metric-row {
      display: flex;
      justify-content: space-between;
      font-size: 0.8rem;
      padding: 4px 0;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
    }
    .metric-label { color: var(--text-muted); }
    .metric-val { font-family: monospace; font-weight: 600; }
    .btn-action {
      background: #252a38;
      color: var(--text);
      border: 1px solid var(--border);
      padding: 4px 10px;
      border-radius: 4px;
      font-size: 0.75rem;
      cursor: pointer;
    }
    .btn-action:hover { background: #32384a; }
  </style>
</head>
<body>
  <header>
    <h1>
      <span>__TITLE__</span>
      <span class="badge">POM Vertices Active</span>
    </h1>
    <div style="display: flex; align-items: center; gap: 12px;">
      <div class="view-toggles">
        <button id="btnMode3D" class="btn-toggle active" onclick="setViewMode('3d')">🤖 3D Mech Model</button>
        <button id="btnModeTile" class="btn-toggle" onclick="setViewMode('tile')">🔲 Flat Material Plane</button>
      </div>
      <button class="btn-action" onclick="resetCamera()">Reset Camera</button>
    </div>
  </header>

  <div class="workspace">
    <!-- Sidebar: Material Hierarchy -->
    <div class="sidebar">
      <div class="sidebar-header">Mech Materials (__COUNT__)</div>
      <ul id="itemList" class="item-list"></ul>
    </div>

    <!-- Main View: 3D Canvas + Channel Strip -->
    <div class="main-view">
      <div class="viewport-container">
        <!-- 3D WebGL Viewport -->
        <div class="preview-panel">
          <div class="panel-header">
            <span id="activeTitle">3D Viewport</span>
            <div style="display: flex; gap: 12px; align-items: center;">
              <label style="font-size:0.75rem; cursor:pointer;"><input type="checkbox" id="togglePOM" checked> POM Active</label>
              <label style="font-size:0.75rem; cursor:pointer;"><input type="checkbox" id="toggleColor" checked> Albedo</label>
              <label style="font-size:0.75rem; cursor:pointer;"><input type="checkbox" id="toggleRotate"> Auto-Rotate</label>
            </div>
          </div>
          <div class="panel-body">
            <canvas id="glCanvas"></canvas>
            <div id="hudHint" class="hud-hint">Left Drag: Orbit · Right/Shift Drag: Pan · Scroll: Zoom</div>
            <div class="controls-overlay">
              <div class="control-group">
                <label>Displacement Scale</label>
                <input type="range" id="paramAmp" min="0" max="250" value="100">
              </div>
              <div class="control-group">
                <label>Roughness</label>
                <input type="range" id="paramRough" min="0" max="100" value="45">
              </div>
              <div class="control-group">
                <label>Reflectivity</label>
                <input type="range" id="paramRefl" min="0" max="100" value="35">
              </div>
              <div class="control-group">
                <label>Sun Azimuth</label>
                <input type="range" id="paramLightAzimuth" min="0" max="360" value="55">
              </div>
              <div class="control-group">
                <label>Sun Elevation</label>
                <input type="range" id="paramLightElevation" min="5" max="85" value="45">
              </div>
            </div>
          </div>
        </div>

        <!-- Channels & Quality Metrics Panel -->
        <div class="channels-panel">
          <h3 style="font-size: 0.85rem; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.5px;">Material Profile & Quality</h3>
          <div id="metricsCard"></div>

          <div class="channel-card">
            <div class="channel-header"><span>DIFFUSE ALBEDO</span><span id="dimLabel"></span></div>
            <img id="imgColor" class="channel-img" alt="Albedo">
          </div>

          <div class="channel-card">
            <div class="channel-header"><span>NORMAL MAP</span><span>BWNRM2 TANGENT</span></div>
            <img id="imgNormal" class="channel-img" alt="Normal">
          </div>

          <div class="channel-card">
            <div class="channel-header"><span>DERIVED HEIGHT</span><span>16-BIT POISSON</span></div>
            <img id="imgHeight" class="channel-img" alt="Height">
          </div>

          <div class="channel-card">
            <div class="channel-header"><span>RE-DERIVED NORMAL</span><span>CENTRAL GRADIENT</span></div>
            <img id="imgRenorm" class="channel-img" alt="Re-derived Normal">
          </div>

          <div class="channel-card">
            <div class="channel-header"><span>ANGULAR ERROR HEATMAP</span><span>&lt;8° GREEN | &gt;25° RED</span></div>
            <img id="imgHeatmap" class="channel-img" alt="Error Heatmap">
          </div>
        </div>
      </div>
    </div>
  </div>

  <script>
    const MATERIALS = __JSON_DATA__;
    const MESH_DATA = __MESH_DATA__;
    let currentIdx = 0;
    let viewMode = MESH_DATA ? "3d" : "tile";

    const itemList = document.getElementById("itemList");

    function renderList() {
      itemList.innerHTML = "";
      MATERIALS.forEach((item, idx) => {
        const li = document.createElement("li");
        li.className = "item-entry" + (idx === currentIdx ? " active" : "");
        const err = item.median_error_deg;
        const pillClass = err < 8 ? "pill-pass" : err < 15 ? "pill-warn" : "pill-fail";
        li.innerHTML = `
          <div>
            <div class="item-name">${item.name}</div>
            <div class="item-sub">${item.width}x${item.height} · amp: ${item.height_amplitude.toFixed(2)}</div>
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
      const item = MATERIALS[idx];
      if (!item) return;

      document.getElementById("activeTitle").innerText = viewMode === "3d" ? "3D Model · Focused: " + item.name : "Material Plane · " + item.name;
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
        <div class="metric-row"><span class="metric-label">Metallic</span><span class="metric-val">${item.metallic.toFixed(2)}</span></div>
      `;

      document.getElementById("paramRough").value = Math.round(item.roughness * 100);
      document.getElementById("paramRefl").value = Math.round(item.reflectivity * 100);
      draw();
    }

    function setViewMode(mode) {
      viewMode = mode;
      document.getElementById("btnMode3D").className = "btn-toggle" + (mode === "3d" ? " active" : "");
      document.getElementById("btnModeTile").className = "btn-toggle" + (mode === "tile" ? " active" : "");
      document.getElementById("hudHint").innerText = mode === "3d" 
        ? "Left Drag: Orbit · Right/Shift Drag: Pan · Scroll: Zoom" 
        : "Left Drag: Tilt Surface · Scroll: Zoom";
      selectItem(currentIdx);
      draw();
    }

    // --- WebGL Setup ---
    const canvas = document.getElementById("glCanvas");
    const gl = canvas.getContext("webgl", { antialias: true, alpha: false, depth: true });
    if (!gl) {
      alert("WebGL not supported in your browser");
    }
    const extDeriv = gl.getExtension("OES_standard_derivatives");

    // 3D Shaders
    const vsSource = `
      attribute vec3 aPos;
      attribute vec3 aNormal;
      attribute vec2 aUV;
      uniform mat4 uMVP;
      uniform mat4 uModel;
      varying vec3 vWorldPos;
      varying vec3 vNormal;
      varying vec2 vUV;
      void main() {
        vWorldPos = (uModel * vec4(aPos, 1.0)).xyz;
        vNormal = normalize((uModel * vec4(aNormal, 0.0)).xyz);
        vUV = aUV;
        gl_Position = uMVP * vec4(aPos, 1.0);
      }
    `;

    const fsSource = `
      #extension GL_OES_standard_derivatives : enable
      precision mediump float;
      varying vec3 vWorldPos;
      varying vec3 vNormal;
      varying vec2 vUV;
      uniform sampler2D uColor;
      uniform sampler2D uNormal;
      uniform sampler2D uHeight;
      uniform bool uEnablePOM;
      uniform bool uEnableColor;
      uniform float uHeightAmp;
      uniform float uDispScale;
      uniform float uRoughness;
      uniform float uReflectivity;
      uniform float uMetallic;
      uniform vec3 uLightDir;
      uniform vec3 uCameraPos;

      void main() {
        vec3 N_geom = normalize(vNormal);
        vec3 V_world = normalize(uCameraPos - vWorldPos);

        // Screen-space cotangent frame derivation
        vec3 dp1 = dFdx(vWorldPos);
        vec3 dp2 = dFdy(vWorldPos);
        vec2 duv1 = dFdx(vUV);
        vec2 duv2 = dFdy(vUV);
        vec3 dp2perp = cross(dp2, N_geom);
        vec3 dp1perp = cross(N_geom, dp1);
        vec3 T = dp2perp * duv1.x + dp1perp * duv2.x;
        vec3 B = dp2perp * duv1.y + dp1perp * duv2.y;
        float invmax = inversesqrt(max(dot(T, T), dot(B, B)) + 1e-6);
        mat3 TBN = mat3(normalize(T * invmax), normalize(B * invmax), N_geom);

        vec3 V_tangent = vec3(
          dot(V_world, TBN[0]),
          dot(V_world, TBN[1]),
          dot(V_world, TBN[2])
        );

        vec2 uv = vUV;
        float totalAmp = uHeightAmp * uDispScale;
        if (uEnablePOM && totalAmp > 0.001 && V_tangent.z > 0.02) {
          vec2 maxOffset = (V_tangent.xy / V_tangent.z) * totalAmp;
          const int NUM_STEPS = 24;
          float stepSize = 1.0 / float(NUM_STEPS);
          vec2 deltaUV = maxOffset * stepSize;
          float currLayerDepth = 0.0;
          vec2 currUV = uv;
          float currHeight = 1.0 - texture2D(uHeight, currUV).r;

          for (int i = 0; i < 24; i++) {
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

        vec3 normSample = texture2D(uNormal, uv).rgb * 2.0 - 1.0;
        vec3 N = normalize(TBN * normSample);
        vec3 L = normalize(uLightDir);
        vec3 H = normalize(L + V_world);

        float NdotL = max(dot(N, L), 0.0);
        float NdotH = max(dot(N, H), 0.0);

        vec3 albedo = uEnableColor ? texture2D(uColor, uv).rgb : vec3(0.65);
        vec3 diffuse = albedo * (0.15 + 0.85 * NdotL);

        float specPower = mix(140.0, 6.0, uRoughness);
        float spec = pow(NdotH, specPower) * uReflectivity * 2.5 * NdotL;

        // Metallic tint for weapons/armor:
        vec3 specColor = mix(vec3(1.0), albedo, uMetallic);
        gl_FragColor = vec4(diffuse + specColor * spec, 1.0);
      }
    `;

    function compileShader(type, src) {
      const s = gl.createShader(type);
      gl.shaderSource(s, src);
      gl.compileShader(s);
      if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
        console.error(gl.getShaderInfoLog(s));
      }
      return s;
    }

    const program = gl.createProgram();
    gl.attachShader(program, compileShader(gl.VERTEX_SHADER, vsSource));
    gl.attachShader(program, compileShader(gl.FRAGMENT_SHADER, fsSource));
    gl.linkProgram(program);
    gl.useProgram(program);

    const aPos = gl.getAttribLocation(program, "aPos");
    const aNormal = gl.getAttribLocation(program, "aNormal");
    const aUV = gl.getAttribLocation(program, "aUV");

    gl.enableVertexAttribArray(aPos);
    gl.enableVertexAttribArray(aNormal);
    gl.enableVertexAttribArray(aUV);

    // Flat Quad Buffer (for Material Tile view)
    const quadBuf = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, quadBuf);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([
      // pos (x,y,z), normal (nx,ny,nz), uv (u,v)
      -2, -2, 0,  0, 0, 1,  0, 1,
       2, -2, 0,  0, 0, 1,  1, 1,
      -2,  2, 0,  0, 0, 1,  0, 0,
      -2,  2, 0,  0, 0, 1,  0, 0,
       2, -2, 0,  0, 0, 1,  1, 1,
       2,  2, 0,  0, 0, 1,  1, 0,
    ]), gl.STATIC_DRAW);

    // Mech Model Geometry Buffers
    const meshBuffers = {};
    if (MESH_DATA && MESH_DATA.materials) {
      for (const [matName, b64] of Object.entries(MESH_DATA.materials)) {
        const bin = atob(b64);
        const bytes = new Uint8Array(bin.length);
        for (let i = 0; i < bin.length; ++i) bytes[i] = bin.charCodeAt(i);
        const floatArr = new Float32Array(bytes.buffer);
        const buf = gl.createBuffer();
        gl.bindBuffer(gl.ARRAY_BUFFER, buf);
        gl.bufferData(gl.ARRAY_BUFFER, floatArr, gl.STATIC_DRAW);
        meshBuffers[matName] = {
          buffer: buf,
          vertCount: MESH_DATA.material_vert_counts[matName] || (floatArr.length / 8)
        };
      }
    }

    // Material Textures
    const matTextures = {};
    function initTexture(src) {
      const tex = gl.createTexture();
      gl.bindTexture(gl.TEXTURE_2D, tex);
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, 1, 1, 0, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array([128, 128, 128, 255]));
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.REPEAT);
      gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.REPEAT);

      const img = new Image();
      img.onload = () => {
        gl.bindTexture(gl.TEXTURE_2D, tex);
        gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, img);
        draw();
      };
      img.src = src;
      return tex;
    }

    MATERIALS.forEach(item => {
      matTextures[item.name] = {
        color: initTexture(item.color_data || item.normal_data),
        normal: initTexture(item.normal_data),
        height: initTexture(item.height_data),
        profile: item
      };
    });

    gl.uniform1i(gl.getUniformLocation(program, "uColor"), 0);
    gl.uniform1i(gl.getUniformLocation(program, "uNormal"), 1);
    gl.uniform1i(gl.getUniformLocation(program, "uHeight"), 2);

    // Matrix Math Helpers
    function mat4Perspective(out, fovy, aspect, near, far) {
      const f = 1.0 / Math.tan(fovy / 2);
      const nf = 1 / (near - far);
      out.fill(0);
      out[0] = f / aspect;
      out[5] = f;
      out[10] = (far + near) * nf;
      out[11] = -1;
      out[14] = (2 * far * near) * nf;
    }

    function mat4LookAt(out, eye, center, up) {
      let z0 = eye[0] - center[0], z1 = eye[1] - center[1], z2 = eye[2] - center[2];
      let len = 1 / Math.hypot(z0, z1, z2);
      z0 *= len; z1 *= len; z2 *= len;
      let x0 = up[1] * z2 - up[2] * z1, x1 = up[2] * z0 - up[0] * z2, x2 = up[0] * z1 - up[1] * z0;
      len = Math.hypot(x0, x1, x2);
      if (!len) { x0 = 1; x1 = 0; x2 = 0; } else { len = 1 / len; x0 *= len; x1 *= len; x2 *= len; }
      let y0 = z1 * x2 - z2 * x1, y1 = z2 * x0 - z0 * x2, y2 = z0 * x1 - z1 * x0;
      out[0] = x0; out[1] = y0; out[2] = z0; out[3] = 0;
      out[4] = x1; out[5] = y1; out[6] = z1; out[7] = 0;
      out[8] = x2; out[9] = y2; out[10] = z2; out[11] = 0;
      out[12] = -(x0 * eye[0] + x1 * eye[1] + x2 * eye[2]);
      out[13] = -(y0 * eye[0] + y1 * eye[1] + y2 * eye[2]);
      out[14] = -(z0 * eye[0] + z1 * eye[1] + z2 * eye[2]);
      out[15] = 1;
    }

    function mat4Multiply(out, a, b) {
      const a00 = a[0], a01 = a[1], a02 = a[2], a03 = a[3];
      const a10 = a[4], a11 = a[5], a12 = a[6], a13 = a[7];
      const a20 = a[8], a21 = a[9], a22 = a[10], a23 = a[11];
      const a30 = a[12], a31 = a[13], a32 = a[14], a33 = a[15];
      let b0 = b[0], b1 = b[1], b2 = b[2], b3 = b[3];
      out[0] = b0 * a00 + b1 * a10 + b2 * a20 + b3 * a30;
      out[1] = b0 * a01 + b1 * a11 + b2 * a21 + b3 * a31;
      out[2] = b0 * a02 + b1 * a12 + b2 * a22 + b3 * a32;
      out[3] = b0 * a03 + b1 * a13 + b2 * a23 + b3 * a33;
      b0 = b[4]; b1 = b[5]; b2 = b[6]; b3 = b[7];
      out[4] = b0 * a00 + b1 * a10 + b2 * a20 + b3 * a30;
      out[5] = b0 * a01 + b1 * a11 + b2 * a21 + b3 * a31;
      out[6] = b0 * a02 + b1 * a12 + b2 * a22 + b3 * a32;
      out[7] = b0 * a03 + b1 * a13 + b2 * a23 + b3 * a33;
      b0 = b[8]; b1 = b[9]; b2 = b[10]; b3 = b[11];
      out[8] = b0 * a00 + b1 * a10 + b2 * a20 + b3 * a30;
      out[9] = b0 * a01 + b1 * a11 + b2 * a21 + b3 * a31;
      out[10] = b0 * a02 + b1 * a12 + b2 * a22 + b3 * a32;
      out[11] = b0 * a03 + b1 * a13 + b2 * a23 + b3 * a33;
      b0 = b[12]; b1 = b[13]; b2 = b[14]; b3 = b[15];
      out[12] = b0 * a00 + b1 * a10 + b2 * a20 + b3 * a30;
      out[13] = b0 * a01 + b1 * a11 + b2 * a21 + b3 * a31;
      out[14] = b0 * a02 + b1 * a12 + b2 * a22 + b3 * a32;
      out[15] = b0 * a03 + b1 * a13 + b2 * a23 + b3 * a33;
    }

    // Camera & Orbit State
    const meshCenter = MESH_DATA ? MESH_DATA.center : [0, 0, 0];
    const meshRadius = MESH_DATA ? MESH_DATA.radius : 3.0;

    let target = [...meshCenter];
    let distance = meshRadius * 1.85;
    let yaw = 0.55;
    let pitch = 0.25;

    function resetCamera() {
      target = [...meshCenter];
      distance = meshRadius * 1.85;
      yaw = 0.55;
      pitch = 0.25;
      draw();
    }

    const uMVPLoc = gl.getUniformLocation(program, "uMVP");
    const uModelLoc = gl.getUniformLocation(program, "uModel");
    const uEnablePOMLoc = gl.getUniformLocation(program, "uEnablePOM");
    const uEnableColorLoc = gl.getUniformLocation(program, "uEnableColor");
    const uHeightAmpLoc = gl.getUniformLocation(program, "uHeightAmp");
    const uDispScaleLoc = gl.getUniformLocation(program, "uDispScale");
    const uRoughnessLoc = gl.getUniformLocation(program, "uRoughness");
    const uReflectivityLoc = gl.getUniformLocation(program, "uReflectivity");
    const uMetallicLoc = gl.getUniformLocation(program, "uMetallic");
    const uLightDirLoc = gl.getUniformLocation(program, "uLightDir");
    const uCameraPosLoc = gl.getUniformLocation(program, "uCameraPos");

    const projMatrix = new Float32Array(16);
    const viewMatrix = new Float32Array(16);
    const mvpMatrix = new Float32Array(16);
    const modelMatrix = new Float32Array([
      1, 0, 0, 0,
      0, 1, 0, 0,
      0, 0, 1, 0,
      0, 0, 0, 1
    ]);

    function draw() {
      canvas.width = canvas.clientWidth;
      canvas.height = canvas.clientHeight;
      gl.viewport(0, 0, canvas.width, canvas.height);
      gl.enable(gl.DEPTH_TEST);
      gl.clearColor(0.04, 0.05, 0.07, 1.0);
      gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);

      const aspect = canvas.width / canvas.height;
      mat4Perspective(projMatrix, 45 * Math.PI / 180, aspect, 0.2, 100.0);

      // Camera Eye
      const camX = target[0] + distance * Math.cos(pitch) * Math.sin(yaw);
      const camY = target[1] + distance * Math.sin(pitch);
      const camZ = target[2] + distance * Math.cos(pitch) * Math.cos(yaw);
      mat4LookAt(viewMatrix, [camX, camY, camZ], target, [0, 1, 0]);
      mat4Multiply(mvpMatrix, projMatrix, viewMatrix);

      gl.uniformMatrix4fv(uMVPLoc, false, mvpMatrix);
      gl.uniformMatrix4fv(uModelLoc, false, modelMatrix);
      gl.uniform3f(uCameraPosLoc, camX, camY, camZ);

      // Sun Lighting Direction
      const az = parseFloat(document.getElementById("paramLightAzimuth").value) * Math.PI / 180;
      const el = parseFloat(document.getElementById("paramLightElevation").value) * Math.PI / 180;
      const lx = Math.cos(el) * Math.sin(az);
      const ly = Math.sin(el);
      const lz = Math.cos(el) * Math.cos(az);
      gl.uniform3f(uLightDirLoc, lx, ly, lz);

      const pomActive = document.getElementById("togglePOM").checked ? 1 : 0;
      const colorActive = document.getElementById("toggleColor").checked ? 1 : 0;
      const dispScale = parseFloat(document.getElementById("paramAmp").value) / 100.0;
      gl.uniform1i(uEnablePOMLoc, pomActive);
      gl.uniform1i(uEnableColorLoc, colorActive);
      gl.uniform1f(uDispScaleLoc, dispScale);

      if (viewMode === "3d" && MESH_DATA) {
        // Draw each material batch of the 3D Mech
        for (const [matName, item] of Object.entries(meshBuffers)) {
          const tex = matTextures[matName];
          if (!tex) continue;

          gl.bindBuffer(gl.ARRAY_BUFFER, item.buffer);
          gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 32, 0);
          gl.vertexAttribPointer(aNormal, 3, gl.FLOAT, false, 32, 12);
          gl.vertexAttribPointer(aUV, 2, gl.FLOAT, false, 32, 24);

          gl.activeTexture(gl.TEXTURE0);
          gl.bindTexture(gl.TEXTURE_2D, tex.color);
          gl.activeTexture(gl.TEXTURE1);
          gl.bindTexture(gl.TEXTURE_2D, tex.normal);
          gl.activeTexture(gl.TEXTURE2);
          gl.bindTexture(gl.TEXTURE_2D, tex.height);

          const prof = tex.profile;
          gl.uniform1f(uHeightAmpLoc, prof.height_amplitude);
          gl.uniform1f(uRoughnessLoc, prof.roughness);
          gl.uniform1f(uReflectivityLoc, prof.reflectivity);
          gl.uniform1f(uMetallicLoc, prof.metallic);

          gl.drawArrays(gl.TRIANGLES, 0, item.vertCount);
        }
      } else {
        // Flat Material Tile Mode
        const item = MATERIALS[currentIdx];
        const tex = matTextures[item.name];
        if (tex) {
          gl.bindBuffer(gl.ARRAY_BUFFER, quadBuf);
          gl.vertexAttribPointer(aPos, 3, gl.FLOAT, false, 32, 0);
          gl.vertexAttribPointer(aNormal, 3, gl.FLOAT, false, 32, 12);
          gl.vertexAttribPointer(aUV, 2, gl.FLOAT, false, 32, 24);

          gl.activeTexture(gl.TEXTURE0);
          gl.bindTexture(gl.TEXTURE_2D, tex.color);
          gl.activeTexture(gl.TEXTURE1);
          gl.bindTexture(gl.TEXTURE_2D, tex.normal);
          gl.activeTexture(gl.TEXTURE2);
          gl.bindTexture(gl.TEXTURE_2D, tex.height);

          gl.uniform1f(uHeightAmpLoc, item.height_amplitude);
          gl.uniform1f(uRoughnessLoc, parseFloat(document.getElementById("paramRough").value) / 100);
          gl.uniform1f(uReflectivityLoc, parseFloat(document.getElementById("paramRefl").value) / 100);
          gl.uniform1f(uMetallicLoc, item.metallic);

          gl.drawArrays(gl.TRIANGLES, 0, 6);
        }
      }
    }

    // Mouse Interaction
    let isDragging = false;
    let dragButton = 0;
    let lastX = 0, lastY = 0;

    canvas.onmousedown = (e) => {
      isDragging = true;
      dragButton = e.button;
      lastX = e.clientX;
      lastY = e.clientY;
    };

    window.onmousemove = (e) => {
      if (!isDragging) return;
      const dx = e.clientX - lastX;
      const dy = e.clientY - lastY;
      lastX = e.clientX;
      lastY = e.clientY;

      if (dragButton === 0 && !e.shiftKey) {
        // Orbit rotate
        yaw -= dx * 0.008;
        pitch += dy * 0.008;
        pitch = Math.max(-1.45, Math.min(1.45, pitch));
      } else {
        // Pan
        const panSpeed = distance * 0.0015;
        const forward = [-Math.sin(yaw), 0, -Math.cos(yaw)];
        const right = [Math.cos(yaw), 0, -Math.sin(yaw)];
        target[0] -= right[0] * dx * panSpeed;
        target[2] -= right[2] * dx * panSpeed;
        target[1] += dy * panSpeed;
      }
      draw();
    };

    window.onmouseup = () => { isDragging = false; };
    canvas.oncontextmenu = (e) => e.preventDefault();

    canvas.onwheel = (e) => {
      e.preventDefault();
      distance *= (1 + e.deltaY * 0.001);
      distance = Math.max(1.0, Math.min(50.0, distance));
      draw();
    };

    // Sliders & Checkboxes Listeners
    ["paramAmp", "paramRough", "paramRefl", "paramLightAzimuth", "paramLightElevation", "togglePOM", "toggleColor"].forEach(id => {
      document.getElementById(id).oninput = draw;
      document.getElementById(id).onchange = draw;
    });

    window.onresize = draw;

    // Turntable animation loop
    function animate() {
      if (document.getElementById("toggleRotate").checked) {
        yaw += 0.005;
        draw();
      }
      requestAnimationFrame(animate);
    }
    requestAnimationFrame(animate);

    // Initial render
    renderList();
    selectItem(0);
    draw();
  </script>
</body>
</html>
"""


def generate_mech_html_report(
    title: str,
    visual_entries: list[dict],
    mesh_data: dict,
    output_path: Path,
) -> None:
    """Generate self-contained interactive 3D WebGL HTML report with full Mech Model."""
    html = MECH_HTML_TEMPLATE.replace("__TITLE__", title)
    html = html.replace("__COUNT__", str(len(visual_entries)))
    html = html.replace("__JSON_DATA__", json.dumps(visual_entries))
    html = html.replace("__MESH_DATA__", json.dumps(mesh_data))
    Path(output_path).write_text(html, encoding="utf-8")
