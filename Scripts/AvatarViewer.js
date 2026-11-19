import * as THREE from "three";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

// Wireframe avatar in the home page hero. The model is built by blender/build_avatar.py.
// Each part ships twice: faces (drawn depth-only, to hide back lines) and "<Part>_lines".
const MODEL_URL = "/Images/Model/dylan-avatar.glb";
const HEAD_PARTS = ["Head", "Ears", "Hair", "Brows", "Moustache", "Teeth", "Eyes"];
const LINE_OPACITY = {
  Head: 0.55, Ears: 0.55, Hair: 0.5, Eyes: 0.95, Teeth: 0.9, Brows: 0.9, Moustache: 0.85,
  Hoodie: 0.32, Drawstrings: 0.6
};
const NECK_PIVOT = new THREE.Vector3(0, -0.13, -0.015);
const MODEL_BOTTOM = -0.36;
const REVEAL_END = 0.2; // a little above the hair, so the scan line has left the model
const REVEAL_SECONDS = 1.8;

const container = document.querySelector("[data-avatar-viewer]");
const canvas = container && container.querySelector(".avatar-canvas");
const toggle = container && container.querySelector(".avatar-toggle");

function hasWebGL() {
  try {
    return !!document.createElement("canvas").getContext("webgl2");
  } catch (error) {
    return false;
  }
}

if (container && canvas && hasWebGL()) {
  init();
}

