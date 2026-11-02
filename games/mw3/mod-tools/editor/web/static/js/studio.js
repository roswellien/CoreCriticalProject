/**
 * MechWarrior 3 - Visual 3D Map Studio
 * Browser preview and local export/launch controls for prototype map edits.
 *
 * state.project holds serializable requests; Three.js objects below are derived
 * display state and must never enter the JSON project. Preview terrain, health
 * and faction controls do not imply that the archive builder applies all fields.
 * Original geometry, when present, is extracted locally from the user's game.
 */

// Project coordinates use X/Z for the ground plane and Y for height. yaw_deg is
// serialized in degrees; Three.js rotations use radians. activeTool is placement
// mode, while selectedAssetId identifies an existing object independently of it.
const state = {
    project: {
        pack_id: "iron_ridge_outpost",
        pack_title: "Iron Ridge Outpost",
        author: "MW3 Modder",
        version: "1.0.0",
        description:
            "Fortified Clan Smoke Jaguar communications outpost nestled in the red canyons of Tranquil.",
        base_operation: "c1",
        terrain: {
            biome: "desert",
            width: 3000.0,
            depth: 3000.0,
            height_scale: 85.0,
            water_level: 2.0,
            roughness: 0.55,
        },
        lighting: {
            preset_name: "sunset",
            azimuth: 235.0,
            elevation: 28.0,
            strength: 0.9,
            ambient: 0.22,
            sun_color: [1.0, 0.82, 0.65],
            sky_tint: [0.35, 0.45, 0.75],
            fog_distance: 1200,
        },
        objectives: {
            primary: [
                {
                    id: "obj_pri_1",
                    desc: "Neutralize Clan Smoke Jaguar defenders",
                    target: "any_enemy",
                    completed: false,
                },
                {
                    id: "obj_pri_2",
                    desc: "Proceed to designated Extraction Zone",
                    target: "trig_evac",
                    completed: false,
                },
            ],
            secondary: [
                {
                    id: "obj_sec_1",
                    desc: "Destroy auxiliary fuel storage silos",
                    target: "fuel_tank",
                    completed: false,
                },
            ],
            briefing_text:
                "Satellite recon has confirmed hostile Clan Smoke Jaguar activity in this sector. Neutralize all perimeter defenses and eliminate the patrol lance before proceeding to extraction.",
            audio_track: "action_theme_1",
        },
        drop_config: {
            player_mech: "mech_madcat",
            drop_type: "orbital_drop_pod",
            tonnage: 75.0,
            armor_tons: 14.0,
            heatsinks: 16,
            jump_jets: 0,
            weapons: {
                left_arm: "ER PPC",
                right_arm: "ER PPC",
                left_torso: "Clan LRM-20",
                right_torso: "Clan LRM-20",
                center_torso: "Medium Pulse Laser",
            },
            lancemates: [
                { name: "Lt. Alan Mattila", mech: "mech_bushwacker", orders: "escort" },
                { name: "Sgt. Epona Rhi", mech: "mech_shadowcat", orders: "free_fire" },
            ],
        },
        assets: [],
    },
    activeTool: null, // asset type string or null
    selectedAssetId: null,
    history: [],
    historyIndex: -1,
    viewMode: "orbit", // 'orbit', 'topdown', 'iso'
};

// Renderer-owned display objects, shared by the event handlers and animation loop.
// assetObjectMap keys are project asset_id values; mesh children are not project IDs.
let scene, camera, renderer, orbitControls, transformControls;
let terrainMesh, waterMesh, sunLight, ambientLight, ghostPreview;
let assetObjectMap = new Map(); // asset_id -> THREE.Group
let raycaster = new THREE.Raycaster();
let mouse = new THREE.Vector2();
let planeIntersect = new THREE.Vector3();

// Sound synthesizer (Web Audio API)
const audioCtx = new (window.AudioContext || window.webkitAudioContext)();
function playBeep(freq = 440, type = "sine", duration = 0.08) {
    try {
        if (audioCtx.state === "suspended") audioCtx.resume();
        const osc = audioCtx.createOscillator();
        const gain = audioCtx.createGain();
        osc.type = type;
        osc.frequency.setValueAtTime(freq, audioCtx.currentTime);
        gain.gain.setValueAtTime(0.08, audioCtx.currentTime);
        gain.gain.exponentialRampToValueAtTime(0.001, audioCtx.currentTime + duration);
        osc.connect(gain);
        gain.connect(audioCtx.destination);
        osc.start();
        osc.stop(audioCtx.currentTime + duration);
    } catch (e) {}
}

/**
 * Evaluate the browser's procedural preview height at one X/Z position.
 * The exported map still uses its base operation's terrain; this function is
 * also used to snap preview placements and does not write original game data.
 */

// Authentic MechWarrior 3 Operation & Biome Environmental Metadata
const OP_ENV_METADATA = {
    c1: {
        name: "Op 1: Coastal Basin / Big Lake",
        center: [-1408, 0],
        waterLevel: 3.0,
        hasWater: true,
        waterColor: 0x145266,
        waterSize: [5000, 5800],
        waterCenter: [-1408, 0],
        palette: { sand: 0xd9c28a, rock: 0x4a7337, peak: 0x5a6975, shoreY: 3.0 },
        preset: "sunset",
        terrainTexture: "/static/assets/textures/terrains/c1_txgter_1.png",
    },
    c2: {
        name: "Op 2: Desert Canyons",
        center: [-512, -1152],
        waterLevel: -200.0,
        hasWater: false,
        waterColor: 0x145266,
        waterSize: [6500, 3500],
        waterCenter: [-512, -1152],
        palette: { sand: 0xd9a76a, rock: 0x9e5b32, peak: 0xc47e45, shoreY: -50.0 },
        preset: "noon",
        terrainTexture: "/static/assets/textures/terrains/c2_ggter_1.png",
    },
    c3: {
        name: "Op 3: Volcanic Badlands",
        center: [256, -3200],
        waterLevel: -20.0,
        hasWater: true,
        waterColor: 0x223820,
        waterSize: [5000, 11000],
        waterCenter: [256, -3200],
        palette: { sand: 0x242426, rock: 0x473232, peak: 0x822a2a, shoreY: -20.0 },
        preset: "storm",
        terrainTexture: "/static/assets/textures/terrains/c3_gter_1.png",
    },
    c4: {
        name: "Op 4: Highland Mountains",
        center: [128, 1280],
        waterLevel: -10.0,
        hasWater: true,
        waterColor: 0x1b4559,
        waterSize: [5500, 8000],
        waterCenter: [128, 1280],
        palette: { sand: 0x526b48, rock: 0x545b63, peak: 0xd9e5eb, shoreY: -10.0 },
        preset: "noon",
        terrainTexture: "/static/assets/textures/terrains/c4_gter_1.png",
    },
    t1: {
        name: "Training Grounds",
        center: [1792, -1408],
        waterLevel: -50.0,
        hasWater: false,
        waterColor: 0x145266,
        waterSize: [4000, 3000],
        waterCenter: [1792, -1408],
        palette: { sand: 0x73695b, rock: 0x4a4744, peak: 0x8a847e, shoreY: -30.0 },
        preset: "noon",
        terrainTexture: "/static/assets/textures/terrains/t1_ggter1.png",
    },
};
OP_ENV_METADATA.coastal = OP_ENV_METADATA.c1;
OP_ENV_METADATA.desert = OP_ENV_METADATA.c2;
OP_ENV_METADATA.volcanic = OP_ENV_METADATA.c3;
OP_ENV_METADATA.highland = OP_ENV_METADATA.c4;
OP_ENV_METADATA.training = OP_ENV_METADATA.t1;
OP_ENV_METADATA.industrial = OP_ENV_METADATA.c1;

function getTerrainHeight(x, z) {
    if (terrainMesh) {
        const ray = new THREE.Raycaster(
            new THREE.Vector3(x, 400.0, z),
            new THREE.Vector3(0, -1, 0),
            0.0,
            1000.0,
        );
        const hits = ray.intersectObject(terrainMesh, false);
        if (hits.length > 0) {
            return Math.round(hits[0].point.y * 10) / 10;
        }
    }
    return 0.0;
}

