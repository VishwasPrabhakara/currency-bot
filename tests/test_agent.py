import sys
from pathlib import Path

from currency_agent import root_agent


def test_agent_registers_mcp_toolset():
    assert root_agent.name == "currency_agent"
    assert len(root_agent.tools) == 1


def test_agent_uses_current_python_for_mcp_subprocess():
    toolset = root_agent.tools[0]
    command = toolset._connection_params.server_params.command

    assert command == sys.executable


def test_cloud_run_agent_declares_mcp_dependency():
    requirements = (
        Path(__file__).parents[1]
        / "agents"
        / "currency_agent"
        / "requirements.txt"
    ).read_text(encoding="utf-8")

    assert "google-adk==2.2.0" in requirements
    assert "mcp==1.27.2" in requirements
