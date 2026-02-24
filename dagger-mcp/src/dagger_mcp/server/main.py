"""MCP server for Dagger engine introspection.

Runs inside a privileged-nested container with access to the Dagger engine
via DAGGER_SESSION_PORT and DAGGER_SESSION_TOKEN environment variables.
"""

import json
import os
from pathlib import Path

import httpx
from mcp.server.fastmcp import FastMCP

from sdl_renderer import render_sdl

mcp = FastMCP("Dagger")

KNOWLEDGE_DIR = Path(__file__).parent / "knowledge"


def _gql(query: str, variables: dict | None = None) -> dict:
    """Execute a GraphQL query against the Dagger engine."""
    port = os.environ["DAGGER_SESSION_PORT"]
    token = os.environ["DAGGER_SESSION_TOKEN"]
    resp = httpx.post(
        f"http://127.0.0.1:{port}/query",
        json={"query": query, "variables": variables or {}},
        auth=(token, ""),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


@mcp.tool()
def dagger_version() -> str:
    """Get the Dagger engine version."""
    result = _gql("{ version }")
    if "errors" in result:
        return f"Error: {json.dumps(result['errors'])}"
    return result["data"]["version"]


@mcp.tool()
def learn_schema(type_name: str) -> str:
    """Introspect a Dagger GraphQL schema type and return its SDL definition.

    Start with "Query" to see the top-level API, then drill into specific
    types like "Container", "Directory", "File", "Service", etc.
    """
    query = """
    query IntrospectType($name: String!) {
      __type(name: $name) {
        kind
        name
        description
        fields(includeDeprecated: true) {
          name
          description
          isDeprecated
          deprecationReason
          args {
            name
            description
            type { ...TypeRef }
            defaultValue
          }
          type { ...TypeRef }
        }
        inputFields {
          name
          description
          type { ...TypeRef }
          defaultValue
        }
        enumValues(includeDeprecated: true) {
          name
          description
          isDeprecated
          deprecationReason
        }
        interfaces { name }
        possibleTypes { name }
      }
    }

    fragment TypeRef on __Type {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
            }
          }
        }
      }
    }
    """
    result = _gql(query, {"name": type_name})
    if "errors" in result:
        return f"Error: {json.dumps(result['errors'])}"

    type_data = result.get("data", {}).get("__type")
    if not type_data:
        return f"Type '{type_name}' not found in the schema."

    return render_sdl(type_data)


@mcp.tool()
def run_query(query: str) -> str:
    """Execute a GraphQL query against the Dagger engine and return the result.

    Use learn_schema first to understand the available types and fields.
    Example: '{ container { from(address: "alpine:3.20") { withExec(args: ["echo", "hi"]) { stdout } } } }'
    """
    result = _gql(query)
    return json.dumps(result, indent=2)


@mcp.tool()
def learn_sdk(sdk: str) -> str:
    """Get SDK-specific guidance for translating GraphQL API to SDK code.

    Supported SDKs: python, typescript, go
    """
    sdk = sdk.lower().strip()
    sdk_map = {
        "python": "python_sdk.md",
        "py": "python_sdk.md",
        "typescript": "typescript_sdk.md",
        "ts": "typescript_sdk.md",
        "go": "go_sdk.md",
        "golang": "go_sdk.md",
    }

    filename = sdk_map.get(sdk)
    if not filename:
        return f"Unknown SDK '{sdk}'. Supported: python, typescript, go"

    path = KNOWLEDGE_DIR / filename
    if not path.exists():
        return f"Knowledge file not found for '{sdk}'."

    return path.read_text()


if __name__ == "__main__":
    mcp.run(transport="stdio")
