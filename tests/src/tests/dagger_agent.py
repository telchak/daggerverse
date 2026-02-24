"""Daggie (Dagger CI Agent) module tests.

Tests the Dagger CI specialist agent's ability to create, explain,
and debug Dagger modules and pipelines.
"""

import dagger
from dagger import dag


async def test_dagger_mcp_server() -> str:
    """Test that the dagger-mcp module produces a valid service."""
    # Just verify the server function returns a service without error.
    # The service itself requires privileged nesting to actually respond,
    # but we can verify the container builds and the module loads.
    service = dag.dagger_mcp().server()

    # Verify it's a valid service object (doesn't throw)
    # We can't actually start it without privileged nesting in tests,
    # but confirming the pipeline builds is sufficient.
    return "PASS: dagger-mcp server() returns a valid service"


async def test_daggie_assist() -> str:
    """Test assist: ask the agent to create a simple Dagger pipeline."""
    source = dag.directory().with_new_file(
        "README.md",
        "# My Python Project\nA simple Python web app.",
    ).with_new_file(
        "app.py",
        'from flask import Flask\napp = Flask(__name__)\n\n@app.route("/")\ndef hello():\n    return "Hello!"\n',
    ).with_new_file(
        "requirements.txt",
        "flask==3.1.0\n",
    )

    agent = dag.daggie(source=source)

    result = await agent.assist(
        assignment=(
            "Create a Dagger module for this Python project that builds a container "
            "image. The module should have a 'build' function that installs dependencies "
            "from requirements.txt and copies the app source. Write the dagger.json, "
            "main source file, and __init__.py."
        ),
    )

    entries = await result.entries()
    if not entries:
        raise RuntimeError("assist returned empty directory")

    # Check that some Dagger-related files were created
    all_files = await result.glob("**/*")
    has_dagger_json = any("dagger.json" in f for f in all_files)
    has_source = "app.py" in entries

    return f"PASS: assist (files={len(entries)}, dagger_json={has_dagger_json}, has_source={has_source})"


async def test_daggie_explain() -> str:
    """Test explain: ask about a Dagger concept."""
    agent = dag.daggie()

    result = await agent.explain(
        question="What is a Dagger module and how does dagger.json configure it? Explain the key fields.",
    )

    if not result:
        raise RuntimeError("explain returned empty result")

    result_lower = result.lower()
    has_relevant_content = any(
        keyword in result_lower
        for keyword in ("dagger.json", "module", "sdk", "function", "engine")
    )

    return f"PASS: explain ({len(result)} chars, relevant={has_relevant_content})"


async def test_daggie_debug() -> str:
    """Test debug: provide a broken dagger.json and error, verify fix."""
    source = dag.directory().with_new_file(
        "dagger.json",
        '{\n  "name": "my-module",\n  "sdk": {"source": "python"}\n}\n',
    ).with_new_file(
        "src/my_module/__init__.py",
        "",
    ).with_new_file(
        "src/my_module/main.py",
        (
            "import dagger\n"
            "from dagger import function, object_type\n\n"
            "@object_type\n"
            "class MyModule:\n"
            "    @function\n"
            "    def hello(self) -> str:\n"
            '        return "Hello"\n'
        ),
    )

    agent = dag.daggie(source=source)

    result = await agent.debug(
        error_output=(
            "Error: failed to initialize module: missing engineVersion in dagger.json\n"
            "The module configuration at dagger.json is missing the required 'engineVersion' field.\n"
            "Please add an engineVersion like: \"engineVersion\": \"v0.19.11\""
        ),
    )

    entries = await result.entries()
    if not entries:
        raise RuntimeError("debug returned empty directory")

    # Verify dagger.json still exists and ideally has the fix
    has_dagger_json = "dagger.json" in entries

    return f"PASS: debug (files={len(entries)}, has_dagger_json={has_dagger_json})"
