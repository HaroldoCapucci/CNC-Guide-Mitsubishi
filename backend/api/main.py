from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit
import time
from ..core.gcode_parser import GcodeParser
from ..core.post_processor import PostProcessorFactory

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='eventlet')

agents_state = {
    'arnaldo': {'status': 'idle', 'task': None},
    'beatriz': {'status': 'idle', 'task': None},
    'carlos': {'status': 'idle', 'task': None}
}

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

@socketio.on('connect')
def handle_connect():
    emit('agents_state', agents_state)

@socketio.on('start_task')
def handle_start_task(data):
    agent = data.get('agent')
    task_name = data.get('task', 'processando G-code')
    if agent in agents_state:
        agents_state[agent]['status'] = 'thinking'
        agents_state[agent]['task'] = task_name
        emit('agents_state', agents_state, broadcast=True)
        
        def simulate_work():
            time.sleep(2)
            agents_state[agent]['status'] = 'working'
            socketio.emit('agents_state', agents_state)
            time.sleep(3)
            agents_state[agent]['status'] = 'idle'
            agents_state[agent]['task'] = None
            socketio.emit('agents_state', agents_state)
        
        socketio.start_background_task(simulate_work)

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
