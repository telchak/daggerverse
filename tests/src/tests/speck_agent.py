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

# Valid values for enum-like fields
_VALID_COMPLEXITIES = {"low", "medium", "high"}


def _clone_realworld() -> dagger.Directory:
    """Clone the FastAPI RealWorld example app."""
    return dag.git(REALWORLD_REPO).branch(REALWORLD_BRANCH).tree()


def _extract_json(raw: str) -> dict:
    """Parse JSON from raw output, handling markdown fences."""
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        match = re.search(r"```(?:json)?\s*\n(.*?)\n```", raw, re.DOTALL)
        if match:
            return json.loads(match.group(1))
        raise RuntimeError(f"Invalid JSON output: {raw[:300]}...")


_VALID_TASK_TYPES = {"implementation", "test", "review"}


def _validate_task(task: dict, index: int, valid_models: set[str]) -> list[str]:
    """Validate a single task object. Returns a list of errors."""
    errors: list[str] = []
    prefix = f"tasks[{index}] (id={task.get('id', '?')})"

    # Required string fields
    for field in ("id", "title", "description", "phase_name"):
        if not isinstance(task.get(field), str) or not task[field]:
            errors.append(f"{prefix}: missing or empty '{field}'")

    # Required int fields
    if not isinstance(task.get("phase"), int):
        errors.append(f"{prefix}: 'phase' must be an integer")

    if not isinstance(task.get("order"), int) or task.get("order", 0) < 1:
        errors.append(f"{prefix}: 'order' must be a positive integer")

    # task_type enum
    if task.get("task_type") not in _VALID_TASK_TYPES:
        errors.append(
            f"{prefix}: 'task_type' must be one of {_VALID_TASK_TYPES}, "
            f"got '{task.get('task_type')}'"
        )

    # estimated_complexity enum
    if task.get("estimated_complexity") not in _VALID_COMPLEXITIES:
        errors.append(
            f"{prefix}: 'estimated_complexity' must be one of {_VALID_COMPLEXITIES}, "
            f"got '{task.get('estimated_complexity')}'"
        )

    # suggested_model must be a valid model ID from the family
    if valid_models and task.get("suggested_model") not in valid_models:
        errors.append(
            f"{prefix}: 'suggested_model' must be one of {valid_models}, "
            f"got '{task.get('suggested_model')}'"
        )

    # definition_of_done must be a non-empty list of strings
    dod = task.get("definition_of_done")
    if not isinstance(dod, list) or not dod:
        errors.append(f"{prefix}: 'definition_of_done' must be a non-empty list")
    elif not all(isinstance(d, str) and d for d in dod):
        errors.append(f"{prefix}: 'definition_of_done' entries must be non-empty strings")

    # boolean field
    if not isinstance(task.get("parallel"), bool):
        errors.append(f"{prefix}: 'parallel' must be a boolean")

    # depends_on must be a list of strings
    deps = task.get("depends_on")
    if not isinstance(deps, list):
        errors.append(f"{prefix}: 'depends_on' must be a list")
    elif not all(isinstance(d, str) for d in deps):
        errors.append(f"{prefix}: 'depends_on' entries must be strings")

    # files_to_modify must be a list of strings
    ftm = task.get("files_to_modify")
    if not isinstance(ftm, list):
        errors.append(f"{prefix}: 'files_to_modify' must be a list")
    elif not all(isinstance(f, str) for f in ftm):
        errors.append(f"{prefix}: 'files_to_modify' entries must be strings")

    # story_label: null or string
    sl = task.get("story_label")
    if sl is not None and not isinstance(sl, str):
        errors.append(f"{prefix}: 'story_label' must be null or a string")

    # suggested_agent: null or object with required fields
    sa = task.get("suggested_agent")
    if sa is not None:
        if not isinstance(sa, dict):
            errors.append(f"{prefix}: 'suggested_agent' must be null or an object")
        else:
            for sa_field in ("name", "source", "entrypoint", "reason"):
                if not isinstance(sa.get(sa_field), str) or not sa[sa_field]:
                    errors.append(f"{prefix}: 'suggested_agent.{sa_field}' missing or empty")

    return errors


