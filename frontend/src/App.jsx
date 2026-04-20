import React, { useState, useEffect } from 'react';
import axios from 'axios';
import OfficeViewer from './components/OfficeViewer';
import { io } from 'socket.io-client';

const API = window.location.hostname === 'localhost' 
  ? 'http://localhost:5000' 
  : `http://${window.location.hostname}:5000`;

function App() {
  const [gcode, setGcode] = useState(
    'G00 X0 Y0 Z0\n' +
    'G01 Z-2 F200\n' +
    'X10 Y0\n' +
    'X10 Y10\n' +
    'X0 Y10\n' +
    'X0 Y20\n' +
    'X20 Y20\n' +
    'X20 Y0\n' +
    'X30 Y0\n' +
    'X30 Y30\n' +
    'X0 Y30\n' +
    'X0 Y40\n' +
    'X40 Y40\n' +
    'X40 Y0\n' +
    'X50 Y0\n' +
    'X50 Y50\n' +
    'X0 Y50\n' +
    'X0 Y0\n' +
    'G00 Z10'
  );
  const [commands, setCommands] = useState([]);
  const [points, setPoints] = useState([]);
  const [machine, setMachine] = useState('mitsubishi');
  const [processed, setProcessed] = useState('');
  const [loading, setLoading] = useState(false);
  const [socket, setSocket] = useState(null);
  const [agentsState, setAgentsState] = useState({});
  const [error, setError] = useState(null);
  const [lastMessage, setLastMessage] = useState(null);
  const [tasks, setTasks] = useState([]);  // NOVO

  // Buscar histórico de tarefas do backend
  const fetchTasks = async () => {
    try {
      const res = await axios.get(`${API}/api/tasks?limit=10`);
      setTasks(res.data);
    } catch (e) {
      console.error('Erro ao buscar histórico:', e);
    }
  };

  useEffect(() => {
    const newSocket = io(API);
    setSocket(newSocket);
    newSocket.on('agents_state', (state) => setAgentsState(state));
    newSocket.on('agent_message', (data) => {
      setLastMessage({ agent: data.agent, text: data.message });
      fetchTasks(); // Atualiza o histórico ao receber nova mensagem
    });
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
      setError(`Erro no parser: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const postProcess = async () => {
    try {
      const res = await axios.post(`${API}/api/post-process`, { gcode, machine });
      setProcessed(res.data.gcode);
    } catch (e) {
      setError(`Erro no post-processador: ${e.message}`);
    }
  };

  const startAgentTask = (agent) => {
    if (socket) socket.emit('start_task', { agent, gcode });
  };

  useEffect(() => {
    parseGcode();
    fetchTasks(); // Carrega histórico ao iniciar
  }, []);

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ width: '350px', background: '#16213e', padding: '1rem', color: 'white', overflowY: 'auto' }}>
        <h2>✏️ Editor G-Code</h2>
        <textarea
          style={{ width: '100%', height: '150px', background: '#0f3460', color: 'white', fontSize: '10px' }}
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
            <span><strong>{name}</strong>: {state.status} {state.task ? `(${state.task})` : ''}</span>
            <button onClick={() => startAgentTask(name)} style={{ fontSize: 12 }}>Iniciar Tarefa</button>
          </div>
        ))}

        {lastMessage && (
          <div style={{ marginTop: 20, background: '#1a2a4a', padding: 10, borderRadius: 8 }}>
            <strong>💬 {lastMessage.agent} diz:</strong>
            <p style={{ margin: '5px 0 0', fontSize: 12 }}>{lastMessage.text}</p>
          </div>
        )}

        {/* NOVO: Painel de Histórico */}
        <h3 style={{ marginTop: 20 }}>📋 Histórico de Análises</h3>
        <div style={{ maxHeight: 300, overflowY: 'auto', background: '#0f1a2e', borderRadius: 8, padding: 8 }}>
          {tasks.length === 0 ? (
            <p style={{ color: '#aaa', fontSize: 12 }}>Nenhuma análise ainda.</p>
          ) : (
            tasks.map(task => (
              <div key={task.id} style={{ borderBottom: '1px solid #334', padding: '6px 0' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <strong>{task.agent}</strong>
                  <span style={{ fontSize: 10, color: '#88aaff' }}>{new Date(task.created_at).toLocaleTimeString()}</span>
                </div>
                <p style={{ margin: '4px 0 0', fontSize: 11, color: '#ccc' }}>{task.response?.substring(0, 100)}...</p>
                <span style={{ fontSize: 10, color: task.status === 'completed' ? '#6f6' : '#f66' }}>{task.status}</span>
              </div>
            ))
          )}
        </div>
      </div>
      <div style={{ flex: 1, background: '#111122' }}>
        <OfficeViewer commands={commands} points={points} />
      </div>
    </div>
  );
}

export default App;
