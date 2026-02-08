import os
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


def render_template(vendor, template_name, dados):
    # Get templates directory relative to project root
    project_root = Path(__file__).parent.parent.parent
    templates_dir = str(project_root / "templates")

    env = Environment(
        loader=FileSystemLoader(templates_dir), trim_blocks=True, lstrip_blocks=True
    )

    template = env.get_template(f"{vendor}/{template_name}")
    return template.render(dados)
