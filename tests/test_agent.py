import sys

from currency_agent import root_agent


def test_agent_registers_mcp_toolset():
    assert root_agent.name == "currency_agent"
    assert len(root_agent.tools) == 1


def test_agent_uses_current_python_for_mcp_subprocess():
    toolset = root_agent.tools[0]
    command = toolset._connection_params.server_params.command

    assert command == sys.executable