// Init Three.js Viewport
function initViewport() {
    const container = document.getElementById("viewport");
    const width = container.clientWidth;
    const height = container.clientHeight;

    // Scene
    scene = new THREE.Scene();
    scene.background = new THREE.Color(0x0e141f);
    scene.fog = new THREE.FogExp2(0x0e141f, 0.0006);

    // Camera
    camera = new THREE.PerspectiveCamera(45, width / height, 2.0, 10000);
    camera.position.set(-600, 450, 750);

    // Renderer
    renderer = new THREE.WebGLRenderer({ antialias: true, powerPreference: "high-performance" });
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.1;
    container.appendChild(renderer.domElement);

    // OrbitControls
    orbitControls = new THREE.OrbitControls(camera, renderer.domElement);
    orbitControls.enableDamping = true;
    orbitControls.dampingFactor = 0.05;
    orbitControls.maxPolarAngle = Math.PI / 2 - 0.02; // Don't go below ground
    orbitControls.minDistance = 20;
    orbitControls.maxDistance = 3500;
    orbitControls.target.set(0, 0, 0);

    // TransformControls
    transformControls = new THREE.TransformControls(camera, renderer.domElement);
    transformControls.setMode("translate");
    transformControls.showY = false; // Restrict translation to X/Z plane (Y snaps to terrain)
    transformControls.addEventListener("dragging-changed", (event) => {
        orbitControls.enabled = !event.value;
    });
    transformControls.addEventListener("change", () => {
        if (transformControls.object && state.selectedAssetId) {
            const pos = transformControls.object.position;
            // Snap Y to terrain height
            const th = getTerrainHeight(
                pos.x,
                pos.z,
                state.project.terrain.biome,
                state.project.terrain.height_scale,
                state.project.terrain.roughness,
            );
            pos.y = th;

            const asset = state.project.assets.find((a) => a.asset_id === state.selectedAssetId);
            if (asset) {
                asset.x = Math.round(pos.x * 10) / 10;
                asset.y = Math.round(pos.y * 10) / 10;
                asset.z = Math.round(pos.z * 10) / 10;
                updateInspector();
            }
        }
    });
    scene.add(transformControls);

    // Sun Directional Light
    sunLight = new THREE.DirectionalLight(0xfffaed, 1.2);
    sunLight.castShadow = true;
    sunLight.shadow.mapSize.width = 2048;
    sunLight.shadow.mapSize.height = 2048;
    sunLight.shadow.camera.near = 100;
    sunLight.shadow.camera.far = 4500;
    const d = 1600;
    sunLight.shadow.camera.left = -d;
    sunLight.shadow.camera.right = d;
    sunLight.shadow.camera.top = d;
    sunLight.shadow.camera.bottom = -d;
    sunLight.shadow.bias = -0.0005;
    scene.add(sunLight);

    // Ambient Light
    ambientLight = new THREE.AmbientLight(0x2a364a, 0.4);
    scene.add(ambientLight);

    // Grid & Compass Marker
    const gridHelper = new THREE.GridHelper(3000, 60, 0x00f0ff, 0x1f2c42);
    gridHelper.position.y = -0.2;
    scene.add(gridHelper);

    // Build Procedural Terrain
    buildTerrain();

    // Create Ghost Preview Object
    ghostPreview = new THREE.Group();
    ghostPreview.visible = false;
    scene.add(ghostPreview);

    // Event Listeners
    window.addEventListener("resize", onWindowResize);
    container.addEventListener("mousemove", onMouseMove);
    container.addEventListener("click", onCanvasClick);
    window.addEventListener("keydown", onKeyDown);

    // Animation Loop
    animate();
}

/**
 * Replace the preview terrain/water using project dimensions and biome settings.
 * Removing objects from scene does not dispose GPU resources. Resource cleanup
 * is a separate outstanding lifecycle concern, not supplied by this rebuild.
 */
let terrainCache = {};

function buildTerrainGeometryFromData(terrainData, opCode) {
    const geom = new THREE.BufferGeometry();
    const verts = terrainData.vertices;
    const faces = terrainData.faces;

    const positions = new Float32Array(faces.length * 3 * 3);
    const colors = new Float32Array(faces.length * 3 * 3);
    const uvs = new Float32Array(faces.length * 3 * 2);
    let ptr = 0;
    let cptr = 0;
    let uvptr = 0;

    const meta = OP_ENV_METADATA[opCode] || OP_ENV_METADATA.c1;
    const pal = meta.palette;
    const colSand = new THREE.Color(pal.sand);
    const colRock = new THREE.Color(pal.rock);
    const colPeak = new THREE.Color(pal.peak);
    const tempCol = new THREE.Color();

    for (let i = 0; i < faces.length; i++) {
        const f = faces[i];
        const v0 = verts[f[0]];
        const v1 = verts[f[1]];
        const v2 = verts[f[2]];
        if (!v0 || !v1 || !v2) continue;

        positions[ptr++] = v0[0];
        positions[ptr++] = v0[1];
        positions[ptr++] = v0[2];

        positions[ptr++] = v1[0];
        positions[ptr++] = v1[1];
        positions[ptr++] = v1[2];

        positions[ptr++] = v2[0];
        positions[ptr++] = v2[1];
        positions[ptr++] = v2[2];

        // Compute vertex colors based on height relative to operation water / floor
        for (const v of [v0, v1, v2]) {
            const y = v[1];
            if (y <= pal.shoreY + 1.5) {
                tempCol.copy(colSand);
            } else if (y < pal.shoreY + 28.0) {
                const t = (y - pal.shoreY) / 28.0;
                tempCol.lerpColors(colSand, colRock, t);
            } else {
                const t = Math.min(1.0, (y - pal.shoreY - 28.0) / 35.0);
                tempCol.lerpColors(colRock, colPeak, t);
            }
            colors[cptr++] = tempCol.r;
            colors[cptr++] = tempCol.g;
            colors[cptr++] = tempCol.b;

            // Planar UV projection (~25m repeat interval) for seamless authentic ground textures
            uvs[uvptr++] = v[0] * 0.04;
            uvs[uvptr++] = v[2] * 0.04;
        }
    }

    geom.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geom.setAttribute("color", new THREE.BufferAttribute(colors, 3));
    geom.setAttribute("uv", new THREE.BufferAttribute(uvs, 2));
    geom.computeVertexNormals();
    return geom;
}

async function buildTerrain() {
    if (terrainMesh) {
        scene.remove(terrainMesh);
        if (terrainMesh.geometry) terrainMesh.geometry.dispose();
        terrainMesh = null;
    }
    if (waterMesh) {
        scene.remove(waterMesh);
        if (waterMesh.geometry) waterMesh.geometry.dispose();
        waterMesh = null;
    }

    const rawOp = state.project.base_operation || state.project.terrain.biome || "c1";
    const opCode =
        rawOp === "coastal"
            ? "c1"
            : rawOp === "desert"
              ? "c2"
              : rawOp === "volcanic"
                ? "c3"
                : rawOp === "highland"
                  ? "c4"
                  : rawOp === "training"
                    ? "t1"
                    : rawOp;
    state.project.base_operation = opCode;
    state.project.terrain.biome = opCode;

    const meta = OP_ENV_METADATA[opCode] || OP_ENV_METADATA.c1;

    // 1. Fetch or use cached authentic terrain mesh
    let tData = terrainCache[opCode];
    if (!tData) {
        try {
            const res = await fetch(`/static/assets/terrains/${opCode}.json`);
            if (res.ok) {
                tData = await res.json();
                terrainCache[opCode] = tData;
            }
        } catch (e) {
            console.warn("Could not load terrain JSON for", opCode, e);
        }
    }

    if (tData) {
        const geom = buildTerrainGeometryFromData(tData, opCode);
        let terrainTex = null;
        if (meta.terrainTexture) {
            terrainTex = new THREE.TextureLoader().load(meta.terrainTexture);
            terrainTex.wrapS = THREE.RepeatWrapping;
            terrainTex.wrapT = THREE.RepeatWrapping;
        }
        const mat = new THREE.MeshStandardMaterial({
            map: terrainTex,
            vertexColors: true,
            roughness: 0.88,
            metalness: 0.1,
            flatShading: false,
        });
        terrainMesh = new THREE.Mesh(geom, mat);
        terrainMesh.receiveShadow = true;
        terrainMesh.name = "terrain";
        scene.add(terrainMesh);
        console.log(
            `[Map Studio] Loaded authentic ${meta.name} terrain mesh (${tData.vertices.length} vertices, ${tData.faces.length} faces) with in-game texture ${meta.terrainTexture}`,
        );
    }

    // 2. Water Plane (if operation features water)
    if (meta.hasWater) {
        const waterGeom = new THREE.PlaneGeometry(meta.waterSize[0], meta.waterSize[1]);
        waterGeom.rotateX(-Math.PI / 2);
        const waterMat = new THREE.MeshStandardMaterial({
            color: meta.waterColor,
            roughness: 0.15,
            metalness: 0.75,
            transparent: true,
            opacity: 0.7,
        });
        waterMesh = new THREE.Mesh(waterGeom, waterMat);
        waterMesh.position.set(meta.waterCenter[0], meta.waterLevel, meta.waterCenter[1]);
        waterMesh.receiveShadow = true;
        scene.add(waterMesh);
    }

    // 3. Center orbit controls around operation center
    orbitControls.target.set(meta.center[0], 0, meta.center[1]);
    camera.position.set(meta.center[0] - 650, 480, meta.center[1] + 750);
    orbitControls.update();

    updateLighting();

    // 4. Snap all placed assets to the authentic terrain surface
    for (const asset of state.project.assets) {
        asset.y = getTerrainHeight(asset.x, asset.z);
    }
    syncSceneAssets();
}

