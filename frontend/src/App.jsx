import React, { useState, useEffect } from 'react';
import axios from 'axios';
import OfficeViewer from './components/OfficeViewer';
import { io } from 'socket.io-client';

// Detecta automaticamente o host do backend
const API = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000' 
  : `http://${window.location.hostname}:5000`;

function App() {
  const [gcode, setGcode] = useState('G00 X0 Y0 Z0\nG01 X50 Y0 Z0\nG01 X50 Y50 Z0\nG01 X0 Y50 Z0\nG01 X0 Y0 Z0');
  const [commands, setCommands] = useState([]);
  const [points, setPoints] = useState([]);
  const [machine, setMachine] = useState('mitsubishi');
  const [processed, setProcessed] = useState('');
  const [loading, setLoading] = useState(false);
  const [socket, setSocket] = useState(null);
  const [agentsState, setAgentsState] = useState({});
  const [error, setError] = useState(null);

  useEffect(() => {
    const newSocket = io(API);
    setSocket(newSocket);
    newSocket.on('agents_state', (state) => setAgentsState(state));
    newSocket.on('connect_error', () => setError('Falha na conexão WebSocket'));
    return () => newSocket.close();
  }, []);

  const parseGcode = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await axios.post(`${API}/api/parse-gcode`, { gcode });
      setCommands(res.data.commands || []);
      setPoints(res.data.path_points || []);
    } catch (e) {
      console.error(e);
      setError(`Erro no parser: ${e.message}. Verifique se o backend está rodando em ${API}`);
    } finally {
      setLoading(false);
    }
  };

  const postProcess = async () => {
    try {
      const res = await axios.post(`${API}/api/post-process`, { gcode, machine });
      setProcessed(res.data.gcode);
    } catch (e) {
      console.error(e);
      setError(`Erro no post-processador: ${e.message}`);
    }
  };

  const startAgentTask = (agent) => {
    if (socket) {
      socket.emit('start_task', { agent, task: 'Analisar G-code', gcode });
    }
  };

  useEffect(() => { parseGcode(); }, []);

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ width: '300px', background: '#16213e', padding: '1rem', color: 'white', overflowY: 'auto' }}>
        <h2>✏️ Editor G-Code</h2>
        <textarea
          style={{ width: '100%', height: '120px', background: '#0f3460', color: 'white' }}
          value={gcode}
          onChange={e => setGcode(e.target.value)}
        />
        <button onClick={parseGcode} disabled={loading} style={{ marginTop: 8 }}>
          {loading ? 'Processando...' : 'Visualizar Trajetória'}
        </button>
        {error && <p style={{ color: '#ff6666' }}>{error}</p>}

        <h3 style={{ marginTop: 20 }}>⚙️ Post-Processador</h3>
        <select value={machine} onChange={e => setMachine(e.target.value)} style={{ width: '100%' }}>
          <option>mitsubishi</option>
          <option>fanuc</option>
        </select>
        <button onClick={postProcess} style={{ marginTop: 8 }}>Gerar G-Code Específico</button>
        {processed && (
          <div style={{ marginTop: 10 }}>
            <h4>Resultado ({machine})</h4>
            <pre style={{ background: '#0a0a1a', padding: 8, fontSize: 10, maxHeight: 200, overflow: 'auto' }}>
              {processed}
            </pre>
          </div>
        )}

        <h3 style={{ marginTop: 20 }}>👔 Agentes</h3>
        {Object.entries(agentsState).map(([name, state]) => (
          <div key={name} style={{ marginBottom: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span>
              <strong>{name}</strong>: {state.status} {state.task ? `(${state.task})` : ''}
            </span>
            <button onClick={() => startAgentTask(name)} style={{ fontSize: 12 }}>Iniciar Tarefa</button>
          </div>
        ))}
      </div>

      <div style={{ flex: 1, background: '#111122' }}>
        <OfficeViewer commands={commands} points={points} />
      </div>
    </div>
  );
}

export default App;
