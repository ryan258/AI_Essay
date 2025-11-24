"""Template management module."""

import yaml
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class EssayTemplate:
    """Represents an essay template."""
    name: str
    description: str
    structure: List[Dict[str, Any]]
    metadata: Dict[str, Any]

class TemplateManager:
    """Manages essay templates (loading, saving, listing)."""

    def __init__(self, user_template_dir: str = "~/.essay-templates"):
        """
        Initialize template manager.

        Args:
            user_template_dir: Directory for user-defined templates
        """
        self.user_dir = Path(user_template_dir).expanduser()
        self.default_dir = Path(__file__).parent / "templates"
        
        # Ensure user directory exists
        if not self.user_dir.exists():
            try:
                self.user_dir.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                logger.warning(f"Could not create user template directory: {e}")

    def list_templates(self) -> List[Dict[str, str]]:
        """
        List all available templates (default and user).

        Returns:
            List of dicts with 'name', 'type' (default/user), and 'description'
        """
        templates = []
        
        # Load default templates
        if self.default_dir.exists():
            for f in self.default_dir.glob("*.yaml"):
                try:
                    data = yaml.safe_load(f.read_text())
                    templates.append({
                        "name": f.stem,
                        "type": "default",
                        "description": data.get("description", "No description")
                    })
                except Exception as e:
                    logger.error(f"Error loading default template {f.name}: {e}")

        # Load user templates
        if self.user_dir.exists():
            for f in self.user_dir.glob("*.yaml"):
                try:
                    data = yaml.safe_load(f.read_text())
                    # Check if it overrides a default
                    existing = next((t for t in templates if t["name"] == f.stem), None)
                    if existing:
                        existing["type"] = "user (override)"
                        existing["description"] = data.get("description", existing["description"])
                    else:
                        templates.append({
                            "name": f.stem,
                            "type": "user",
                            "description": data.get("description", "No description")
                        })
                except Exception as e:
                    logger.error(f"Error loading user template {f.name}: {e}")
        
        return sorted(templates, key=lambda x: x["name"])

    def get_template(self, name: str) -> Optional[EssayTemplate]:
        """
        Load a specific template by name.

        Args:
            name: Template name (without extension)

        Returns:
            EssayTemplate object or None if not found
        """
        # Check user dir first
        user_path = self.user_dir / f"{name}.yaml"
        if user_path.exists():
            return self._load_template_file(user_path)
        
        # Check default dir
        default_path = self.default_dir / f"{name}.yaml"
        if default_path.exists():
            return self._load_template_file(default_path)
            
        return None

    def _load_template_file(self, path: Path) -> Optional[EssayTemplate]:
        """Helper to load and parse a template file."""
        try:
            data = yaml.safe_load(path.read_text())
            return EssayTemplate(
                name=path.stem,
                description=data.get("description", ""),
                structure=data.get("structure", []),
                metadata=data.get("metadata", {})
            )
        except Exception as e:
            logger.error(f"Failed to load template {path}: {e}")
            return None

    def create_template(self, name: str, description: str, structure: List[Dict[str, Any]]) -> bool:
        """
        Save a new user template.

        Args:
            name: Name of the template
            description: Brief description
            structure: List of section definitions

        Returns:
            True if successful
        """
        data = {
            "description": description,
            "structure": structure,
            "metadata": {"created_at": datetime.now().isoformat()}
        }
        
        try:
            path = self.user_dir / f"{name}.yaml"
            path.write_text(yaml.dump(data, sort_keys=False))
            return True
        except Exception as e:
            logger.error(f"Failed to save template {name}: {e}")
            return False

    def render_template(self, template: EssayTemplate, topic: str) -> str:
        """
        Render a template into an initial essay draft/outline.

        Args:
            template: The template object
            topic: The essay topic

        Returns:
            Formatted string content
        """
        output = [f"# {topic}\n"]
        
        for section in template.structure:
            title = section.get("title", "Section")
            desc = section.get("description", "")
            word_count = section.get("word_count", "flexible")
            
            output.append(f"## {title}")
            if desc:
                output.append(f"<!-- {desc} -->")
            output.append(f"<!-- Target length: {word_count} words -->\n")
            output.append("(Write here...)\n")
            
        return "\n".join(output)
