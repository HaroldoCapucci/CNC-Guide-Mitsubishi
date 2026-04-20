import React, { useState, useEffect } from 'react';
import axios from 'axios';
import OfficeViewer from './components/OfficeViewer';
import { io } from 'socket.io-client';
import { Bar } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend);

// API fixa para o backend rodando no Termux
const API = 'http://localhost:5000';

function App() {
  const [gcode, setGcode] = useState(
    'G00 X0 Y0 Z0\n' +
    'G01 Z-2 F200\n' +
    'X10 Y0\nX10 Y10\nX0 Y10\nX0 Y20\nX20 Y20\nX20 Y0\nX30 Y0\nX30 Y30\nX0 Y30\nX0 Y40\nX40 Y40\nX40 Y0\nX50 Y0\nX50 Y50\nX0 Y50\nX0 Y0\n' +
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
  const [tasks, setTasks] = useState([]);
  const [estimation, setEstimation] = useState(null);
  const [dateFilter, setDateFilter] = useState('all');
  const [customStart, setCustomStart] = useState('');
  const [customEnd, setCustomEnd] = useState('');

  const fetchTasks = async () => {
    let start, end;
    const today = new Date();
    if (dateFilter === 'today') {
      start = today.toISOString().split('T')[0];
      end = start;
    } else if (dateFilter === 'week') {
      const weekAgo = new Date(today);
      weekAgo.setDate(today.getDate() - 7);
      start = weekAgo.toISOString().split('T')[0];
      end = today.toISOString().split('T')[0];
    } else if (dateFilter === 'month') {
      const monthAgo = new Date(today);
      monthAgo.setMonth(today.getMonth() - 1);
      start = monthAgo.toISOString().split('T')[0];
      end = today.toISOString().split('T')[0];
    } else if (dateFilter === 'custom') {
      start = customStart;
      end = customEnd;
    }
    const params = { limit: 100 };
    if (start) params.start_date = start;
    if (end) params.end_date = end;
    try {
      const res = await axios.get(`${API}/api/tasks`, { params });
      setTasks(res.data);
    } catch (e) {
      console.error('Erro ao buscar histórico:', e);
    }
  };

  const exportCSV = () => {
    let url = `${API}/api/tasks/export/csv`;
    const params = new URLSearchParams();
    if (dateFilter === 'today') {
      const today = new Date().toISOString().split('T')[0];
      params.append('start_date', today);
      params.append('end_date', today);
    } else if (dateFilter === 'week') {
      const today = new Date();
      const weekAgo = new Date(today);
      weekAgo.setDate(today.getDate() - 7);
      params.append('start_date', weekAgo.toISOString().split('T')[0]);
      params.append('end_date', today.toISOString().split('T')[0]);
    } else if (dateFilter === 'month') {
      const today = new Date();
      const monthAgo = new Date(today);
      monthAgo.setMonth(today.getMonth() - 1);
      params.append('start_date', monthAgo.toISOString().split('T')[0]);
      params.append('end_date', today.toISOString().split('T')[0]);
    } else if (dateFilter === 'custom') {
      if (customStart) params.append('start_date', customStart);
      if (customEnd) params.append('end_date', customEnd);
    }
    const query = params.toString();
    if (query) url += '?' + query;
    window.open(url);
  };

  useEffect(() => {
    const newSocket = io(API);
    setSocket(newSocket);
    newSocket.on('agents_state', (state) => setAgentsState(state));
    newSocket.on('agent_message', (data) => {
      setLastMessage({ agent: data.agent, text: data.message });
      fetchTasks();
    });
    newSocket.on('connect_error', () => setError('Falha na conexão WebSocket. Verifique se o backend está rodando.'));
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

  const estimateTime = async () => {
    try {
      const res = await axios.post(`${API}/api/estimate`, { gcode, hourly_rate: 150 });
      setEstimation(res.data);
    } catch (e) {
      setError(`Erro na estimativa: ${e.message}`);
    }
  };

  const startAgentTask = (agent) => {
    if (socket) socket.emit('start_task', { agent, gcode });
  };

  useEffect(() => {
    parseGcode();
    fetchTasks();
  }, []);

  useEffect(() => {
    fetchTasks();
  }, [dateFilter, customStart, customEnd]);

  const agentNames = ['Arnaldo', 'Beatriz', 'Carlos', 'Diana', 'Eduardo'];
  const taskCounts = agentNames.map(name => 
    tasks.filter(t => t.agent === name && t.status === 'completed').length
  );

  const chartData = {
    labels: agentNames,
    datasets: [{
      label: 'Tarefas Concluídas',
      data: taskCounts,
      backgroundColor: ['#ff6384', '#36a2eb', '#ffce56', '#4bc0c0', '#9966ff']
    }]
  };

  return (
    <div style={{ display: 'flex', height: '100vh' }}>
      <div style={{ width: '380px', background: '#16213e', padding: '1rem', color: 'white', overflowY: 'auto' }}>
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

        <h3 style={{ marginTop: 20 }}>⏱️ Estimativa de Tempo/Custo</h3>
        <button onClick={estimateTime} style={{ marginTop: 8 }}>Calcular</button>
        {estimation && (
          <div style={{ marginTop: 10, background: '#1a2a4a', padding: 10, borderRadius: 8 }}>
            <p>⏱️ Tempo: <strong>{estimation.total_time_formatted}</strong></p>
            <p>💰 Custo: <strong>R$ {estimation.estimated_cost}</strong></p>
            <p>📏 Distância: <strong>{estimation.total_distance_mm} mm</strong></p>
            <p>🔄 Mov. rápidos: {estimation.rapid_moves} | Corte: {estimation.cutting_moves}</p>
          </div>
        )}

        <h3 style={{ marginTop: 20 }}>👔 Agentes</h3>
        {Object.entries(agentsState).map(([name, state]) => (
          <div key={name} style={{ marginBottom: 8, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span><strong>{name}</strong>: {state.status} {state.task ? `(${state.task})` : ''}</span>
            <button onClick={() => startAgentTask(name)} style={{ fontSize: 12 }}>Iniciar</button>
          </div>
        ))}

        {lastMessage && (
          <div style={{ marginTop: 20, background: '#1a2a4a', padding: 10, borderRadius: 8 }}>
            <strong>💬 {lastMessage.agent} diz:</strong>
            <p style={{ margin: '5px 0 0', fontSize: 12 }}>{lastMessage.text}</p>
          </div>
        )}

        <h3 style={{ marginTop: 20 }}>📊 Produtividade</h3>
        <div style={{ background: '#0f1a2e', padding: 8, borderRadius: 8 }}>
          <Bar data={chartData} options={{ responsive: true, maintainAspectRatio: true, plugins: { legend: { labels: { color: 'white' } } } }} />
        </div>

        <h3 style={{ marginTop: 20 }}>📋 Histórico</h3>
        <div style={{ marginBottom: 8 }}>
          <select value={dateFilter} onChange={e => setDateFilter(e.target.value)} style={{ width: '100%', background: '#0f3460', color: 'white' }}>
            <option value="all">Todo período</option>
            <option value="today">Hoje</option>
            <option value="week">Última semana</option>
            <option value="month">Último mês</option>
            <option value="custom">Personalizado</option>
          </select>
          {dateFilter === 'custom' && (
            <div style={{ display: 'flex', gap: '4px', marginTop: 4 }}>
              <input type="date" value={customStart} onChange={e => setCustomStart(e.target.value)} style={{ flex: 1, background: '#0f3460', color: 'white' }} />
              <input type="date" value={customEnd} onChange={e => setCustomEnd(e.target.value)} style={{ flex: 1, background: '#0f3460', color: 'white' }} />
            </div>
          )}
          <button onClick={fetchTasks} style={{ marginTop: 4, width: '100%' }}>Filtrar</button>
        </div>
        <button onClick={exportCSV} style={{ marginBottom: 8, width: '100%' }}>📥 Exportar CSV</button>
        <div style={{ maxHeight: 200, overflowY: 'auto', background: '#0f1a2e', borderRadius: 8, padding: 8 }}>
          {tasks.slice(0, 10).map(task => (
            <div key={task.id} style={{ borderBottom: '1px solid #334', padding: '6px 0' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <strong>{task.agent}</strong>
                <span style={{ fontSize: 10, color: '#88aaff' }}>{new Date(task.created_at).toLocaleTimeString()}</span>
              </div>
              <p style={{ margin: '4px 0 0', fontSize: 11, color: '#ccc' }}>{task.response?.substring(0, 80)}...</p>
              <span style={{ fontSize: 10, color: task.status === 'completed' ? '#6f6' : '#f66' }}>{task.status}</span>
            </div>
          ))}
        </div>
      </div>
      <div style={{ flex: 1, background: '#111122' }}>
        <OfficeViewer commands={commands} points={points} />
      </div>
    </div>
  );
}

export default App;
