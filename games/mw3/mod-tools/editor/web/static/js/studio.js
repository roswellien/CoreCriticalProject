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
            time_of_day: 18.0,
            azimuth: 235.0,
            elevation: 28.0,
            strength: 0.9,
            sun_strength: 0.9,
            ambient: 0.22,
            ambient_strength: 0.22,
            sun_color: [1.0, 0.75, 0.5],
            ambient_color: [0.38, 0.32, 0.45],
            sky_tint: [0.38, 0.28, 0.48],
            fog_distance: 1200,
            shadows: true,
            rain_intensity: 0.0,
            wet_reflection: 0.0,
            has_lightning: false,
            dust_intensity: 0.0,
            smog_intensity: 0.0,
            heat_shimmer: 0.0,
            volcanic_ash: 0.0,
            lava_glow: 0.0,
            is_interior: false,
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
    sculpt: {
        enabled: false,
        mode: "raise",
        radius: 45.0,
        strength: 1.2,
        falloff: "smooth",
        isMouseDown: false,
        targetHeight: 0,
        originalPositions: null,
    },
    campaign: {
        campaign_id: "operation_damocles",
        campaign_title: "Operation Damocles",
        author: "MW3 Modder",
        version: "1.0.0",
        description: "Deep strike behind Clan Smoke Jaguar lines on Tranquil to disrupt regional communications and neutralize command garrisons.",
        faction: "Inner Sphere",
        theater: "Tranquil Coastal Basin",
        continuity_rules: {
            salvage_enabled: true,
            starting_salvage_points: 1000,
            repair_points: 500,
            shared_pilots: true,
        },
        missions: [
            {
                mission_id: "m01_recon",
                pack_id: "iron_ridge_outpost",
                title: "Mission 1: Recon In Force",
                theater: "Tranquil Coastal Basin",
                briefing_text: "Infiltrate the perimeter and destroy the Clan sensor arrays. Maintain visual stealth.",
                audio_track: "action_theme_1",
                next_mission_id: "m02_assault",
                branch_conditions: {
                    on_secondary_complete: "m02_assault",
                    on_secondary_failed: "m02_flank",
                },
            },
            {
                mission_id: "m02_assault",
                pack_id: "iron_ridge_outpost",
                title: "Mission 2: Fortress Breach",
                theater: "Tranquil Coastal Basin",
                briefing_text: "Launch direct assault against the fortified command citadel.",
                audio_track: "action_theme_2",
                next_mission_id: null,
                branch_conditions: {},
            },
        ],
    },
};