// Update Lighting from State
function updateLighting() {
    const lcfg = state.project.lighting;
    const azRad = THREE.MathUtils.degToRad(lcfg.azimuth);
    const elRad = THREE.MathUtils.degToRad(lcfg.elevation);

    const dist = 2200;
    const sx = Math.sin(azRad) * Math.cos(elRad) * dist;
    const sy = Math.sin(elRad) * dist;
    const sz = Math.cos(azRad) * Math.cos(elRad) * dist;

    sunLight.position.set(sx, sy, sz);
    sunLight.color.setRGB(lcfg.sun_color[0], lcfg.sun_color[1], lcfg.sun_color[2]);
    sunLight.intensity = lcfg.strength * 1.5;

    ambientLight.intensity = lcfg.ambient;

    const skyCol = new THREE.Color().fromArray(lcfg.sky_tint);
    scene.background = skyCol;
    scene.fog.color = skyCol;
    scene.fog.density = 1.0 / (lcfg.fog_distance * 2.2);
}

let gameAssetsData = {};

// Build Three.js BufferGeometry from in-game vertex & polygon data
function buildGeometryFromData(assetData) {
    const geom = new THREE.BufferGeometry();
    const verts = assetData.vertices;
    const faces = assetData.faces;

    const positions = new Float32Array(faces.length * 3 * 3);
    let ptr = 0;
    for (let i = 0; i < faces.length; i++) {
        const f = faces[i];
        const v0 = verts[f[0]];
        const v1 = verts[f[1]];
        const v2 = verts[f[2]];
        if (!v0 || !v1 || !v2) continue;

        positions[ptr++] = v0[0];
        positions[ptr++] = v0[1];
        positions[ptr++] = v0[2];
        positions[ptr++] = v1[0];
        positions[ptr++] = v1[1];
        positions[ptr++] = v1[2];
        positions[ptr++] = v2[0];
        positions[ptr++] = v2[1];
        positions[ptr++] = v2[2];
    }

    geom.setAttribute("position", new THREE.BufferAttribute(positions, 3));
    geom.computeVertexNormals();
    return geom;
}

/**
 * Optionally read locally extracted static meshes after the initial UI appears.
 * A missing catalog leaves procedural markers usable. syncSceneAssets updates
 * existing groups rather than rebuilding them, so loading does not guarantee
 * that every already-created placeholder is replaced with extracted geometry.
 */
async function loadGameAssets() {
    try {
        const res = await fetch("/static/assets/game_assets_3d.json");
        if (res.ok) {
            gameAssetsData = await res.json();
            console.log(
                "[Map Studio] Loaded authentic MW3 in-game 3D assets:",
                Object.keys(gameAssetsData),
            );
            // Refresh placements after loading; existing groups retain their geometry.
            syncSceneAssets();
        }
    } catch (e) {
        console.warn("[Map Studio] Could not load in-game assets JSON:", e);
    }
}

/**
 * Build one display group from extracted geometry or procedural tactical shapes.
 * The root group carries asset_id for selection; child meshes carry geometry.
 * This does not create a native game entity, physics body or animation rig.
 */
