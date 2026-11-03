"""Python Build Module - Build, lint, test, and typecheck Python applications."""

from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, check, dag, function, object_type

# What the checks never read from the workspace: environments, caches and build output
_WORKSPACE_EXCLUDE = [
    ".venv/", "**/__pycache__/", ".git/", "dist/", "build/",
    ".mypy_cache/", ".pytest_cache/", ".ruff_cache/",
]


@object_type
class PythonBuild:
    """Python build, lint, test, and typecheck utilities for Dagger pipelines.

    Installed in a workspace, its checks lint, test, type-check and build the
    workspace's Python project with `dagger check`.
    """

    # Settings of the checks. The checks take the workspace as an argument,
    # which Dagger injects for `dagger check`: an injected workspace on the
    # constructor would fail every call from another module, which has to pass
    # a workspace explicitly.
    path: Annotated[str, Doc("Path of the Python project in the workspace, for the checks")] = "."
    python_version: Annotated[str, Doc("Python version for the checks")] = "3.13"

    def _workspace_project(self, ws: dagger.Workspace) -> dagger.Directory:
        return ws.directory(self.path, exclude=_WORKSPACE_EXCLUDE)

    async def _check_container(self, ws: dagger.Workspace) -> dagger.Container:
        """The workspace's project with its dependencies installed, for the checks."""
        project = self._workspace_project(ws)
        return await self._install_deps(self._base_container(project, self.python_version), project)

    @function
    @check
    async def check_lint(self, ws: dagger.Workspace) -> None:
        """Check that the workspace's Python project passes ruff check."""
        ctr = self._base_container(self._workspace_project(ws), self.python_version)
        await ctr.with_exec(["sh", "-c", "uv pip install --system ruff && ruff check ."]).sync()

    @function
    @check
    async def check_test(self, ws: dagger.Workspace) -> None:
        """Check that the workspace's Python project passes its tests (pytest)."""
        ctr = await self._check_container(ws)
        await ctr.with_exec(["sh", "-c", "python -m pytest --version >/dev/null 2>&1 || uv pip install --system pytest; python -m pytest"]).sync()

    @function
    @check
    async def check_typecheck(self, ws: dagger.Workspace) -> None:
        """Check that the workspace's Python project passes mypy."""
        ctr = await self._check_container(ws)
        await ctr.with_exec(["sh", "-c", "uv pip install --system mypy && python -m mypy ."]).sync()

    @function
    @check
    async def check_build(self, ws: dagger.Workspace) -> None:
        """Check that the workspace's Python project builds (python -m build)."""
        await self.build(self._workspace_project(ws), python_version=self.python_version)

    def _base_container(
        self,
        source: dagger.Directory,
        python_version: str = "3.13",
        pip_cache: dagger.CacheVolume | None = None,
        uv_cache: dagger.CacheVolume | None = None,
    ) -> dagger.Container:
        """Create a container with Python, uv, and source mounted.

        Mounts pip and uv cache volumes by default to speed up repeated installs.
        """
        _pip_cache = pip_cache or dag.cache_volume("python-pip")
        _uv_cache = uv_cache or dag.cache_volume("python-uv")
        return (
            dag.container()
            .from_(f"python:{python_version}-slim")
            .with_mounted_cache("/root/.cache/pip", _pip_cache)
            .with_mounted_cache("/root/.cache/uv", _uv_cache)
            .with_exec(["pip", "install", "uv"])
            .with_directory("/app", source)
            .with_workdir("/app")
        )

    @function
    async def build(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Python project source directory")],
        command: Annotated[str, Doc("Custom build command (auto-detects if empty)")] = "",
        python_version: Annotated[str, Doc("Python version")] = "3.13",
        pip_cache: Annotated[dagger.CacheVolume | None, Doc("Custom pip cache volume (uses default if not provided)")] = None,
        uv_cache: Annotated[dagger.CacheVolume | None, Doc("Custom uv cache volume (uses default if not provided)")] = None,
    ) -> dagger.Directory:
        """Build a Python project and return the source with dist/.

        Auto-detects the build system or runs a custom command.
        Defaults to `python -m build` if no build command is specified.
        """
        container = self._base_container(source, python_version, pip_cache, uv_cache)

        # Install dependencies first
        container = await self._install_deps(container, source)

        if command:
            build_cmd = command
        else:
            build_cmd = "uv pip install --system build && python -m build"

        result = await (
            container
            .with_exec(["sh", "-c", build_cmd], expect=dagger.ReturnType.ANY)
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
        pip_cache: Annotated[dagger.CacheVolume | None, Doc("Custom pip cache volume (uses default if not provided)")] = None,
        uv_cache: Annotated[dagger.CacheVolume | None, Doc("Custom uv cache volume (uses default if not provided)")] = None,
    ) -> str:
        """Lint a Python project.

        Returns the lint output.
        """
        container = self._base_container(source, python_version, pip_cache, uv_cache)

        if tool == "ruff":
            install_cmd = "uv pip install --system ruff"
            lint_cmd = "ruff check --fix ." if fix else "ruff check ."
        elif tool == "flake8":
            install_cmd = "uv pip install --system flake8"
            lint_cmd = "flake8 ."
        elif tool == "pylint":
            install_cmd = "uv pip install --system pylint"
            lint_cmd = "pylint --recursive=y ."
        else:
            raise ValueError(f"Unsupported lint tool: {tool}. Use 'ruff', 'flake8', or 'pylint'.")

        result = await (
            container
            .with_exec(["sh", "-c", install_cmd])
            .with_exec(["sh", "-c", lint_cmd], expect=dagger.ReturnType.ANY)
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
        pip_cache: Annotated[dagger.CacheVolume | None, Doc("Custom pip cache volume (uses default if not provided)")] = None,
        uv_cache: Annotated[dagger.CacheVolume | None, Doc("Custom uv cache volume (uses default if not provided)")] = None,
    ) -> str:
        """Run tests for a Python project.

        Auto-detects pytest or unittest, or runs a custom command.
        Returns the test output.
        """
        container = self._base_container(source, python_version, pip_cache, uv_cache)
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
            .with_exec(["sh", "-c", test_cmd], expect=dagger.ReturnType.ANY)
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
        pip_cache: Annotated[dagger.CacheVolume | None, Doc("Custom pip cache volume (uses default if not provided)")] = None,
        uv_cache: Annotated[dagger.CacheVolume | None, Doc("Custom uv cache volume (uses default if not provided)")] = None,
    ) -> str:
        """Type-check a Python project.

        Returns the type checker output.
        """
        container = self._base_container(source, python_version, pip_cache, uv_cache)
        container = await self._install_deps(container, source)

        if tool == "mypy":
            install_cmd = "uv pip install --system mypy"
            check_cmd = "python -m mypy ."
        elif tool == "pyright":
            install_cmd = "uv pip install --system pyright"
            check_cmd = "python -m pyright ."
        else:
            raise ValueError(f"Unsupported typecheck tool: {tool}. Use 'mypy' or 'pyright'.")

        result = await (
            container
            .with_exec(["sh", "-c", install_cmd])
            .with_exec(["sh", "-c", check_cmd], expect=dagger.ReturnType.ANY)
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
        pip_cache: Annotated[dagger.CacheVolume | None, Doc("Custom pip cache volume (uses default if not provided)")] = None,
        uv_cache: Annotated[dagger.CacheVolume | None, Doc("Custom uv cache volume (uses default if not provided)")] = None,
    ) -> dagger.Directory:
        """Install Python project dependencies.

        Auto-detects the package manager (pyproject.toml, requirements.txt, setup.py)
        and installs dependencies. Returns the source directory with deps installed.
        """
        container = self._base_container(source, python_version, pip_cache, uv_cache)
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
                ["sh", "-c", "uv pip install --system -e '.[dev]' 2>/dev/null || uv pip install --system -e . 2>/dev/null || true"],
            )
        elif "requirements.txt" in entries:
            return container.with_exec(
                ["sh", "-c", "uv pip install --system -r requirements.txt"],
            )
        elif "setup.py" in entries:
            return container.with_exec(
                ["sh", "-c", "uv pip install --system -e . 2>/dev/null || true"],
            )

        return container
