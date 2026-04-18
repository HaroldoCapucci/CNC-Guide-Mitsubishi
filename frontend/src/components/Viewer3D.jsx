import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

const Viewer3D = ({ commands, points }) => {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const groupRef = useRef(new THREE.Group());

  useEffect(() => {
    if (!containerRef.current) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x111122);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(75, containerRef.current.clientWidth / containerRef.current.clientHeight, 0.1, 1000);
    camera.position.set(60, 40, 80);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    renderer.shadowMap.enabled = true;
    containerRef.current.appendChild(renderer.domElement);
    rendererRef.current = renderer;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.autoRotate = true;
    controlsRef.current = controls;

    // Luzes
    scene.add(new THREE.AmbientLight(0x404060));
    const light1 = new THREE.DirectionalLight(0xffffff, 1);
    light1.position.set(1, 2, 1);
    scene.add(light1);
    const light2 = new THREE.DirectionalLight(0xffaa88, 0.5);
    light2.position.set(-1, 1, -1);
    scene.add(light2);

    // Grid e eixos
    scene.add(new THREE.GridHelper(200, 20, 0x888888, 0x444444));
    scene.add(new THREE.AxesHelper(100));

    scene.add(groupRef.current);

    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    const handleResize = () => {
      const w = containerRef.current.clientWidth;
      const h = containerRef.current.clientHeight;
      renderer.setSize(w, h);
      camera.aspect = w / h;
      camera.updateProjectionMatrix();
    };
    window.addEventListener('resize', handleResize);

    return () => {
      window.removeEventListener('resize', handleResize);
      containerRef.current?.removeChild(renderer.domElement);
      renderer.dispose();
    };
  }, []);

  // Atualiza trajetória com cores por tipo de comando
  useEffect(() => {
    const group = groupRef.current;
    while(group.children.length) group.remove(group.children[0]);

    if (!commands || commands.length === 0) return;

    let currentPos = [0, 0, 0];
    const segments = { G00: [], G01: [] };

    commands.forEach(cmd => {
      const x = cmd.x !== undefined ? cmd.x : currentPos[0];
      const y = cmd.y !== undefined ? cmd.y : currentPos[1];
      const z = cmd.z !== undefined ? cmd.z : currentPos[2];
      const nextPos = [x, y, z];
      const type = cmd.command === 'G00' ? 'G00' : 'G01';
      segments[type].push([currentPos, nextPos]);
      currentPos = nextPos;
    });

    // G00 - vermelho
    if (segments.G00.length) {
      const points = segments.G00.flatMap(seg => [new THREE.Vector3(...seg[0]), new THREE.Vector3(...seg[1])]);
      const geom = new THREE.BufferGeometry().setFromPoints(points);
      const mat = new THREE.LineBasicMaterial({ color: 0xff5555 });
      group.add(new THREE.LineSegments(geom, mat));
    }

    // G01 - verde
    if (segments.G01.length) {
      const points = segments.G01.flatMap(seg => [new THREE.Vector3(...seg[0]), new THREE.Vector3(...seg[1])]);
      const geom = new THREE.BufferGeometry().setFromPoints(points);
      const mat = new THREE.LineBasicMaterial({ color: 0x55ff55 });
      group.add(new THREE.LineSegments(geom, mat));
    }

    // Esferas nos vértices (pontos)
    const sphereMat = new THREE.MeshStandardMaterial({ color: 0xffaa00, emissive: new THREE.Color(0x442200) });
    points.forEach(p => {
      const sphere = new THREE.Mesh(new THREE.SphereGeometry(1.5, 8, 8), sphereMat);
      sphere.position.set(p[0], p[1], p[2]);
      group.add(sphere);
    });

    // Ajusta câmera
    if (points.length) {
      const last = points[points.length-1];
      cameraRef.current?.lookAt(last[0], last[1], last[2]);
    }
  }, [commands, points]);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
};

export default Viewer3D;