function createAssetMesh(asset) {
    const group = new THREE.Group();
    group.name = asset.asset_id;

    const factionColors = {
        player: 0x00ff88,
        friendly: 0x00d2ff,
        enemy: 0xff3366,
        neutral: 0xffaa00,
    };
    const fColor = factionColors[asset.faction] || 0xffaa00;

    // Material helpers
    const matArmor = new THREE.MeshStandardMaterial({
        color: 0x5a6372,
        roughness: 0.35,
        metalness: 0.65,
    });
    const matTrim = new THREE.MeshStandardMaterial({
        color: fColor,
        roughness: 0.2,
        metalness: 0.8,
    });
    const matGlow = new THREE.MeshBasicMaterial({ color: fColor });

    // 1. Check if authentic in-game 3D geometry is available
    if (gameAssetsData && gameAssetsData[asset.asset_type]) {
        const geom = buildGeometryFromData(gameAssetsData[asset.asset_type]);
        const mesh = new THREE.Mesh(geom, matArmor);
        mesh.castShadow = true;
        mesh.receiveShadow = true;
        group.add(mesh);

        // Subtle edge / faction outline
        const wire = new THREE.Mesh(
            geom,
            new THREE.MeshBasicMaterial({
                color: fColor,
                wireframe: true,
                transparent: true,
                opacity: 0.25,
            }),
        );
        group.add(wire);

        // If it's a BattleMech, add a glowing tactical beacon ring at feet
        if (asset.asset_type.startsWith("mech_") || asset.asset_type === "patrol") {
            const ring = new THREE.Mesh(new THREE.RingGeometry(3.5, 4.2, 24), matGlow);
            ring.rotation.x = -Math.PI / 2;
            ring.position.y = 0.15;
            group.add(ring);
        }

        group.position.set(asset.x, asset.y, asset.z);
        group.rotation.y = THREE.MathUtils.degToRad(asset.yaw_deg || 0);
        return group;
    }

    // 2. Procedural Fallbacks for non-mesh types or until JSON finishes loading
    if (asset.asset_type === "turret_srm") {
        // Octagonal base
        const base = new THREE.Mesh(new THREE.CylinderGeometry(8, 10, 6, 8), matArmor);
        base.position.y = 3;
        base.castShadow = true;
        group.add(base);

        // Turret head
        const head = new THREE.Mesh(new THREE.BoxGeometry(9, 7, 10), matArmor);
        head.position.y = 9;
        head.castShadow = true;
        group.add(head);

        // Twin missile pods
        const podL = new THREE.Mesh(new THREE.BoxGeometry(4, 5, 8), matTrim);
        podL.position.set(-6, 9, 2);
        podL.castShadow = true;
        group.add(podL);

        const podR = new THREE.Mesh(new THREE.BoxGeometry(4, 5, 8), matTrim);
        podR.position.set(6, 9, 2);
        podR.castShadow = true;
        group.add(podR);
    } else if (asset.asset_type === "turret_laser") {
        // Tall triangular lattice tower
        const tower = new THREE.Mesh(new THREE.CylinderGeometry(3, 7, 24, 4), matArmor);
        tower.position.y = 12;
        tower.castShadow = true;
        group.add(tower);

        // Swivel laser emitter dome
        const dome = new THREE.Mesh(new THREE.SphereGeometry(5, 8, 8), matTrim);
        dome.position.y = 25;
        dome.castShadow = true;
        group.add(dome);

        // Barrel
        const barrel = new THREE.Mesh(new THREE.CylinderGeometry(1.2, 1.2, 10, 6), matArmor);
        barrel.rotation.x = Math.PI / 2;
        barrel.position.set(0, 25, 5);
        group.add(barrel);
    } else if (asset.asset_type === "bunker") {
        // Low profile reinforced bunker
        const bldg = new THREE.Mesh(new THREE.BoxGeometry(28, 10, 22), matArmor);
        bldg.position.y = 5;
        bldg.castShadow = true;
        group.add(bldg);

        // Sloped blast shield
        const shield = new THREE.Mesh(new THREE.ConeGeometry(22, 6, 4), matTrim);
        shield.rotation.y = Math.PI / 4;
        shield.position.y = 12;
        shield.castShadow = true;
        group.add(shield);
    } else if (asset.asset_type === "comm_center") {
        // Headquarters dome
        const base = new THREE.Mesh(new THREE.CylinderGeometry(14, 16, 12, 10), matArmor);
        base.position.y = 6;
        base.castShadow = true;
        group.add(base);

        // Radar antenna mast & rotating dish
        const mast = new THREE.Mesh(new THREE.CylinderGeometry(1, 1.5, 18, 6), matArmor);
        mast.position.y = 18;
        group.add(mast);

        const dish = new THREE.Mesh(new THREE.CylinderGeometry(8, 1, 3, 12, 1, true), matTrim);
        dish.rotation.x = Math.PI / 3;
        dish.position.set(0, 26, 0);
        dish.castShadow = true;
        group.add(dish);
    } else if (asset.asset_type === "repair_station") {
        // Heavy dual crane pylons
        const pylonL = new THREE.Mesh(new THREE.BoxGeometry(4, 26, 4), matTrim);
        pylonL.position.set(-14, 13, 0);
        pylonL.castShadow = true;
        group.add(pylonL);

        const pylonR = new THREE.Mesh(new THREE.BoxGeometry(4, 26, 4), matTrim);
        pylonR.position.set(14, 13, 0);
        pylonR.castShadow = true;
        group.add(pylonR);

        // Cross beam
        const beam = new THREE.Mesh(new THREE.BoxGeometry(32, 4, 6), matArmor);
        beam.position.set(0, 26, 0);
        beam.castShadow = true;
        group.add(beam);

        // Glowing repair pad grid
        const pad = new THREE.Mesh(new THREE.PlaneGeometry(24, 24), matGlow);
        pad.rotation.x = -Math.PI / 2;
        pad.position.y = 0.3;
        group.add(pad);
    } else if (asset.asset_type === "factory") {
        // Industrial warehouse
        const bldg = new THREE.Mesh(new THREE.BoxGeometry(42, 18, 30), matArmor);
        bldg.position.y = 9;
        bldg.castShadow = true;
        group.add(bldg);

        // Twin smokestacks
        const s1 = new THREE.Mesh(new THREE.CylinderGeometry(2, 2.5, 24, 8), matTrim);
        s1.position.set(-12, 21, -8);
        s1.castShadow = true;
        group.add(s1);

        const s2 = new THREE.Mesh(new THREE.CylinderGeometry(2, 2.5, 24, 8), matTrim);
        s2.position.set(-5, 21, -8);
        s2.castShadow = true;
        group.add(s2);
    } else if (asset.asset_type === "fuel_tank") {
        // Twin cylindrical storage tanks
        const t1 = new THREE.Mesh(new THREE.CylinderGeometry(8, 8, 16, 12), matArmor);
        t1.position.set(-10, 8, 0);
        t1.castShadow = true;
        group.add(t1);

        const t2 = new THREE.Mesh(new THREE.CylinderGeometry(8, 8, 16, 12), matArmor);
        t2.position.set(10, 8, 0);
        t2.castShadow = true;
        group.add(t2);
    } else if (asset.asset_type === "spawn") {
        // Player orbital drop zone beacon
        const ring = new THREE.Mesh(new THREE.RingGeometry(12, 15, 24), matGlow);
        ring.rotation.x = -Math.PI / 2;
        ring.position.y = 0.5;
        group.add(ring);

        // Vertical holographic light beam
        const beam = new THREE.Mesh(
            new THREE.CylinderGeometry(1, 1, 80, 8),
            new THREE.MeshBasicMaterial({
                color: 0x00ff88,
                transparent: true,
                opacity: 0.35,
            }),
        );
        beam.position.y = 40;
        group.add(beam);
    } else if (asset.asset_type === "nav") {
        // Floating tactical waypoint diamond
        const diamond = new THREE.Mesh(new THREE.OctahedronGeometry(6), matTrim);
        diamond.position.y = 16;
        group.add(diamond);

        // Pulsing ground ring
        const pRing = new THREE.Mesh(new THREE.RingGeometry(6, 8, 16), matGlow);
        pRing.rotation.x = -Math.PI / 2;
        pRing.position.y = 0.4;
        group.add(pRing);
    } else if (asset.asset_type === "patrol") {
        // Enemy BattleMech silhouette marker
        const mechTorso = new THREE.Mesh(new THREE.BoxGeometry(10, 8, 8), matTrim);
        mechTorso.position.y = 14;
        group.add(mechTorso);

        const head = new THREE.Mesh(new THREE.BoxGeometry(4, 3, 5), matArmor);
        head.position.set(0, 19, 2);
        group.add(head);

        const cone = new THREE.Mesh(
            new THREE.ConeGeometry(8, 20, 8),
            new THREE.MeshBasicMaterial({
                color: 0xff3366,
                transparent: true,
                opacity: 0.3,
            }),
        );
        cone.rotation.x = Math.PI / 2;
        cone.position.set(0, 0.5, 14);
        group.add(cone);
    } else if (asset.asset_type.startsWith("trig_")) {
        const radius = asset.trigger_radius || 40.0;
        const height = 18.0;

        let trigColor = 0x00ff88;
        if (asset.asset_type === "trig_ambush") {
            trigColor = 0xff3366;
        } else if (asset.asset_type === "trig_sensor") {
            trigColor = 0x00f0ff;
        } else if (asset.asset_type === "trig_minefield") {
            trigColor = 0xffaa00;
        }

        // Cylindrical trigger volume
        const volGeom = new THREE.CylinderGeometry(radius, radius, height, 32);
        const volMat = new THREE.MeshBasicMaterial({
            color: trigColor,
            transparent: true,
            opacity: 0.18,
            side: THREE.DoubleSide,
            depthWrite: false,
        });
        const volMesh = new THREE.Mesh(volGeom, volMat);
        volMesh.position.y = height / 2;
        group.add(volMesh);

        // Perimeter cage
        const wireGeom = new THREE.CylinderGeometry(radius, radius, height, 16);
        const wireMat = new THREE.MeshBasicMaterial({
            color: trigColor,
            wireframe: true,
            transparent: true,
            opacity: 0.4,
        });
        const wireMesh = new THREE.Mesh(wireGeom, wireMat);
        wireMesh.position.y = height / 2;
        group.add(wireMesh);

        // Ground ring
        const ringGeom = new THREE.RingGeometry(radius - 2.0, radius, 32);
        const ringMat = new THREE.MeshBasicMaterial({
            color: trigColor,
            side: THREE.DoubleSide,
        });
        const ringMesh = new THREE.Mesh(ringGeom, ringMat);
        ringMesh.rotation.x = -Math.PI / 2;
        ringMesh.position.y = 0.35;
        group.add(ringMesh);

        // Vertical holographic beacon beam
        const beam = new THREE.Mesh(
            new THREE.CylinderGeometry(0.8, 0.8, 50, 8),
            new THREE.MeshBasicMaterial({ color: trigColor, transparent: true, opacity: 0.55 }),
        );
        beam.position.y = 25;
        group.add(beam);
    }

    // Position and yaw
    group.position.set(asset.x, asset.y, asset.z);
    group.rotation.y = THREE.MathUtils.degToRad(asset.yaw_deg || 0);

    return group;
}

// Dynamic waypoint route line
let waypointTrajectoryLine = null;

function updateWaypointTrajectories() {
    if (waypointTrajectoryLine) {
        scene.remove(waypointTrajectoryLine);
        if (waypointTrajectoryLine.geometry) waypointTrajectoryLine.geometry.dispose();
        waypointTrajectoryLine = null;
    }

    const navPoints = state.project.assets
        .filter((a) => a.asset_type === "nav" || a.asset_type === "spawn")
        .sort((a, b) => {
            if (a.asset_type === "spawn") return -1;
            if (b.asset_type === "spawn") return 1;
            return (a.name || "").localeCompare(b.name || "");
        });

    if (navPoints.length < 2) return;

    const points = navPoints.map((p) => new THREE.Vector3(p.x, p.y + 3.0, p.z));
    const geom = new THREE.BufferGeometry().setFromPoints(points);
    const mat = new THREE.LineDashedMaterial({
        color: 0x00f0ff,
        dashSize: 20,
        gapSize: 10,
        linewidth: 2,
    });
    waypointTrajectoryLine = new THREE.Line(geom, mat);
    waypointTrajectoryLine.computeLineDistances();
    scene.add(waypointTrajectoryLine);
}

/**
 * Reconcile project IDs with display groups, then update transforms/selection.
 * Existing meshes retain their geometry/materials. Callers that change appearance
 * currently remove a group explicitly before requesting a fresh one.
 */
function syncSceneAssets() {
    // Remove deleted assets
    for (const [id, grp] of assetObjectMap.entries()) {
        if (!state.project.assets.some((a) => a.asset_id === id)) {
            scene.remove(grp);
            assetObjectMap.delete(id);
        }
    }

    // Add or update assets
    for (const asset of state.project.assets) {
        let grp = assetObjectMap.get(asset.asset_id);
        if (!grp) {
            grp = createAssetMesh(asset);
            scene.add(grp);
            assetObjectMap.set(asset.asset_id, grp);
        } else {
            grp.position.set(asset.x, asset.y, asset.z);
            grp.rotation.y = THREE.MathUtils.degToRad(asset.yaw_deg || 0);
        }
    }

    // Update dynamic waypoint trajectory routes
    updateWaypointTrajectories();

    // Update selection
    if (state.selectedAssetId && assetObjectMap.has(state.selectedAssetId)) {
        transformControls.attach(assetObjectMap.get(state.selectedAssetId));
    } else {
        transformControls.detach();
    }

    document.getElementById("stat-entities").innerText = state.project.assets.length;
}

