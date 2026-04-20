import React, { useEffect, useRef } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';

const OfficeViewer = () => {
  const containerRef = useRef(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Cena
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x111122);

    // Câmera
    const camera = new THREE.PerspectiveCamera(
      45,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      1000
    );
    camera.position.set(10, 6, 15);
    camera.lookAt(0, 2, 0);

    // Renderer
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.setSize(containerRef.current.clientWidth, containerRef.current.clientHeight);
    renderer.shadowMap.enabled = true;
    containerRef.current.appendChild(renderer.domElement);

    // Controles
    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.target.set(0, 2, 0);

    // Luzes
    scene.add(new THREE.AmbientLight(0x404060, 0.8));
    const dirLight = new THREE.DirectionalLight(0xffffff, 1);
    dirLight.position.set(5, 10, 5);
    dirLight.castShadow = true;
    dirLight.receiveShadow = true;
    scene.add(dirLight);

    // Piso
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(30, 30),
      new THREE.MeshStandardMaterial({ color: 0x336699 })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    scene.add(floor);

    const grid = new THREE.GridHelper(30, 15, 0x88aaff, 0x334466);
    grid.position.y = 0.01;
    scene.add(grid);

    // Função para criar boneco
    const createAgent = (x, z, color, name) => {
      const group = new THREE.Group();
      
      // Corpo
      const body = new THREE.Mesh(
        new THREE.CylinderGeometry(0.6, 0.7, 1.4),
        new THREE.MeshStandardMaterial({ color, roughness: 0.6 })
      );
      body.position.y = 0.9;
      body.castShadow = true;
      body.receiveShadow = true;
      group.add(body);
      
      // Cabeça
      const head = new THREE.Mesh(
        new THREE.SphereGeometry(0.5, 16, 16),
        new THREE.MeshStandardMaterial({ color, roughness: 0.3 })
      );
      head.position.y = 1.7;
      head.castShadow = true;
      head.receiveShadow = true;
      group.add(head);
      
      // Olhos
      const eyeGeo = new THREE.SphereGeometry(0.08);
      const eyeMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
      const pupilGeo = new THREE.SphereGeometry(0.04);
      const pupilMat = new THREE.MeshStandardMaterial({ color: 0x000000 });
      
      const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
      leftEye.position.set(-0.15, 1.65, 0.5);
      group.add(leftEye);
      const leftPupil = new THREE.Mesh(pupilGeo, pupilMat);
      leftPupil.position.set(-0.15, 1.65, 0.57);
      group.add(leftPupil);
      
      const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
      rightEye.position.set(0.15, 1.65, 0.5);
      group.add(rightEye);
      const rightPupil = new THREE.Mesh(pupilGeo, pupilMat);
      rightPupil.position.set(0.15, 1.65, 0.57);
      group.add(rightPupil);
      
      group.position.set(x, 0, z);
      return group;
    };

    // Adiciona 5 bonecos
    const colors = [0x4d7db3, 0xb34d7d, 0x7db34d, 0xb37d4d, 0x7d4db3];
    const positions = [-8, -2, 4, 10, 16];
    positions.forEach((x, i) => {
      scene.add(createAgent(x, 0, colors[i], `Agent${i+1}`));
    });

    // Animação
    const animate = () => {
      requestAnimationFrame(animate);
      controls.update();
      renderer.render(scene, camera);
    };
    animate();

    // Redimensionamento
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

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
};

export default OfficeViewer;
