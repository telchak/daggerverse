"""Python Build Module - Build, lint, test, and typecheck Python applications."""

from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type


@object_type
class PythonBuild:
    """Python build, lint, test, and typecheck utilities for Dagger pipelines."""

    def _base_container(
        self,
        source: dagger.Directory,
        python_version: str = "3.13",
    ) -> dagger.Container:
        """Create a container with Python, uv, and source mounted."""
        return (
            dag.container()
            .from_(f"python:{python_version}-slim")
            .with_exec(["pip", "install", "--no-cache-dir", "uv"])
            .with_directory("/app", source)
            .with_workdir("/app")
        )

    @function
    async def build(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Python project source directory")],
        command: Annotated[str, Doc("Custom build command (auto-detects if empty)")] = "",
        python_version: Annotated[str, Doc("Python version")] = "3.13",
    ) -> dagger.Directory:
        """Build a Python project and return the source with dist/.

        Auto-detects the build system or runs a custom command.
        Defaults to `python -m build` if no build command is specified.
        """
        container = self._base_container(source, python_version)

        # Install dependencies first
        container = await self._install_deps(container, source)

        if command:
            build_cmd = command
        else:
            build_cmd = "uv pip install build && python -m build"

        result = await (
            container
            .with_exec(["sh", "-c", build_cmd], expect=dagger.ExecExpect.ANY)
            .sync()
        )

        exit_code = await result.exit_code()
        if exit_code != 0:
            stderr = await result.stderr()
            stdout = await result.stdout()
            raise RuntimeError(
                f"Build failed (exit code {exit_code}):\n{stdout}\n{stderr}"
            )

        return result.directory("/app")

    @function
    async def lint(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Python project source directory")],
        tool: Annotated[str, Doc("Lint tool to use: 'ruff', 'flake8', 'pylint'")] = "ruff",
        fix: Annotated[bool, Doc("Automatically fix lint errors (ruff only)")] = False,
        python_version: Annotated[str, Doc("Python version")] = "3.13",
    ) -> str:
        """Lint a Python project.

        Returns the lint output.
        """
        container = self._base_container(source, python_version)

        if tool == "ruff":
            install_cmd = "uv pip install ruff"
            lint_cmd = "ruff check --fix ." if fix else "ruff check ."
        elif tool == "flake8":
            install_cmd = "uv pip install flake8"
            lint_cmd = "flake8 ."
        elif tool == "pylint":
            install_cmd = "uv pip install pylint"
            lint_cmd = "pylint --recursive=y ."
        else:
            raise ValueError(f"Unsupported lint tool: {tool}. Use 'ruff', 'flake8', or 'pylint'.")

        result = await (
            container
            .with_exec(["sh", "-c", install_cmd])
            .with_exec(["sh", "-c", lint_cmd], expect=dagger.ExecExpect.ANY)
            .sync()
        )

        stdout = await result.stdout()
        stderr = await result.stderr()
        return f"{stdout}\n{stderr}".strip()

    @function
    async def test(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Python project source directory")],
        command: Annotated[str, Doc("Custom test command (auto-detects if empty)")] = "",
        python_version: Annotated[str, Doc("Python version")] = "3.13",
    ) -> str:
        """Run tests for a Python project.

        Auto-detects pytest or unittest, or runs a custom command.
        Returns the test output.
        """
        container = self._base_container(source, python_version)
        container = await self._install_deps(container, source)

        if command:
            test_cmd = command
        else:
            # Auto-detect: check if pytest is available
            test_cmd = (
                "python -m pytest -v 2>/dev/null || "
                "python -m unittest discover -v 2>/dev/null || "
                "echo 'No test framework detected'"
            )

        result = await (
            container
            .with_exec(["sh", "-c", test_cmd], expect=dagger.ExecExpect.ANY)
            .sync()
        )

        stdout = await result.stdout()
        stderr = await result.stderr()
        return f"{stdout}\n{stderr}".strip()

    @function
    async def typecheck(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Python project source directory")],
        tool: Annotated[str, Doc("Type checker to use: 'mypy', 'pyright'")] = "mypy",
        python_version: Annotated[str, Doc("Python version")] = "3.13",
    ) -> str:
        """Type-check a Python project.

        Returns the type checker output.
        """
        container = self._base_container(source, python_version)
        container = await self._install_deps(container, source)

        if tool == "mypy":
            install_cmd = "uv pip install mypy"
            check_cmd = "python -m mypy ."
        elif tool == "pyright":
            install_cmd = "uv pip install pyright"
            check_cmd = "python -m pyright ."
        else:
            raise ValueError(f"Unsupported typecheck tool: {tool}. Use 'mypy' or 'pyright'.")

        result = await (
            container
            .with_exec(["sh", "-c", install_cmd])
            .with_exec(["sh", "-c", check_cmd], expect=dagger.ExecExpect.ANY)
            .sync()
        )

        stdout = await result.stdout()
        stderr = await result.stderr()
        return f"{stdout}\n{stderr}".strip()

    @function
    async def install(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Python project source directory")],
        python_version: Annotated[str, Doc("Python version")] = "3.13",
    ) -> dagger.Directory:
        """Install Python project dependencies.

        Auto-detects the package manager (pyproject.toml, requirements.txt, setup.py)
        and installs dependencies. Returns the source directory with deps installed.
        """
        container = self._base_container(source, python_version)
        container = await self._install_deps(container, source)
        return container.directory("/app")

    async def _install_deps(
        self,
        container: dagger.Container,
        source: dagger.Directory,
    ) -> dagger.Container:
        """Auto-detect and install project dependencies."""
        entries = await source.entries()

        if "pyproject.toml" in entries:
            return container.with_exec(
                ["sh", "-c", "uv pip install -e '.[dev]' 2>/dev/null || uv pip install -e . 2>/dev/null || true"],
            )
        elif "requirements.txt" in entries:
            return container.with_exec(
                ["sh", "-c", "uv pip install -r requirements.txt"],
            )
        elif "setup.py" in entries:
            return container.with_exec(
                ["sh", "-c", "uv pip install -e . 2>/dev/null || true"],
            )

        return container
