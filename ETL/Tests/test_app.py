from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app import app, tasks, TaskStatus, _run_seeder


@pytest.fixture(autouse=True)
def clear_tasks():
    """Reset task store before each test."""
    tasks.clear()
    yield
    tasks.clear()


client = TestClient(app)


# ── Health check ────────────────────────────────────────


@patch("app.Redis")
@patch("app.MongoClient")
@patch("app.RedisDBConfig")
@patch("app.MongoDBConfig")
def test_health_all_ok(mock_mg_cnf, mock_rd_cnf, mock_mongo, mock_redis):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "mongo": "ok", "redis": "ok"}


@patch("app.Redis")
@patch("app.MongoClient", side_effect=Exception("connection refused"))
@patch("app.RedisDBConfig")
@patch("app.MongoDBConfig")
def test_health_mongo_down(mock_mg_cnf, mock_rd_cnf, mock_mongo, mock_redis):
    data = client.get("/health").json()
    assert data["status"] == "degraded"
    assert data["mongo"] == "unreachable"
    assert data["redis"] == "ok"


@patch("app.Redis")
@patch("app.MongoClient")
@patch("app.RedisDBConfig", side_effect=Exception("connection refused"))
@patch("app.MongoDBConfig")
def test_health_redis_down(mock_mg_cnf, mock_rd_cnf, mock_mongo, mock_redis):
    data = client.get("/health").json()
    assert data["status"] == "degraded"
    assert data["mongo"] == "ok"
    assert data["redis"] == "unreachable"


@patch("app.Redis")
@patch("app.MongoClient", side_effect=Exception("mongo down"))
@patch("app.RedisDBConfig", side_effect=Exception("redis down"))
@patch("app.MongoDBConfig")
def test_health_both_down(mock_mg_cnf, mock_rd_cnf, mock_mongo, mock_redis):
    data = client.get("/health").json()
    assert data["status"] == "degraded"
    assert data["mongo"] == "unreachable"
    assert data["redis"] == "unreachable"


# ── POST /seed ──────────────────────────────────────────


@patch("app.MainSeeder")
@patch("app.Thread")
def test_seed_starts_task(mock_thread, mock_seeder):
    response = client.post("/seed")
    data = response.json()
    assert response.status_code == 200
    assert data["status"] == "ongoing"
    assert "task_id" in data
    mock_thread.return_value.start.assert_called_once()


@patch("app.MainSeeder")
@patch("app.Thread")
def test_seed_no_duplicate(mock_thread, mock_seeder):
    first = client.post("/seed").json()
    second = client.post("/seed").json()
    assert first["task_id"] == second["task_id"]
    assert mock_thread.return_value.start.call_count == 1


@patch("app.MainSeeder")
@patch("app.Thread")
def test_seed_allows_new_after_finished(mock_thread, mock_seeder):
    first = client.post("/seed").json()
    tasks[first["task_id"]] = TaskStatus.FINISHED

    second = client.post("/seed").json()
    assert second["task_id"] != first["task_id"]
    assert mock_thread.return_value.start.call_count == 2


@patch("app.MainSeeder")
@patch("app.Thread")
def test_seed_allows_new_after_failed(mock_thread, mock_seeder):
    first = client.post("/seed").json()
    tasks[first["task_id"]] = TaskStatus.FAILED

    second = client.post("/seed").json()
    assert second["task_id"] != first["task_id"]


# ── GET /seed/status ────────────────────────────────────


def test_status_ongoing():
    tasks["abc123"] = TaskStatus.ONGOING
    data = client.get("/seed/status/abc123").json()
    assert data == {"task_id": "abc123", "status": "ongoing"}


def test_status_finished():
    tasks["abc123"] = TaskStatus.FINISHED
    data = client.get("/seed/status/abc123").json()
    assert data == {"task_id": "abc123", "status": "finished"}


def test_status_failed():
    tasks["abc123"] = TaskStatus.FAILED
    data = client.get("/seed/status/abc123").json()
    assert data == {"task_id": "abc123", "status": "failed"}


def test_status_unknown_task():
    response = client.get("/seed/status/nonexistent")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


# ── _run_seeder background logic ────────────────────────


@patch("app.log_etl")
@patch("app.MainSeeder")
def test_run_seeder_success(mock_seeder_cls, mock_log):
    tasks["t1"] = TaskStatus.ONGOING
    _run_seeder("t1")

    instance = mock_seeder_cls.return_value
    instance.run_seeder.assert_called_once()
    instance.run_upsert.assert_called_once()
    assert tasks["t1"] == TaskStatus.FINISHED


@patch("app.LogException")
@patch("app.log_etl")
@patch("app.MainSeeder")
def test_run_seeder_init_fails(mock_seeder_cls, mock_log, mock_log_exc):
    mock_seeder_cls.side_effect = Exception("init failed")
    tasks["t2"] = TaskStatus.ONGOING
    _run_seeder("t2")
    assert tasks["t2"] == TaskStatus.FAILED


@patch("app.LogException")
@patch("app.log_etl")
@patch("app.MainSeeder")
def test_run_seeder_run_seeder_fails(mock_seeder_cls, mock_log, mock_log_exc):
    mock_seeder_cls.return_value.run_seeder.side_effect = Exception("seeder failed")
    tasks["t3"] = TaskStatus.ONGOING
    _run_seeder("t3")
    assert tasks["t3"] == TaskStatus.FAILED


@patch("app.LogException")
@patch("app.log_etl")
@patch("app.MainSeeder")
def test_run_seeder_upsert_fails(mock_seeder_cls, mock_log, mock_log_exc):
    mock_seeder_cls.return_value.run_upsert.side_effect = Exception("upsert failed")
    tasks["t4"] = TaskStatus.ONGOING
    _run_seeder("t4")
    assert tasks["t4"] == TaskStatus.FAILED