/** Convert viewport pixels to a ray hit on the preview terrain, or null. */
function raycastTerrain(event) {
    const container = document.getElementById("viewport");
    const rect = container.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;

    raycaster.setFromCamera(mouse, camera);
    const intersects = raycaster.intersectObjects([terrainMesh], true);
    if (intersects.length > 0) {
        return intersects[0].point;
    }
    return null;
}

// Mouse Move Handler
function onMouseMove(event) {
    const pt = raycastTerrain(event);
    if (pt) {
        document.getElementById("stat-coords").innerText =
            `X: ${Math.round(pt.x)} | Y: ${Math.round(pt.y)} | Z: ${Math.round(pt.z)}`;

        if (state.activeTool) {
            ghostPreview.position.copy(pt);
            ghostPreview.visible = true;
        }
    } else {
        if (state.activeTool) ghostPreview.visible = false;
    }
}

// Canvas Click Handler (Place or Select)
function onCanvasClick(event) {
    // If dragging transform controls, ignore
    if (transformControls.dragging) return;

    const container = document.getElementById("viewport");
    const rect = container.getBoundingClientRect();
    mouse.x = ((event.clientX - rect.left) / container.clientWidth) * 2 - 1;
    mouse.y = -((event.clientY - rect.top) / container.clientHeight) * 2 + 1;
    raycaster.setFromCamera(mouse, camera);

    // If in placement mode:
    if (state.activeTool) {
        const pt = raycastTerrain(event);
        if (pt) {
            const newAsset = {
                asset_id: `asset_${Date.now()}`,
                asset_type: state.activeTool,
                name: getDefaultName(state.activeTool),
                x: Math.round(pt.x * 10) / 10,
                y: Math.round(pt.y * 10) / 10,
                z: Math.round(pt.z * 10) / 10,
                yaw_deg: 0,
                faction: getDefaultFaction(state.activeTool),
                health: 100,
                is_objective:
                    state.activeTool.includes("comm") || state.activeTool.includes("bunker"),
            };

            state.project.assets.push(newAsset);
            state.selectedAssetId = newAsset.asset_id;
            playBeep(580, "triangle", 0.1);

            syncSceneAssets();
            updateInspector();

            // Auto-exit placement mode after placement (press Esc or tool card)
            clearActiveTool();
        }
        return;
    }

    // Otherwise: Select placed asset
    const objectCandidates = Array.from(assetObjectMap.values());
    const hits = raycaster.intersectObjects(objectCandidates, true);
    if (hits.length > 0) {
        // Find root group in assetObjectMap
        let cur = hits[0].object;
        while (cur && cur.parent && !assetObjectMap.has(cur.name)) {
            cur = cur.parent;
        }
        if (cur && assetObjectMap.has(cur.name)) {
            state.selectedAssetId = cur.name;
            playBeep(720, "sine", 0.05);
            syncSceneAssets();
            updateInspector();
            return;
        }
    }

    // Clicked on empty terrain -> deselect
    state.selectedAssetId = null;
    syncSceneAssets();
    updateInspector();
}

// Helpers for Asset Defaults
function getDefaultName(type) {
    const titles = {
        turret_srm: "SRM Defense Turret",
        turret_laser: "Heavy Laser Battery",
        bunker: "Command Bunker Alpha",
        comm_center: "Satellite Comms Array",
        repair_station: "Mobile Field Base (MFB)",
        factory: "Mech Assembly Plant",
        fuel_tank: "Coolant Storage Silo",
        city_building: "Fortified City Garrison",
        bridge_span: "Highway Bridge Span",
        ramp: "Heavy Vehicle Ramp",
        dock: "Shoreline Platform Dock",
        defense_wall: "Perimeter Blast Wall",
        security_gate: "Security Blast Gate",
        powerline_pole: "Utility Powerline Pole",
        mech_madcat: "Timber Wolf / Mad Cat",
        mech_bushwacker: "Bushwacker BSW-X1",
        mech_thor: "Summoner / Thor",
        mech_shadowcat: "Shadow Cat",
        mech_vulture: "Mad Dog / Vulture",
        mech_daishi: "Dire Wolf / Daishi",
        spawn: "Player Orbital Drop Zone",
        nav: "Nav Point Able",
        patrol: "OpFor Patrol Lance",
    };
    return titles[type] || "World Installation";
}

function getDefaultFaction(type) {
    if (type === "spawn") return "player";
    if (type === "patrol" || type.startsWith("mech_")) return "enemy";
    if (type === "turret_srm" || type === "turret_laser" || type === "bunker") return "enemy";
    return "neutral";
}

// Active Tool Selection
function selectTool(type) {
    if (state.activeTool === type) {
        clearActiveTool();
        return;
    }
    state.activeTool = type;

    // Highlight UI
    document.querySelectorAll(".asset-card").forEach((el) => {
        el.classList.toggle("active", el.dataset.type === type);
    });

    const banner = document.getElementById("placement-banner");
    banner.style.display = "flex";
    banner.innerText = `PLACING: ${getDefaultName(type).toUpperCase()} (Click on terrain to place, ESC to cancel)`;

    // Update ghost preview mesh
    while (ghostPreview.children.length > 0) {
        ghostPreview.remove(ghostPreview.children[0]);
    }
    const previewAsset = {
        asset_id: "ghost",
        asset_type: type,
        faction: getDefaultFaction(type),
        x: 0,
        y: 0,
        z: 0,
        yaw_deg: 0,
    };
    const previewMesh = createAssetMesh(previewAsset);
    previewMesh.traverse((child) => {
        if (child.isMesh) {
            child.material = new THREE.MeshBasicMaterial({
                color: 0x00f0ff,
                wireframe: true,
                transparent: true,
                opacity: 0.7,
            });
        }
    });
    ghostPreview.add(previewMesh);
}

function clearActiveTool() {
    state.activeTool = null;
    document.querySelectorAll(".asset-card").forEach((el) => el.classList.remove("active"));
    document.getElementById("placement-banner").style.display = "none";
    ghostPreview.visible = false;
}

// Update Property Inspector UI
function updateInspector() {
    const card = document.getElementById("inspector-content");
    const emptyNotice = document.getElementById("inspector-empty");

    if (!state.selectedAssetId) {
        card.style.display = "none";
        emptyNotice.style.display = "block";
        return;
    }

    const asset = state.project.assets.find((a) => a.asset_id === state.selectedAssetId);
    if (!asset) {
        card.style.display = "none";
        emptyNotice.style.display = "block";
        return;
    }

    card.style.display = "block";
    emptyNotice.style.display = "none";

    document.getElementById("insp-name").value = asset.name;
    document.getElementById("insp-type").innerText = asset.asset_type.toUpperCase();
    document.getElementById("insp-pos-x").value = asset.x;
    document.getElementById("insp-pos-y").value = asset.y;
    document.getElementById("insp-pos-z").value = asset.z;
    document.getElementById("insp-yaw").value = Math.round(asset.yaw_deg || 0);
    document.getElementById("insp-yaw-label").innerText = `${Math.round(asset.yaw_deg || 0)}°`;
    document.getElementById("insp-faction").value = asset.faction;
    document.getElementById("insp-health").value = asset.health;
    document.getElementById("insp-health-label").innerText = asset.health;
    document.getElementById("insp-objective").checked = !!asset.is_objective;

    const objDescEl = document.getElementById("insp-objective-desc");
    if (objDescEl) objDescEl.value = asset.objective_desc || "";

    const isTrig = (asset.asset_type || "").startsWith("trig_");
    const trigSec = document.getElementById("insp-trigger-section");
    if (trigSec) {
        trigSec.style.display = isTrig ? "block" : "none";
        if (isTrig) {
            document.getElementById("insp-trigger-radius").value = asset.trigger_radius || 40;
            document.getElementById("insp-trigger-radius-label").innerText =
                `${asset.trigger_radius || 40}m`;
            document.getElementById("insp-trigger-action").value =
                asset.trigger_action ||
                (asset.asset_type === "trig_evac" ? "evac_complete" : "spawn_ambush");
            document.getElementById("insp-trigger-msg").value = asset.trigger_message || "";
        }
    }
}

