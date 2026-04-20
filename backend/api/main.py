from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
from ..core.gcode_parser import GcodeParser
from ..core.post_processor import PostProcessorFactory
from ..core.ai_client import AIClient
from ..core.database import get_db, init_db
from ..core.time_estimator import TimeEstimator
from ..core.time_estimator import TimeEstimator
import sqlite3

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

# Inicializa o banco de dados
init_db()

# Carrega estado inicial dos agentes do banco (ou usa padrão)
def load_agents_state():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT agent, status, task FROM agent_state')
    rows = cursor.fetchall()
    conn.close()
    state = {}
    for row in rows:
        state[row['agent']] = {'status': row['status'], 'task': row['task']}
    # Se não houver registros, cria os padrões
    if not state:
        state = {
            'Arnaldo': {'status': 'idle', 'task': None},
            'Beatriz': {'status': 'idle', 'task': None},
            'Carlos': {'status': 'idle', 'task': None}
        }
        save_agents_state(state)
    return state

def save_agents_state(state):
    conn = get_db()
    cursor = conn.cursor()
    for agent, data in state.items():
        cursor.execute('''
            INSERT OR REPLACE INTO agent_state (agent, status, task)
            VALUES (?, ?, ?)
        ''', (agent, data['status'], data['task']))
    conn.commit()
    conn.close()

agents_state = load_agents_state()

# --- REST endpoints (já existentes) ---
@app.route('/api/parse-gcode', methods=['POST'])
def parse_gcode():
    data = request.json
    gcode = data.get('gcode', '')
    if not gcode:
        return jsonify({'error': 'No G-code provided'}), 400
    parser = GcodeParser()
    commands = parser.parse(gcode)
    points = parser.get_path_points()
    commands_dict = [
        {
            'command': c.command,
            'x': c.x,
            'y': c.y,
            'z': c.z,
            'feed_rate': c.feed_rate,
            'spindle_speed': c.spindle_speed
        }
        for c in commands
    ]
    return jsonify({
        'commands': commands_dict,
        'path_points': points,
        'success': True
    })

@app.route('/api/post-process', methods=['POST'])
def post_process():
    data = request.json
    gcode = data.get('gcode', '')
    machine = data.get('machine', 'mitsubishi')
    if not gcode:
        return jsonify({'error': 'No G-code provided'}), 400
    parser = GcodeParser()
    commands = parser.parse(gcode)
    try:
        processor = PostProcessorFactory.create(machine)
        output = processor.process(commands)
        return jsonify({'gcode': output, 'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

# --- NOVO: Endpoint para histórico de tarefas ---
@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    agent = request.args.get('agent')
    limit = int(request.args.get('limit', 20))
    conn = get_db()
    cursor = conn.cursor()
    query = 'SELECT * FROM tasks'
    params = []
    if agent:
        query += ' WHERE agent = ?'
        params.append(agent)
    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    tasks = [dict(row) for row in rows]
    return jsonify(tasks)

# --- Socket.IO events (com persistência) ---
@app.route("/api/estimate", methods=["POST"])

def estimate_time():

    data = request.json

    gcode = data.get("gcode", "")

    hourly_rate = data.get("hourly_rate", 150.0)

    if not gcode:

        return jsonify({"error": "No G-code provided"}), 400

    parser = GcodeParser()

    commands = parser.parse(gcode)

    estimator = TimeEstimator(hourly_rate)

    result = estimator.estimate(commands)

    return jsonify({

        "total_time_seconds": result.total_time_seconds,

        "total_time_formatted": result.total_time_formatted,

        "total_distance_mm": round(result.total_distance_mm, 2),

        "estimated_cost": round(result.estimated_cost, 2),

        "rapid_moves": result.rapid_moves,

        "cutting_moves": result.cutting_moves,

        "success": True

    })

@app.route("/api/estimate", methods=["POST"])

def estimate_time():

    data = request.json

    gcode = data.get("gcode", "")

    hourly_rate = data.get("hourly_rate", 150.0)

    if not gcode:

        return jsonify({"error": "No G-code provided"}), 400

    parser = GcodeParser()

    commands = parser.parse(gcode)

    estimator = TimeEstimator(hourly_rate)

    result = estimator.estimate(commands)

    return jsonify({

        "total_time_seconds": result.total_time_seconds,

        "total_time_formatted": result.total_time_formatted,

        "total_distance_mm": round(result.total_distance_mm, 2),

        "estimated_cost": round(result.estimated_cost, 2),

        "rapid_moves": result.rapid_moves,

        "cutting_moves": result.cutting_moves,

        "success": True

    })

@socketio.on('connect')
def handle_connect():
    emit('agents_state', agents_state)

@socketio.on('start_task')
def handle_start_task(data):
    agent = data.get('agent')
    gcode = data.get('gcode', '')
    if agent not in agents_state:
        return

    agents_state[agent]['status'] = 'thinking'
    agents_state[agent]['task'] = 'Analisando G-code...'
    save_agents_state(agents_state)
    emit('agents_state', agents_state, broadcast=True)

    def ai_work():
        conn = get_db()
        cursor = conn.cursor()
        try:
            client = AIClient()
            result = client.analyze_gcode(gcode, agent)
            agents_state[agent]['status'] = 'idle'
            agents_state[agent]['task'] = None
            # Salva a tarefa no histórico
            cursor.execute('''
                INSERT INTO tasks (agent, gcode, response, status)
                VALUES (?, ?, ?, ?)
            ''', (agent, gcode, result, 'completed'))
            conn.commit()
            socketio.emit('agent_message', {'agent': agent, 'message': result})
        except Exception as e:
            agents_state[agent]['status'] = 'error'
            agents_state[agent]['task'] = str(e)
            cursor.execute('''
                INSERT INTO tasks (agent, gcode, response, status)
                VALUES (?, ?, ?, ?)
            ''', (agent, gcode, str(e), 'error'))
            conn.commit()
        finally:
            conn.close()
            save_agents_state(agents_state)
            socketio.emit('agents_state', agents_state)

    socketio.start_background_task(ai_work)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
