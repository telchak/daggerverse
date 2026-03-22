"""Speck (Spec-Driven Development Agent) module tests.

Uses the FastAPI RealWorld example app as a realistic test target.
Tests the full SDD pipeline: specify, plan, decompose.
"""

import json
import re

import dagger
from dagger import dag


REALWORLD_REPO = "https://github.com/nsidnev/fastapi-realworld-example-app.git"
REALWORLD_BRANCH = "master"

# Shared test constants
_MONTY_SOURCE = "github.com/telchak/daggerverse/monty"
_MONTY_SPECIALIZATION = "Python backend development"
_TECH_STACK_PYTHON = "Python, FastAPI, PostgreSQL"
_ERROR_LIST_SEP = "\n  - "

# Valid values for enum-like fields
_VALID_COMPLEXITIES = {"low", "medium", "high"}
_VALID_TASK_TYPES = {"implementation", "test", "review"}
_VALID_CLAUDE_MODELS = {"claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"}


def _clone_realworld() -> dagger.Directory:
    """Clone the FastAPI RealWorld example app."""
    return dag.git(REALWORLD_REPO).branch(REALWORLD_BRANCH).tree()


def _extract_json(raw: str) -> dict:
    """Parse JSON from raw output, handling markdown fences."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?[ \t]*\n(.*?)\n```", raw, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise RuntimeError(f"Invalid JSON output: {raw[:300]}...")


def _make_agents_registry() -> str:
    """Build the standard agents registry JSON for tests."""
    return json.dumps([
        {
            "name": "monty",
            "source": _MONTY_SOURCE,
            "specialization": _MONTY_SPECIALIZATION,
            "capabilities": ["assist", "review", "write_tests", "build", "upgrade"],
        },
    ])


def _validate_string_list(value, field_name: str, prefix: str) -> list[str]:
    """Validate that a field is a list of strings."""
    if not isinstance(value, list):
        return [f"{prefix}: '{field_name}' must be a list"]
    if not all(isinstance(item, str) for item in value):
        return [f"{prefix}: '{field_name}' entries must be strings"]
    return []


def _validate_nonempty_string_list(value, field_name: str, prefix: str) -> list[str]:
    """Validate that a field is a non-empty list of non-empty strings."""
    if not isinstance(value, list) or not value:
        return [f"{prefix}: '{field_name}' must be a non-empty list"]
    if not all(isinstance(item, str) and item for item in value):
        return [f"{prefix}: '{field_name}' entries must be non-empty strings"]
    return []


def _validate_suggested_agent(sa, prefix: str) -> list[str]:
    """Validate the suggested_agent sub-object."""
    if sa is None:
        return []
    if not isinstance(sa, dict):
        return [f"{prefix}: 'suggested_agent' must be null or an object"]
    errors = []
    for field in ("name", "source", "entrypoint", "reason"):
        if not isinstance(sa.get(field), str) or not sa[field]:
            errors.append(f"{prefix}: 'suggested_agent.{field}' missing or empty")
    return errors


def _validate_task(task: dict, index: int, valid_models: set[str]) -> list[str]:
    """Validate a single task object. Returns a list of errors."""
    errors: list[str] = []
    prefix = f"tasks[{index}] (id={task.get('id', '?')})"

    for field in ("id", "title", "description", "phase_name"):
        if not isinstance(task.get(field), str) or not task[field]:
            errors.append(f"{prefix}: missing or empty '{field}'")

    if not isinstance(task.get("phase"), int):
        errors.append(f"{prefix}: 'phase' must be an integer")

    if not isinstance(task.get("order"), int) or task.get("order", 0) < 1:
        errors.append(f"{prefix}: 'order' must be a positive integer")

    if task.get("task_type") not in _VALID_TASK_TYPES:
        errors.append(f"{prefix}: 'task_type' must be one of {_VALID_TASK_TYPES}, got '{task.get('task_type')}'")

    if task.get("estimated_complexity") not in _VALID_COMPLEXITIES:
        errors.append(f"{prefix}: 'estimated_complexity' must be one of {_VALID_COMPLEXITIES}, got '{task.get('estimated_complexity')}'")

    if valid_models and task.get("suggested_model") not in valid_models:
        errors.append(f"{prefix}: 'suggested_model' must be one of {valid_models}, got '{task.get('suggested_model')}'")

    errors.extend(_validate_nonempty_string_list(task.get("definition_of_done"), "definition_of_done", prefix))

    if not isinstance(task.get("parallel"), bool):
        errors.append(f"{prefix}: 'parallel' must be a boolean")

    errors.extend(_validate_string_list(task.get("depends_on"), "depends_on", prefix))
    errors.extend(_validate_string_list(task.get("files_to_modify"), "files_to_modify", prefix))

    sl = task.get("story_label")
    if sl is not None and not isinstance(sl, str):
        errors.append(f"{prefix}: 'story_label' must be null or a string")

    errors.extend(_validate_suggested_agent(task.get("suggested_agent"), prefix))

    return errors


def _validate_phase(phase: dict, index: int) -> list[str]:
    """Validate a single phase object. Returns a list of errors."""
    errors: list[str] = []
    pfx = f"execution_plan.phases[{index}]"

    if not isinstance(phase.get("phase"), int):
        errors.append(f"{pfx}: 'phase' must be an integer")
    if not isinstance(phase.get("name"), str) or not phase["name"]:
        errors.append(f"{pfx}: 'name' missing or empty")
    if not isinstance(phase.get("tasks"), list) or not phase["tasks"]:
        errors.append(f"{pfx}: 'tasks' must be a non-empty list")
    if not isinstance(phase.get("parallel"), bool):
        errors.append(f"{pfx}: 'parallel' must be a boolean")

    pb = phase.get("pr_branch")
    if pb is not None and not isinstance(pb, str):
        errors.append(f"{pfx}: 'pr_branch' must be null or a string")
    if isinstance(pb, str) and (" " in pb or pb != pb.lower()):
        errors.append(f"{pfx}: 'pr_branch' must be lowercase with no spaces")

    return errors


def _validate_execution_plan(plan: dict) -> list[str]:
    """Validate the execution_plan object. Returns a list of errors."""
    errors: list[str] = []

    if not isinstance(plan.get("total_phases"), int):
        errors.append("execution_plan: 'total_phases' must be an integer")

    phases = plan.get("phases")
    if not isinstance(phases, list) or not phases:
        errors.append("execution_plan: 'phases' must be a non-empty list")
    else:
        for i, phase in enumerate(phases):
            errors.extend(_validate_phase(phase, i))

    if not isinstance(plan.get("critical_path"), list):
        errors.append("execution_plan: 'critical_path' must be a list")

    if not isinstance(plan.get("parallelizable_groups"), list):
        errors.append("execution_plan: 'parallelizable_groups' must be a list")

    return errors


def _validate_dependency_refs(tasks: list[dict]) -> list[str]:
    """Validate that all depends_on references point to existing task IDs."""
    errors: list[str] = []
    task_ids = {t.get("id") for t in tasks}
    for i, task in enumerate(tasks):
        for dep in task.get("depends_on", []):
            if dep not in task_ids:
                errors.append(
                    f"tasks[{i}] (id={task.get('id')}): depends_on references unknown task '{dep}'"
                )
    return errors


def _validate_decompose_output(data: dict, valid_models: set[str]) -> list[str]:
    """Validate the full decompose JSON output. Returns a list of errors."""
    errors: list[str] = []

    for field in ("feature", "spec_summary"):
        if not isinstance(data.get(field), str) or not data[field]:
            errors.append(f"top-level: missing or empty '{field}'")

    if not isinstance(data.get("total_tasks"), int):
        errors.append("top-level: 'total_tasks' must be an integer")

    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("top-level: 'tasks' must be a non-empty list")
        return errors

    if isinstance(data.get("total_tasks"), int) and data["total_tasks"] != len(tasks):
        errors.append(f"top-level: 'total_tasks' is {data['total_tasks']} but 'tasks' has {len(tasks)} entries")

    for i, task in enumerate(tasks):
        errors.extend(_validate_task(task, i, valid_models))

    errors.extend(_validate_dependency_refs(tasks))

    if not isinstance(data.get("agent_registry_used"), list):
        errors.append("top-level: 'agent_registry_used' must be a list")

    ep = data.get("execution_plan")
    if not isinstance(ep, dict):
        errors.append("top-level: 'execution_plan' must be an object")
    else:
        errors.extend(_validate_execution_plan(ep))

    return errors


def _raise_if_errors(errors: list[str]) -> None:
    """Raise RuntimeError if there are validation errors."""
    if errors:
        error_list = _ERROR_LIST_SEP.join(errors)
        raise RuntimeError(f"Schema validation failed ({len(errors)} errors):{_ERROR_LIST_SEP}{error_list}")


def _validate_entrypoints(tasks: list[dict]) -> None:
    """Validate that test/review tasks use the correct entrypoints."""
    for task in tasks:
        sa = task.get("suggested_agent")
        if not sa:
            continue
        ep = sa.get("entrypoint", "")
        if task.get("task_type") == "test" and ep.replace("-", "_") != "write_tests":
            raise RuntimeError(f"Test task {task['id']} should use 'write_tests' entrypoint, got '{ep}'")
        if task.get("task_type") == "review" and ep != "review":
            raise RuntimeError(f"Review task {task['id']} should use 'review' entrypoint, got '{ep}'")


def _validate_task_ordering(tasks: list[dict]) -> None:
    """Validate that task ordering respects dependency chains."""
    order_values = [t["order"] for t in tasks]
    if min(order_values) < 1:
        raise RuntimeError("Order values must be positive integers")

    task_map = {t["id"]: t for t in tasks}
    for task in tasks:
        if task.get("task_type") not in ("test", "review"):
            continue
        for dep_id in task.get("depends_on", []):
            dep = task_map.get(dep_id)
            if dep and dep["order"] >= task["order"]:
                raise RuntimeError(
                    f"Task {task['id']} (order={task['order']}) depends on "
                    f"{dep_id} (order={dep['order']}) but should have higher order"
                )


async def test_speck_specify(source: dagger.Directory) -> str:
    """Test specify: generate a feature spec from a prompt — returns str."""
    agent = dag.speck(source=source)

    result = await agent.specify(
        prompt=(
            "Add a favorites feature where users can bookmark articles. "
            "Users should be able to favorite/unfavorite articles and see "
            "a list of their favorited articles on their profile."
        ),
    )

    if not result:
        raise RuntimeError("specify returned empty result")

    result_lower = result.lower()
    has_structure = any(
        keyword in result_lower
        for keyword in ("user stor", "requirement", "acceptance", "success criteria")
    )

    return f"PASS: specify ({len(result)} chars, structured={has_structure})"


async def test_speck_plan(source: dagger.Directory) -> str:
    """Test plan: generate a technical plan from a spec — returns str."""
    agent = dag.speck(source=source)

    spec = await agent.specify(
        prompt="Add a tagging system for articles with autocomplete suggestions.",
    )

    result = await agent.plan(
        spec=spec,
        tech_stack=_TECH_STACK_PYTHON,
    )

    if not result:
        raise RuntimeError("plan returned empty result")

    result_lower = result.lower()
    has_structure = any(
        keyword in result_lower
        for keyword in ("architecture", "decision", "structure", "dependenc", "complexity")
    )

    return f"PASS: plan ({len(result)} chars, structured={has_structure})"


async def test_speck_decompose(source: dagger.Directory) -> str:
    """Test decompose: full pipeline producing validated JSON."""
    agent = dag.speck(source=source)

    result = await agent.decompose(
        prompt=(
            "Add a commenting system where users can post comments on articles, "
            "edit their own comments, and delete their own comments."
        ),
        agents=_make_agents_registry(),
        tech_stack=_TECH_STACK_PYTHON,
        model_family="claude",
    )

    if not result:
        raise RuntimeError("decompose returned empty result")

    data = _extract_json(result)
    errors = _validate_decompose_output(data, _VALID_CLAUDE_MODELS)
    _raise_if_errors(errors)

    task_types = {t.get("task_type") for t in data["tasks"]}
    if task_types != {"implementation"}:
        raise RuntimeError(
            f"Expected only 'implementation' tasks when include_tests/include_review are off, got {task_types}"
        )

    for phase in data["execution_plan"]["phases"]:
        if phase.get("pr_branch") is not None:
            raise RuntimeError(
                f"Phase {phase['phase']}: pr_branch should be null when create_pr is off, got '{phase['pr_branch']}'"
            )

    task_count = len(data["tasks"])
    phases = data["execution_plan"]["total_phases"]
    models_used = {t["suggested_model"] for t in data["tasks"]}

    return f"PASS: decompose (tasks={task_count}, phases={phases}, models={models_used}, schema=valid)"


async def test_speck_decompose_with_pipeline(source: dagger.Directory) -> str:
    """Test decompose with include_tests and include_review enabled."""
    agent = dag.speck(source=source)

    result = await agent.decompose(
        prompt="Add a user profile page that shows bio, avatar, and recent articles.",
        agents=_make_agents_registry(),
        tech_stack=_TECH_STACK_PYTHON,
        model_family="claude",
        include_tests=True,
        include_review=True,
    )

    if not result:
        raise RuntimeError("decompose (with pipeline) returned empty result")

    data = _extract_json(result)
    errors = _validate_decompose_output(data, _VALID_CLAUDE_MODELS)
    _raise_if_errors(errors)

    task_types = {t.get("task_type") for t in data["tasks"]}
    if "test" not in task_types:
        raise RuntimeError("Expected 'test' tasks when include_tests=True, but none found")
    if "review" not in task_types:
        raise RuntimeError("Expected 'review' tasks when include_review=True, but none found")

    _validate_entrypoints(data["tasks"])
    _validate_task_ordering(data["tasks"])

    impl_count = sum(1 for t in data["tasks"] if t["task_type"] == "implementation")
    test_count = sum(1 for t in data["tasks"] if t["task_type"] == "test")
    review_count = sum(1 for t in data["tasks"] if t["task_type"] == "review")
    order_values = [t["order"] for t in data["tasks"]]

    return (
        f"PASS: decompose_pipeline (impl={impl_count}, tests={test_count}, "
        f"reviews={review_count}, order_range={min(order_values)}-{max(order_values)}, "
        f"schema=valid)"
    )


async def test_speck_decompose_with_pr(source: dagger.Directory) -> str:
    """Test decompose with create_pr enabled (one PR per phase)."""
    agent = dag.speck(source=source)

    result = await agent.decompose(
        prompt="Add a health check endpoint that returns service status.",
        agents=_make_agents_registry(),
        tech_stack="Python, FastAPI",
        model_family="claude",
        create_pr=True,
    )

    if not result:
        raise RuntimeError("decompose (with PR) returned empty result")

    data = _extract_json(result)
    errors = _validate_decompose_output(data, _VALID_CLAUDE_MODELS)
    _raise_if_errors(errors)

    phases = data["execution_plan"]["phases"]
    for phase in phases:
        pb = phase.get("pr_branch")
        if not isinstance(pb, str) or not pb:
            raise RuntimeError(f"Phase {phase['phase']}: pr_branch must be a non-empty string when create_pr=True, got {pb!r}")
        if " " in pb or pb != pb.lower():
            raise RuntimeError(f"Phase {phase['phase']}: pr_branch must be lowercase with no spaces, got '{pb}'")
        if not pb.startswith("speck/"):
            raise RuntimeError(f"Phase {phase['phase']}: pr_branch must start with 'speck/', got '{pb}'")

    branches = [p["pr_branch"] for p in phases]
    if len(branches) != len(set(branches)):
        raise RuntimeError(
            f"Each phase must have a unique pr_branch. "
            f"Got duplicates: {[b for b in branches if branches.count(b) > 1]}"
        )

    task_count = len(data["tasks"])
    phase_count = len(phases)
    return f"PASS: decompose_pr (tasks={task_count}, phases={phase_count}, branches={len(branches)}, schema=valid)"
