"""Angular Module - Build, lint, test, and serve Angular applications."""

import json
from typing import Annotated

import dagger
from dagger import DefaultPath, Doc, dag, function, object_type


@object_type
class Angular:
    """Angular build, lint, test, and serve utilities for Dagger pipelines."""

    def _base_container(
        self,
        source: dagger.Directory,
        node_version: str = "22",
        npm_cache: dagger.CacheVolume | None = None,
    ) -> dagger.Container:
        """Create a container with Node.js, Angular CLI, and dependencies installed.

        Mounts an npm cache volume by default to speed up repeated installs.
        """
        cache = npm_cache or dag.cache_volume("angular-npm")
        return (
            dag.container()
            .from_(f"node:{node_version}-slim")
            .with_mounted_cache("/root/.npm", cache)
            .with_exec(["npm", "install", "-g", "@angular/cli"])
            .with_directory("/app", source)
            .with_workdir("/app")
            .with_exec(["sh", "-c", "npm ci --prefer-offline 2>/dev/null || npm install --prefer-offline"])
        )

    @function
    async def build(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Angular project source directory")],
        configuration: Annotated[str, Doc("Build configuration (e.g. 'production', 'development')")] = "production",
        output_path: Annotated[str, Doc("Custom output path (auto-detected from angular.json if empty)")] = "",
        node_version: Annotated[str, Doc("Node.js version")] = "22",
        npm_cache: Annotated[dagger.CacheVolume | None, Doc("Custom npm cache volume (uses default if not provided)")] = None,
    ) -> dagger.Directory:
        """Build an Angular project and return the dist directory.

        Runs `ng build` with the specified configuration. Auto-detects the
        output path from angular.json if not explicitly provided.
        """
        container = self._base_container(source, node_version, npm_cache)

        # Run ng build
        build_result = await (
            container
            .with_exec(
                ["ng", "build", "--configuration", configuration],
                expect=dagger.ReturnType.ANY,
            )
            .sync()
        )

        exit_code = await build_result.exit_code()
        if exit_code != 0:
            stderr = await build_result.stderr()
            stdout = await build_result.stdout()
            raise RuntimeError(
                f"ng build failed (exit code {exit_code}):\n{stdout}\n{stderr}"
            )

        # Determine the dist output path
        if output_path:
            dist_path = output_path
        else:
            dist_path = await self._detect_dist_path(source)

        return build_result.directory(dist_path)

    async def _detect_dist_path(
        self,
        source: dagger.Directory,
    ) -> str:
        """Auto-detect the dist output path from angular.json."""
        try:
            angular_json_content = await source.file("angular.json").contents()
            angular_json = json.loads(angular_json_content)
        except Exception:
            return "/app/dist"

        projects = angular_json.get("projects", {})
        if not projects:
            return "/app/dist"

        # Get the first (or default) project
        default_project = angular_json.get("defaultProject")
        if default_project and default_project in projects:
            project_config = projects[default_project]
        else:
            project_config = next(iter(projects.values()))

        # Get outputPath from build architect config
        output_path_value = (
            project_config
            .get("architect", {})
            .get("build", {})
            .get("options", {})
            .get("outputPath", "")
        )

        if not output_path_value:
            # Try the project name as fallback
            project_name = default_project or next(iter(projects.keys()))
            return f"/app/dist/{project_name}"

        # Angular 17+ uses object format: {"base": "dist", "browser": ""}
        if isinstance(output_path_value, dict):
            base = output_path_value.get("base", "dist")
            browser = output_path_value.get("browser", "")
            if browser:
                return f"/app/{base}/{browser}"
            return f"/app/{base}"

        # String format: "dist/app-name"
        return f"/app/{output_path_value}"

    @function
    async def lint(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Angular project source directory")],
        fix: Annotated[bool, Doc("Automatically fix lint errors")] = False,
        node_version: Annotated[str, Doc("Node.js version")] = "22",
        npm_cache: Annotated[dagger.CacheVolume | None, Doc("Custom npm cache volume (uses default if not provided)")] = None,
    ) -> str:
        """Lint an Angular project using ng lint.

        Returns the lint output. Requires @angular-eslint to be configured.
        """
        container = self._base_container(source, node_version, npm_cache)
        cmd = ["ng", "lint"]
        if fix:
            cmd.append("--fix")

        result = await (
            container
            .with_exec(cmd, expect=dagger.ReturnType.ANY)
            .sync()
        )

        stdout = await result.stdout()
        stderr = await result.stderr()
        return f"{stdout}\n{stderr}".strip()

    @function
    async def test(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Angular project source directory")],
        watch: Annotated[bool, Doc("Run tests in watch mode")] = False,
        browsers: Annotated[str, Doc("Browser to use for tests")] = "ChromeHeadless",
        node_version: Annotated[str, Doc("Node.js version")] = "22",
        npm_cache: Annotated[dagger.CacheVolume | None, Doc("Custom npm cache volume (uses default if not provided)")] = None,
    ) -> str:
        """Run Angular project tests using ng test.

        Returns the test output.
        """
        container = self._base_container(source, node_version, npm_cache)
        cmd = ["ng", "test", f"--watch={'true' if watch else 'false'}"]
        if browsers:
            cmd.append(f"--browsers={browsers}")

        result = await (
            container
            .with_exec(cmd, expect=dagger.ReturnType.ANY)
            .sync()
        )

        stdout = await result.stdout()
        stderr = await result.stderr()
        return f"{stdout}\n{stderr}".strip()

    @function
    def serve(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Angular project source directory")],
        port: Annotated[int, Doc("Port to serve on")] = 4200,
        node_version: Annotated[str, Doc("Node.js version")] = "22",
        npm_cache: Annotated[dagger.CacheVolume | None, Doc("Custom npm cache volume (uses default if not provided)")] = None,
    ) -> dagger.Service:
        """Start the Angular development server.

        Returns a Dagger Service running `ng serve`.
        """
        return (
            self._base_container(source, node_version, npm_cache)
            .with_exec(["ng", "serve", "--host", "0.0.0.0", "--port", str(port)])
            .with_exposed_port(port)
            .as_service()
        )

    @function
    def install(
        self,
        source: Annotated[dagger.Directory, DefaultPath("."), Doc("Angular project source directory")],
        node_version: Annotated[str, Doc("Node.js version")] = "22",
        npm_cache: Annotated[dagger.CacheVolume | None, Doc("Custom npm cache volume (uses default if not provided)")] = None,
    ) -> dagger.Directory:
        """Install Angular project dependencies.

        Runs `npm ci` (or `npm install` if no lockfile) and returns the source directory with node_modules.
        """
        return self._base_container(source, node_version, npm_cache).directory("/app")
