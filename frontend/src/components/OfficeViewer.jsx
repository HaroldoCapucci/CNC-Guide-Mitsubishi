import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { io } from 'socket.io-client';

const OfficeViewer = ({ commands, points }) => {
  const containerRef = useRef(null);
  const [agentsState, setAgentsState] = useState({});
  const sceneRef = useRef(null);
  const cameraRef = useRef(null);
  const rendererRef = useRef(null);
  const controlsRef = useRef(null);
  const agentsRef = useRef({});
  const trajectoryRef = useRef(null);

  // Socket
  useEffect(() => {
    const socket = io('http://localhost:5000');
    socket.on('agents_state', (state) => setAgentsState(state));
    socket.on('agent_message', (data) => {
      console.log(`Mensagem de ${data.agent}: ${data.message}`);
    });
    return () => socket.close();
  }, []);

  // Inicialização Three.js
  useEffect(() => {
    if (!containerRef.current) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(
      45,
      containerRef.current.clientWidth / containerRef.current.clientHeight,
      0.1,
      1000
    );
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
    controls.dampingFactor = 0.05;
    controls.target.set(4, 2, 0);
    controlsRef.current = controls;

    // Luzes
    scene.add(new THREE.AmbientLight(0x404060, 0.8));
    const dirLight = new THREE.DirectionalLight(0xffffff, 1);
    dirLight.position.set(10, 20, 5);
    dirLight.castShadow = true;
    dirLight.receiveShadow = true;
    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    scene.add(dirLight);
    scene.add(new THREE.PointLight(0x4466ff, 0.5, 30));

    // Piso
    const floor = new THREE.Mesh(
      new THREE.PlaneGeometry(50, 50),
      new THREE.MeshStandardMaterial({ color: 0x336699 })
    );
    floor.rotation.x = -Math.PI / 2;
    floor.receiveShadow = true;
    scene.add(floor);

    const grid = new THREE.GridHelper(50, 25, 0x88aaff, 0x334466);
    grid.position.y = 0.01;
    scene.add(grid);

    // Paredes
    const wallMat = new THREE.MeshStandardMaterial({ color: 0x2a3a5a, transparent: true, opacity: 0.3, side: THREE.DoubleSide });
    const backWall = new THREE.Mesh(new THREE.PlaneGeometry(50, 10), wallMat);
    backWall.position.set(0, 5, -25);
    scene.add(backWall);
    const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(50, 10), wallMat);
    leftWall.rotation.y = Math.PI / 2;
    leftWall.position.set(-25, 5, 0);
    scene.add(leftWall);
    const rightWall = new THREE.Mesh(new THREE.PlaneGeometry(50, 10), wallMat);
    rightWall.rotation.y = -Math.PI / 2;
    rightWall.position.set(25, 5, 0);
    scene.add(rightWall);

    // Mesas
    const createDesk = (x, z) => {
      const group = new THREE.Group();
      const top = new THREE.Mesh(new THREE.BoxGeometry(4, 0.2, 3), new THREE.MeshStandardMaterial({ color: 0x8B5A2B }));
      top.position.y = 1.5;
      top.castShadow = true;
      top.receiveShadow = true;
      group.add(top);
      const legMat = new THREE.MeshStandardMaterial({ color: 0x555555 });
      [[-1.8, 0.75, -1.3], [1.8, 0.75, -1.3], [-1.8, 0.75, 1.3], [1.8, 0.75, 1.3]].forEach(pos => {
        const leg = new THREE.Mesh(new THREE.BoxGeometry(0.3, 1.5, 0.3), legMat);
        leg.position.set(pos[0], pos[1], pos[2]);
        leg.castShadow = true;
        leg.receiveShadow = true;
        group.add(leg);
      });
      group.position.set(x, 0, z);
      return group;
    };

    scene.add(createDesk(-12, 0));
    scene.add(createDesk(-4, 0));
    scene.add(createDesk(4, 0));
    scene.add(createDesk(12, 0));
    scene.add(createDesk(20, 0));

    // Agentes (avatares simples)
    const agentPositions = {
      Arnaldo: [-12, 0, 0],
      Beatriz: [-4, 0, 0],
      Carlos: [4, 0, 0],
      Diana: [12, 0, 0],
      Eduardo: [20, 0, 0]
    };

    const colors = {
      Arnaldo: 0x4d7db3,
      Beatriz: 0xb34d7d,
      Carlos: 0x7db34d,
      Diana: 0xb37d4d,
      Eduardo: 0x7d4db3
    };

    Object.entries(agentPositions).forEach(([name, pos]) => {
      const group = new THREE.Group();
      
      const body = new THREE.Mesh(
        new THREE.CylinderGeometry(0.5, 0.6, 1.2),
        new THREE.MeshStandardMaterial({ color: colors[name], roughness: 0.6 })
      );
      body.position.y = 1.0;
      body.castShadow = true;
      body.receiveShadow = true;
      group.add(body);
      
      const head = new THREE.Mesh(
        new THREE.SphereGeometry(0.5, 16, 16),
        new THREE.MeshStandardMaterial({ color: colors[name], roughness: 0.3 })
      );
      head.position.y = 1.7;
      head.castShadow = true;
      head.receiveShadow = true;
      group.add(head);
      
      const eyeGeo = new THREE.SphereGeometry(0.08);
      const eyeMat = new THREE.MeshStandardMaterial({ color: 0xffffff });
      const pupilGeo = new THREE.SphereGeometry(0.04);
      const pupilMat = new THREE.MeshStandardMaterial({ color: 0x000000 });
      
      const leftEye = new THREE.Mesh(eyeGeo, eyeMat);
      leftEye.position.set(-0.15, 1.65, 0.51);
      group.add(leftEye);
      const leftPupil = new THREE.Mesh(pupilGeo, pupilMat);
      leftPupil.position.set(-0.15, 1.65, 0.58);
      group.add(leftPupil);
      
      const rightEye = new THREE.Mesh(eyeGeo, eyeMat);
      rightEye.position.set(0.15, 1.65, 0.51);
      group.add(rightEye);
      const rightPupil = new THREE.Mesh(pupilGeo, pupilMat);
      rightPupil.position.set(0.15, 1.65, 0.58);
      group.add(rightPupil);
      
      group.position.set(pos[0], pos[1], pos[2]);
      scene.add(group);
      
      agentsRef.current[name] = { head, body };
    });

    // Grupo da trajetória
    const trajectoryGroup = new THREE.Group();
    scene.add(trajectoryGroup);
    trajectoryRef.current = trajectoryGroup;

    // Animação
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

  // Atualiza cores dos agentes
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

  // ATUALIZAÇÃO DA TRAJETÓRIA (CORRIGIDA)
  useEffect(() => {
    const group = trajectoryRef.current;
    if (!group) return;

    // Remove linhas antigas
    while (group.children.length) {
      group.remove(group.children[0]);
    }

    // Verifica se há pontos suficientes
    if (!points || points.length < 2) {
      console.log('Nenhum ponto para desenhar trajetória');
      return;
    }

    console.log(`Desenhando trajetória com ${points.length} pontos`);

    // Converte os pontos para coordenadas 3D escaladas (divisão por 10 e elevação em Y)
    const positions = [];
    points.forEach(p => {
      // p é [x, y, z]
      positions.push(p[0] / 10, p[1] / 10 + 3, p[2] / 10);
    });

    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    
    const material = new THREE.LineBasicMaterial({ color: 0xffaa00 });
    const line = new THREE.Line(geometry, material);
    
    group.add(line);
    
    console.log('Trajetória adicionada à cena');
  }, [points]);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
};

export default OfficeViewer;
