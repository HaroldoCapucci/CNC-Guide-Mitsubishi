from flask import Flask, request, jsonify, make_response, send_from_directory
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import csv
import io
import os
from ..core.gcode_parser import GcodeParser
from ..core.post_processor import PostProcessorFactory
from ..core.ai_client import AIClient
from ..core.database import get_db, init_db
from ..core.time_estimator import TimeEstimator

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

init_db()

def load_agents_state():
    # Lista fixa de agentes (sempre os 5)
    default_state = {
        'Arnaldo': {'status': 'idle', 'task': None},
        'Beatriz': {'status': 'idle', 'task': None},
        'Carlos': {'status': 'idle', 'task': None},
        'Diana': {'status': 'idle', 'task': None},
        'Eduardo': {'status': 'idle', 'task': None}
    }
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT agent, status, task FROM agent_state')
    rows = cursor.fetchall()
    conn.close()
    # Mescla com o estado padrão (caso algum agente não esteja no banco)
    state = default_state.copy()
    for row in rows:
        if row['agent'] in state:
            state[row['agent']] = {'status': row['status'], 'task': row['task']}
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

# ------------------------------------------------------------
# REST endpoints (mantidos iguais)
# ------------------------------------------------------------
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

@app.route('/api/tasks', methods=['GET'])
def get_tasks():
    agent = request.args.get('agent')
    limit = int(request.args.get('limit', 20))
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    conn = get_db()
    cursor = conn.cursor()
    query = 'SELECT * FROM tasks WHERE 1=1'
    params = []
    if agent:
        query += ' AND agent = ?'
        params.append(agent)
    if start_date:
        query += ' AND created_at >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND created_at <= ?'
        params.append(end_date + ' 23:59:59')
    query += ' ORDER BY created_at DESC LIMIT ?'
    params.append(limit)
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    tasks = [dict(row) for row in rows]
    return jsonify(tasks)

@app.route('/api/estimate', methods=['POST'])
def estimate_time():
    data = request.json
    gcode = data.get('gcode', '')
    hourly_rate = data.get('hourly_rate', 150.0)
    if not gcode:
        return jsonify({'error': 'No G-code provided'}), 400
    parser = GcodeParser()
    commands = parser.parse(gcode)
    estimator = TimeEstimator(hourly_rate)
    result = estimator.estimate(commands)
    return jsonify({
        'total_time_seconds': result.total_time_seconds,
        'total_time_formatted': result.total_time_formatted,
        'total_distance_mm': round(result.total_distance_mm, 2),
        'estimated_cost': round(result.estimated_cost, 2),
        'rapid_moves': result.rapid_moves,
        'cutting_moves': result.cutting_moves,
        'success': True
    })

@app.route('/api/tasks/export/csv', methods=['GET'])
def export_tasks_csv():
    agent = request.args.get('agent')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    conn = get_db()
    cursor = conn.cursor()
    query = 'SELECT agent, gcode, response, status, created_at FROM tasks WHERE 1=1'
    params = []
    if agent:
        query += ' AND agent = ?'
        params.append(agent)
    if start_date:
        query += ' AND created_at >= ?'
        params.append(start_date)
    if end_date:
        query += ' AND created_at <= ?'
        params.append(end_date + ' 23:59:59')
    query += ' ORDER BY created_at DESC'
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['Agente', 'G-code', 'Resposta', 'Status', 'Data'])
    for row in rows:
        writer.writerow([row['agent'], row['gcode'][:100], row['response'], row['status'], row['created_at']])
    
    response = make_response(output.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=tarefas_cnc.csv'
    response.headers['Content-type'] = 'text/csv; charset=utf-8'
    return response

# Rotas para servir o frontend estático (produção)
@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder = os.path.join(os.path.dirname(__file__), '..', 'static')
    if path != "" and os.path.exists(os.path.join(static_folder, path)):
        return send_from_directory(static_folder, path)
    else:
        return send_from_directory(static_folder, 'index.html')

# ------------------------------------------------------------
# Socket.IO events
# ------------------------------------------------------------
@socketio.on('connect')
def handle_connect():
    emit('agents_state', agents_state)

@socketio.on('start_task')
def handle_start_task(data):
    agent = data.get('agent')
    gcode = data.get('gcode', '')
    if agent not in agents_state:
        return

    if agent == 'Diana':
        task_desc = 'Pós-processando...'
    elif agent == 'Eduardo':
        task_desc = 'Analisando trajetória...'
    else:
        task_desc = 'Analisando G-code...'

    agents_state[agent]['status'] = 'thinking'
    agents_state[agent]['task'] = task_desc
    save_agents_state(agents_state)
    emit('agents_state', agents_state, broadcast=True)

    def ai_work():
        conn = get_db()
        cursor = conn.cursor()
        try:
            if agent == 'Diana':
                parser = GcodeParser()
                commands = parser.parse(gcode)
                processor = PostProcessorFactory.create('fanuc')
                result = processor.process(commands)
                response_msg = f"Pós-processamento (Fanuc) concluído com sucesso. Total de {len(commands)} comandos."
            elif agent == 'Eduardo':
                parser = GcodeParser()
                commands = parser.parse(gcode)
                points = parser.get_path_points()
                rapid = sum(1 for c in commands if c.command == 'G00')
                linear = sum(1 for c in commands if c.command == 'G01')
                response_msg = f"Trajetória com {len(points)} pontos. Movimentos rápidos: {rapid}, interpolações: {linear}."
            else:
                client = AIClient()
                response_msg = client.analyze_gcode(gcode, agent)

            agents_state[agent]['status'] = 'idle'
            agents_state[agent]['task'] = None
            cursor.execute('''
                INSERT INTO tasks (agent, gcode, response, status)
                VALUES (?, ?, ?, ?)
            ''', (agent, gcode, response_msg, 'completed'))
            conn.commit()
            socketio.emit('agent_message', {'agent': agent, 'message': response_msg})
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
