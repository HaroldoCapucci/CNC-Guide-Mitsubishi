import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { io } from 'socket.io-client';

// Componente auxiliar para criar braço
const createLimb = (color, position, rotation, scale = [1, 1, 1]) => {
  const group = new THREE.Group();
  const limb = new THREE.Mesh(
    new THREE.CylinderGeometry(0.15, 0.15, 0.8),
    new THREE.MeshStandardMaterial({ color, roughness: 0.6 })
  );
  limb.position.y = -0.4;
  limb.castShadow = true;
  limb.receiveShadow = true;
  group.add(limb);
  group.position.set(...position);
  group.rotation.set(...rotation);
  group.scale.set(...scale);
  return group;
};

const OfficeViewer = ({ commands, points }) => {
  const containerRef = useRef(null);
  const [agentsState, setAgentsState] = useState({});
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const controlsRef = useRef(null);
  const agentsRef = useRef({});
  const trajectoryRef = useRef(null);

  useEffect(() => {
    const socket = io('http://localhost:5000');
    socket.on('agents_state', (state) => setAgentsState(state));
    return () => socket.close();
  }, []);

  useEffect(() => {
    if (!containerRef.current) return;
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, containerRef.current.clientWidth / containerRef.current.clientHeight, 0.1, 1000);
    camera.position.set(20, 12, 30);
    camera.lookAt(4, 2, 0);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    renderer.shadowMap.enabled = true;
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(4, 2, 0);
    controlsRef.current = controls;

    scene.add(new THREE.AmbientLight(0x404060, 0.8));
    const dirLight = new THREE.DirectionalLight(0xffffff, 1);
    dirLight.position.set(10, 20, 5);
    dirLight.castShadow = true;
    dirLight.receiveShadow = true;
    scene.add(dirLight);

    const floor = new THREE.Mesh(new THREE.PlaneGeometry(50, 50), new THREE.MeshStandardMaterial({ color: 0x336699 }));
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    scene.add(floor);
    scene.add(new THREE.GridHelper(50, 25, 0x88aaff, 0x334466));

    // Mesas e agentes
    const agentPositions = { Arnaldo: [-12,0,0], Beatriz: [-4,0,0], Carlos: [4,0,0], Diana: [12,0,0], Eduardo: [20,0,0] };
    const colors = { Arnaldo: 0x4d7db3, Beatriz: 0xb34d7d, Carlos: 0x7db34d, Diana: 0xb37d4d, Eduardo: 0x7d4db3 };

    Object.entries(agentPositions).forEach(([name, pos]) => {
      const group = new THREE.Group();
      const color = colors[name];

      // Corpo
      const body = new THREE.Mesh(new THREE.CylinderGeometry(0.5, 0.6, 1.2), new THREE.MeshStandardMaterial({ color, roughness: 0.6 }));
      body.position.y = 1.0;
      body.castShadow = true;
      body.receiveShadow = true;
      group.add(body);

      // Cabeça
      const head = new THREE.Mesh(new THREE.SphereGeometry(0.5, 16, 16), new THREE.MeshStandardMaterial({ color, roughness: 0.3 }));
      head.position.y = 1.7;
      head.castShadow = true;
      head.receiveShadow = true;
      group.add(head);

      // Olhos e boca
      const eyeGeo = new THREE.SphereGeometry(0.08);
      const eyeMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
      const pupilGeo = new THREE.SphereGeometry(0.04);
      const pupilMat = new THREE.MeshStandardMaterial({ color: 0x000000 });
      const leftEye = new THREE.Mesh(eyeGeo, eyeMat); leftEye.position.set(-0.15, 1.65, 0.51); group.add(leftEye);
      const leftPupil = new THREE.Mesh(pupilGeo, pupilMat); leftPupil.position.set(-0.15, 1.65, 0.58); group.add(leftPupil);
      const rightEye = new THREE.Mesh(eyeGeo, eyeMat); rightEye.position.set(0.15, 1.65, 0.51); group.add(rightEye);
      const rightPupil = new THREE.Mesh(pupilGeo, pupilMat); rightPupil.position.set(0.15, 1.65, 0.58); group.add(rightPupil);
      const mouth = new THREE.Mesh(new THREE.TorusGeometry(0.1, 0.03, 8, 20), new THREE.MeshStandardMaterial({ color: 0x442222 }));
      mouth.position.set(0, 1.5, 0.55); mouth.rotation.x = 0.2; group.add(mouth);

      // Braços
      group.add(createLimb(color, [-0.6, 1.5, 0], [0, 0, -0.3], [1, 1.2, 1]));
      group.add(createLimb(color, [0.6, 1.5, 0], [0, 0, 0.3], [1, 1.2, 1]));

      group.position.set(pos[0], pos[1], pos[2]);
      scene.add(group);
      agentsRef.current[name] = { head, body };
    });

    const trajectoryGroup = new THREE.Group();
    scene.add(trajectoryGroup);
    trajectoryRef.current = trajectoryGroup;

    const animate = () => { requestAnimationFrame(animate); controls.update(); renderer.render(scene, camera); };
    animate();

    return () => { containerRef.current?.removeChild(renderer.domElement); renderer.dispose(); };
  }, []);

  // Atualiza cores e trajetória (mantido igual)
  useEffect(() => {
    Object.entries(agentsState).forEach(([name, state]) => {
      const obj = agentsRef.current[name];
      if (!obj) return;
      let color;
      switch (state.status) {
        case 'idle': color = 0x3399ff; break;
        case 'thinking': color = 0xffaa00; break;
        case 'working': color = 0x00cc66; break;
        case 'error': color = 0xff3333; break;
        default: color = 0x3399ff;
      }
      obj.head.material.color.setHex(color);
    });
  }, [agentsState]);

  useEffect(() => {
    const group = trajectoryRef.current;
    if (!group || !points || points.length < 2) return;
    while (group.children.length) group.remove(group.children[0]);
    const positions = points.flatMap(p => [p[0]/10, p[1]/10 + 3, p[2]/10]);
    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    group.add(new THREE.Line(geom, new THREE.LineBasicMaterial({ color: 0xffaa00 })));
  }, [points]);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
};

export default OfficeViewer;
