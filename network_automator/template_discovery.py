import os
import re
from typing import Dict, List, Optional, Tuple


class TemplateInfo:
    """Informações sobre um template descoberto"""

    def __init__(
        self,
        name: str,
        path: str,
        vendor: str,
        description: str = "",
        safe: bool = True,
        changes_hostname: bool = False,
    ):
        self.name = name
        self.path = path
        self.vendor = vendor
        self.description = description
        self.safe = safe
        self.changes_hostname = changes_hostname

    def __repr__(self):
        return f"TemplateInfo(name={self.name}, vendor={self.vendor}, description='{self.description}')"


class TemplateDiscovery:
    """Sistema de descoberta dinâmica de templates"""

    def __init__(self, templates_dir: str = "templates"):
        import os
        from pathlib import Path

        # If path is relative, make it relative to the project root (parent of network_automator)
        if not os.path.isabs(templates_dir):
            project_root = Path(__file__).parent.parent
            self.templates_dir = str(project_root / templates_dir)
        else:
            self.templates_dir = templates_dir
        self._templates_cache = None

    def _parse_template_metadata(self, content: str) -> Dict[str, any]:
        """Extrai metadados do comentário Jinja2 no início do template"""
        metadata = {
            "description": "",
            "safe": True,
            "changes_hostname": False,
        }

        # Procura por comentários Jinja2 no início do arquivo
        comment_pattern = r"^\{#\s*(.*?)\s*#\}"
        match = re.search(comment_pattern, content, re.DOTALL | re.MULTILINE)

        if match:
            comment_content = match.group(1)

            # Parse das propriedades dentro do comentário
            for line in comment_content.split("\n"):
                line = line.strip()
                if ":" in line:
                    key, value = line.split(":", 1)
                    key = key.strip()
                    value = value.strip()

                    if key == "description":
                        metadata["description"] = value
                    elif key == "safe":
                        metadata["safe"] = value.lower() in ["true", "yes", "1"]
                    elif key == "changes_hostname":
                        metadata["changes_hostname"] = value.lower() in [
                            "true",
                            "yes",
                            "1",
                        ]

        return metadata

    def _discover_vendor_templates(self, vendor_dir: str) -> List[TemplateInfo]:
        """Descobre templates para um vendor específico"""
        templates = []
        vendor_name = os.path.basename(vendor_dir)

        if not os.path.isdir(vendor_dir):
            return templates

        for file_name in os.listdir(vendor_dir):
            if file_name.endswith(".j2"):
                file_path = os.path.join(vendor_dir, file_name)
                template_name = file_name.replace(".j2", "")

                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()

                    metadata = self._parse_template_metadata(content)

                    template_info = TemplateInfo(
                        name=template_name,
                        path=file_path,
                        vendor=vendor_name,
                        description=metadata["description"],
                        safe=metadata["safe"],
                        changes_hostname=metadata["changes_hostname"],
                    )

                    templates.append(template_info)

                except Exception as e:
                    # Se houver erro ao ler o template, cria entrada básica
                    template_info = TemplateInfo(
                        name=template_name,
                        path=file_path,
                        vendor=vendor_name,
                        description=f"Error reading template: {str(e)}",
                        safe=False,
                        changes_hostname=True,  # Assume o pior caso
                    )
                    templates.append(template_info)

        return sorted(templates, key=lambda t: t.name)

    def discover_all_templates(
        self, force_refresh: bool = False
    ) -> Dict[str, List[TemplateInfo]]:
        """Descobre todos os templates disponíveis organizados por vendor"""
        if self._templates_cache is not None and not force_refresh:
            return self._templates_cache

        all_templates = {}

        if not os.path.exists(self.templates_dir):
            return all_templates

        for vendor_name in os.listdir(self.templates_dir):
            vendor_path = os.path.join(self.templates_dir, vendor_name)
            if os.path.isdir(vendor_path):
                templates = self._discover_vendor_templates(vendor_path)
                if templates:
                    all_templates[vendor_name] = templates

        self._templates_cache = all_templates
        return all_templates

    def get_vendor_templates(self, vendor: str) -> List[TemplateInfo]:
        """Obtém templates para um vendor específico"""
        all_templates = self.discover_all_templates()
        return all_templates.get(vendor, [])

    def find_template(self, vendor: str, template_name: str) -> Optional[TemplateInfo]:
        """Encontra um template específico por vendor e nome"""
        vendor_templates = self.get_vendor_templates(vendor)
        for template in vendor_templates:
            if template.name == template_name:
                return template
        return None

    def get_template_path(self, vendor: str, template_name: str) -> Optional[str]:
        """Obtém o caminho completo de um template"""
        template = self.find_template(vendor, template_name)
        return template.path if template else None

    def template_exists(self, vendor: str, template_name: str) -> bool:
        """Verifica se um template existe"""
        return self.find_template(vendor, template_name) is not None

    def get_available_vendors(self) -> List[str]:
        """Retorna lista de vendors disponíveis"""
        all_templates = self.discover_all_templates()
        return sorted(all_templates.keys())

    def get_all_template_names(self, vendor: str) -> List[str]:
        """Retorna lista de nomes de templates para um vendor"""
        templates = self.get_vendor_templates(vendor)
        return [t.name for t in templates]

    def get_fallback_template(self, vendor: str) -> Optional[TemplateInfo]:
        """Encontra o template de fallback (default) para um vendor"""
        return self.find_template(vendor, "default")

    def validate_template_reference(
        self, vendor: str, template_name: str
    ) -> Tuple[bool, str]:
        """Valida se uma referência de template é válida"""
        if not vendor:
            return False, "Vendor not specified"

        if vendor not in self.get_available_vendors():
            return False, f"Vendor '{vendor}' not found"

        if not template_name:
            # Se não especificar template, tenta usar default
            if self.template_exists(vendor, "default"):
                return True, "Will use default template"
            else:
                return False, f"No default template found for vendor '{vendor}'"

        if not self.template_exists(vendor, template_name):
            available = self.get_all_template_names(vendor)
            return (
                False,
                f"Template '{template_name}' not found for vendor '{vendor}'. Available: {available}",
            )

        return True, "Template reference is valid"

    def get_template_summary(self) -> Dict[str, Dict[str, int]]:
        """Obtém resumo estatístico dos templates"""
        all_templates = self.discover_all_templates()
        summary = {}

        for vendor, templates in all_templates.items():
            summary[vendor] = {
                "total": len(templates),
                "safe": sum(1 for t in templates if t.safe),
                "unsafe": sum(1 for t in templates if not t.safe),
                "changes_hostname": sum(1 for t in templates if t.changes_hostname),
            }

        return summary
