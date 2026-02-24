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


def _render_field(field: dict) -> str:
    """Render a single field definition."""
    parts = []

    desc = _render_description(field.get("description"), "  ")
    if desc:
        parts.append(desc)

    args = _render_args(field.get("args", []))
    type_str = _render_type_ref(field["type"])
    line = f"  {field['name']}{args}: {type_str}"

    if field.get("isDeprecated"):
        reason = field.get("deprecationReason", "")
        if reason:
            line += f' @deprecated(reason: "{reason}")'
        else:
            line += " @deprecated"

    parts.append(line)
    return "\n".join(parts)


def render_sdl(type_data: dict) -> str:
    """Convert a __type introspection result to SDL format."""
    kind = type_data.get("kind")
    name = type_data.get("name", "Unknown")
    description = type_data.get("description")

    lines = []

    desc = _render_description(description)
    if desc:
        lines.append(desc.rstrip())

    if kind == "OBJECT":
        interfaces = type_data.get("interfaces") or []
        impl = ""
        if interfaces:
            impl = " implements " + " & ".join(i["name"] for i in interfaces)
        lines.append(f"type {name}{impl} {{")
        for field in type_data.get("fields") or []:
            lines.append(_render_field(field))
        lines.append("}")

    elif kind == "INPUT_OBJECT":
        lines.append(f"input {name} {{")
        for field in type_data.get("inputFields") or []:
            desc = _render_description(field.get("description"), "  ")
            if desc:
                lines.append(desc.rstrip())
            type_str = _render_type_ref(field["type"])
            line = f"  {field['name']}: {type_str}"
            if field.get("defaultValue") is not None:
                line += f" = {field['defaultValue']}"
            lines.append(line)
        lines.append("}")

    elif kind == "ENUM":
        lines.append(f"enum {name} {{")
        for val in type_data.get("enumValues") or []:
            desc = _render_description(val.get("description"), "  ")
            if desc:
                lines.append(desc.rstrip())
            line = f"  {val['name']}"
            if val.get("isDeprecated"):
                reason = val.get("deprecationReason", "")
                if reason:
                    line += f' @deprecated(reason: "{reason}")'
                else:
                    line += " @deprecated"
            lines.append(line)
        lines.append("}")

    elif kind == "INTERFACE":
        lines.append(f"interface {name} {{")
        for field in type_data.get("fields") or []:
            lines.append(_render_field(field))
        lines.append("}")

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