def _validate_execution_plan(plan: dict) -> list[str]:
    """Validate the execution_plan object. Returns a list of errors."""
    errors: list[str] = []

    if not isinstance(plan.get("total_phases"), int):
        errors.append("execution_plan: 'total_phases' must be an integer")

    # phases array
    phases = plan.get("phases")
    if not isinstance(phases, list) or not phases:
        errors.append("execution_plan: 'phases' must be a non-empty list")
    else:
        for i, phase in enumerate(phases):
            if not isinstance(phase.get("phase"), int):
                errors.append(f"execution_plan.phases[{i}]: 'phase' must be an integer")
            if not isinstance(phase.get("name"), str) or not phase["name"]:
                errors.append(f"execution_plan.phases[{i}]: 'name' missing or empty")
            if not isinstance(phase.get("tasks"), list) or not phase["tasks"]:
                errors.append(f"execution_plan.phases[{i}]: 'tasks' must be a non-empty list")
            if not isinstance(phase.get("parallel"), bool):
                errors.append(f"execution_plan.phases[{i}]: 'parallel' must be a boolean")
            # pr_branch: null or string
            pb = phase.get("pr_branch")
            if pb is not None and not isinstance(pb, str):
                errors.append(f"execution_plan.phases[{i}]: 'pr_branch' must be null or a string")
            if isinstance(pb, str) and (" " in pb or pb != pb.lower()):
                errors.append(f"execution_plan.phases[{i}]: 'pr_branch' must be lowercase with no spaces")

    # critical_path
    cp = plan.get("critical_path")
    if not isinstance(cp, list):
        errors.append("execution_plan: 'critical_path' must be a list")

    # parallelizable_groups
    pg = plan.get("parallelizable_groups")
    if not isinstance(pg, list):
        errors.append("execution_plan: 'parallelizable_groups' must be a list")

    return errors