// These handlers mutate state.project directly; the history fields in state are
// not a complete undo implementation. Sync/redraw is distinct from persistence.
function bindInspectorEvents() {
    document.getElementById("insp-name").addEventListener("input", (e) => {
        const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
        if (a) a.name = e.target.value;
    });

    const objDescInput = document.getElementById("insp-objective-desc");
    if (objDescInput) {
        objDescInput.addEventListener("input", (e) => {
            const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
            if (a) a.objective_desc = e.target.value;
        });
    }

    const trigRadius = document.getElementById("insp-trigger-radius");
    if (trigRadius) {
        trigRadius.addEventListener("input", (e) => {
            const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
            if (a) {
                a.trigger_radius = parseFloat(e.target.value);
                document.getElementById("insp-trigger-radius-label").innerText =
                    `${a.trigger_radius}m`;
                const grp = assetObjectMap.get(a.asset_id);
                if (grp) scene.remove(grp);
                assetObjectMap.delete(a.asset_id);
                syncSceneAssets();
            }
        });
    }

    const trigAction = document.getElementById("insp-trigger-action");
    if (trigAction) {
        trigAction.addEventListener("change", (e) => {
            const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
            if (a) a.trigger_action = e.target.value;
        });
    }

    const trigMsg = document.getElementById("insp-trigger-msg");
    if (trigMsg) {
        trigMsg.addEventListener("input", (e) => {
            const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
            if (a) a.trigger_message = e.target.value;
        });
    }

    document.getElementById("insp-yaw").addEventListener("input", (e) => {
        const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
        if (a) {
            a.yaw_deg = parseFloat(e.target.value);
            document.getElementById("insp-yaw-label").innerText = `${a.yaw_deg}°`;
            syncSceneAssets();
        }
    });

    document.getElementById("insp-faction").addEventListener("change", (e) => {
        const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
        if (a) {
            a.faction = e.target.value;
            // Re-create mesh for new colors
            const grp = assetObjectMap.get(a.asset_id);
            if (grp) scene.remove(grp);
            assetObjectMap.delete(a.asset_id);
            syncSceneAssets();
        }
    });

    document.getElementById("insp-health").addEventListener("input", (e) => {
        const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
        if (a) {
            a.health = parseInt(e.target.value);
            document.getElementById("insp-health-label").innerText = a.health;
        }
    });

    document.getElementById("insp-objective").addEventListener("change", (e) => {
        const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
        if (a) a.is_objective = e.target.checked;
    });

    document.getElementById("btn-insp-delete").addEventListener("click", () => {
        if (state.selectedAssetId) {
            state.project.assets = state.project.assets.filter(
                (a) => a.asset_id !== state.selectedAssetId,
            );
            state.selectedAssetId = null;
            playBeep(320, "sawtooth", 0.1);
            syncSceneAssets();
            updateInspector();
        }
    });

    document.getElementById("btn-insp-dup").addEventListener("click", () => {
        const orig = state.project.assets.find((a) => a.asset_id === state.selectedAssetId);
        if (orig) {
            const copy = JSON.parse(JSON.stringify(orig));
            copy.asset_id = `asset_${Date.now()}`;
            copy.name = `${orig.name} (Copy)`;
            copy.x += 25;
            copy.z += 25;
            copy.y = getTerrainHeight(
                copy.x,
                copy.z,
                state.project.terrain.biome,
                state.project.terrain.height_scale,
                state.project.terrain.roughness,
            );
            state.project.assets.push(copy);
            state.selectedAssetId = copy.asset_id;
            playBeep(640, "triangle", 0.08);
            syncSceneAssets();
            updateInspector();
        }
    });
}

// Camera View Mode Presets
function setViewMode(mode) {
    state.viewMode = mode;
    document.querySelectorAll(".hud-btn").forEach((btn) => btn.classList.remove("active"));
    document.getElementById(`btn-view-${mode}`).classList.add("active");

    const opCode = state.project.base_operation || "c1";
    const meta = OP_ENV_METADATA[opCode] || OP_ENV_METADATA.c1;
    const cx = meta.center[0];
    const cz = meta.center[1];

    orbitControls.reset();
    orbitControls.target.set(cx, 0, cz);

    if (mode === "topdown") {
        camera.position.set(cx, 2400, cz);
        orbitControls.maxPolarAngle = 0.001; // Lock to top-down
    } else if (mode === "iso") {
        camera.position.set(cx - 1100, 1100, cz + 1100);
        orbitControls.maxPolarAngle = Math.PI / 2 - 0.02;
    } else {
        // orbit
        camera.position.set(cx - 650, 480, cz + 750);
        orbitControls.maxPolarAngle = Math.PI / 2 - 0.02;
    }
    orbitControls.update();
}

// Environment Presets
function setEnvPreset(preset) {
    state.project.lighting.preset_name = preset;
    document.querySelectorAll(".preset-chip").forEach((c) => c.classList.remove("active"));
    document.getElementById(`preset-${preset}`).classList.add("active");

    if (preset === "noon") {
        state.project.lighting.azimuth = 180;
        state.project.lighting.elevation = 75;
        state.project.lighting.strength = 1.0;
        state.project.lighting.ambient = 0.35;
        state.project.lighting.sun_color = [1.0, 1.0, 0.95];
        state.project.lighting.sky_tint = [0.45, 0.65, 0.95];
    } else if (preset === "sunset") {
        state.project.lighting.azimuth = 235;
        state.project.lighting.elevation = 28;
        state.project.lighting.strength = 0.9;
        state.project.lighting.ambient = 0.22;
        state.project.lighting.sun_color = [1.0, 0.75, 0.5];
        state.project.lighting.sky_tint = [0.38, 0.28, 0.48];
    } else if (preset === "night") {
        state.project.lighting.azimuth = 45;
        state.project.lighting.elevation = 15;
        state.project.lighting.strength = 0.15;
        state.project.lighting.ambient = 0.08;
        state.project.lighting.sun_color = [0.4, 0.55, 0.85];
        state.project.lighting.sky_tint = [0.04, 0.06, 0.12];
    } else if (preset === "storm") {
        state.project.lighting.azimuth = 200;
        state.project.lighting.elevation = 40;
        state.project.lighting.strength = 0.45;
        state.project.lighting.ambient = 0.15;
        state.project.lighting.sun_color = [0.8, 0.65, 0.45];
        state.project.lighting.sky_tint = [0.25, 0.22, 0.2];
    }

    // Update slider UI
    document.getElementById("env-azimuth").value = state.project.lighting.azimuth;
    document.getElementById("env-elevation").value = state.project.lighting.elevation;
    document.getElementById("env-strength").value = state.project.lighting.strength;
    document.getElementById("env-ambient").value = state.project.lighting.ambient;

    updateLighting();
}

