import React, { useEffect, useRef, useState } from 'react';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { io } from 'socket.io-client';

const OfficeViewer = ({ commands, points }) => {
  const containerRef = useRef(null);
  const sceneRef = useRef(null);
  const rendererRef = useRef(null);
  const cameraRef = useRef(null);
  const controlsRef = useRef(null);
  const agentsRef = useRef({});
  const trajectoryRef = useRef(null);
  const [agentsState, setAgentsState] = useState({});

  // Socket para receber estado dos agentes (opcional, mas útil)
  useEffect(() => {
    const socket = io('http://localhost:5000');
    socket.on('agents_state', (state) => setAgentsState(state));
    return () => socket.close();
  }, []);

  // Inicialização da cena 3D
  useEffect(() => {
    if (!containerRef.current) return;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0x1a1a2e);
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(45, containerRef.current.clientWidth / containerRef.current.clientHeight, 0.1, 1000);
    camera.position.set(20, 15, 30);
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
    controls.target.set(0, 2, 0);
    controlsRef.current = controls;

    // Iluminação
    scene.add(new THREE.AmbientLight(0x404060, 0.6));
    const dirLight = new THREE.DirectionalLight(0xffeedd, 1);
    dirLight.position.set(10, 20, 5);
    dirLight.castShadow = true;
    dirLight.receiveShadow = true;
    dirLight.shadow.mapSize.width = 1024;
    dirLight.shadow.mapSize.height = 1024;
    const d = 30;
    dirLight.shadow.camera.left = -d;
    dirLight.shadow.camera.right = d;
    dirLight.shadow.camera.top = d;
    dirLight.shadow.camera.bottom = -d;
    dirLight.shadow.camera.near = 1;
    dirLight.shadow.camera.far = 50;
    scene.add(dirLight);
    
    const fillLight = new THREE.PointLight(0x4466ff, 0.5);
    fillLight.position.set(-5, 5, 10);
    scene.add(fillLight);

    // Piso
    const floorMat = new THREE.MeshStandardMaterial({ color: 0x336699, roughness: 0.7, metalness: 0.1 });
    const floor = new THREE.Mesh(new THREE.PlaneGeometry(40, 40), floorMat);
    floor.rotation.x = -Math.PI / 2;
    floor.position.y = 0;
    floor.receiveShadow = true;
    scene.add(floor);
    
    const gridHelper = new THREE.GridHelper(40, 20, 0x88aaff, 0x334466);
    gridHelper.position.y = 0.01;
    scene.add(gridHelper);

    // Paredes simples
    const wallMat = new THREE.MeshStandardMaterial({ color: 0x2a3a5a, transparent: true, opacity: 0.3, side: THREE.DoubleSide });
    const backWall = new THREE.Mesh(new THREE.PlaneGeometry(40, 10), wallMat);
    backWall.position.set(0, 5, -20);
    scene.add(backWall);
    const leftWall = new THREE.Mesh(new THREE.PlaneGeometry(40, 10), wallMat);
    leftWall.rotation.y = Math.PI / 2;
    leftWall.position.set(-20, 5, 0);
    scene.add(leftWall);
    const rightWall = new THREE.Mesh(new THREE.PlaneGeometry(40, 10), wallMat);
    rightWall.rotation.y = -Math.PI / 2;
    rightWall.position.set(20, 5, 0);
    scene.add(rightWall);

    // Função para criar mesa com agente
    const createDesk = (x, z, agentName) => {
      const group = new THREE.Group();
      
      const topMat = new THREE.MeshStandardMaterial({ color: 0x8B5A2B });
      const top = new THREE.Mesh(new THREE.BoxGeometry(4, 0.2, 3), topMat);
      top.position.y = 1.5;
      top.castShadow = true;
      top.receiveShadow = true;
      group.add(top);
      
      const legMat = new THREE.MeshStandardMaterial({ color: 0x555555 });
      const legPositions = [[-1.8, 0.75, -1.3], [1.8, 0.75, -1.3], [-1.8, 0.75, 1.3], [1.8, 0.75, 1.3]];
      legPositions.forEach(pos => {
        const leg = new THREE.Mesh(new THREE.BoxGeometry(0.3, 1.5, 0.3), legMat);
        leg.position.set(pos[0], pos[1], pos[2]);
        leg.castShadow = true;
        leg.receiveShadow = true;
        group.add(leg);
      });
      
      const screenMat = new THREE.MeshStandardMaterial({ color: 0x111122, emissive: new THREE.Color(0x224466) });
      const screen = new THREE.Mesh(new THREE.BoxGeometry(2, 1.5, 0.1), screenMat);
      screen.position.set(0, 2.5, -1);
      screen.castShadow = true;
      screen.receiveShadow = true;
      group.add(screen);
      
      const stand = new THREE.Mesh(new THREE.CylinderGeometry(0.2, 0.2, 0.5), new THREE.MeshStandardMaterial({ color: 0x888888 }));
      stand.position.set(0, 1.9, -1);
      stand.castShadow = true;
      stand.receiveShadow = true;
      group.add(stand);
      
      // Agente (esfera)
      const agentMat = new THREE.MeshStandardMaterial({ color: 0x3399ff });
      const agent = new THREE.Mesh(new THREE.SphereGeometry(0.6, 16, 16), agentMat);
      agent.position.set(0, 2.0, 0.8);
      agent.castShadow = true;
      agent.receiveShadow = true;
      agent.userData.name = agentName;
      group.add(agent);
      
      agentsRef.current[agentName] = agent;
      
      group.position.set(x, 0, z);
      return group;
    };

    scene.add(createDesk(-8, 0, 'Arnaldo'));
    scene.add(createDesk(0, 0, 'Beatriz'));
    scene.add(createDesk(8, 0, 'Carlos'));

    // Grupo para a trajetória
    const trajectoryGroup = new THREE.Group();
    scene.add(trajectoryGroup);
    trajectoryRef.current = trajectoryGroup;

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

  // Atualiza cores dos agentes conforme estado recebido via socket ou props
  useEffect(() => {
    Object.entries(agentsState).forEach(([name, state]) => {
      const agent = agentsRef.current[name];
      if (agent) {
        let color;
        switch (state.status) {
          case 'idle': color = 0x3399ff; break;
          case 'thinking': color = 0xffaa00; break;
          case 'working': color = 0x00cc66; break;
          case 'error': color = 0xff3333; break;
          default: color = 0x3399ff;
        }
        agent.material.color.setHex(color);
        // Pulsa se estiver pensando
        if (state.status === 'thinking') {
          const scale = 1 + Math.sin(Date.now() * 0.01) * 0.1;
          agent.scale.set(scale, scale, scale);
        } else {
          agent.scale.set(1, 1, 1);
        }
      }
    });
  }, [agentsState]);

  // Atualiza trajetória quando points mudam
  useEffect(() => {
    const group = trajectoryRef.current;
    if (!group) return;
    
    // Remove linha antiga
    while(group.children.length) group.remove(group.children[0]);
    
    if (!points || points.length < 2) return;
    
    const positions = points.flatMap(p => [p[0]/10, p[1]/10 + 3, p[2]/10]); // escala e elevação
    const geom = new THREE.BufferGeometry();
    geom.setAttribute('position', new THREE.Float32BufferAttribute(positions, 3));
    const mat = new THREE.LineBasicMaterial({ color: 0xffaa00 });
    const line = new THREE.Line(geom, mat);
    group.add(line);
  }, [points]);

  return <div ref={containerRef} style={{ width: '100%', height: '100%' }} />;
};

export default OfficeViewer;