def _validate_decompose_output(data: dict, valid_models: set[str]) -> list[str]:
    """Validate the full decompose JSON output. Returns a list of errors."""
    errors: list[str] = []

    # Top-level required string fields
    for field in ("feature", "spec_summary"):
        if not isinstance(data.get(field), str) or not data[field]:
            errors.append(f"top-level: missing or empty '{field}'")

    # total_tasks
    if not isinstance(data.get("total_tasks"), int):
        errors.append("top-level: 'total_tasks' must be an integer")

    # tasks array
    tasks = data.get("tasks")
    if not isinstance(tasks, list) or not tasks:
        errors.append("top-level: 'tasks' must be a non-empty list")
        return errors  # can't validate further

    # total_tasks consistency
    if isinstance(data.get("total_tasks"), int) and data["total_tasks"] != len(tasks):
        errors.append(
            f"top-level: 'total_tasks' is {data['total_tasks']} but 'tasks' has {len(tasks)} entries"
        )

    # Validate each task
    for i, task in enumerate(tasks):
        errors.extend(_validate_task(task, i, valid_models))

    # Validate depends_on references
    task_ids = {t.get("id") for t in tasks}
    for i, task in enumerate(tasks):
        for dep in task.get("depends_on", []):
            if dep not in task_ids:
                errors.append(
                    f"tasks[{i}] (id={task.get('id')}): depends_on references unknown task '{dep}'"
                )

    # agent_registry_used
    aru = data.get("agent_registry_used")
    if not isinstance(aru, list):
        errors.append("top-level: 'agent_registry_used' must be a list")

    # execution_plan
    ep = data.get("execution_plan")
    if not isinstance(ep, dict):
        errors.append("top-level: 'execution_plan' must be an object")
    else:
        errors.extend(_validate_execution_plan(ep))

    return errors


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

    # First generate a spec
    spec = await agent.specify(
        prompt="Add a tagging system for articles with autocomplete suggestions.",
    )

    # Then generate a plan from it
    result = await agent.plan(
        spec=spec,
        tech_stack="Python, FastAPI, PostgreSQL",
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

    agents_registry = json.dumps([
        {
            "name": "monty",
            "source": "github.com/telchak/daggerverse/monty",
            "specialization": "Python backend development",
            "capabilities": ["assist", "review", "write_tests", "build", "upgrade"],
        },
    ])

    result = await agent.decompose(
        prompt=(
            "Add a commenting system where users can post comments on articles, "
            "edit their own comments, and delete their own comments."
        ),
        agents=agents_registry,
        tech_stack="Python, FastAPI, PostgreSQL",
        model_family="claude",
    )

    if not result:
        raise RuntimeError("decompose returned empty result")

    data = _extract_json(result)

    # Valid model IDs for the claude family
    valid_models = {"claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"}

    errors = _validate_decompose_output(data, valid_models)
    if errors:
        error_list = "\n  - ".join(errors)
        raise RuntimeError(f"Schema validation failed ({len(errors)} errors):\n  - {error_list}")

    task_count = len(data["tasks"])
    phases = data["execution_plan"]["total_phases"]
    models_used = {t["suggested_model"] for t in data["tasks"]}

    # All tasks should be implementation type when include_tests/include_review are off
    task_types = {t.get("task_type") for t in data["tasks"]}
    if task_types != {"implementation"}:
        raise RuntimeError(
            f"Expected only 'implementation' tasks when include_tests/include_review are off, "
            f"got {task_types}"
        )

    # pr_branch should be null on phases when create_pr is off (default)
    for phase in data["execution_plan"]["phases"]:
        if phase.get("pr_branch") is not None:
            raise RuntimeError(
                f"Phase {phase['phase']}: pr_branch should be null when create_pr is off, "
                f"got '{phase['pr_branch']}'"
            )

    return (
        f"PASS: decompose (tasks={task_count}, phases={phases}, "
        f"models={models_used}, schema=valid)"
    )


async def test_speck_decompose_with_pipeline(source: dagger.Directory) -> str:
    """Test decompose with include_tests and include_review enabled."""
    agent = dag.speck(source=source)

    agents_registry = json.dumps([
        {
            "name": "monty",
            "source": "github.com/telchak/daggerverse/monty",
            "specialization": "Python backend development",
            "capabilities": ["assist", "review", "write_tests", "build", "upgrade"],
        },
    ])

    result = await agent.decompose(
        prompt=(
            "Add a user profile page that shows bio, avatar, and recent articles."
        ),
        agents=agents_registry,
        tech_stack="Python, FastAPI, PostgreSQL",
        model_family="claude",
        include_tests=True,
        include_review=True,
    )

    if not result:
        raise RuntimeError("decompose (with pipeline) returned empty result")

    data = _extract_json(result)

    valid_models = {"claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"}

    errors = _validate_decompose_output(data, valid_models)
    if errors:
        error_list = "\n  - ".join(errors)
        raise RuntimeError(f"Schema validation failed ({len(errors)} errors):\n  - {error_list}")

    # Verify test and review tasks exist
    task_types = {t.get("task_type") for t in data["tasks"]}
    if "test" not in task_types:
        raise RuntimeError("Expected 'test' tasks when include_tests=True, but none found")
    if "review" not in task_types:
        raise RuntimeError("Expected 'review' tasks when include_review=True, but none found")

    # Verify test tasks use write_tests entrypoint
    for task in data["tasks"]:
        if task.get("task_type") == "test" and task.get("suggested_agent"):
            if task["suggested_agent"].get("entrypoint") != "write_tests":
                raise RuntimeError(
                    f"Test task {task['id']} should use 'write_tests' entrypoint, "
                    f"got '{task['suggested_agent'].get('entrypoint')}'"
                )
        if task.get("task_type") == "review" and task.get("suggested_agent"):
            if task["suggested_agent"].get("entrypoint") != "review":
                raise RuntimeError(
                    f"Review task {task['id']} should use 'review' entrypoint, "
                    f"got '{task['suggested_agent'].get('entrypoint')}'"
                )

    # Verify order is monotonically increasing per dependency chain
    order_values = [t["order"] for t in data["tasks"]]
    if min(order_values) < 1:
        raise RuntimeError("Order values must be positive integers")

    # Verify test/review tasks come after implementation tasks they depend on
    task_map = {t["id"]: t for t in data["tasks"]}
    for task in data["tasks"]:
        if task.get("task_type") in ("test", "review"):
            for dep_id in task.get("depends_on", []):
                dep = task_map.get(dep_id)
                if dep and dep["order"] >= task["order"]:
                    raise RuntimeError(
                        f"Task {task['id']} (order={task['order']}) depends on "
                        f"{dep_id} (order={dep['order']}) but should have higher order"
                    )

    impl_count = sum(1 for t in data["tasks"] if t["task_type"] == "implementation")
    test_count = sum(1 for t in data["tasks"] if t["task_type"] == "test")
    review_count = sum(1 for t in data["tasks"] if t["task_type"] == "review")

    return (
        f"PASS: decompose_pipeline (impl={impl_count}, tests={test_count}, "
        f"reviews={review_count}, order_range={min(order_values)}-{max(order_values)}, "
        f"schema=valid)"
    )


async def test_speck_decompose_with_pr(source: dagger.Directory) -> str:
    """Test decompose with create_pr enabled (one PR per phase)."""
    agent = dag.speck(source=source)

    agents_registry = json.dumps([
        {
            "name": "monty",
            "source": "github.com/telchak/daggerverse/monty",
            "specialization": "Python backend development",
            "capabilities": ["assist", "review", "write_tests", "build", "upgrade"],
        },
    ])

    result = await agent.decompose(
        prompt="Add a health check endpoint that returns service status.",
        agents=agents_registry,
        tech_stack="Python, FastAPI",
        model_family="claude",
        create_pr=True,
    )

    if not result:
        raise RuntimeError("decompose (with PR) returned empty result")

    data = _extract_json(result)

    valid_models = {"claude-haiku-4-5", "claude-sonnet-4-6", "claude-opus-4-6"}

    errors = _validate_decompose_output(data, valid_models)
    if errors:
        error_list = "\n  - ".join(errors)
        raise RuntimeError(f"Schema validation failed ({len(errors)} errors):\n  - {error_list}")

    # Verify all phases have pr_branch set (not null)
    phases = data["execution_plan"]["phases"]
    for phase in phases:
        pb = phase.get("pr_branch")
        if not isinstance(pb, str) or not pb:
            raise RuntimeError(
                f"Phase {phase['phase']}: pr_branch must be a non-empty string when create_pr=True, "
                f"got {pb!r}"
            )
        if " " in pb or pb != pb.lower():
            raise RuntimeError(
                f"Phase {phase['phase']}: pr_branch must be lowercase with no spaces, "
                f"got '{pb}'"
            )
        if not pb.startswith("speck/"):
            raise RuntimeError(
                f"Phase {phase['phase']}: pr_branch must start with 'speck/', got '{pb}'"
            )

    # Each phase should have a unique branch
    branches = [p["pr_branch"] for p in phases]
    if len(branches) != len(set(branches)):
        raise RuntimeError(
            f"Each phase must have a unique pr_branch. "
            f"Got duplicates: {[b for b in branches if branches.count(b) > 1]}"
        )

    task_count = len(data["tasks"])
    phase_count = len(phases)
    return f"PASS: decompose_pr (tasks={task_count}, phases={phase_count}, branches={len(branches)}, schema=valid)"
