"""Tests for DatabaseManager."""
import os
import json
import pytest
from app.utils.database import DatabaseManager


def _fresh_db():
    db = DatabaseManager()
    db._initialized = False
    db.init_app()
    return db


class TestDatabaseManager:
    def test_save_and_get_project(self):
        db = _fresh_db()
        project_id = "test-proj-1"
        data = {"name": "Test Project", "sim_type": "academic", "status": "running"}
        db.save_project(project_id, data)
        result = db.get_project(project_id)
        assert result is not None
        assert result["id"] == project_id
        assert result["name"] == "Test Project"
        assert result["sim_type"] == "academic"
        assert result["status"] == "running"

    def test_get_project_not_found(self):
        db = _fresh_db()
        assert db.get_project("nonexistent") is None

    def test_delete_project(self):
        db = _fresh_db()
        project_id = "test-proj-del"
        db.save_project(project_id, {"name": "To Delete"})
        assert db.get_project(project_id) is not None
        db.delete_project(project_id)
        assert db.get_project(project_id) is None

    def test_list_projects(self):
        db = _fresh_db()
        db.save_project("p1", {"name": "Alpha", "sim_type": "academic"})
        db.save_project("p2", {"name": "Beta", "sim_type": "political"})
        projects = db.list_projects()
        ids = [p["id"] for p in projects]
        assert "p1" in ids
        assert "p2" in ids

    def test_list_projects_empty(self):
        db = _fresh_db()
        db.conn.execute("DELETE FROM projects")
        db.conn.commit()
        assert db.list_projects() == []

    def test_update_project_overwrites(self):
        db = _fresh_db()
        db.save_project("p1", {"name": "Original", "status": "pending"})
        db.save_project("p1", {"name": "Updated", "status": "completed"})
        result = db.get_project("p1")
        assert result["name"] == "Updated"
        assert result["status"] == "completed"

    def test_singleton_pattern(self):
        db1 = DatabaseManager()
        db2 = DatabaseManager()
        assert db1 is db2

    def test_project_data_merges_with_columns(self):
        db = _fresh_db()
        extra = {"custom_field": "hello", "nested": {"a": 1}}
        db.save_project("p-extra", {"name": "Extra", **extra})
        result = db.get_project("p-extra")
        assert result["custom_field"] == "hello"
        assert result["nested"] == {"a": 1}
        assert result["name"] == "Extra"
