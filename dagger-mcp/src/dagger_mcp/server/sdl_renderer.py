"""Convert GraphQL introspection JSON to SDL (Schema Definition Language)."""


def _render_type_ref(type_ref: dict) -> str:
    """Render a __Type reference as an SDL type string (e.g. '[String!]!')."""
    kind = type_ref.get("kind")
    name = type_ref.get("name")
    of_type = type_ref.get("ofType")

    if kind == "NON_NULL":
        return f"{_render_type_ref(of_type)}!"
    if kind == "LIST":
        return f"[{_render_type_ref(of_type)}]"
    return name or "Unknown"


def _render_description(desc: str | None, indent: str = "") -> str:
    """Render a description as a triple-quoted SDL string."""
    if not desc:
        return ""
    # Escape triple quotes in descriptions
    escaped = desc.replace('"""', '\\"\\"\\"')
    if "\n" in desc:
        lines = escaped.split("\n")
        formatted = "\n".join(f"{indent}{line}" for line in lines)
        return f'{indent}"""\n{formatted}\n{indent}"""\n'
    return f'{indent}"""{escaped}"""\n'


def _render_args(args: list[dict]) -> str:
    """Render field arguments inline or multiline."""
    if not args:
        return ""

    parts = []
    for arg in args:
        arg_str = f"{arg['name']}: {_render_type_ref(arg['type'])}"
        if arg.get("defaultValue") is not None:
            arg_str += f" = {arg['defaultValue']}"
        parts.append(arg_str)

    # Use multiline if more than 2 args or total length > 60
    joined = ", ".join(parts)
    if len(args) <= 2 and len(joined) <= 60:
        return f"({joined})"

    lines = []
    for arg in args:
        desc = _render_description(arg.get("description"), "    ")
        arg_str = f"    {arg['name']}: {_render_type_ref(arg['type'])}"
        if arg.get("defaultValue") is not None:
            arg_str += f" = {arg['defaultValue']}"
        lines.append(desc + arg_str)
    return "(\n" + "\n".join(lines) + "\n  )"


def _render_deprecation(item: dict) -> str:
    """Render a @deprecated directive if applicable."""
    if not item.get("isDeprecated"):
        return ""
    reason = item.get("deprecationReason", "")
    if reason:
        return f' @deprecated(reason: "{reason}")'
    return " @deprecated"


def _render_field(field: dict) -> str:
    """Render a single field definition."""
    parts = []

    desc = _render_description(field.get("description"), "  ")
    if desc:
        parts.append(desc)

    args = _render_args(field.get("args", []))
    type_str = _render_type_ref(field["type"])
    line = f"  {field['name']}{args}: {type_str}{_render_deprecation(field)}"

    parts.append(line)
    return "\n".join(parts)


def _render_input_field(field: dict) -> str:
    """Render a single input field definition."""
    parts = []
    desc = _render_description(field.get("description"), "  ")
    if desc:
        parts.append(desc.rstrip())
    type_str = _render_type_ref(field["type"])
    line = f"  {field['name']}: {type_str}"
    if field.get("defaultValue") is not None:
        line += f" = {field['defaultValue']}"
    parts.append(line)
    return "\n".join(parts)


def _render_enum_value(val: dict) -> str:
    """Render a single enum value definition."""
    parts = []
    desc = _render_description(val.get("description"), "  ")
    if desc:
        parts.append(desc.rstrip())
    parts.append(f"  {val['name']}{_render_deprecation(val)}")
    return "\n".join(parts)


def _render_object(name: str, type_data: dict) -> list[str]:
    """Render an OBJECT type definition."""
    interfaces = type_data.get("interfaces") or []
    impl = ""
    if interfaces:
        impl = " implements " + " & ".join(i["name"] for i in interfaces)
    lines = [f"type {name}{impl} {{"]
    for field in type_data.get("fields") or []:
        lines.append(_render_field(field))
    lines.append("}")
    return lines


def _render_input_object(name: str, type_data: dict) -> list[str]:
    """Render an INPUT_OBJECT type definition."""
    lines = [f"input {name} {{"]
    for field in type_data.get("inputFields") or []:
        lines.append(_render_input_field(field))
    lines.append("}")
    return lines


def _render_enum(name: str, type_data: dict) -> list[str]:
    """Render an ENUM type definition."""
    lines = [f"enum {name} {{"]
    for val in type_data.get("enumValues") or []:
        lines.append(_render_enum_value(val))
    lines.append("}")
    return lines


def _render_interface(name: str, type_data: dict) -> list[str]:
    """Render an INTERFACE type definition."""
    lines = [f"interface {name} {{"]
    for field in type_data.get("fields") or []:
        lines.append(_render_field(field))
    lines.append("}")
    return lines


_KIND_RENDERERS = {
    "OBJECT": _render_object,
    "INPUT_OBJECT": _render_input_object,
    "ENUM": _render_enum,
    "INTERFACE": _render_interface,
}


def render_sdl(type_data: dict) -> str:
    """Convert a __type introspection result to SDL format."""
    kind = type_data.get("kind")
    name = type_data.get("name", "Unknown")
    description = type_data.get("description")

    lines = []

    desc = _render_description(description)
    if desc:
        lines.append(desc.rstrip())

    renderer = _KIND_RENDERERS.get(kind)
    if renderer:
        lines.extend(renderer(name, type_data))
    elif kind == "UNION":
        types = type_data.get("possibleTypes") or []
        type_names = " | ".join(t["name"] for t in types)
        lines.append(f"union {name} = {type_names}")
    elif kind == "SCALAR":
        lines.append(f"scalar {name}")
    else:
        lines.append(f"# Unknown kind: {kind}")
        lines.append(f"# Name: {name}")

    return "\n".join(lines)