// Load Demo Map Layout (Iron Ridge Outpost)
function loadDemoMap() {
    state.project.pack_id = "iron_ridge_outpost";
    state.project.pack_title = "Iron Ridge Outpost";
    state.project.description =
        "Fortified Clan Smoke Jaguar communications outpost nestled in the coastal bluff of Tranquil.";
    state.project.base_operation = "c1";
    state.project.terrain.biome = "c1";
    state.project.terrain.water_level = 3.0;

    state.project.assets = [
        // Player Spawn
        {
            asset_id: "p_spawn",
            asset_type: "spawn",
            name: "Player Orbital Drop Zone",
            x: -650,
            y: 0,
            z: -700,
            yaw_deg: 45,
            faction: "player",
            health: 100,
        },
        // Command Bunker & Comms (In-Game 3D Models)
        {
            asset_id: "bunk_cmd",
            asset_type: "bunker",
            name: "Outpost Command Bunker",
            x: -420,
            y: 0,
            z: -680,
            yaw_deg: 180,
            faction: "enemy",
            health: 250,
            is_objective: true,
        },
        {
            asset_id: "comm_main",
            asset_type: "comm_center",
            name: "Primary Comms Dish",
            x: -360,
            y: 0,
            z: -620,
            yaw_deg: 210,
            faction: "enemy",
            health: 150,
            is_objective: true,
        },
        // Defense Perimeter (In-Game 3D Models)
        {
            asset_id: "tur_srm_1",
            asset_type: "turret_srm",
            name: "Perimeter SRM Alpha",
            x: -560,
            y: 0,
            z: -780,
            yaw_deg: 135,
            faction: "enemy",
            health: 120,
        },
        {
            asset_id: "tur_srm_2",
            asset_type: "turret_srm",
            name: "Perimeter SRM Beta",
            x: -300,
            y: 0,
            z: -820,
            yaw_deg: 225,
            faction: "enemy",
            health: 120,
        },
        {
            asset_id: "tur_las_1",
            asset_type: "turret_laser",
            name: "Ridge Laser Tower",
            x: -480,
            y: 0,
            z: -560,
            yaw_deg: 0,
            faction: "enemy",
            health: 150,
        },
        // Coolant Silo & Garrison (In-Game 3D Models)
        {
            asset_id: "fuel_1",
            asset_type: "fuel_tank",
            name: "Refinery Coolant Silo",
            x: -320,
            y: 0,
            z: -580,
            yaw_deg: 45,
            faction: "neutral",
            health: 60,
        },
        {
            asset_id: "garrison_1",
            asset_type: "city_building",
            name: "Forward Garrison Block",
            x: -520,
            y: 0,
            z: -620,
            yaw_deg: 0,
            faction: "enemy",
            health: 180,
        },
        // Authentic In-Game Environment Props
        {
            asset_id: "dock_1",
            asset_type: "dock",
            name: "Shoreline Platform Dock",
            x: -780,
            y: 0,
            z: -850,
            yaw_deg: 40,
            faction: "neutral",
            health: 200,
        },
        {
            asset_id: "wall_1",
            asset_type: "defense_wall",
            name: "North Perimeter Wall",
            x: -480,
            y: 0,
            z: -800,
            yaw_deg: 90,
            faction: "neutral",
            health: 300,
        },
        {
            asset_id: "gate_1",
            asset_type: "security_gate",
            name: "Base Security Blast Gate",
            x: -420,
            y: 0,
            z: -800,
            yaw_deg: 90,
            faction: "enemy",
            health: 250,
        },
        {
            asset_id: "pole_1",
            asset_type: "powerline_pole",
            name: "High-Voltage Power Pole",
            x: -380,
            y: 0,
            z: -750,
            yaw_deg: 0,
            faction: "neutral",
            health: 50,
        },
        {
            asset_id: "ramp_1",
            asset_type: "ramp",
            name: "Vehicle Access Ramp",
            x: -600,
            y: 0,
            z: -730,
            yaw_deg: 130,
            faction: "neutral",
            health: 200,
        },
        // In-Game BattleMechs (Patrol & Defense)
        {
            asset_id: "mech_guard",
            asset_type: "mech_madcat",
            name: "Smoke Jaguar Timber Wolf",
            x: -400,
            y: 0,
            z: -640,
            yaw_deg: 195,
            faction: "enemy",
            health: 350,
            is_objective: true,
        },
        {
            asset_id: "mech_patrol",
            asset_type: "mech_bushwacker",
            name: "Recon Bushwacker BSW-X1",
            x: -540,
            y: 0,
            z: -660,
            yaw_deg: 60,
            faction: "enemy",
            health: 220,
        },
        // Nav Points
        {
            asset_id: "nav_alpha",
            asset_type: "nav",
            name: "Nav Point Alpha (Drop Zone)",
            x: -650,
            y: 0,
            z: -700,
            yaw_deg: 0,
            faction: "neutral",
            health: 100,
        },
        {
            asset_id: "nav_beta",
            asset_type: "nav",
            name: "Nav Point Beta (Outpost Gate)",
            x: -420,
            y: 0,
            z: -800,
            yaw_deg: 0,
            faction: "neutral",
            health: 100,
        },
        // Mission Triggers & Volumes
        {
            asset_id: "trig_evac_zone",
            asset_type: "trig_evac",
            name: "Dust-Off Extraction Zone",
            x: -350,
            y: 0,
            z: -900,
            yaw_deg: 0,
            faction: "player",
            health: 100,
            trigger_radius: 50.0,
            trigger_action: "evac_complete",
            trigger_message: "HQ: Dropship touchdown confirmed! Mission accomplished.",
        },
        {
            asset_id: "trig_ridge_ambush",
            asset_type: "trig_ambush",
            name: "Ridge Ambush Sensor Perimeter",
            x: -480,
            y: 0,
            z: -720,
            yaw_deg: 0,
            faction: "enemy",
            health: 100,
            trigger_radius: 65.0,
            trigger_action: "spawn_ambush",
            trigger_message: "WARNING: Clan reinforcements detected descending from ridge!",
        },
    ];

    // Update form inputs
    document.getElementById("project-title").value = state.project.pack_title;
    document.getElementById("project-id").value = state.project.pack_id;
    document.getElementById("biome-select").value = state.project.base_operation;

    buildTerrain().then(() => {
        setEnvPreset("sunset");
        syncSceneAssets();
        updateInspector();
        playBeep(880, "sine", 0.12);
    });
}

/**
 * Send a snapshot of requested edits to the local builder; show its result.
 * A successful response means output was written, not that gameplay loaded or
 * that every preview property was applied. The server validates pack paths.
 */
async function exportMapPack() {
    const btn = document.getElementById("btn-export");
    btn.innerText = "COMPILING PACK...";
    btn.disabled = true;

    try {
        const res = await fetch("/api/export-pack", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(state.project),
        });

        const data = await res.json();
        if (data.status === "ok") {
            playBeep(980, "sine", 0.15);
            showExportSuccessModal(data);
        } else {
            alert("Export failed: " + (data.message || "Unknown error"));
        }
    } catch (err) {
        alert("Export connection error: " + err);
    } finally {
        btn.innerText = "⚡ EXPORT MAP PACK";
        btn.disabled = false;
    }
}

// Show Export Success Modal
function showExportSuccessModal(data) {
    const modal = document.getElementById("export-modal");
    const details = document.getElementById("modal-export-details");

    details.innerHTML = `
    <div style="font-family: var(--font-mono); font-size: 12px; background: rgba(0,0,0,0.4); padding: 12px; border-radius: 4px; border: 1px solid var(--border-color); margin-top: 10px;">
      <div><span style="color:var(--text-muted)">Pack ID:</span> <b style="color:var(--accent-cyan)">${data.pack_id}</b></div>
      <div><span style="color:var(--text-muted)">Location:</span> <b>${data.pack_folder}</b></div>
      <div><span style="color:var(--text-muted)">Entities Placed:</span> <b>${data.total_placed_assets}</b></div>
      <div><span style="color:var(--text-muted)">Launcher:</span> <span style="color:var(--accent-green)">${data.launcher_script}</span></div>
    </div>
  `;

    modal.style.display = "flex";
}

/**
 * Ask the server to start the existing exported pack's launcher.
 * This does not export unsaved preview changes or wait for native-game success.
 */
async function launchGameEngine() {
    const btn = document.getElementById("btn-launch-game");
    btn.innerText = "LAUNCHING...";
    btn.disabled = true;

    try {
        const res = await fetch("/api/launch-map", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pack_id: state.project.pack_id }),
        });
        const data = await res.json();
        if (data.status === "ok") {
            playBeep(1200, "sine", 0.2);
        } else {
            alert("Launch error: " + data.message);
        }
    } catch (e) {
        alert("Launch failed: " + e);
    } finally {
        btn.innerText = "▶️ LAUNCH NATIVE ENGINE";
        btn.disabled = false;
    }
}

// Keyboard shortcuts
function onKeyDown(e) {
    if (
        e.target.tagName === "INPUT" ||
        e.target.tagName === "SELECT" ||
        e.target.tagName === "TEXTAREA"
    )
        return;

    if (e.key === "Escape") {
        clearActiveTool();
        state.selectedAssetId = null;
        syncSceneAssets();
        updateInspector();
    } else if (e.key === "Delete" || e.key === "Backspace") {
        if (state.selectedAssetId) {
            document.getElementById("btn-insp-delete").click();
        }
    } else if (e.key === "t" || e.key === "T") {
        setViewMode("topdown");
    } else if (e.key === "o" || e.key === "O") {
        setViewMode("orbit");
    } else if (e.key === "i" || e.key === "I") {
        setViewMode("iso");
    }
}

// Window resize
function onWindowResize() {
    const container = document.getElementById("viewport");
    camera.aspect = container.clientWidth / container.clientHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(container.clientWidth, container.clientHeight);
}

// Animation loop
function animate() {
    requestAnimationFrame(animate);
    orbitControls.update();

    // Subtle water ripple
    if (waterMesh) {
        waterMesh.material.opacity = 0.65 + Math.sin(Date.now() * 0.0015) * 0.05;
    }

    renderer.render(scene, camera);
}

// Objectives Modal Logic
function openObjectivesModal() {
    document.getElementById("briefing-textarea").value =
        state.project.objectives.briefing_text || "";
    document.getElementById("audio-track-select").value =
        state.project.objectives.audio_track || "action_theme_1";
    renderObjectivesLists();
    document.getElementById("objectives-modal").style.display = "flex";
}

function renderObjectivesLists() {
    const priBox = document.getElementById("primary-objectives-list");
    priBox.innerHTML = "";
    (state.project.objectives.primary || []).forEach((obj, idx) => {
        const row = document.createElement("div");
        row.className = "objective-item-row";
        row.innerHTML = `
      <span style="color:var(--accent-cyan); font-weight:700;">${idx + 1}.</span>
      <input type="text" value="${obj.desc}" oninput="state.project.objectives.primary[${idx}].desc = this.value;">
      <button class="btn-tiny-del" onclick="removeObjective('primary', ${idx})">&times;</button>
    `;
        priBox.appendChild(row);
    });

    const secBox = document.getElementById("secondary-objectives-list");
    secBox.innerHTML = "";
    (state.project.objectives.secondary || []).forEach((obj, idx) => {
        const row = document.createElement("div");
        row.className = "objective-item-row";
        row.innerHTML = `
      <span style="color:var(--accent-amber); font-weight:700;">${idx + 1}.</span>
      <input type="text" value="${obj.desc}" oninput="state.project.objectives.secondary[${idx}].desc = this.value;">
      <button class="btn-tiny-del" onclick="removeObjective('secondary', ${idx})">&times;</button>
    `;
        secBox.appendChild(row);
    });
}

