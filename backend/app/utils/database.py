"""
Central database manager — SQLite for persistence
Supports both file-based SQLite and in-memory for testing
"""
import sqlite3
import os
import json
from ..config import Config


class DatabaseManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def init_app(self, app=None):
        """Initialize database — called once at app startup"""
        if self._initialized:
            return
        db_path = Config.SQLITE_PATH
        db_dir = os.path.dirname(db_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._create_tables()
        self._initialized = True

    def _create_tables(self):
        self._conn.executescript("""
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT DEFAULT '',
                sim_type TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                simulation_id TEXT DEFAULT '',
                data TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT DEFAULT '',
                type TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                metadata TEXT DEFAULT '{}',
                result TEXT DEFAULT '',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                simulation_id TEXT DEFAULT '',
                project_id TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                title TEXT DEFAULT '',
                data TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS survey_results (
                id TEXT PRIMARY KEY,
                project_id TEXT DEFAULT '',
                data TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS simulations (
                id TEXT PRIMARY KEY,
                project_id TEXT DEFAULT '',
                status TEXT DEFAULT 'pending',
                config TEXT DEFAULT '{}',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        self._conn.commit()

    @property
    def conn(self):
        if not self._initialized:
            self.init_app()
        return self._conn

    def close(self):
        if self._initialized:
            self._conn.close()
            self._initialized = False

    # Project operations
    def save_project(self, project_id, data):
        self.conn.execute("""
            INSERT INTO projects (id, name, sim_type, status, simulation_id, data, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, sim_type=excluded.sim_type,
                status=excluded.status, simulation_id=excluded.simulation_id,
                data=excluded.data, updated_at=CURRENT_TIMESTAMP
        """, (
            project_id,
            data.get('name', ''),
            data.get('sim_type', ''),
            data.get('status', 'pending'),
            data.get('simulation_id', ''),
            json.dumps(data)
        ))
        self.conn.commit()

    def get_project(self, project_id):
        row = self.conn.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if row:
            result = dict(row)
            result.update(json.loads(result.pop('data', '{}')))
            return result
        return None

    def delete_project(self, project_id):
        self.conn.execute("DELETE FROM projects WHERE id=?", (project_id,))
        self.conn.commit()

    def list_projects(self):
        rows = self.conn.execute("SELECT id, name, sim_type, status, created_at FROM projects ORDER BY updated_at DESC").fetchall()
        return [dict(r) for r in rows]

    # Task operations
    def save_task(self, task_id, data):
        self.conn.execute("""
            INSERT INTO tasks (id, project_id, type, status, metadata, result, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(id) DO UPDATE SET
                project_id=excluded.project_id, type=excluded.type,
                status=excluded.status, metadata=excluded.metadata,
                result=excluded.result, updated_at=CURRENT_TIMESTAMP
        """, (
            task_id,
            data.get('project_id', ''),
            data.get('type', data.get('task_type', '')),
            data.get('status', 'pending'),
            json.dumps(data.get('metadata', {})),
            json.dumps(data.get('result', ''))
        ))
        self.conn.commit()

    def get_task(self, task_id):
        row = self.conn.execute("SELECT * FROM tasks WHERE id=?", (task_id,)).fetchone()
        if row:
            return dict(row)
        return None

    def list_tasks(self, task_type=None):
        if task_type:
            rows = self.conn.execute("SELECT * FROM tasks WHERE type=? ORDER BY created_at DESC", (task_type,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM tasks ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    def delete_task(self, task_id):
        self.conn.execute("DELETE FROM tasks WHERE id=?", (task_id,))
        self.conn.commit()

    # Report operations
    def save_report(self, report_id, data):
        self.conn.execute("""
            INSERT INTO reports (id, simulation_id, project_id, status, title, data, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                simulation_id=excluded.simulation_id, project_id=excluded.project_id,
                status=excluded.status, title=excluded.title,
                data=excluded.data
        """, (
            report_id,
            data.get('simulation_id', ''),
            data.get('project_id', ''),
            data.get('status', 'pending'),
            data.get('title', ''),
            json.dumps(data),
            data.get('created_at')
        ))
        self.conn.commit()

    def get_report(self, report_id):
        row = self.conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
        if row:
            return dict(row)
        return None

    def list_reports(self, project_id=None):
        if project_id:
            rows = self.conn.execute("SELECT * FROM reports WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM reports ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    # Survey result operations
    def save_survey_result(self, survey_id, data):
        self.conn.execute("""
            INSERT INTO survey_results (id, project_id, data, created_at)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                project_id=excluded.project_id, data=excluded.data
        """, (
            survey_id,
            data.get('project_id', ''),
            json.dumps(data),
            data.get('created_at')
        ))
        self.conn.commit()

    def get_survey_result(self, survey_id):
        row = self.conn.execute("SELECT * FROM survey_results WHERE id=?", (survey_id,)).fetchone()
        if row:
            result = dict(row)
            result['data'] = json.loads(result['data'])
            return result
        return None

    def list_survey_results(self, project_id=None):
        if project_id:
            rows = self.conn.execute("SELECT * FROM survey_results WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM survey_results ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]

    # Simulation operations
    def save_simulation(self, sim_id, data):
        self.conn.execute("""
            INSERT INTO simulations (id, project_id, status, config, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                project_id=excluded.project_id, status=excluded.status,
                config=excluded.config
        """, (
            sim_id,
            data.get('project_id', ''),
            data.get('status', 'pending'),
            json.dumps(data),
            data.get('created_at')
        ))
        self.conn.commit()

    def get_simulation(self, sim_id):
        row = self.conn.execute("SELECT * FROM simulations WHERE id=?", (sim_id,)).fetchone()
        if row:
            return dict(row)
        return None

    def list_simulations(self, project_id=None):
        if project_id:
            rows = self.conn.execute("SELECT * FROM simulations WHERE project_id=? ORDER BY created_at DESC", (project_id,)).fetchall()
        else:
            rows = self.conn.execute("SELECT * FROM simulations ORDER BY created_at DESC").fetchall()
        return [dict(r) for r in rows]
