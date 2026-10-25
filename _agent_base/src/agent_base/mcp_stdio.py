"""Stdio MCP servers for the agents, one exec per request.

Dagger v1.0.0-beta.21 hangs on the second step of an LLM loop that has an MCP
server (`LLM.with_mcp_server`): the engine dials the server again for each
step and gets back the already-running service, without its stdin and stdout
attached, so `initialize` is never answered. Until that is fixed, an agent
lists each server's tools in its system prompt and calls them through its own
`mcp` tool, which runs a small driver in the server's container: it starts
the server, sends `initialize` and one request, and prints the answer.

Set ENGINE_MCP to True to go back to `LLM.with_mcp_server` once the engine
keeps MCP sessions across steps.
"""

import json
import uuid
from dataclasses import dataclass

import dagger

ENGINE_MCP = False

_DRIVER_PATH = "/tmp/dagger_agent_mcp_driver.py"
_TIMEOUT_SECONDS = 120
_MAX_DESCRIPTION_CHARS = 300

# Runs in the server's container: Python 3 with the standard library only.
_DRIVER = r'''
import json, subprocess, sys, threading

command, method, params, timeout = json.loads(sys.argv[1]), sys.argv[2], json.loads(sys.argv[3]), float(sys.argv[4])
server = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True, bufsize=1)
timer = threading.Timer(timeout, server.kill)
timer.daemon = True
timer.start()


def send(message):
    server.stdin.write(json.dumps(message) + "\n")
    server.stdin.flush()


def receive(request_id):
    for line in server.stdout:
        try:
            message = json.loads(line)
        except ValueError:
            continue  # a server may log on stdout
        if isinstance(message, dict) and message.get("id") == request_id:
            return message
    sys.exit("MCP server exited before answering request %s" % request_id)


send({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {
    "protocolVersion": "2025-06-18", "capabilities": {},
    "clientInfo": {"name": "dagger-agent", "version": "1.0"}}})
receive(1)
send({"jsonrpc": "2.0", "method": "notifications/initialized"})
send({"jsonrpc": "2.0", "id": 2, "method": method, "params": params})
response = receive(2)
server.kill()
print(json.dumps(response))
'''


@dataclass
class McpServer:
    """A stdio MCP server: the container it runs in, with Python 3, and its command."""

    name: str
    container: dagger.Container
    command: list[str]
    # Calls read live state (cloud resources, the engine): never reuse a cached answer
    live: bool = False
    # Whether the server may call the Dagger engine (dagger-mcp needs it)
    dagger_access: bool = False

    def service(self) -> dagger.Service:
        """The server as a Dagger service, for LLM.with_mcp_server."""
        return self.container.with_default_args(self.command).as_service(
            disable_dagger_in_dagger=not self.dagger_access,
        )


async def _request(server: McpServer, method: str, params: dict, live: bool = False) -> dict:
    ctr = server.container.with_new_file(_DRIVER_PATH, _DRIVER)
    if live:
        ctr = ctr.with_env_variable("DAGGER_AGENT_MCP_CALL", str(uuid.uuid4()))
    out = await ctr.with_exec(
        ["python3", _DRIVER_PATH, json.dumps(server.command), method, json.dumps(params), str(_TIMEOUT_SECONDS)],
        disable_dagger_in_dagger=not server.dagger_access,
    ).stdout()
    response = json.loads(out)
    if response.get("error"):
        error = response["error"]
        message = error.get("message", error) if isinstance(error, dict) else error
        raise RuntimeError(f"MCP server {server.name!r}: {message}")
    return response.get("result") or {}


def _summary(text: str) -> str:
    text = " ".join((text or "").split())
    if len(text) > _MAX_DESCRIPTION_CHARS:
        text = text[:_MAX_DESCRIPTION_CHARS].rstrip() + "…"
    return text


async def catalog(servers: list[McpServer]) -> str:
    """A system-prompt section listing the servers' tools and how to call them."""
    if not servers:
        return ""
    sections = []
    for server in servers:
        try:
            result = await _request(server, "tools/list", {})
        except Exception as exc:  # a broken server must not break the agent
            sections.append(f"### `{server.name}`\n\nUnavailable: {_summary(str(exc))}")
            continue
        lines = []
        for tool in result.get("tools") or []:
            properties = (tool.get("inputSchema") or {}).get("properties") or {}
            arguments = ", ".join(sorted(properties)) or "no arguments"
            lines.append(f"- `{tool.get('name')}` ({arguments}): {_summary(tool.get('description', ''))}")
        sections.append(f"### `{server.name}`\n\n" + ("\n".join(lines) or "No tools."))
    return (
        "\n\n## MCP Servers\n\n"
        "Call these tools with `mcp(server, tool, arguments)`, where `arguments` is a JSON "
        "object holding the tool's arguments.\n\n" + "\n\n".join(sections)
    )


async def call(server: McpServer, tool: str, arguments: str) -> str:
    """Call one tool of an MCP server and return its text content."""
    try:
        args = json.loads(arguments) if arguments.strip() else {}
    except ValueError as exc:
        raise ValueError(f"arguments must be a JSON object: {exc}") from exc
    if not isinstance(args, dict):
        raise ValueError("arguments must be a JSON object")
    result = await _request(server, "tools/call", {"name": tool, "arguments": args}, live=server.live)
    texts = [part.get("text", "") for part in result.get("content") or [] if part.get("type") == "text"]
    text = "\n".join(t for t in texts if t) or json.dumps(result)
    if result.get("isError"):
        raise RuntimeError(text)
    return text


async def attach(llm: dagger.LLM, servers: list[McpServer]) -> tuple[dagger.LLM, str]:
    """Give an LLM its MCP servers: engine sessions, or the catalog for the `mcp` tool.

    Returns the LLM and the system-prompt text to append.
    """
    if ENGINE_MCP:
        for server in servers:
            llm = llm.with_mcp_server(server.name, server.service())
        return llm, ""
    return llm, await catalog(servers)


def blocked_tools(servers: list[McpServer]) -> list[str]:
    """Tools to hide: the `mcp` tool when there is no server to call through it."""
    return [] if servers and not ENGINE_MCP else ["mcp"]
