import sqlite3
import json
from datetime import datetime
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / 'data' / 'cnc_guide.db'

def get_db():
    """Retorna uma conexão com o banco de dados."""
    DB_PATH.parent.mkdir(exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row  # Permite acesso por nome de coluna
    return conn

def init_db():
    """Cria as tabelas se não existirem."""
    conn = get_db()
    cursor = conn.cursor()
    
    # Tabela de tarefas (análises dos agentes)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent TEXT NOT NULL,
            gcode TEXT NOT NULL,
            response TEXT,
            status TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Tabela de estado atual dos agentes (opcional, para persistir após reinício)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS agent_state (
            agent TEXT PRIMARY KEY,
            status TEXT,
            task TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados inicializado em", DB_PATH)

if __name__ == '__main__':
    init_db()
