"""
MCP server for Dagger engine introspection — learn schema, run GraphQL queries, and get SDK guidance.

Provides a Model Context Protocol (MCP) server that enables AI agents to explore the Dagger API schema,
execute GraphQL queries against the live engine, and translate patterns into SDK-specific code.
"""

from .main import DaggerMcp

__all__ = ["DaggerMcp"]
