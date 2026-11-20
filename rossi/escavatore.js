// Escavatore 3D per la testata: modello procedurale in Three.js (nessun file 3D esterno).
// Se WebGL non è disponibile la testata resta com'è, senza il riquadro 3D.
import * as THREE from 'https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js';

const hero = document.querySelector('.hero');
const box = document.querySelector('.hero-3d');
const canvas = box && box.querySelector('canvas');

function webglOk() {
  try {
    const c = document.createElement('canvas');
    return !!(window.WebGLRenderingContext && (c.getContext('webgl2') || c.getContext('webgl')));
  } catch (e) { return false; }
}

if (canvas && webglOk()) {
  try { start(); } catch (e) { hero.classList.remove('has-3d'); }
}

function start() {
  const YELLOW = 0xf5a300, BLACK = 0x161616, DARK = 0x2b2b2b, STEEL = 0x8a8a8a;
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  const renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(32, 1, 0.1, 100);
  const target = new THREE.Vector3(1.25, 1.0, -0.4);

  scene.add(new THREE.HemisphereLight(0xfff4e0, 0x1a1a1a, 1.6));
  const sun = new THREE.DirectionalLight(0xffffff, 2.4);
  sun.position.set(4, 9, 6);
  scene.add(sun);
  const rim = new THREE.DirectionalLight(0xffc04d, 1.2);
  rim.position.set(-6, 4, -5);
  scene.add(rim);

  const mat = (color, o = {}) => new THREE.MeshStandardMaterial({ color, roughness: 0.55, metalness: 0.1, ...o });
  const mYellow = mat(YELLOW, { roughness: 0.45 });
  const mBlack = mat(BLACK, { roughness: 0.8 });
  const mDark = mat(DARK, { roughness: 0.7 });
  const mSteel = mat(STEEL, { roughness: 0.35, metalness: 0.5 });
  const mGlass = mat(0x1d2a33, { roughness: 0.15, metalness: 0.3 });
  const mEarth = mat(0x8a7356, { roughness: 1, flatShading: true });
  const mRock = mat(0xb9ab94, { roughness: 1, flatShading: true });
  const mBucket = mat(0x8f8b84, { roughness: 0.75, metalness: 0.35 });
  const mChrome = mat(0xd9dde0, { roughness: 0.2, metalness: 0.6 });
  const mHose = mat(0x0e0e0e, { roughness: 0.6 });

  const boxMesh = (w, h, d, m, x = 0, y = 0, z = 0) => {
    const mesh = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
    mesh.position.set(x, y, z);
    return mesh;
  };

  // Trave tra due punti nel piano xy del gruppo
  function beam(parent, ax, ay, bx, by, thick, depth, m) {
    const dx = bx - ax, dy = by - ay, len = Math.hypot(dx, dy);
    const mesh = boxMesh(len, thick, depth, m, (ax + bx) / 2, (ay + by) / 2, 0);
    mesh.rotation.z = Math.atan2(dy, dx);
    parent.add(mesh);
    return mesh;
  }
  function pin(parent, x, y, r, depth) {
    const c = new THREE.Mesh(new THREE.CylinderGeometry(r, r, depth, 20), mSteel);
    c.rotation.x = Math.PI / 2;
    c.position.set(x, y, 0);
    parent.add(c);
  }

  const root = new THREE.Group();
  scene.add(root);

  // --- Carro cingolato
  const L = 3.0, H = 0.62, r = H / 2;
  const trackShape = new THREE.Shape();
  trackShape.moveTo(-L / 2 + r, -r);
  trackShape.lineTo(L / 2 - r, -r);
  trackShape.absarc(L / 2 - r, 0, r, -Math.PI / 2, Math.PI / 2, false);
  trackShape.lineTo(-L / 2 + r, r);
  trackShape.absarc(-L / 2 + r, 0, r, Math.PI / 2, Math.PI * 1.5, false);
  const trackGeo = new THREE.ExtrudeGeometry(trackShape, { depth: 0.5, bevelEnabled: true, bevelSize: 0.03, bevelThickness: 0.03, bevelSegments: 2, curveSegments: 16 });
  trackGeo.translate(0, r, -0.25);

  const padGeo = new THREE.BoxGeometry(0.1, 0.05, 0.56);
  for (const side of [-1, 1]) {
    const z = side * 0.78;
    const track = new THREE.Mesh(trackGeo, mBlack);
    track.position.z = z;
    root.add(track);
    // tacchetti del cingolo sopra e sotto
    const pads = new THREE.InstancedMesh(padGeo, mDark, 26);
    const m4 = new THREE.Matrix4();
    for (let i = 0; i < 13; i++) {
      const x = -L / 2 + r + (i / 12) * (L - 2 * r);
      m4.makeTranslation(x, H + 0.03, z); pads.setMatrixAt(i, m4);
      m4.makeTranslation(x, -0.01, z); pads.setMatrixAt(13 + i, m4);
    }
    root.add(pads);
    // ruote (motrice, tendicingolo, rulli)
    for (const [x, rad] of [[-1.2, 0.24], [1.2, 0.24], [-0.6, 0.13], [0, 0.13], [0.6, 0.13]]) {
      const w = new THREE.Mesh(new THREE.CylinderGeometry(rad, rad, 0.06, 20), mSteel);
      w.rotation.x = Math.PI / 2;
      w.position.set(x, rad === 0.24 ? r : 0.17, z + side * 0.29);
      root.add(w);
    }
  }
  root.add(boxMesh(1.5, 0.32, 1.1, mDark, 0, 0.5, 0));
  const ring = new THREE.Mesh(new THREE.CylinderGeometry(0.72, 0.72, 0.14, 32), mDark);
  ring.position.y = 0.72;
  root.add(ring);

  // --- Torretta
  const upper = new THREE.Group();
  upper.position.y = 0.8;
  root.add(upper);
  upper.add(boxMesh(2.7, 0.22, 1.9, mYellow, -0.1, 0.11, 0));
  const engine = boxMesh(1.3, 0.7, 1.86, mYellow, -0.75, 0.57, 0);
  upper.add(engine);
  upper.add(boxMesh(1.32, 0.04, 1.88, mBlack, -0.75, 0.93, 0)); // bordo cofano

  // Contrappeso con strisce di cantiere
  const stripeCanvas = document.createElement('canvas');
  stripeCanvas.width = stripeCanvas.height = 128;
  const sc = stripeCanvas.getContext('2d');
  sc.fillStyle = '#f5a300'; sc.fillRect(0, 0, 128, 128);
  sc.fillStyle = '#161616';
  for (let i = -128; i < 256; i += 32) {
    sc.beginPath(); sc.moveTo(i, 0); sc.lineTo(i + 16, 0); sc.lineTo(i + 16 - 128, 128); sc.lineTo(i - 128, 128); sc.fill();
  }
  const stripeTex = new THREE.CanvasTexture(stripeCanvas);
  stripeTex.colorSpace = THREE.SRGBColorSpace;
  stripeTex.wrapS = stripeTex.wrapT = THREE.RepeatWrapping;
  stripeTex.repeat.set(3, 1);
  const mStripe = mat(0xffffff, { map: stripeTex, roughness: 0.6 });
  const cw = new THREE.Mesh(new THREE.BoxGeometry(0.36, 0.72, 1.9), [mStripe, mBlack, mBlack, mBlack, mBlack, mBlack]);
  cw.rotation.y = Math.PI; // faccia con strisce rivolta all'indietro
  cw.position.set(-1.56, 0.5, 0);
  upper.add(cw);

  // Logo Rossi sui due fianchi del vano motore
  const logoTex = new THREE.TextureLoader().load('logo.png', () => renderOnce());
  logoTex.colorSpace = THREE.SRGBColorSpace;
  logoTex.anisotropy = 4;
  const logoMat = new THREE.MeshStandardMaterial({ map: logoTex, transparent: true, roughness: 0.5, polygonOffset: true, polygonOffsetFactor: -2 });
  const logoGeo = new THREE.PlaneGeometry(1.2, 1.2 * 205 / 748);
  for (const side of [1, -1]) {
    const p = new THREE.Mesh(logoGeo, logoMat);
    p.position.set(-0.75, 0.58, side * 0.932);
    if (side < 0) p.rotation.y = Math.PI;
    upper.add(p);
  }

  // Cabina
  upper.add(boxMesh(0.95, 1.0, 0.85, mYellow, 0.55, 0.72, 0.5));
  upper.add(boxMesh(0.97, 0.62, 0.87, mGlass, 0.56, 0.86, 0.5));
  upper.add(boxMesh(1.02, 0.07, 0.92, mYellow, 0.55, 1.24, 0.5));
  for (const [x, z] of [[1.04, 0.07], [1.04, 0.93]]) upper.add(boxMesh(0.06, 0.66, 0.06, mYellow, x, 0.86, z));
  // Grata di protezione nera davanti alla cabina
  const bar = new THREE.BoxGeometry(0.03, 0.03, 1);
  const grille = new THREE.InstancedMesh(bar, mBlack, 12);
  const gm = new THREE.Matrix4(), gq = new THREE.Quaternion(), gs = new THREE.Vector3();
  for (let i = 0; i < 6; i++) { // orizzontali
    gs.set(1, 1, 0.8); gm.compose(new THREE.Vector3(1.09, 0.6 + i * 0.12, 0.5), gq.identity(), gs); grille.setMatrixAt(i, gm);
  }
  for (let i = 0; i < 6; i++) { // verticali
    gs.set(1, 1, 0.68); gm.compose(new THREE.Vector3(1.09, 0.9, 0.12 + i * 0.152), gq.setFromAxisAngle(new THREE.Vector3(1, 0, 0), Math.PI / 2), gs); grille.setMatrixAt(6 + i, gm);
  }
  upper.add(grille);
  // Corrimano sul cofano e specchietto
  const rail = (x1, z1, x2, z2) => {
    const len = Math.hypot(x2 - x1, z2 - z1);
    const r1 = boxMesh(len, 0.03, 0.03, mBlack, (x1 + x2) / 2, 1.28, (z1 + z2) / 2);
    r1.rotation.y = -Math.atan2(z2 - z1, x2 - x1);
    upper.add(r1);
    for (const [x, z] of [[x1, z1], [x2, z2]]) upper.add(boxMesh(0.03, 0.34, 0.03, mBlack, x, 1.11, z));
  };
  rail(-1.3, 0.85, -0.2, 0.85);
  rail(-1.3, -0.85, -0.5, -0.85);
  upper.add(boxMesh(0.02, 0.16, 0.1, mBlack, 1.12, 1.05, 0.98));
  const exhaust = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.05, 0.45, 12), mBlack);
  exhaust.position.set(-0.45, 1.12, -0.55);
  upper.add(exhaust);

  // --- Braccio curvo (come nella foto di riferimento), avambraccio e benna
  const boom = new THREE.Group();
  boom.position.set(0.8, 0.42, -0.22);
  upper.add(boom);
  const bShape = new THREE.Shape();
  bShape.moveTo(0.02, -0.18);
  bShape.quadraticCurveTo(0.95, 0.62, 1.5, 0.98);
  bShape.quadraticCurveTo(2.1, 0.98, 2.66, 0.6);
  bShape.lineTo(2.62, 0.92);
  bShape.quadraticCurveTo(2.05, 1.46, 1.38, 1.46);
  bShape.quadraticCurveTo(0.6, 1.08, -0.08, 0.16);
  bShape.closePath();
  const boomGeo = new THREE.ExtrudeGeometry(bShape, { depth: 0.36, bevelEnabled: true, bevelSize: 0.03, bevelThickness: 0.03, bevelSegments: 2, curveSegments: 20 });
  boomGeo.translate(0, 0, -0.18);
  boom.add(new THREE.Mesh(boomGeo, mYellow));
  pin(boom, 0, 0, 0.13, 0.46);
  pin(boom, 2.6, 0.75, 0.12, 0.44);
  pin(boom, 1.42, 1.38, 0.08, 0.42);

  // Logo Rossi sui fianchi del braccio, inclinato come la trave
  const boomLogoGeo = new THREE.PlaneGeometry(0.95, 0.95 * 205 / 748);
  for (const side of [1, -1]) {
    const p = new THREE.Mesh(boomLogoGeo, logoMat);
    p.position.set(0.86, 0.72, side * 0.215);
    p.rotation.set(0, side < 0 ? Math.PI : 0, side * 0.66);
    boom.add(p);
  }

  const stick = new THREE.Group();
  stick.position.set(2.6, 0.75, 0);
  boom.add(stick);
  beam(stick, -0.24, 0.5, 0.05, -1.62, 0.34, 0.3, mYellow);
  beam(stick, -0.26, 0.5, -0.05, 0.62, 0.22, 0.3, mYellow); // testa dell'avambraccio
  pin(stick, -0.2, 0.55, 0.08, 0.36);

  const bucket = new THREE.Group();
  bucket.position.set(0.05, -1.62, 0);
  stick.add(bucket);
  const bs = new THREE.Shape();
  bs.moveTo(0, 0.1);
  bs.lineTo(-0.2, 0.02);
  bs.quadraticCurveTo(-0.5, -0.55, 0.04, -0.88);
  bs.lineTo(0.66, -0.78);
  bs.lineTo(0.26, -0.32);
  bs.quadraticCurveTo(0.2, 0.05, 0, 0.1);
  const bGeo = new THREE.ExtrudeGeometry(bs, { depth: 0.8, bevelEnabled: true, bevelSize: 0.025, bevelThickness: 0.025, bevelSegments: 1, curveSegments: 14 });
  bGeo.translate(0, 0, -0.4);
  bucket.add(new THREE.Mesh(bGeo, mBucket));
  // piastre antiusura sul dorso della benna
  for (let i = 0; i < 4; i++) {
    const a = 0.35 + i * 0.32;
    const strip = boxMesh(0.06, 0.05, 0.84, mDark, -0.3 + Math.cos(a + 1.9) * 0.05 - i * 0.02, -0.12 - i * 0.18, 0);
    strip.position.x = -0.22 - Math.sin(a) * 0.18 + i * 0.06;
    bucket.add(strip);
  }
  pin(bucket, 0, 0, 0.1, 0.86);
  for (let i = 0; i < 5; i++) {
    const t = new THREE.Mesh(new THREE.ConeGeometry(0.055, 0.2, 6), mBucket);
    t.rotation.z = -Math.PI / 2 + 0.15;
    t.position.set(0.72, -0.77, -0.32 + i * 0.16);
    bucket.add(t);
  }

  // Pistoni idraulici: cilindro nero con stelo cromato, seguono le articolazioni
  const cylGeo = new THREE.CylinderGeometry(1, 1, 1, 14);
  const pistons = [
    [upper, [1.2, 0.26, -0.42], boom, [1.0, 0.5, -0.2], 0.075],
    [upper, [1.2, 0.26, -0.02], boom, [1.0, 0.5, 0.2], 0.075],
    [boom, [1.0, 1.32, 0], stick, [-0.24, 0.6, 0], 0.07],
    [stick, [-0.08, 0.3, 0], bucket, [-0.16, 0.1, 0], 0.06],
  ].map(([pa, a, pb, b, rad]) => {
    const barrel = new THREE.Mesh(cylGeo, mHose);
    const rod = new THREE.Mesh(cylGeo, mChrome);
    barrel.scale.set(rad, 1, rad);
    rod.scale.set(rad * 0.55, 1, rad * 0.55);
    root.add(barrel, rod);
    return { pa, a: new THREE.Vector3(...a), pb, b: new THREE.Vector3(...b), barrel, rod };
  });
  const va = new THREE.Vector3(), vb = new THREE.Vector3(), dir = new THREE.Vector3(), mid = new THREE.Vector3(), up = new THREE.Vector3(0, 1, 0);
  function place(mesh, from, len, d) {
    mesh.position.copy(from).addScaledVector(d, len / 2);
    mesh.scale.y = len;
    mesh.quaternion.setFromUnitVectors(up, d);
  }
  function updatePistons() {
    root.updateMatrixWorld(true);
    for (const p of pistons) {
      va.copy(p.a).applyMatrix4(p.pa.matrixWorld);
      vb.copy(p.b).applyMatrix4(p.pb.matrixWorld);
      root.worldToLocal(va); root.worldToLocal(vb);
      dir.copy(vb).sub(va);
      const len = dir.length();
      dir.normalize();
      const barrelLen = Math.min(len * 0.62, 1.15);
      place(p.barrel, va, barrelLen, dir);
      mid.copy(va).addScaledVector(dir, barrelLen * 0.85);
      place(p.rod, mid, len - barrelLen * 0.85, dir);
    }
  }

  // Terreno: ombra morbida e due cumuli di terra
  const shCanvas = document.createElement('canvas');
  shCanvas.width = shCanvas.height = 128;
  const sh = shCanvas.getContext('2d');
  const g = sh.createRadialGradient(64, 64, 4, 64, 64, 64);
  g.addColorStop(0, 'rgba(0,0,0,0.55)'); g.addColorStop(1, 'rgba(0,0,0,0)');
  sh.fillStyle = g; sh.fillRect(0, 0, 128, 128);
  const shadow = new THREE.Mesh(new THREE.PlaneGeometry(7.5, 5.5), new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(shCanvas), transparent: true, depthWrite: false }));
  shadow.rotation.x = -Math.PI / 2;
  shadow.position.set(0.6, 0.002, 0);
  root.add(shadow);
  // Cumuli di terra e sassi (deterministici, nessun numero casuale)
  let seed = 7;
  const rnd = () => ((seed = (seed * 16807) % 2147483647) / 2147483647);
  const rockGeo = new THREE.DodecahedronGeometry(1, 0);
  const rocks = new THREE.InstancedMesh(rockGeo, mRock, 60);
  let rockN = 0;
  const rm = new THREE.Matrix4(), rq = new THREE.Quaternion(), re = new THREE.Euler();
  const mound = (x, z, rad, h) => {
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(1, 1), mEarth);
    m.scale.set(rad, h, rad * 0.85);
    m.position.set(x, 0, z);
    root.add(m);
    for (let i = 0; i < 20; i++) {
      const a = rnd() * Math.PI * 2, d = Math.sqrt(rnd()) * rad * 0.95, sz = 0.05 + rnd() * 0.09;
      const y = h * Math.sqrt(Math.max(0, 1 - (d / rad) ** 2)) - sz * 0.3;
      re.set(rnd() * 3, rnd() * 3, rnd() * 3);
      rm.compose(new THREE.Vector3(x + Math.cos(a) * d, y, z + Math.sin(a) * d * 0.85), rq.setFromEuler(re), new THREE.Vector3(sz, sz * 0.7, sz));
      rocks.setMatrixAt(rockN++, rm);
    }
  };
  mound(3.7, -0.2, 0.85, 0.3);
  const dumpA = 1.05;
  mound(Math.cos(dumpA) * 3.3, -Math.sin(dumpA) * 3.3 - 0.2, 0.7, 0.45);
  mound(-0.6, -1.7, 0.8, 0.2);
  rocks.count = rockN;
  root.add(rocks);

  // Ciclo di scavo: [t, rotazione torretta, braccio, avambraccio, benna]
  const keys = [
    [0.00, 0, 0.10, 0.55, 0.45],
    [0.18, 0, 0.0, 0.42, 0.2],
    [0.38, 0, 0.04, -0.15, -0.7],
    [0.50, 0, 0.18, -0.18, -0.85],
    [0.68, dumpA, 0.24, 0.05, -0.85],
    [0.80, dumpA, 0.20, 0.42, 0.75],
    [0.88, dumpA, 0.18, 0.45, 0.6],
    [1.00, 0, 0.10, 0.55, 0.45],
  ];
  const ease = (x) => x * x * (3 - 2 * x);
  function pose(t) {
    let i = 0;
    while (i < keys.length - 2 && t > keys[i + 1][0]) i++;
    const [t0, ...a] = keys[i], [t1, ...b] = keys[i + 1];
    const k = ease(Math.min(1, Math.max(0, (t - t0) / (t1 - t0))));
    const v = a.map((x, j) => x + (b[j] - x) * k);
    upper.rotation.y = v[0];
    boom.rotation.z = v[1];
    stick.rotation.z = v[2];
    bucket.rotation.z = v[3];
  }

  function resize() {
    const w = box.clientWidth, h = box.clientHeight;
    if (!w || !h) return;
    renderer.setSize(w, h, false);
    camera.aspect = w / h;
    const k = w < 600 ? 1.0 : 1.08; // su telefono più vicino
    camera.position.set(target.x + 6.6 * k, 0.95 + 3.4 * k, 9.2 * k);
    camera.lookAt(target);
    camera.updateProjectionMatrix();
  }

  const CYCLE = 8000;
  let visible = true, startTime = performance.now();
  function frame(now) {
    const t = ((now - startTime) % CYCLE) / CYCLE;
    pose(t);
    root.rotation.y = Math.sin(now / 5200) * 0.22 - 0.35;
    updatePistons();
    renderer.render(scene, camera);
  }
  function renderOnce() {
    if (reduceMotion) { pose(0.30); root.rotation.y = -0.35; updatePistons(); renderer.render(scene, camera); }
  }

  hero.classList.add('has-3d');
  resize();
  new ResizeObserver(() => { resize(); renderOnce(); }).observe(box);

  if (reduceMotion) {
    renderOnce();
  } else {
    const run = () => renderer.setAnimationLoop(visible && !document.hidden ? frame : null);
    new IntersectionObserver(([e]) => { visible = e.isIntersecting; run(); }).observe(box);
    document.addEventListener('visibilitychange', run);
    run();
  }
}