function init() {
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)");
  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(26, 1, 0.05, 10);
  camera.position.set(0, -0.095, 0.98);
  camera.lookAt(0, -0.095, 0);

  const uniforms = {
    color: { value: new THREE.Color() },
    reveal: { value: reduceMotion.matches ? REVEAL_END : MODEL_BOTTOM }
  };

  const occluder = new THREE.MeshBasicMaterial({
    colorWrite: false,
    side: THREE.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor: 1,
    polygonOffsetUnits: 1
  });

  function lineMaterial(opacity) {
    return new THREE.ShaderMaterial({
      uniforms: { color: uniforms.color, reveal: uniforms.reveal, opacity: { value: opacity } },
      vertexShader: `
        varying float vY;
        void main() {
          vec4 world = modelMatrix * vec4(position, 1.0);
          vY = world.y;
          gl_Position = projectionMatrix * viewMatrix * world;
        }`,
      fragmentShader: `
        uniform vec3 color;
        uniform float opacity;
        uniform float reveal;
        varying float vY;
        void main() {
          float base = smoothstep(${MODEL_BOTTOM.toFixed(3)}, ${(MODEL_BOTTOM + 0.12).toFixed(3)}, vY);
          float shown = 1.0 - smoothstep(reveal - 0.015, reveal, vY);
          float scan = 1.0 - smoothstep(0.0, 0.03, abs(vY - reveal));
          gl_FragColor = vec4(color, min(1.0, opacity * base * shown + scan * 0.8 * base));
          #include <colorspace_fragment>
        }`,
      transparent: true,
      depthWrite: false
    });
  }

  function readAccent() {
    const accent = getComputedStyle(document.documentElement).getPropertyValue("--color-accent").trim();
    uniforms.color.value.set(accent || "#38bdf8");
    requestRender();
  }

  const avatar = new THREE.Group();
  const headPivot = new THREE.Group();
  const headParts = new THREE.Group();
  headPivot.position.copy(NECK_PIVOT);
  headParts.position.copy(NECK_PIVOT).negate();
  headPivot.add(headParts);
  avatar.add(headPivot);
  scene.add(avatar);

  new GLTFLoader().load(MODEL_URL, (gltf) => {
    const parts = [];
    gltf.scene.traverse((node) => {
      if (node.isMesh || node.isLineSegments) {
        parts.push(node);
      }
    });
    for (const node of parts) {
      const part = node.name.replace(/_lines$/, "");
      if (node.isLineSegments) {
        node.material = lineMaterial(LINE_OPACITY[part] ?? 0.5);
        node.renderOrder = 1;
      } else {
        node.material = occluder;
      }
      node.updateWorldMatrix(true, false);
      node.matrix.copy(node.matrixWorld);
      node.matrix.decompose(node.position, node.quaternion, node.scale);
      (HEAD_PARTS.includes(part) ? headParts : avatar).add(node);
    }
    readAccent();
    container.classList.add("is-ready", "is-3d");
    if (toggle) {
      toggle.hidden = false;
    }
    revealStart = performance.now();
    requestRender();
  }, undefined, () => {
    container.classList.remove("is-ready", "is-3d");
  });

  // --- interaction -----------------------------------------------------------
  const pose = { headYaw: 0, headPitch: 0, bodyYaw: 0 };
  const target = { headYaw: 0, headPitch: 0, bodyYaw: 0 };
  let lastPointer = -Infinity;
  let revealStart = 0;

  window.addEventListener("pointermove", (event) => {
    if (event.pointerType === "touch") {
      return;
    }
    const rect = canvas.getBoundingClientRect();
    const nx = THREE.MathUtils.clamp((event.clientX - (rect.left + rect.width / 2)) / (window.innerWidth / 2), -1, 1);
    const ny = THREE.MathUtils.clamp((event.clientY - (rect.top + rect.height * 0.35)) / (window.innerHeight / 2), -1, 1);
    target.headYaw = nx * 0.55;
    target.headPitch = ny * 0.22;
    target.bodyYaw = nx * 0.2;
    lastPointer = performance.now();
    requestRender();
  }, { passive: true });

  function updateTargets(now) {
    if (now - lastPointer < 2500) {
      return;
    }
    if (reduceMotion.matches) {
      target.headYaw = 0.12;
      target.bodyYaw = 0.25;
      target.headPitch = 0;
      return;
    }
    const t = now / 1000;
    target.bodyYaw = Math.sin(t * 0.35) * 0.32;
    target.headYaw = Math.sin(t * 0.35 - 0.6) * 0.18;
    target.headPitch = Math.sin(t * 0.5) * 0.04;
  }

  // --- rendering -------------------------------------------------------------
  let frame = 0;
  let lastTime = performance.now();
  let visible = true;

  function requestRender() {
    if (!frame && visible && container.classList.contains("is-3d")) {
      frame = requestAnimationFrame(render);
    }
  }

  function render(now) {
    frame = 0;
    const dt = Math.min((now - lastTime) / 1000, 0.1);
    lastTime = now;

    updateTargets(now);
    const ease = reduceMotion.matches ? 1 : 1 - Math.exp(-dt * 4);
    let moving = false;
    for (const key of Object.keys(pose)) {
      pose[key] += (target[key] - pose[key]) * ease;
      moving = moving || Math.abs(target[key] - pose[key]) > 1e-4;
    }
    avatar.rotation.y = pose.bodyYaw;
    headPivot.rotation.set(pose.headPitch, pose.headYaw, 0, "YXZ");

    if (revealStart && uniforms.reveal.value < REVEAL_END) {
      const k = Math.min((now - revealStart) / (REVEAL_SECONDS * 1000), 1);
      uniforms.reveal.value = MODEL_BOTTOM + (REVEAL_END - MODEL_BOTTOM) * (1 - Math.pow(1 - k, 3));
      moving = true;
    }

    renderer.render(scene, camera);
    if (moving || !reduceMotion.matches) {
      requestRender();
    }
  }

  function resize() {
    const { width, height } = canvas.getBoundingClientRect();
    if (!width || !height) {
      return;
    }
    renderer.setSize(width, height, false);
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    requestRender();
  }

  new ResizeObserver(resize).observe(canvas);
  new IntersectionObserver(([entry]) => {
    visible = entry.isIntersecting && !document.hidden;
    if (visible) {
      lastTime = performance.now();
      requestRender();
    }
  }).observe(canvas);
  document.addEventListener("visibilitychange", () => {
    visible = !document.hidden;
    if (visible) {
      lastTime = performance.now();
      requestRender();
    }
  });

  new MutationObserver(readAccent).observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", readAccent);
  reduceMotion.addEventListener("change", requestRender);

  if (toggle) {
    toggle.addEventListener("click", () => {
      const showPhoto = container.classList.toggle("is-3d") === false;
      toggle.setAttribute("aria-pressed", String(showPhoto));
      toggle.querySelector(".avatar-toggle-label").textContent = showPhoto ? "3D" : "Photo";
      toggle.querySelector("i").className = showPhoto ? "fa-solid fa-cube" : "fa-solid fa-camera";
      toggle.setAttribute("aria-label", showPhoto ? "Show 3D wireframe model" : "Show photo");
      if (!showPhoto) {
        requestRender();
      }
    });
  }
}