// Renderer-owned display objects, shared by the event handlers and animation loop.
// assetObjectMap keys are project asset_id values; mesh children are not project IDs.
let scene, camera, perspCamera, orthoCamera, renderer, orbitControls, transformControls;
let terrainMesh, waterMesh, reconMapMesh, sunLight, ambientLight, ghostPreview, brushCursorRing;
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
    flat: {
        name: "Flat Plain / Blank Canvas",
        center: [0, 0],
        waterLevel: -100.0,
        hasWater: false,
        waterColor: 0x145266,
        waterSize: [3000, 3000],
        waterCenter: [0, 0],
        palette: { sand: 0x5a6350, rock: 0x475240, peak: 0x3d4737, shoreY: -50.0 },
        preset: "noon",
        terrainTexture: "static/assets/textures/terrains/c1_txgter_1.png",
        reconMap: null,
    },
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
        terrainTexture: "static/assets/textures/terrains/c1_txgter_1.png",
        reconMap: {
            texture: "static/assets/maps/c1m1.png",
            mpp: 3.476,
            offset: [-1114.434, 0.0, -659.279],
            widthPx: 640,
            heightPx: 480,
        },
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
        terrainTexture: "static/assets/textures/terrains/c2_ggter_1.png",
        reconMap: {
            texture: "static/assets/maps/c2m1.png",
            mpp: 4.273,
            offset: [1930.0, 0.0, -41.6],
            widthPx: 640,
            heightPx: 480,
        },
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
        terrainTexture: "static/assets/textures/terrains/c3_gter_1.png",
        reconMap: {
            texture: "static/assets/maps/c3m1.png",
            mpp: -5.175,
            offset: [-1255.0, 0.0, -224.0],
            widthPx: 640,
            heightPx: 480,
        },
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
        terrainTexture: "static/assets/textures/terrains/c4_gter_1.png",
        reconMap: {
            texture: "static/assets/maps/c4m1.png",
            mpp: -7.100,
            offset: [-2365.0, 0.0, 1629.0],
            widthPx: 640,
            heightPx: 480,
        },
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
        terrainTexture: "static/assets/textures/terrains/t1_ggter1.png",
        reconMap: {
            texture: "static/assets/maps/t1m1.png",
            mpp: 5.144,
            offset: [3382.0, 0.0, -2.0],
            widthPx: 640,
            heightPx: 480,
        },
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

    // Dual Cameras: 3D Perspective and 2D Orthographic
    const aspect = width / height;
    perspCamera = new THREE.PerspectiveCamera(45, aspect, 2.0, 10000);
    perspCamera.position.set(-600, 450, 750);

    const frustumSize = 1800;
    orthoCamera = new THREE.OrthographicCamera(
        (frustumSize * aspect) / -2,
        (frustumSize * aspect) / 2,
        frustumSize / 2,
        frustumSize / -2,
        1.0,
        10000
    );
    orthoCamera.position.set(-1408, 1600, 0);
    orthoCamera.lookAt(-1408, 0, 0);

    camera = perspCamera;

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

    // Sculpt Cursor Ring
    const ringGeom = new THREE.RingGeometry(43.5, 45.0, 32);
    ringGeom.rotateX(-Math.PI / 2);
    const ringMat = new THREE.MeshBasicMaterial({
        color: 0x00f0ff,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.8,
    });
    brushCursorRing = new THREE.Mesh(ringGeom, ringMat);
    brushCursorRing.visible = false;
    scene.add(brushCursorRing);

    // Event Listeners
    window.addEventListener("resize", onWindowResize);
    container.addEventListener("mousedown", onMouseDown);
    container.addEventListener("mousemove", onMouseMove);
    container.addEventListener("mouseup", onMouseUp);
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
            const res = await fetch(`static/assets/terrains/${opCode}.json`);
            if (res.ok) {
                tData = await res.json();
                terrainCache[opCode] = tData;
            }
        } catch (e) {
            console.warn("Could not load terrain JSON for", opCode, e);
        }
    }

    if (opCode === "flat") {
        // Build authentic flat level plain (3000m x 3000m, 80x80 segments)
        const size = 3000;
        const segments = 80;
        const geom = new THREE.PlaneGeometry(size, size, segments, segments);
        geom.rotateX(-Math.PI / 2);

        const count = geom.attributes.position.count;
        const colors = new Float32Array(count * 3);
        const uvs = geom.attributes.uv.array;
        for (let i = 0; i < uvs.length; i++) {
            uvs[i] *= 30.0;
        }
        geom.attributes.uv.needsUpdate = true;

        const baseCol = new THREE.Color(0x4f5e48);
        for (let i = 0; i < count; i++) {
            colors[i * 3] = baseCol.r;
            colors[i * 3 + 1] = baseCol.g;
            colors[i * 3 + 2] = baseCol.b;
        }
        geom.setAttribute("color", new THREE.BufferAttribute(colors, 3));
        geom.computeVertexNormals();

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
        state.sculpt.originalPositions = new Float32Array(geom.attributes.position.array);

        if (state.project.terrain && state.project.terrain.height_modifications) {
            const hmods = state.project.terrain.height_modifications;
            const pos = geom.attributes.position;
            let appliedCount = 0;
            for (let i = 0; i < pos.count; i++) {
                const vx = Math.round(pos.getX(i) * 10) / 10;
                const vz = Math.round(pos.getZ(i) * 10) / 10;
                const k = `${vx},${vz}`;
                if (hmods[k] !== undefined) {
                    pos.setY(i, hmods[k]);
                    appliedCount++;
                }
            }
            if (appliedCount > 0) {
                pos.needsUpdate = true;
                geom.computeVertexNormals();
            }
        }
        console.log(`[Map Studio] Loaded flat blank canvas terrain (${count} vertices)`);
    } else if (tData) {
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
        state.sculpt.originalPositions = new Float32Array(geom.attributes.position.array);

        // Apply saved terrain sculpt height modifications if present
        if (state.project.terrain && state.project.terrain.height_modifications) {
            const hmods = state.project.terrain.height_modifications;
            const pos = geom.attributes.position;
            let appliedCount = 0;
            for (let i = 0; i < pos.count; i++) {
                const vx = Math.round(pos.getX(i) * 10) / 10;
                const vz = Math.round(pos.getZ(i) * 10) / 10;
                const k = `${vx},${vz}`;
                if (hmods[k] !== undefined) {
                    pos.setY(i, hmods[k]);
                    appliedCount++;
                }
            }
            if (appliedCount > 0) {
                pos.needsUpdate = true;
                geom.computeVertexNormals();
                console.log(`[Map Studio] Applied ${appliedCount} saved terrain height modifications`);
            }
        }

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

    // 2b. Calibrated Authentic 2D Satellite Recon Map Overlay
    if (reconMapMesh) {
        scene.remove(reconMapMesh);
        if (reconMapMesh.geometry) reconMapMesh.geometry.dispose();
        reconMapMesh = null;
    }
    if (meta.reconMap) {
        const rm = meta.reconMap;
        const worldW = Math.abs(rm.widthPx * rm.mpp);
        const worldH = Math.abs(rm.heightPx * rm.mpp);
        const rmGeom = new THREE.PlaneGeometry(worldW, worldH);
        rmGeom.rotateX(-Math.PI / 2);
        const rmTex = new THREE.TextureLoader().load(rm.texture);
        const rmMat = new THREE.MeshBasicMaterial({
            map: rmTex,
            transparent: true,
            opacity: 0.88,
            depthWrite: false,
        });
        reconMapMesh = new THREE.Mesh(rmGeom, rmMat);
        reconMapMesh.position.set(rm.offset[0], -1.2, rm.offset[2]);
        if (rm.mpp < 0) {
            reconMapMesh.scale.set(-1, 1, -1);
        }
        reconMapMesh.name = "reconMapOverlay";
        reconMapMesh.visible = (state.viewMode === "topdown" || !!state.showReconOverlay);
        scene.add(reconMapMesh);
        console.log(
            `[Map Studio] Calibrated 2D satellite recon map loaded: ${rm.texture} (${worldW.toFixed(1)}m x ${worldH.toFixed(1)}m) at [${rm.offset[0]}, ${rm.offset[2]}]`,
        );
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

// Color Conversion Helpers
function rgbToHex(rgb) {
    if (!Array.isArray(rgb) || rgb.length < 3) return "#ffffff";
    const r = Math.round(Math.min(1, Math.max(0, rgb[0])) * 255);
    const g = Math.round(Math.min(1, Math.max(0, rgb[1])) * 255);
    const b = Math.round(Math.min(1, Math.max(0, rgb[2])) * 255);
    return `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
}

function hexToRgb(hex) {
    const clean = hex.replace("#", "");
    const num = parseInt(clean.length === 3 ? clean.split("").map((c) => c + c).join("") : clean, 16);
    return [((num >> 16) & 255) / 255.0, ((num >> 8) & 255) / 255.0, (num & 255) / 255.0];
}

// Update Lighting and Atmospheric Effects from State
function updateLighting() {
    const lcfg = state.project.lighting;
    const isInterior = Boolean(lcfg.is_interior);

    if (isInterior) {
        sunLight.intensity = 0.0;
        ambientLight.intensity = Math.max(0.05, (lcfg.ambient_strength || lcfg.ambient || 0.22) * 0.6);
        ambientLight.color.setRGB(0.3, 0.32, 0.35);
        scene.background = new THREE.Color(0x050608);
        scene.fog.color = new THREE.Color(0x050608);
        scene.fog.density = 1.0 / 600.0;
        return;
    }

    const azRad = THREE.MathUtils.degToRad(lcfg.azimuth);
    const elRad = THREE.MathUtils.degToRad(lcfg.elevation);

    const dist = 2200;
    const sx = Math.sin(azRad) * Math.cos(elRad) * dist;
    const sy = Math.sin(elRad) * dist;
    const sz = Math.cos(azRad) * Math.cos(elRad) * dist;

    sunLight.position.set(sx, sy, sz);
    const sunCol = lcfg.sun_color || [1.0, 0.85, 0.7];
    sunLight.color.setRGB(sunCol[0], sunCol[1], sunCol[2]);
    sunLight.intensity = (lcfg.sun_strength ?? lcfg.strength ?? 0.9) * 1.5;
    sunLight.castShadow = Boolean(lcfg.shadows !== false);

    const ambCol = lcfg.ambient_color || [0.4, 0.4, 0.45];
    ambientLight.color.setRGB(ambCol[0], ambCol[1], ambCol[2]);
    ambientLight.intensity = lcfg.ambient_strength ?? lcfg.ambient ?? 0.22;

    const skyCol = new THREE.Color().fromArray(lcfg.sky_tint || [0.38, 0.28, 0.48]);
    scene.background = skyCol;
    scene.fog.color = skyCol;
    const fogDist = lcfg.fog_distance || 1200;
    scene.fog.density = 1.0 / (fogDist * 2.2);

    // Dynamic Weather Ground Wetness Response
    if (terrainMesh && terrainMesh.material) {
        const wetness = Number(lcfg.wet_reflection || lcfg.rain_intensity || 0.0);
        terrainMesh.material.roughness = Math.max(0.15, 0.85 - wetness * 0.65);
        terrainMesh.material.metalness = Math.min(0.4, wetness * 0.35);
        terrainMesh.material.needsUpdate = true;
    }
}

function openAtmosphereModal() {
    syncAtmosphereUIFromState();
    document.getElementById("atmosphere-modal").style.display = "flex";
}

function closeAtmosphereModal() {
    document.getElementById("atmosphere-modal").style.display = "none";
}

function syncAtmosphereUIFromState() {
    const lcfg = state.project.lighting;
    const todSlider = document.getElementById("atmo-tod-slider");
    if (todSlider) todSlider.value = lcfg.time_of_day || 18.0;

    const hr = Math.floor(lcfg.time_of_day || 18.0);
    const mn = Math.floor(((lcfg.time_of_day || 18.0) - hr) * 60);
    const todDisp = document.getElementById("atmo-tod-display");
    if (todDisp) {
        todDisp.textContent = `${String(hr).padStart(2, "0")}:${String(mn).padStart(2, "0")} (${(lcfg.preset_name || "Custom").toUpperCase()})`;
    }

    const azSlider = document.getElementById("atmo-azimuth");
    if (azSlider) {
        azSlider.value = Math.round(lcfg.azimuth);
        const azVal = document.getElementById("atmo-azimuth-val");
        if (azVal) azVal.textContent = `${Math.round(lcfg.azimuth)}°`;
    }

    const elSlider = document.getElementById("atmo-elevation");
    if (elSlider) {
        elSlider.value = Math.round(lcfg.elevation);
        const elVal = document.getElementById("atmo-elevation-val");
        if (elVal) elVal.textContent = `${Math.round(lcfg.elevation)}°`;
    }

    const sunCol = document.getElementById("atmo-sun-color");
    if (sunCol) sunCol.value = rgbToHex(lcfg.sun_color || [1.0, 0.75, 0.5]);

    const sunStr = document.getElementById("atmo-sun-strength");
    if (sunStr) sunStr.value = lcfg.sun_strength ?? lcfg.strength ?? 0.9;

    const ambCol = document.getElementById("atmo-ambient-color");
    if (ambCol) ambCol.value = rgbToHex(lcfg.ambient_color || [0.38, 0.32, 0.45]);

    const ambStr = document.getElementById("atmo-ambient-strength");
    if (ambStr) ambStr.value = lcfg.ambient_strength ?? lcfg.ambient ?? 0.22;

    const skyCol = document.getElementById("atmo-sky-tint");
    if (skyCol) skyCol.value = rgbToHex(lcfg.sky_tint || [0.38, 0.28, 0.48]);

    const fogDist = document.getElementById("atmo-fog-dist");
    if (fogDist) fogDist.value = lcfg.fog_distance || 1200;

    const rainSlider = document.getElementById("weather-rain");
    if (rainSlider) {
        rainSlider.value = lcfg.rain_intensity || 0;
        const rainVal = document.getElementById("weather-rain-val");
        if (rainVal) rainVal.textContent = `${Math.round((lcfg.rain_intensity || 0) * 100)}%`;
    }

    const wetSlider = document.getElementById("weather-wetness");
    if (wetSlider) {
        wetSlider.value = lcfg.wet_reflection || 0;
        const wetVal = document.getElementById("weather-wetness-val");
        if (wetVal) wetVal.textContent = `${Math.round((lcfg.wet_reflection || 0) * 100)}%`;
    }

    const lightCheck = document.getElementById("weather-lightning-check");
    if (lightCheck) lightCheck.checked = Boolean(lcfg.has_lightning);

    const dustSlider = document.getElementById("weather-dust");
    if (dustSlider) {
        dustSlider.value = lcfg.dust_intensity || 0;
        const dustVal = document.getElementById("weather-dust-val");
        if (dustVal) dustVal.textContent = `${Math.round((lcfg.dust_intensity || 0) * 100)}%`;
    }

    const smogSlider = document.getElementById("weather-smog");
    if (smogSlider) {
        smogSlider.value = lcfg.smog_intensity || 0;
        const smogVal = document.getElementById("weather-smog-val");
        if (smogVal) smogVal.textContent = `${Math.round((lcfg.smog_intensity || 0) * 100)}%`;
    }

    const shimSlider = document.getElementById("weather-shimmer");
    if (shimSlider) {
        shimSlider.value = lcfg.heat_shimmer || 0;
        const shimVal = document.getElementById("weather-shimmer-val");
        if (shimVal) shimVal.textContent = `${Math.round((lcfg.heat_shimmer || 0) * 100)}%`;
    }

    const volcSlider = document.getElementById("weather-volcano");
    if (volcSlider) {
        volcSlider.value = lcfg.volcanic_ash || 0;
        const volcVal = document.getElementById("weather-volcano-val");
        if (volcVal) volcVal.textContent = `${Math.round((lcfg.volcanic_ash || 0) * 100)}%`;
    }

    const intCheck = document.getElementById("weather-interior-check");
    if (intCheck) intCheck.checked = Boolean(lcfg.is_interior);

    const shadowCheck = document.getElementById("atmo-shadows-check");
    if (shadowCheck) shadowCheck.checked = Boolean(lcfg.shadows !== false);
}

function onAtmosphereDirectInput() {
    const lcfg = state.project.lighting;
    lcfg.azimuth = parseFloat(document.getElementById("atmo-azimuth").value);
    lcfg.elevation = parseFloat(document.getElementById("atmo-elevation").value);
    lcfg.sun_color = hexToRgb(document.getElementById("atmo-sun-color").value);
    lcfg.sun_strength = parseFloat(document.getElementById("atmo-sun-strength").value);
    lcfg.strength = lcfg.sun_strength;

    lcfg.ambient_color = hexToRgb(document.getElementById("atmo-ambient-color").value);
    lcfg.ambient_strength = parseFloat(document.getElementById("atmo-ambient-strength").value);
    lcfg.ambient = lcfg.ambient_strength;

    lcfg.sky_tint = hexToRgb(document.getElementById("atmo-sky-tint").value);
    lcfg.fog_distance = parseFloat(document.getElementById("atmo-fog-dist").value);

    lcfg.rain_intensity = parseFloat(document.getElementById("weather-rain").value);
    lcfg.wet_reflection = parseFloat(document.getElementById("weather-wetness").value);
    lcfg.has_lightning = document.getElementById("weather-lightning-check").checked;
    lcfg.dust_intensity = parseFloat(document.getElementById("weather-dust").value);
    lcfg.smog_intensity = parseFloat(document.getElementById("weather-smog").value);
    lcfg.heat_shimmer = parseFloat(document.getElementById("weather-shimmer").value);
    lcfg.volcanic_ash = parseFloat(document.getElementById("weather-volcano").value);
    lcfg.lava_glow = lcfg.volcanic_ash;
    lcfg.is_interior = document.getElementById("weather-interior-check").checked;
    lcfg.shadows = document.getElementById("atmo-shadows-check").checked;

    document.getElementById("atmo-azimuth-val").textContent = `${Math.round(lcfg.azimuth)}°`;
    document.getElementById("atmo-elevation-val").textContent = `${Math.round(lcfg.elevation)}°`;
    document.getElementById("weather-rain-val").textContent = `${Math.round(lcfg.rain_intensity * 100)}%`;
    document.getElementById("weather-wetness-val").textContent = `${Math.round(lcfg.wet_reflection * 100)}%`;
    document.getElementById("weather-dust-val").textContent = `${Math.round(lcfg.dust_intensity * 100)}%`;
    document.getElementById("weather-smog-val").textContent = `${Math.round(lcfg.smog_intensity * 100)}%`;
    document.getElementById("weather-shimmer-val").textContent = `${Math.round(lcfg.heat_shimmer * 100)}%`;
    document.getElementById("weather-volcano-val").textContent = `${Math.round(lcfg.volcanic_ash * 100)}%`;

    updateLighting();
}

function onTimeOfDaySliderChange(hour) {
    const h = parseFloat(hour);
    state.project.lighting.time_of_day = h;

    const sunProgress = (h - 6.0) / 12.0;
    let el, az;
    if (sunProgress >= 0.0 && sunProgress <= 1.0) {
        el = Math.sin(sunProgress * Math.PI) * 75.0;
        az = 90.0 + sunProgress * 180.0;
    } else {
        const nightProgress = ((h - 18.0 + 24.0) % 24.0) / 12.0;
        el = Math.sin(nightProgress * Math.PI) * 35.0;
        az = (270.0 + nightProgress * 180.0) % 360.0;
    }
    state.project.lighting.elevation = Math.max(1.0, Math.round(el * 10) / 10);
    state.project.lighting.azimuth = Math.round(az * 10) / 10;

    let label = "Sunset";
    if (h >= 5.0 && h < 7.0) {
        label = "Dawn";
        state.project.lighting.preset_name = "dawn";
        state.project.lighting.sun_color = [1.0, 0.65, 0.4];
        state.project.lighting.sky_tint = [0.4, 0.3, 0.55];
        state.project.lighting.sun_strength = 0.6;
        state.project.lighting.ambient = 0.18;
    } else if (h >= 7.0 && h < 11.0) {
        label = "Morning";
        state.project.lighting.preset_name = "morning";
        state.project.lighting.sun_color = [1.0, 0.92, 0.8];
        state.project.lighting.sky_tint = [0.42, 0.62, 0.9];
        state.project.lighting.sun_strength = 0.95;
        state.project.lighting.ambient = 0.28;
    } else if (h >= 11.0 && h < 15.0) {
        label = "High Noon";
        state.project.lighting.preset_name = "noon";
        state.project.lighting.sun_color = [1.0, 1.0, 0.95];
        state.project.lighting.sky_tint = [0.45, 0.65, 0.95];
        state.project.lighting.sun_strength = 1.15;
        state.project.lighting.ambient = 0.35;
    } else if (h >= 15.0 && h < 17.5) {
        label = "Afternoon";
        state.project.lighting.preset_name = "afternoon";
        state.project.lighting.sun_color = [1.0, 0.9, 0.75];
        state.project.lighting.sky_tint = [0.4, 0.58, 0.88];
        state.project.lighting.sun_strength = 1.0;
        state.project.lighting.ambient = 0.3;
    } else if (h >= 17.5 && h < 19.5) {
        label = "Sunset";
        state.project.lighting.preset_name = "sunset";
        state.project.lighting.sun_color = [1.0, 0.75, 0.5];
        state.project.lighting.sky_tint = [0.38, 0.28, 0.48];
        state.project.lighting.sun_strength = 0.85;
        state.project.lighting.ambient = 0.22;
    } else if (h >= 19.5 && h < 21.5) {
        label = "Dusk";
        state.project.lighting.preset_name = "dusk";
        state.project.lighting.sun_color = [0.65, 0.35, 0.45];
        state.project.lighting.sky_tint = [0.18, 0.16, 0.3];
        state.project.lighting.sun_strength = 0.25;
        state.project.lighting.ambient = 0.12;
    } else {
        label = "Night";
        state.project.lighting.preset_name = "night";
        state.project.lighting.sun_color = [0.55, 0.65, 0.85];
        state.project.lighting.sky_tint = [0.08, 0.1, 0.18];
        state.project.lighting.sun_strength = 0.18;
        state.project.lighting.ambient = 0.08;
    }

    const hr = Math.floor(h);
    const mn = Math.floor((h - hr) * 60);
    const todDisp = document.getElementById("atmo-tod-display");
    if (todDisp) {
        todDisp.textContent = `${String(hr).padStart(2, "0")}:${String(mn).padStart(2, "0")} (${label})`;
    }

    syncAtmosphereUIFromState();
    updateLighting();
}

function applyTimeOfDayPreset(presetName) {
    const p = presetName.toLowerCase();
    if (p === "dawn") onTimeOfDaySliderChange(6.0);
    else if (p === "morning") onTimeOfDaySliderChange(9.0);
    else if (p === "noon") onTimeOfDaySliderChange(12.5);
    else if (p === "afternoon") onTimeOfDaySliderChange(15.5);
    else if (p === "sunset") onTimeOfDaySliderChange(18.2);
    else if (p === "dusk") onTimeOfDaySliderChange(20.0);
    else if (p === "night") onTimeOfDaySliderChange(23.5);
    else if (p === "stealth") onTimeOfDaySliderChange(1.0);
}

function applyWeatherPreset(type) {
    const lcfg = state.project.lighting;
    lcfg.is_interior = false;
    lcfg.rain_intensity = 0.0;
    lcfg.wet_reflection = 0.0;
    lcfg.has_lightning = false;
    lcfg.dust_intensity = 0.0;
    lcfg.smog_intensity = 0.0;
    lcfg.heat_shimmer = 0.0;
    lcfg.volcanic_ash = 0.0;
    lcfg.lava_glow = 0.0;

    if (type === "clear") {
        lcfg.preset_name = "clear";
    } else if (type === "rain") {
        lcfg.preset_name = "rain";
        lcfg.rain_intensity = 0.70;
        lcfg.wet_reflection = 0.85;
        lcfg.fog_distance = 900.0;
    } else if (type === "storm") {
        lcfg.preset_name = "storm";
        lcfg.rain_intensity = 0.95;
        lcfg.wet_reflection = 1.0;
        lcfg.has_lightning = true;
        lcfg.fog_distance = 650.0;
        lcfg.sky_tint = [0.22, 0.25, 0.35];
    } else if (type === "dust") {
        lcfg.preset_name = "dust";
        lcfg.dust_intensity = 0.85;
        lcfg.heat_shimmer = 0.50;
        lcfg.fog_distance = 450.0;
        lcfg.sky_tint = [0.55, 0.45, 0.30];
    } else if (type === "smog") {
        lcfg.preset_name = "smog";
        lcfg.smog_intensity = 0.80;
        lcfg.wet_reflection = 0.35;
        lcfg.fog_distance = 550.0;
        lcfg.sky_tint = [0.35, 0.38, 0.30];
    } else if (type === "heat") {
        lcfg.preset_name = "heat";
        lcfg.heat_shimmer = 0.85;
        lcfg.dust_intensity = 0.25;
        lcfg.sun_strength = 1.25;
    } else if (type === "volcanic") {
        lcfg.preset_name = "volcanic";
        lcfg.volcanic_ash = 0.80;
        lcfg.lava_glow = 0.90;
        lcfg.fog_distance = 600.0;
        lcfg.sky_tint = [0.25, 0.15, 0.15];
    } else if (type === "interior") {
        lcfg.preset_name = "interior";
        lcfg.is_interior = true;
        lcfg.sun_strength = 0.0;
        lcfg.ambient_strength = 0.15;
        lcfg.fog_distance = 300.0;
    }

    syncAtmosphereUIFromState();
    updateLighting();
}

function triggerLightningFlash() {
    playBeep(180, "sawtooth", 0.15);
    const origColor = sunLight.color.clone();
    const origIntensity = sunLight.intensity;
    const origAmbient = ambientLight.intensity;

    sunLight.color.setRGB(1.0, 1.0, 1.0);
    sunLight.intensity = 3.5;
    ambientLight.intensity = 1.8;
    scene.background = new THREE.Color(0xddeeff);

    setTimeout(() => {
        sunLight.intensity = 0.4;
        ambientLight.intensity = 0.25;
        setTimeout(() => {
            sunLight.color.copy(origColor);
            sunLight.intensity = origIntensity;
            ambientLight.intensity = origAmbient;
            scene.background = new THREE.Color().fromArray(state.project.lighting.sky_tint || [0.38, 0.28, 0.48]);
        }, 80);
    }, 60);
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
        const res = await fetch("static/assets/game_assets_3d.json");
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
    if (typeof renderSceneOutliner === "function") renderSceneOutliner();
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

        if (state.sculpt && state.sculpt.enabled && brushCursorRing) {
            brushCursorRing.position.set(pt.x, pt.y + 0.25, pt.z);
            brushCursorRing.visible = true;
            if (state.sculpt.isMouseDown) {
                applyTerrainSculpt(pt);
            }
        }

        if (state.activeTool) {
            ghostPreview.position.copy(pt);
            ghostPreview.visible = true;
        }
    } else {
        if (state.activeTool) ghostPreview.visible = false;
        if (brushCursorRing && (!state.sculpt || !state.sculpt.isMouseDown)) {
            brushCursorRing.visible = false;
        }
    }
}

function onMouseDown(event) {
    if (state.sculpt && state.sculpt.enabled && event.button === 0) {
        const pt = raycastTerrain(event);
        if (pt) {
            state.sculpt.isMouseDown = true;
            state.sculpt.targetHeight = pt.y;
            applyTerrainSculpt(pt);
            playBeep(620, "sine", 0.04);
        }
    }
}

function onMouseUp(event) {
    if (state.sculpt && state.sculpt.isMouseDown) {
        state.sculpt.isMouseDown = false;
    }
}

// Canvas Click Handler (Place or Select)
function onCanvasClick(event) {
    if (state.sculpt && state.sculpt.enabled) return;
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
        mech_annihilator: "Annihilator ANH-1A",
        mech_avatar: "Avatar AV1-O",
        mech_blackhawk: "Black Hawk / Nova",
        mech_cauldron: "Cauldron-Born / Ebon Jag",
        mech_champion: "Champion 1N",
        mech_dragonfly: "Dragonfly / Viper",
        mech_firefly: "Firefly FFL-4A",
        mech_orion: "Orion ON1-K",
        mech_strider: "Strider SR1-O",
        mech_sunder: "Sunder SD1-O",
        mech_supernova: "Supernova",
        mech_marauder: "Marauder MAD-3R",
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

    const hOffsetEl = document.getElementById("insp-height-offset");
    if (hOffsetEl) {
        hOffsetEl.value = Math.round(asset.height_offset || 0);
        document.getElementById("insp-height-offset-val").innerText = `${Math.round(asset.height_offset || 0)}m`;
    }

    const aiSec = document.getElementById("insp-ai-section");
    const isCombat = (asset.asset_type || "").startsWith("mech_") || (asset.asset_type || "").startsWith("turret_");
    if (aiSec) {
        aiSec.style.display = isCombat ? "block" : "none";
        if (isCombat) {
            document.getElementById("insp-ai-skill").value = asset.ai_skill || "regular";
            document.getElementById("insp-ai-stance").value = asset.ai_stance || "guard";
            document.getElementById("insp-ai-range").value = asset.ai_range || "medium";
            document.getElementById("insp-ai-retreat").value = asset.ai_retreat_health ?? 15;
            document.getElementById("insp-ai-retreat-val").innerText = `${asset.ai_retreat_health ?? 15}%`;
        }
    }

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
            const trigAudioEl = document.getElementById("insp-trigger-audio");
            if (trigAudioEl) trigAudioEl.value = asset.trigger_audio || "betty_alarm";
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

    const hOffsetInput = document.getElementById("insp-height-offset");
    if (hOffsetInput) {
        hOffsetInput.addEventListener("input", (e) => {
            const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
            if (a) {
                a.height_offset = parseFloat(e.target.value);
                document.getElementById("insp-height-offset-val").innerText = `${Math.round(a.height_offset)}m`;
                const groundY = getTerrainHeight(a.x, a.z);
                a.y = Math.round((groundY + a.height_offset) * 10) / 10;
                syncSceneAssets();
            }
        });
    }

    document.getElementById("insp-ai-skill")?.addEventListener("change", (e) => {
        const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
        if (a) a.ai_skill = e.target.value;
    });

    document.getElementById("insp-ai-stance")?.addEventListener("change", (e) => {
        const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
        if (a) a.ai_stance = e.target.value;
    });

    document.getElementById("insp-ai-range")?.addEventListener("change", (e) => {
        const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
        if (a) a.ai_range = e.target.value;
    });

    document.getElementById("insp-ai-retreat")?.addEventListener("input", (e) => {
        const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
        if (a) {
            a.ai_retreat_health = parseInt(e.target.value);
            document.getElementById("insp-ai-retreat-val").innerText = `${a.ai_retreat_health}%`;
        }
    });

    document.getElementById("insp-trigger-audio")?.addEventListener("change", (e) => {
        const a = state.project.assets.find((x) => x.asset_id === state.selectedAssetId);
        if (a) a.trigger_audio = e.target.value;
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

// Camera View Mode Presets (True 2D Orthographic Tactical vs 3D Perspective Studio)
function setViewMode(mode) {
    state.viewMode = mode;
    document.querySelectorAll(".hud-btn").forEach((btn) => btn.classList.remove("active"));
    const activeBtn = document.getElementById(`btn-view-${mode}`);
    if (activeBtn) activeBtn.classList.add("active");

    const opCode = state.project.base_operation || "c1";
    const meta = OP_ENV_METADATA[opCode] || OP_ENV_METADATA.c1;
    const cx = meta.center[0];
    const cz = meta.center[1];

    const modeToggleBtn = document.getElementById("btn-mode-toggle");

    if (mode === "topdown") {
        // True 2D Orthographic Tactical Map Mode
        camera = orthoCamera;
        orthoCamera.position.set(cx, 1800, cz);
        orthoCamera.lookAt(cx, 0, cz);

        orbitControls.object = orthoCamera;
        orbitControls.enableRotate = false; // Lock rotation in 2D mode
        orbitControls.screenSpacePanning = true;
        orbitControls.target.set(cx, 0, cz);
        transformControls.camera = orthoCamera;

        if (modeToggleBtn) modeToggleBtn.innerHTML = "Mode: 2D Tactical (Click for 3D)";
    } else if (mode === "iso") {
        // 3D Isometric View
        camera = perspCamera;
        orbitControls.object = perspCamera;
        orbitControls.enableRotate = true;
        orbitControls.maxPolarAngle = Math.PI / 2 - 0.02;
        perspCamera.position.set(cx - 1100, 1100, cz + 1100);
        orbitControls.target.set(cx, 0, cz);
        transformControls.camera = perspCamera;

        if (modeToggleBtn) modeToggleBtn.innerHTML = "Mode: Isometric (Click for 2D)";
    } else {
        // Full 3D Perspective Studio Mode
        camera = perspCamera;
        orbitControls.object = perspCamera;
        orbitControls.enableRotate = true;
        orbitControls.maxPolarAngle = Math.PI / 2 - 0.02;
        perspCamera.position.set(cx - 650, 480, cz + 750);
        orbitControls.target.set(cx, 0, cz);
        transformControls.camera = perspCamera;

        if (modeToggleBtn) modeToggleBtn.innerHTML = "Mode: 3D Studio (Click for 2D)";
    }

    if (reconMapMesh) {
        reconMapMesh.visible = (mode === "topdown" || !!state.showReconOverlay);
    }

    orbitControls.update();
}

function toggleViewMode() {
    if (state.viewMode === "topdown") {
        setViewMode("orbit");
    } else {
        setViewMode("topdown");
    }
}

function toggleReconOverlay() {
    state.showReconOverlay = !state.showReconOverlay;
    if (reconMapMesh) {
        reconMapMesh.visible = (state.viewMode === "topdown" || !!state.showReconOverlay);
    }
    const btn = document.getElementById("btn-recon-overlay");
    if (btn) {
        if (state.showReconOverlay) btn.classList.add("active");
        else btn.classList.remove("active");
    }
    showToast(`Satellite Recon Overlay: ${state.showReconOverlay ? "ON" : "OFF"}`);
    playBeep(520, "sine", 0.05);
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
        const payload = JSON.parse(JSON.stringify(state.project));
        if (payload.base_operation === "flat") {
            payload.base_operation = "t1"; // Map to authentic Training grounds archive for flat canvas
        }
        const res = await fetch("/api/export-pack", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload),
        });

        if (res.ok) {
            const data = await res.json();
            if (data.status === "ok") {
                playBeep(980, "sine", 0.15);
                showExportSuccessModal(data);
                return;
            }
        }
        exportClientSideProject();
    } catch (err) {
        exportClientSideProject();
    } finally {
        btn.innerText = "EXPORT MAP PACK";
        btn.disabled = false;
    }
}

function exportClientSideProject() {
    playBeep(980, "sine", 0.15);
    const blob = new Blob([JSON.stringify(state.project, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${state.project.pack_id || "custom_map"}.mw3pack.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    showExportSuccessModal({
        pack_id: state.project.pack_id,
        pack_folder: "Downloaded directly to browser as .mw3pack.json",
        total_placed_assets: (state.project.assets || []).length,
        launcher_script: "Import into local Mod Studio or Core Critical Launcher to play",
    });
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
        btn.innerText = "LAUNCH NATIVE ENGINE";
        btn.disabled = false;
    }
}

// Palette Search and Category Filtering
function filterAssetPalette(query) {
    const q = (query || "").trim().toLowerCase();
    document.querySelectorAll(".asset-card").forEach((card) => {
        const name = (card.querySelector(".asset-name")?.textContent || "").toLowerCase();
        const type = (card.dataset.type || "").toLowerCase();
        const match = !q || name.includes(q) || type.includes(q);
        card.style.display = match ? "flex" : "none";
    });
}

function setPaletteCategory(cat) {
    document.querySelectorAll(".palette-pill").forEach((pill) => pill.classList.remove("active"));
    const activePill = Array.from(document.querySelectorAll(".palette-pill")).find(
        (p) => p.textContent.toLowerCase() === cat.toLowerCase()
    );
    if (activePill) activePill.classList.add("active");

    document.querySelectorAll(".section-title").forEach((title) => {
        const titleCat = title.dataset.category;
        title.style.display = (cat === "all" || titleCat === cat) ? "block" : "none";
    });

    document.querySelectorAll(".asset-grid").forEach((grid) => {
        const gridCat = grid.dataset.category;
        grid.style.display = (cat === "all" || gridCat === cat) ? "grid" : "none";
    });
}

// Real-Time Terrain Sculpting Engine
function toggleSculptMode() {
    state.sculpt.enabled = !state.sculpt.enabled;
    const btn = document.getElementById("btn-sculpt-mode");
    const toolbar = document.getElementById("sculpt-toolbar");

    if (state.sculpt.enabled) {
        if (btn) btn.classList.add("active");
        if (toolbar) toolbar.style.display = "flex";
        clearActiveTool();
        transformControls.detach();
        orbitControls.enabled = false;
        if (brushCursorRing) brushCursorRing.visible = true;
        playBeep(520, "sine", 0.08);
    } else {
        if (btn) btn.classList.remove("active");
        if (toolbar) toolbar.style.display = "none";
        orbitControls.enabled = true;
        if (brushCursorRing) brushCursorRing.visible = false;
        playBeep(420, "sine", 0.08);
    }
}

function setSculptBrushMode(mode) {
    state.sculpt.mode = mode;
    document.querySelectorAll(".sculpt-mode-btn").forEach((b) => b.classList.remove("active"));
    const activeBtn = document.getElementById(`sculpt-btn-${mode}`);
    if (activeBtn) activeBtn.classList.add("active");
    playBeep(640, "triangle", 0.05);
}

function updateSculptParams() {
    const rad = parseFloat(document.getElementById("sculpt-radius").value);
    const str = parseFloat(document.getElementById("sculpt-strength").value);
    const falloff = document.getElementById("sculpt-falloff").value;

    state.sculpt.radius = rad;
    state.sculpt.strength = str;
    state.sculpt.falloff = falloff;

    document.getElementById("sculpt-radius-val").textContent = `${rad}m`;
    document.getElementById("sculpt-strength-val").textContent = str.toFixed(1);

    if (brushCursorRing) {
        brushCursorRing.geometry.dispose();
        const rInner = Math.max(1, rad - 1.5);
        const rOuter = rad;
        const geom = new THREE.RingGeometry(rInner, rOuter, 32);
        geom.rotateX(-Math.PI / 2);
        brushCursorRing.geometry = geom;
    }
}

function resetSculptedTerrain() {
    if (!terrainMesh || !state.sculpt.originalPositions) return;
    const posAttr = terrainMesh.geometry.attributes.position;
    posAttr.array.set(state.sculpt.originalPositions);
    posAttr.needsUpdate = true;
    terrainMesh.geometry.computeVertexNormals();

    if (state.project.terrain) {
        state.project.terrain.height_modifications = {};
    }

    for (const asset of state.project.assets) {
        const groundY = getTerrainHeight(asset.x, asset.z);
        asset.y = Math.round((groundY + (asset.height_offset || 0.0)) * 10) / 10;
    }
    syncSceneAssets();
    if (state.selectedAssetId) updateInspector();
    playBeep(330, "sawtooth", 0.15);
}

function applyTerrainSculpt(hitPoint) {
    if (!terrainMesh || !terrainMesh.geometry) return;
    const geom = terrainMesh.geometry;
    const posAttr = geom.attributes.position;
    const colAttr = geom.attributes.color;
    const count = posAttr.count;

    const hx = hitPoint.x;
    const hz = hitPoint.z;
    const r = state.sculpt.radius;
    const rSq = r * r;
    const str = state.sculpt.strength * 0.45;
    const mode = state.sculpt.mode;
    const falloff = state.sculpt.falloff;

    let modified = false;

    for (let i = 0; i < count; i++) {
        const vx = posAttr.getX(i);
        const vz = posAttr.getZ(i);
        const dx = vx - hx;
        const dz = vz - hz;
        const dSq = dx * dx + dz * dz;

        if (dSq < rSq) {
            const d = Math.sqrt(dSq);
            const normDist = d / r;
            let w = 1.0;
            if (falloff === "linear") {
                w = 1.0 - normDist;
            } else if (falloff === "sharp") {
                w = Math.sqrt(Math.max(0, 1.0 - normDist));
            } else {
                const t = 1.0 - normDist * normDist;
                w = t * t;
            }

            let curY = posAttr.getY(i);
            let newY = curY;

            if (mode === "raise") {
                newY = curY + str * w;
            } else if (mode === "lower") {
                newY = curY - str * w;
            } else if (mode === "flatten") {
                const target = state.sculpt.targetHeight || 0.0;
                newY = curY + (target - curY) * str * 0.25 * w;
            } else if (mode === "smooth") {
                const target = state.sculpt.targetHeight || curY;
                newY = curY + (target - curY) * str * 0.15 * w;
            } else if (mode === "noise") {
                const n = Math.sin(vx * 0.12) * Math.cos(vz * 0.12);
                newY = curY + n * str * 0.8 * w;
            }

            if (newY !== curY) {
                posAttr.setY(i, newY);
                modified = true;

                if (!state.project.terrain.height_modifications) {
                    state.project.terrain.height_modifications = {};
                }
                const coordKey = `${Math.round(vx * 10) / 10},${Math.round(vz * 10) / 10}`;
                state.project.terrain.height_modifications[coordKey] = Math.round(newY * 10) / 10;

                if (colAttr) {
                    const opCode = state.project.base_operation || "c1";
                    const meta = OP_ENV_METADATA[opCode] || OP_ENV_METADATA.c1;
                    const pal = meta.palette;
                    const colSand = new THREE.Color(pal.sand);
                    const colRock = new THREE.Color(pal.rock);
                    const colPeak = new THREE.Color(pal.peak);
                    const tempCol = new THREE.Color();

                    if (newY <= pal.shoreY + 1.5) {
                        tempCol.copy(colSand);
                    } else if (newY < pal.shoreY + 28.0) {
                        const t = (newY - pal.shoreY) / 28.0;
                        tempCol.lerpColors(colSand, colRock, t);
                    } else {
                        const t = Math.min(1.0, (newY - pal.shoreY - 28.0) / 35.0);
                        tempCol.lerpColors(colRock, colPeak, t);
                    }
                    colAttr.setXYZ(i, tempCol.r, tempCol.g, tempCol.b);
                }
            }
        }
    }

    if (modified) {
        posAttr.needsUpdate = true;
        if (colAttr) colAttr.needsUpdate = true;
        geom.computeVertexNormals();

        for (const asset of state.project.assets) {
            const groundY = getTerrainHeight(asset.x, asset.z);
            asset.y = Math.round((groundY + (asset.height_offset || 0.0)) * 10) / 10;
        }
        syncSceneAssets();
        if (state.selectedAssetId) updateInspector();
    }
}

// Campaign Creator & Multi-Mission Sequencer
function openCampaignModal() {
    renderCampaignMissions();
    document.getElementById("campaign-modal").style.display = "flex";
}

function closeCampaignModal() {
    document.getElementById("campaign-modal").style.display = "none";
}

function renderCampaignMissions() {
    const box = document.getElementById("campaign-missions-list");
    if (!box) return;
    box.innerHTML = "";

    const camp = state.campaign;
    document.getElementById("camp-title").value = camp.campaign_title || "Operation Damocles";
    document.getElementById("camp-id").value = camp.campaign_id || "operation_damocles";
    document.getElementById("camp-faction").value = camp.faction || "Inner Sphere";
    document.getElementById("camp-theater").value = camp.theater || "Tranquil Coastal Basin";
    document.getElementById("camp-desc").value = camp.description || "";
    document.getElementById("camp-salvage-enabled").checked = Boolean(
        camp.continuity_rules?.salvage_enabled !== false
    );

    (camp.missions || []).forEach((m, idx) => {
        const card = document.createElement("div");
        card.className = "campaign-mission-card";
        card.innerHTML = `
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 8px;">
                    <span class="campaign-stage-badge">STAGE ${idx + 1}</span>
                    <b style="color: var(--accent-cyan); font-size: 13px;">${m.title}</b>
                    <span style="font-family: var(--font-mono); font-size: 11px; color: var(--text-muted);">(${m.mission_id})</span>
                </div>
                <div style="display: flex; gap: 4px;">
                    <button class="btn" style="padding: 1px 6px; font-size: 10px;" onclick="moveCampaignMission(${idx}, -1)" ${idx === 0 ? "disabled" : ""}>▲</button>
                    <button class="btn" style="padding: 1px 6px; font-size: 10px;" onclick="moveCampaignMission(${idx}, 1)" ${idx === camp.missions.length - 1 ? "disabled" : ""}>▼</button>
                    <button class="btn-tiny-del" onclick="removeCampaignMission(${idx})">&times;</button>
                </div>
            </div>
            <div style="display: grid; grid-template-columns: 1.5fr 1fr 1fr; gap: 8px; margin-top: 4px;">
                <div>
                    <span style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Mission Title</span>
                    <input type="text" class="text-input" style="width: 100%; font-size: 11px;" value="${m.title}" oninput="state.campaign.missions[${idx}].title = this.value;" />
                </div>
                <div>
                    <span style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Mission ID</span>
                    <input type="text" class="text-input" style="width: 100%; font-size: 11px;" value="${m.mission_id}" oninput="state.campaign.missions[${idx}].mission_id = this.value.toLowerCase().replace(/[^a-z0-9_]/g, '_');" />
                </div>
                <div>
                    <span style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Map Pack ID</span>
                    <input type="text" class="text-input" style="width: 100%; font-size: 11px;" value="${m.pack_id || state.project.pack_id}" oninput="state.campaign.missions[${idx}].pack_id = this.value;" />
                </div>
            </div>
            <div style="margin-top: 4px;">
                <span style="font-size: 10px; color: var(--text-muted); text-transform: uppercase;">Tactical Dossier / Intel Briefing</span>
                <input type="text" class="text-input" style="width: 100%; font-size: 11px;" value="${m.briefing_text || ""}" oninput="state.campaign.missions[${idx}].briefing_text = this.value;" />
            </div>
        `;
        box.appendChild(card);
    });
}

function addCampaignMission() {
    const nextIdx = (state.campaign.missions || []).length + 1;
    if (!state.campaign.missions) state.campaign.missions = [];
    state.campaign.missions.push({
        mission_id: `m0${nextIdx}_mission`,
        pack_id: state.project.pack_id,
        title: `Mission ${nextIdx}: Operational Objective`,
        briefing_text: "Destroy designated target units and proceed to recovery point.",
        theater: state.campaign.theater || "Tranquil Coastal Basin",
        audio_track: "action_theme_1",
        next_mission_id: null,
        branch_conditions: {},
    });
    renderCampaignMissions();
    playBeep(720, "sine", 0.06);
}

function removeCampaignMission(idx) {
    state.campaign.missions.splice(idx, 1);
    renderCampaignMissions();
}

function moveCampaignMission(idx, dir) {
    const targetIdx = idx + dir;
    if (targetIdx < 0 || targetIdx >= state.campaign.missions.length) return;
    const item = state.campaign.missions.splice(idx, 1)[0];
    state.campaign.missions.splice(targetIdx, 0, item);
    renderCampaignMissions();
}

async function exportCampaignProject() {
    const btn = document.getElementById("btn-export-campaign");
    btn.innerText = "COMPILING CAMPAIGN...";
    btn.disabled = true;

    try {
        state.campaign.campaign_title = document.getElementById("camp-title").value;
        state.campaign.campaign_id = document.getElementById("camp-id").value;
        state.campaign.faction = document.getElementById("camp-faction").value;
        state.campaign.theater = document.getElementById("camp-theater").value;
        state.campaign.description = document.getElementById("camp-desc").value;
        state.campaign.continuity_rules.salvage_enabled = document.getElementById("camp-salvage-enabled").checked;

        const res = await fetch("/api/export-campaign", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(state.campaign),
        });

        const data = await res.json();
        if (data.status === "ok") {
            playBeep(980, "sine", 0.15);
            alert(`Campaign "${data.campaign_id}" successfully compiled!\nTotal Missions: ${data.total_missions}\nLocation: ${data.campaign_folder}\nLauncher: ${data.launcher_script}`);
        } else {
            alert("Campaign export failed: " + (data.message || "Unknown error"));
        }
    } catch (err) {
        alert("Campaign export error: " + err);
    } finally {
        btn.innerText = "Compile Campaign Pack";
        btn.disabled = false;
    }
}

async function launchCampaignProject() {
    const btn = document.getElementById("btn-launch-campaign");
    btn.innerText = "LAUNCHING...";
    btn.disabled = true;

    try {
        const campId = document.getElementById("camp-id").value || state.campaign.campaign_id;
        const res = await fetch("/api/launch-campaign", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ campaign_id: campId }),
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
        btn.innerText = "Play Campaign";
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

    if ((e.ctrlKey || e.metaKey) && (e.key === "n" || e.key === "N")) {
        e.preventDefault();
        openNewMissionModal();
        return;
    }
    if ((e.ctrlKey || e.metaKey) && (e.key === "o" || e.key === "O")) {
        e.preventDefault();
        triggerImportMapFile();
        return;
    }
    if (e.key === "Escape") {
        if (state.sculpt && state.sculpt.enabled) {
            toggleSculptMode();
        }
        clearActiveTool();
        state.selectedAssetId = null;
        syncSceneAssets();
        updateInspector();
    } else if (e.key === "f" || e.key === "F") {
        if (typeof focusSelectedEntity === "function") focusSelectedEntity();
    } else if (e.key === "[") {
        if (typeof toggleLeftSidebar === "function") toggleLeftSidebar();
    } else if (e.key === "]") {
        if (typeof toggleRightSidebar === "function") toggleRightSidebar();
    } else if (e.key === "?") {
        if (typeof openShortcutsModal === "function") openShortcutsModal();
    } else if (e.key === "1") {
        switchWorkspaceMode("world");
    } else if (e.key === "2") {
        switchWorkspaceMode("sculpt");
    } else if (e.key === "3") {
        switchWorkspaceMode("atmosphere");
    } else if (e.key === "4") {
        switchWorkspaceMode("mechlab");
    } else if (e.key === "5") {
        switchWorkspaceMode("objectives");
    } else if (e.key === "6") {
        switchWorkspaceMode("campaign");
    } else if (e.key === "Delete" || e.key === "Backspace") {
        if (state.selectedAssetId) {
            document.getElementById("btn-insp-delete").click();
        }
    } else if (e.key === "Tab") {
        e.preventDefault();
        toggleViewMode();
    } else if (e.key === "a" || e.key === "A") {
        openAtmosphereModal();
    } else if (e.key === "s" || e.key === "S") {
        toggleSculptMode();
    } else if (e.key === "c" || e.key === "C") {
        openCampaignModal();
    } else if (e.key === "t" || e.key === "T") {
        setViewMode("topdown");
    } else if (e.key === "o" || e.key === "O") {
        setViewMode("orbit");
    } else if (e.key === "i" || e.key === "I") {
        setViewMode("iso");
    } else if (e.key === "m" || e.key === "M") {
        toggleReconOverlay();
    }
}

// Window resize
function onWindowResize() {
    const container = document.getElementById("viewport");
    if (!container || !renderer) return;
    const width = container.clientWidth;
    const height = container.clientHeight;
    const aspect = width / height;

    if (perspCamera) {
        perspCamera.aspect = aspect;
        perspCamera.updateProjectionMatrix();
    }
    if (orthoCamera) {
        const frustumSize = 1800;
        orthoCamera.left = (frustumSize * aspect) / -2;
        orthoCamera.right = (frustumSize * aspect) / 2;
        orthoCamera.top = frustumSize / 2;
        orthoCamera.bottom = frustumSize / -2;
        orthoCamera.updateProjectionMatrix();
    }
    renderer.setSize(width, height);
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
    checkSystemStatus();
    loadGameAssets();
    loadDemoMap();
    applyRouteFromHash();
    window.addEventListener("hashchange", applyRouteFromHash);
});

function applyRouteFromHash() {
    const raw = window.location.hash.replace(/^#/, "");
    if (!raw) return;
    const params = new URLSearchParams(raw);
    if (params.get("mode")) switchWorkspaceMode(params.get("mode"));
    if (params.get("left")) switchLeftTab(params.get("left"));
    if (params.get("right")) switchRightTab(params.get("right"));
    if (params.get("select")) {
        const id = params.get("select");
        if (typeof selectAssetById === "function") selectAssetById(id);
    }
    if (params.get("new") === "1") {
        if (typeof openNewMissionModal === "function") openNewMissionModal();
    }
    if (params.get("shortcuts") === "1") {
        if (typeof openShortcutsModal === "function") openShortcutsModal();
    }
    if (params.get("mechlab") === "1") {
        if (typeof openMechLabModal === "function") openMechLabModal();
    }
    if (params.get("objectives") === "1") {
        if (typeof openObjectivesModal === "function") openObjectivesModal();
    }
}

// System Status and Game Directory Setup
async function checkSystemStatus() {
    const banner = document.getElementById("game-dir-banner");
    const pill = document.getElementById("status-game-pill");
    const dot = document.getElementById("status-game-dot");
    const text = document.getElementById("status-game-text");
    const modalInput = document.getElementById("modal-game-path-input");

    try {
        const res = await fetch("/api/status");
        if (res.ok) {
            const data = await res.json();
            if (modalInput && data.game_directory) {
                modalInput.value = data.game_directory;
            }

            if (!data.game_installed) {
                if (banner) banner.style.display = "flex";
                if (dot) { dot.className = "status-dot warning"; }
                if (text) { text.innerText = "Game Unset"; }
                if (pill) { pill.title = "Click to set MechWarrior 3 directory"; }
            } else {
                if (banner) banner.style.display = "none";
                if (dot) { dot.className = "status-dot"; }
                if (text) { text.innerText = "MW3 Connected"; }
                if (pill) { pill.title = `Connected: ${data.game_directory}`; }
            }
            return;
        }
    } catch (e) {
        // Fall through to cloud/web static mode
    }

    // Static web hosting mode (e.g. corecritical.dev/studio)
    if (banner) banner.style.display = "none";
    if (dot) { dot.className = "status-dot"; }
    if (text) { text.innerText = "Web Cloud Studio"; }
    if (pill) { pill.title = "Running in cloud web mode on corecritical.dev. Export downloads .mw3pack.json directly."; }
}

async function submitGameDirectory() {
    const input = document.getElementById("setup-game-path-input");
    if (!input || !input.value.trim()) {
        alert("Please enter a valid path to your MechWarrior 3 folder.");
        return;
    }
    const pathStr = input.value.trim();
    try {
        const res = await fetch("/api/set-game-directory", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ game_path: pathStr }),
        });
        const data = await res.json();
        if (data.status === "ok") {
            alert("Game directory set successfully! Reloading studio...");
            location.reload();
        } else {
            alert("Error setting game directory: " + data.message);
        }
    } catch (e) {
        alert("Failed to set game directory: " + e);
    }
}

async function packageCurrentMapZip() {
    const packId = state.project.pack_id;
    if (!packId) {
        alert("Please export the map pack first before packaging.");
        return;
    }
    try {
        showToast("Compressing map package for distribution...");
        const res = await fetch("/api/package-pack", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ pack_id: packId }),
        });
        const data = await res.json();
        if (data.status === "ok") {
            alert(`Map Pack Packaged Successfully!\n\nArchive: ${data.zip_name} (${(data.size_bytes / 1024).toFixed(1)} KB)\nLocation: ${data.zip_path}\n\nPlayers on other PCs can extract this ZIP into their MW3 directory and double-click the launcher to play!`);
            playBeep(880, "sine", 0.15);
        } else {
            alert("Packaging failed: " + data.message);
        }
    } catch (e) {
        alert("Packaging error: " + e);
    }
}

async function packageCampaignZip() {
    const campId = document.getElementById("camp-id").value || state.campaign.campaign_id;
    if (!campId) {
        alert("Please enter a campaign ID.");
        return;
    }
    try {
        showToast("Compressing campaign package for distribution...");
        const res = await fetch("/api/package-campaign", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ campaign_id: campId }),
        });
        const data = await res.json();
        if (data.status === "ok") {
            alert(`Campaign Packaged Successfully!\n\nArchive: ${data.zip_name} (${(data.size_bytes / 1024).toFixed(1)} KB)\nLocation: ${data.zip_path}\n\nPlayers on other PCs can extract this ZIP into their MW3 directory and play the multi-mission campaign with 1 click!`);
            playBeep(880, "sine", 0.15);
        } else {
            alert("Campaign packaging failed: " + data.message);
        }
    } catch (e) {
        alert("Campaign packaging error: " + e);
    }
}


// ============================================================================
// ENHANCED UI: SCENE OUTLINER, WORKSPACES & COLLAPSIBLE SIDEBARS
// ============================================================================

function escapeHtml(str) {
    if (!str) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

function renderSceneOutliner() {
    const listEl = document.getElementById("outliner-list");
    const countEl = document.getElementById("outliner-count");
    if (!listEl) return;

    const searchInput = document.getElementById("outliner-search-input");
    const query = (searchInput?.value || "").toLowerCase().trim();
    const assets = state.project.assets || [];

    if (countEl) countEl.innerText = `${assets.length} items`;

    const iconMap = {
        mech: "[MECH]",
        turret: "[TURRET]",
        bunker: "[BUNKER]",
        comm: "[COMMS]",
        repair: "[REPAIR]",
        factory: "[FACTORY]",
        fuel: "[FUEL]",
        city: "[BUILDING]",
        bridge: "[BRIDGE]",
        ramp: "[RAMP]",
        dock: "[DOCK]",
        wall: "[WALL]",
        gate: "[GATE]",
        pole: "[UTILITY]",
        spawn: "[SPAWN]",
        nav: "[NAV]",
        trig_evac: "[EVAC]",
        trig_ambush: "[AMBUSH]",
        trig_sensor: "[SENSOR]",
        trig_minefield: "[MINES]",
    };

    function getIcon(type) {
        for (const [k, v] of Object.entries(iconMap)) {
            if (type.includes(k)) return v;
        }
        return "[ITEM]";
    }

    const filtered = assets.filter((a) => {
        if (!query) return true;
        return (
            (a.name || "").toLowerCase().includes(query) ||
            (a.asset_type || "").toLowerCase().includes(query) ||
            (a.faction || "").toLowerCase().includes(query)
        );
    });

    if (filtered.length === 0) {
        listEl.innerHTML = `<div style="padding: 18px; text-align: center; color: var(--text-muted); font-size: 11px;">
            ${assets.length === 0 ? "No entities in map.<br>Click any asset in the palette to place." : "No matching entities found."}
        </div>`;
        return;
    }

    listEl.innerHTML = filtered
        .map((a) => {
            const isSelected = a.asset_id === state.selectedAssetId;
            const icon = getIcon(a.asset_type || "");
            const factionClass = `faction-${a.faction || "neutral"}`;
            const factionLabel = (a.faction || "neutral").slice(0, 4).toUpperCase();
            return `
            <div class="outliner-item ${isSelected ? "active" : ""}" 
                 onclick="selectAssetById('${a.asset_id}')"
                 ondblclick="focusEntity('${a.asset_id}')"
                 title="Click to inspect, double-click to focus camera">
                <div class="outliner-item-left">
                    <span class="outliner-item-icon">${icon}</span>
                    <span class="outliner-item-name">${escapeHtml(a.name || a.asset_type)}</span>
                    <span class="outliner-faction-badge ${factionClass}">${factionLabel}</span>
                </div>
                <div style="display: flex; align-items: center; gap: 6px;">
                    <span style="font-family: var(--font-mono); font-size: 10px; color: var(--text-muted);">${Math.round(a.x)},${Math.round(a.z)}</span>
                    <button class="outliner-item-del" onclick="event.stopPropagation(); deleteAssetById('${a.asset_id}')" title="Delete">&times;</button>
                </div>
            </div>`;
        })
        .join("");
}

function selectAssetById(assetId) {
    state.selectedAssetId = assetId;
    playBeep(720, "sine", 0.05);
    syncSceneAssets();
    updateInspector();
    renderSceneOutliner();
}

function focusEntity(assetId) {
    const asset = state.project.assets.find((a) => a.asset_id === assetId);
    if (!asset) return;
    selectAssetById(assetId);
    if (orbitControls) {
        orbitControls.target.set(asset.x, asset.y, asset.z);
        if (state.viewMode === "topdown") {
            camera.position.set(asset.x, 600, asset.z);
        } else {
            camera.position.set(asset.x - 70, asset.y + 45, asset.z + 70);
        }
        orbitControls.update();
        playBeep(520, "sine", 0.05);
    }
}

function focusSelectedEntity() {
    if (state.selectedAssetId) {
        focusEntity(state.selectedAssetId);
    } else if (state.project.assets && state.project.assets.length > 0) {
        focusEntity(state.project.assets[0].asset_id);
    }
}

function deleteAssetById(assetId) {
    state.project.assets = state.project.assets.filter((a) => a.asset_id !== assetId);
    if (state.selectedAssetId === assetId) {
        state.selectedAssetId = null;
    }
    playBeep(320, "sawtooth", 0.08);
    syncSceneAssets();
    updateInspector();
    renderSceneOutliner();
}

function deleteSelectedAssetFromUI() {
    if (state.selectedAssetId) {
        deleteAssetById(state.selectedAssetId);
    }
}

// Sidebar Tab Switching
function switchLeftTab(tabName) {
    const paletteBtn = document.getElementById("tab-palette-btn");
    const sculptBtn = document.getElementById("tab-sculpt-btn");
    const paletteView = document.getElementById("left-palette-view");
    const sculptView = document.getElementById("left-sculpt-view");

    if (paletteBtn) paletteBtn.classList.toggle("active", tabName === "palette");
    if (sculptBtn) sculptBtn.classList.toggle("active", tabName === "sculpt");
    if (paletteView) paletteView.style.display = tabName === "palette" ? "flex" : "none";
    if (sculptView) sculptView.style.display = tabName === "sculpt" ? "flex" : "none";

    if (tabName === "sculpt" && (!state.sculpt || !state.sculpt.enabled)) {
        toggleSculptMode();
    } else if (tabName === "palette" && state.sculpt && state.sculpt.enabled) {
        toggleSculptMode();
    }
}

function switchRightTab(tabName) {
    const inspBtn = document.getElementById("tab-inspector-btn");
    const outlinerBtn = document.getElementById("tab-outliner-btn");
    const atmoBtn = document.getElementById("tab-atmosphere-btn");
    const inspView = document.getElementById("right-inspector-view");
    const outlinerView = document.getElementById("right-outliner-view");
    const atmoView = document.getElementById("right-atmosphere-view");

    if (inspBtn) inspBtn.classList.toggle("active", tabName === "inspector");
    if (outlinerBtn) outlinerBtn.classList.toggle("active", tabName === "outliner");
    if (atmoBtn) atmoBtn.classList.toggle("active", tabName === "atmosphere");

    if (inspView) inspView.style.display = tabName === "inspector" ? "flex" : "none";
    if (outlinerView) outlinerView.style.display = tabName === "outliner" ? "flex" : "none";
    if (atmoView) atmoView.style.display = tabName === "atmosphere" ? "flex" : "none";

    if (tabName === "outliner") {
        renderSceneOutliner();
    } else if (tabName === "atmosphere") {
        syncAtmosphereUIFromState();
    }
}

// Workspace Mode Switching
function switchWorkspaceMode(mode) {
    const tabs = ["world", "sculpt", "atmosphere", "mechlab", "objectives", "campaign"];
    tabs.forEach((t) => {
        const el = document.getElementById(`nav-mode-${t}`);
        if (el) el.classList.toggle("active", t === mode);
    });

    if (mode === "world") {
        switchLeftTab("palette");
        switchRightTab("inspector");
        if (state.sidebarLeftCollapsed) toggleLeftSidebar();
        if (state.sidebarRightCollapsed) toggleRightSidebar();
    } else if (mode === "sculpt") {
        switchLeftTab("sculpt");
        if (state.sidebarLeftCollapsed) toggleLeftSidebar();
    } else if (mode === "atmosphere") {
        switchRightTab("atmosphere");
        if (state.sidebarRightCollapsed) toggleRightSidebar();
    } else if (mode === "mechlab") {
        openMechLabModal();
    } else if (mode === "objectives") {
        openObjectivesModal();
    } else if (mode === "campaign") {
        openCampaignModal();
    }
    playBeep(600, "sine", 0.04);
}

// Sidebar Collapse / Expand
state.sidebarLeftCollapsed = false;
state.sidebarRightCollapsed = false;

function toggleLeftSidebar() {
    const el = document.getElementById("sidebar-left");
    const pin = document.getElementById("btn-toggle-left-sidebar");
    if (!el) return;
    state.sidebarLeftCollapsed = !state.sidebarLeftCollapsed;
    el.classList.toggle("collapsed", state.sidebarLeftCollapsed);
    if (pin) pin.innerText = state.sidebarLeftCollapsed ? "›" : "‹";
    setTimeout(onWindowResize, 260);
}

function toggleRightSidebar() {
    const el = document.getElementById("sidebar-right");
    const pin = document.getElementById("btn-toggle-right-sidebar");
    if (!el) return;
    state.sidebarRightCollapsed = !state.sidebarRightCollapsed;
    el.classList.toggle("collapsed", state.sidebarRightCollapsed);
    if (pin) pin.innerText = state.sidebarRightCollapsed ? "‹" : "›";
    setTimeout(onWindowResize, 260);
}

// Modals
function openShortcutsModal() {
    const m = document.getElementById("shortcuts-modal");
    if (m) m.style.display = "flex";
}

function closeShortcutsModal() {
    const m = document.getElementById("shortcuts-modal");
    if (m) m.style.display = "none";
}

function openGameDirModal() {
    const m = document.getElementById("gamedir-modal");
    if (m) m.style.display = "flex";
}

function closeGameDirModal() {
    const m = document.getElementById("gamedir-modal");
    if (m) m.style.display = "none";
}

async function submitModalGameDirectory() {
    const input = document.getElementById("modal-game-path-input");
    const statusEl = document.getElementById("gamedir-modal-status");
    if (!input || !input.value.trim()) {
        if (statusEl) {
            statusEl.style.color = "var(--accent-red)";
            statusEl.innerText = "Please specify a folder path.";
        }
        return;
    }
    try {
        if (statusEl) {
            statusEl.style.color = "var(--accent-cyan)";
            statusEl.innerText = "Connecting to game directory...";
        }
        const res = await fetch("/api/set-game-directory", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ game_path: input.value.trim() }),
        });
        const data = await res.json();
        if (data.status === "ok") {
            alert("MechWarrior 3 folder verified & connected! Reloading studio...");
            location.reload();
        } else {
            if (statusEl) {
                statusEl.style.color = "var(--accent-red)";
                statusEl.innerText = data.message;
            }
        }
    } catch (e) {
        if (statusEl) {
            statusEl.style.color = "var(--accent-red)";
            statusEl.innerText = String(e);
        }
    }
}

function closeObjectivesModal() {
    const m = document.getElementById("objectives-modal");
    if (m) m.style.display = "none";
    switchWorkspaceMode("world");
}

function closeMechLabModal() {
    const m = document.getElementById("mechlab-modal");
    if (m) m.style.display = "none";
    switchWorkspaceMode("world");
}


// ============================================================================
// NEW MISSION CREATION WIZARD & IMPORT CONTROLS
// ============================================================================

function openNewMissionModal() {
    const m = document.getElementById("new-mission-modal");
    if (m) {
        m.style.display = "flex";
        const titleEl = document.getElementById("new-mission-title");
        if (titleEl) {
            titleEl.focus();
            titleEl.select();
        }
    }
}

function closeNewMissionModal() {
    const m = document.getElementById("new-mission-modal");
    if (m) m.style.display = "none";
}

function handleNewMissionTemplateChange(template) {
    const biomeEl = document.getElementById("new-mission-biome");
    if (!biomeEl) return;
    if (template === "blank") {
        biomeEl.value = "flat";
    } else {
        biomeEl.value = "c1";
    }
}

function autoSlugNewMissionId() {
    const titleEl = document.getElementById("new-mission-title");
    const idEl = document.getElementById("new-mission-id");
    if (titleEl && idEl) {
        idEl.value = titleEl.value.trim().toLowerCase().replace(/[^a-z0-9_]/g, "_");
    }
}

function confirmCreateNewMission() {
    const title = (document.getElementById("new-mission-title")?.value || "Custom Mission").trim();
    const packId = (document.getElementById("new-mission-id")?.value || "custom_mission").trim().toLowerCase().replace(/[^a-z0-9_]/g, "_");
    const biome = document.getElementById("new-mission-biome")?.value || "flat";
    const template = document.getElementById("new-mission-template")?.value || "blank";
    const playerMech = document.getElementById("new-mission-mech")?.value || "Mad Cat / Timber Wolf";

    let assets = [];
    if (template === "blank") {
        assets = [
            {
                asset_id: "p_spawn",
                asset_type: "spawn",
                name: "Player Orbital Drop Zone",
                x: 0,
                y: 0,
                z: 0,
                yaw_deg: 0,
                faction: "player",
                health: 100,
            }
        ];
    } else if (template === "outpost") {
        assets = [
            {
                asset_id: "p_spawn",
                asset_type: "spawn",
                name: "Player Orbital Drop Zone",
                x: -300,
                y: 0,
                z: -300,
                yaw_deg: 45,
                faction: "player",
                health: 100,
            },
            {
                asset_id: "base_bunker",
                asset_type: "bunker",
                name: "Perimeter Bunker",
                x: 0,
                y: 0,
                z: 0,
                yaw_deg: 180,
                faction: "enemy",
                health: 200,
                is_objective: true,
            },
            {
                asset_id: "base_radar",
                asset_type: "comm_center",
                name: "Sensor Array Dish",
                x: 60,
                y: 0,
                z: -40,
                yaw_deg: 210,
                faction: "enemy",
                health: 150,
                is_objective: true,
            },
            {
                asset_id: "tur_defense",
                asset_type: "turret_laser",
                name: "Perimeter Laser Tower",
                x: -60,
                y: 0,
                z: 80,
                yaw_deg: 0,
                faction: "enemy",
                health: 120,
            }
        ];
    } else if (template === "skirmish") {
        assets = [
            {
                asset_id: "p_spawn",
                asset_type: "spawn",
                name: "Player Orbital Drop Zone",
                x: -400,
                y: 0,
                z: -400,
                yaw_deg: 45,
                faction: "player",
                health: 100,
            },
            {
                asset_id: "enemy_patrol_1",
                asset_type: "mech_bushwacker",
                name: "Hostile Bushwacker BSW-X1",
                x: 100,
                y: 0,
                z: 100,
                yaw_deg: 225,
                faction: "enemy",
                health: 220,
                is_objective: true,
            },
            {
                asset_id: "enemy_patrol_2",
                asset_type: "mech_shadowcat",
                name: "Hostile Shadow Cat",
                x: 160,
                y: 0,
                z: 180,
                yaw_deg: 225,
                faction: "enemy",
                health: 180,
                is_objective: true,
            }
        ];
    }

    // Reset project state cleanly
    state.project.pack_id = packId;
    state.project.pack_title = title;
    state.project.description = `Custom MechWarrior 3 mission: ${title}`;
    state.project.base_operation = biome;
    state.project.terrain.biome = biome;
    state.project.terrain.water_level = biome === "c1" ? 3.0 : 0.0;
    state.project.terrain.height_modifications = {};
    state.project.assets = assets;
    state.project.objectives = {
        primary: [
            { id: "obj_1", description: "Neutralize hostile forces in sector" }
        ],
        secondary: [],
        briefing_text: `Tactical briefing for ${title}. Eliminate enemy presence and secure the area.`,
        audio_track: "theme1",
    };
    state.project.drop_config = {
        player_mech: playerMech,
        drop_type: "pod",
        weapons: {
            left_arm: "Clan ER PPC",
            center_torso: "Medium Pulse Laser",
            right_arm: "Clan ER PPC",
            left_torso: "Clan LRM-20 Rack",
            right_torso: "Clan LRM-20 Rack",
        },
        armor_tons: 14.0,
        heatsinks: 16,
        jump_jets: 0,
        lancemates: [],
    };

    // Update form inputs in sub-bar
    const titleInput = document.getElementById("project-title");
    const idInput = document.getElementById("project-id");
    const biomeSelect = document.getElementById("biome-select");
    if (titleInput) titleInput.value = title;
    if (idInput) idInput.value = packId;
    if (biomeSelect) biomeSelect.value = biome;

    // Deselect active object and detach gizmos
    state.selectedAssetId = null;
    if (transformControls) transformControls.detach();

    closeNewMissionModal();

    buildTerrain().then(() => {
        syncSceneAssets();
        updateInspector();
        renderSceneOutliner();

        // Re-center camera and controls on player drop zone (0, 0, 0)
        if (orbitControls) {
            orbitControls.target.set(0, 0, 0);
            orbitControls.update();
        }
        if (perspCamera) {
            perspCamera.position.set(0, 80, 160);
            perspCamera.lookAt(0, 0, 0);
        }

        playBeep(1040, "sine", 0.15);
        alert(`Created new mission "${title}" (${template === "blank" ? "Blank Slate" : template} on ${OP_ENV_METADATA[biome]?.name || biome})`);
    });
}

function triggerImportMapFile() {
    const input = document.getElementById("input-import-map-file");
    if (input) input.click();
}

function handleImportMapFile(event) {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        try {
            const data = JSON.parse(e.target.result);
            if (!data.pack_id && !data.assets) {
                alert("Invalid map file format. Expected a .mw3pack.json or project file.");
                return;
            }
            state.project = Object.assign(state.project, data);

            const titleInput = document.getElementById("project-title");
            const idInput = document.getElementById("project-id");
            const biomeSelect = document.getElementById("biome-select");
            if (titleInput && state.project.pack_title) titleInput.value = state.project.pack_title;
            if (idInput && state.project.pack_id) idInput.value = state.project.pack_id;
            if (biomeSelect && state.project.base_operation) biomeSelect.value = state.project.base_operation;

            state.selectedAssetId = null;
            if (transformControls) transformControls.detach();

            buildTerrain().then(() => {
                syncSceneAssets();
                updateInspector();
                renderSceneOutliner();
                playBeep(980, "sine", 0.15);
                alert(`Successfully loaded "${state.project.pack_title || state.project.pack_id}" (${(state.project.assets || []).length} entities)`);
            });
        } catch (err) {
            alert("Could not parse map file: " + err);
        }
    };
    reader.readAsText(file);
    event.target.value = "";
}
