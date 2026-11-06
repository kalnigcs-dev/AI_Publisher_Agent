import pytest
from publisher_mcp.server import ping, get_system_status


def test_ping():
    assert ping() == "pong"


def test_system_status():
    status = get_system_status()
    assert status["status"] == "online"
    assert status["service"] == "ai-publisher-mcp"
    assert "version" in status
    assert "python_version" in status
