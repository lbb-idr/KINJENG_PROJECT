"""
One-time migration script: reads all JSON files from uploads/ directories
and inserts them into SQLite tables via DatabaseManager.

Usage:
    cd backend
    python scripts/migrate_to_sqlite.py
    # or with explicit path:
    python scripts/migrate_to_sqlite.py --db-path ../data/mirofish.db
"""
import os
import sys
import json
import glob
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

os.environ.setdefault('SQLITE_PATH', os.path.join(os.path.dirname(__file__), '../data/mirofish.db'))

from app.utils.database import DatabaseManager
from app.config import Config


def find_json_files(base_dir, pattern):
    return glob.glob(os.path.join(base_dir, pattern), recursive=True)


def migrate_projects(db, uploads_dir):
    projects_dir = os.path.join(uploads_dir, 'projects')
    if not os.path.exists(projects_dir):
        print("  No projects directory found, skipping.")
        return 0

    count = 0
    for proj_dir in os.listdir(projects_dir):
        meta_path = os.path.join(projects_dir, proj_dir, 'project.json')
        if not os.path.exists(meta_path):
            continue
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            project_id = data.get('project_id', proj_dir)
            db.save_project(project_id, data)
            count += 1
            print(f"  ✓ Project {project_id}: {data.get('name', 'Unnamed')}")
        except Exception as e:
            print(f"  ✗ Error migrating project {proj_dir}: {e}")

    return count


def migrate_tasks(db, uploads_dir):
    tasks_dir = os.path.join(uploads_dir, 'tasks')
    tasks_file = os.path.join(tasks_dir, 'tasks.json')
    if not os.path.exists(tasks_file):
        print("  No tasks.json found, skipping.")
        return 0

    count = 0
    try:
        with open(tasks_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for task_id, task_data in data.items():
            db.save_task(task_id, task_data)
            count += 1
            print(f"  ✓ Task {task_id}: {task_data.get('task_type', 'unknown')}")
    except Exception as e:
        print(f"  ✗ Error migrating tasks: {e}")

    return count


def migrate_reports(db, uploads_dir):
    reports_dir = os.path.join(uploads_dir, 'reports')
    if not os.path.exists(reports_dir):
        print("  No reports directory found, skipping.")
        return 0

    count = 0
    for report_dir in os.listdir(reports_dir):
        meta_path = os.path.join(reports_dir, report_dir, 'meta.json')
        if not os.path.exists(meta_path):
            continue
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            report_id = data.get('report_id', report_dir)
            db.save_report(report_id, data)
            count += 1
            title = data.get('title', data.get('outline', {}).get('title', 'Untitled'))
            print(f"  ✓ Report {report_id}: {title}")
        except Exception as e:
            print(f"  ✗ Error migrating report {report_dir}: {e}")

    return count


def migrate_survey_results(db, uploads_dir):
    results_dir = os.path.join(uploads_dir, 'survey_results')
    if not os.path.exists(results_dir):
        print("  No survey_results directory found, skipping.")
        return 0

    count = 0
    for proj_dir in os.listdir(results_dir):
        result_path = os.path.join(results_dir, proj_dir, 'results.json')
        if not os.path.exists(result_path):
            continue
        try:
            with open(result_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            survey_id = f"survey_{proj_dir}"
            db.save_survey_result(survey_id, data)
            count += 1
            print(f"  ✓ Survey result {survey_id}: project {data.get('project_id', 'unknown')}")
        except Exception as e:
            print(f"  ✗ Error migrating survey result {proj_dir}: {e}")

    return count


def migrate_simulations(db, uploads_dir):
    sims_dir = os.path.join(uploads_dir, 'simulations')
    if not os.path.exists(sims_dir):
        print("  No simulations directory found, skipping.")
        return 0

    count = 0
    for sim_dir in os.listdir(sims_dir):
        config_path = os.path.join(sims_dir, sim_dir, 'simulation_config.json')
        if not os.path.exists(config_path):
            continue
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            sim_id = data.get('simulation_id', sim_dir)
            db.save_simulation(sim_id, data)
            count += 1
            print(f"  ✓ Simulation {sim_id}: project {data.get('project_id', 'unknown')}")
        except Exception as e:
            print(f"  ✗ Error migrating simulation {sim_dir}: {e}")

    return count


def main():
    parser = argparse.ArgumentParser(description='Migrate JSON data to SQLite')
    parser.add_argument('--db-path', help='Override SQLite database path')
    args = parser.parse_args()

    if args.db_path:
        os.environ['SQLITE_PATH'] = args.db_path

    db = DatabaseManager()
    db.init_app()

    uploads_dir = Config.UPLOAD_FOLDER
    print(f"Uploads directory: {uploads_dir}")
    print(f"SQLite database: {os.environ['SQLITE_PATH']}")
    print()

    sections = [
        ("Projects", migrate_projects),
        ("Tasks", migrate_tasks),
        ("Reports", migrate_reports),
        ("Survey Results", migrate_survey_results),
        ("Simulations", migrate_simulations),
    ]

    totals = {}
    for name, func in sections:
        print(f"[{name}]")
        totals[name] = func(db, uploads_dir)
        print()

    print("=" * 50)
    print("Migration Summary:")
    for name, count in totals.items():
        print(f"  {name}: {count} records migrated")
    print(f"  Total: {sum(totals.values())} records")
    print("=" * 50)

    db.close()


if __name__ == '__main__':
    main()