function addObjective(type) {
    if (!state.project.objectives[type]) state.project.objectives[type] = [];
    state.project.objectives[type].push({
        id: `obj_${type}_${Date.now()}`,
        desc: type === "primary" ? "New Tactical Goal" : "Optional Secondary Goal",
        completed: false,
    });
    renderObjectivesLists();
}

function removeObjective(type, idx) {
    state.project.objectives[type].splice(idx, 1);
    renderObjectivesLists();
}

// MechLab Modal Logic
const CHASSIS_DATA = {
    mech_madcat: { name: "Mad Cat / Timber Wolf", tons: 75.0 },
    mech_bushwacker: { name: "Bushwacker BSW-X1", tons: 55.0 },
    mech_thor: { name: "Thor / Summoner", tons: 70.0 },
    mech_shadowcat: { name: "Shadow Cat", tons: 45.0 },
    mech_vulture: { name: "Vulture / Mad Dog", tons: 60.0 },
    mech_daishi: { name: "Daishi / Dire Wolf", tons: 100.0 },
};

function openMechLabModal() {
    const dc = state.project.drop_config;
    document.getElementById("mechlab-chassis").value = dc.player_mech || "mech_madcat";
    document.getElementById("mechlab-drop-type").value = dc.drop_type || "orbital_drop_pod";
    document.getElementById("wpn-left-arm").value = dc.weapons?.left_arm || "ER PPC";
    document.getElementById("wpn-center-torso").value =
        dc.weapons?.center_torso || "Medium Pulse Laser";
    document.getElementById("wpn-right-arm").value = dc.weapons?.right_arm || "ER PPC";
    document.getElementById("wpn-left-torso").value = dc.weapons?.left_torso || "Clan LRM-20";
    document.getElementById("wpn-right-torso").value = dc.weapons?.right_torso || "Clan LRM-20";
    document.getElementById("mechlab-armor").value = dc.armor_tons || 14.0;
    document.getElementById("mechlab-armor-val").innerText = `${dc.armor_tons || 14.0}T`;
    document.getElementById("mechlab-heatsinks").value = dc.heatsinks || 16;
    document.getElementById("mechlab-jumpjets").value = dc.jump_jets || 0;
    updateMechLabTonnage();
    renderLancemates();
    document.getElementById("mechlab-modal").style.display = "flex";
}

function updateMechLabTonnage() {
    const chassis = document.getElementById("mechlab-chassis").value;
    const maxTons = CHASSIS_DATA[chassis]?.tons || 75.0;
    state.project.drop_config.tonnage = maxTons;
    const badge = document.getElementById("mechlab-tonnage-badge");
    if (badge) {
        badge.innerText = `${maxTons.toFixed(1)} / ${maxTons.toFixed(1)} TONS`;
    }
}

function renderLancemates() {
    const box = document.getElementById("lancemate-list");
    if (!box) return;
    box.innerHTML = "";
    (state.project.drop_config.lancemates || []).forEach((m, idx) => {
        const row = document.createElement("div");
        row.className = "lancemate-item-row";
        row.innerHTML = `
      <input type="text" value="${m.name}" style="width:130px;" oninput="state.project.drop_config.lancemates[${idx}].name = this.value;">
      <select class="select-input" style="width:140px; font-size:11px;" onchange="state.project.drop_config.lancemates[${idx}].mech = this.value;">
        <option value="mech_bushwacker" ${m.mech === "mech_bushwacker" ? "selected" : ""}>Bushwacker (55T)</option>
        <option value="mech_shadowcat" ${m.mech === "mech_shadowcat" ? "selected" : ""}>Shadow Cat (45T)</option>
        <option value="mech_thor" ${m.mech === "mech_thor" ? "selected" : ""}>Thor (70T)</option>
        <option value="mech_vulture" ${m.mech === "mech_vulture" ? "selected" : ""}>Vulture (60T)</option>
      </select>
      <select class="select-input" style="width:100px; font-size:11px;" onchange="state.project.drop_config.lancemates[${idx}].orders = this.value;">
        <option value="escort" ${m.orders === "escort" ? "selected" : ""}>Escort</option>
        <option value="free_fire" ${m.orders === "free_fire" ? "selected" : ""}>Free Fire</option>
        <option value="defend" ${m.orders === "defend" ? "selected" : ""}>Defend Base</option>
      </select>
      <button class="btn-tiny-del" onclick="removeLancemate(${idx})">&times;</button>
    `;
        box.appendChild(row);
    });
}

function addLancemate() {
    if (!state.project.drop_config.lancemates) state.project.drop_config.lancemates = [];
    state.project.drop_config.lancemates.push({
        name: "Lt. Alan Mattila",
        mech: "mech_bushwacker",
        orders: "escort",
    });
    renderLancemates();
}

function removeLancemate(idx) {
    state.project.drop_config.lancemates.splice(idx, 1);
    renderLancemates();
}

// Initialization deliberately starts optional asset loading without awaiting it.
// The demo and animation loop are available while that local request completes.
window.addEventListener("DOMContentLoaded", () => {
    initViewport();
    bindInspectorEvents();

    // UI Event Bindings
    document.getElementById("project-title").addEventListener("input", (e) => {
        state.project.pack_title = e.target.value;
    });

    document.getElementById("project-id").addEventListener("input", (e) => {
        state.project.pack_id = e.target.value.toLowerCase().replace(/[^a-z0-9_]/g, "_");
    });

    document.getElementById("biome-select").addEventListener("change", (e) => {
        state.project.base_operation = e.target.value;
        state.project.terrain.biome = e.target.value;
        buildTerrain();
    });

    document.querySelectorAll(".asset-card").forEach((card) => {
        card.addEventListener("click", () => selectTool(card.dataset.type));
    });

    document.getElementById("btn-export").addEventListener("click", exportMapPack);
    document.getElementById("btn-load-demo").addEventListener("click", loadDemoMap);
    document.getElementById("btn-launch-game").addEventListener("click", launchGameEngine);
    document.getElementById("btn-modal-close").addEventListener("click", () => {
        document.getElementById("export-modal").style.display = "none";
    });

    // Objectives and MechLab Event Bindings
    document.getElementById("btn-objectives").addEventListener("click", openObjectivesModal);
    document.getElementById("btn-close-objectives").addEventListener("click", () => {
        state.project.objectives.briefing_text = document.getElementById("briefing-textarea").value;
        state.project.objectives.audio_track = document.getElementById("audio-track-select").value;
        document.getElementById("objectives-modal").style.display = "none";
    });
    document
        .getElementById("btn-add-primary-obj")
        .addEventListener("click", () => addObjective("primary"));
    document
        .getElementById("btn-add-secondary-obj")
        .addEventListener("click", () => addObjective("secondary"));

    document.getElementById("btn-mechlab").addEventListener("click", openMechLabModal);
    document.getElementById("btn-close-mechlab").addEventListener("click", () => {
        state.project.drop_config.player_mech = document.getElementById("mechlab-chassis").value;
        state.project.drop_config.drop_type = document.getElementById("mechlab-drop-type").value;
        state.project.drop_config.weapons = {
            left_arm: document.getElementById("wpn-left-arm").value,
            center_torso: document.getElementById("wpn-center-torso").value,
            right_arm: document.getElementById("wpn-right-arm").value,
            left_torso: document.getElementById("wpn-left-torso").value,
            right_torso: document.getElementById("wpn-right-torso").value,
        };
        state.project.drop_config.armor_tons = parseFloat(
            document.getElementById("mechlab-armor").value,
        );
        state.project.drop_config.heatsinks = parseInt(
            document.getElementById("mechlab-heatsinks").value,
        );
        state.project.drop_config.jump_jets = parseInt(
            document.getElementById("mechlab-jumpjets").value,
        );
        document.getElementById("mechlab-modal").style.display = "none";
    });
    document.getElementById("mechlab-chassis").addEventListener("change", updateMechLabTonnage);
    document.getElementById("mechlab-armor").addEventListener("input", (e) => {
        document.getElementById("mechlab-armor-val").innerText = `${e.target.value}T`;
    });
    document.getElementById("btn-add-lancemate").addEventListener("click", addLancemate);

    // Load authentic in-game 3D models and initial demo
    loadGameAssets();
    loadDemoMap();
});
