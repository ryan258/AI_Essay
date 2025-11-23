"""Essay Drafter module."""

import asyncio
import logging
from pathlib import Path
from typing import List, Dict, Any
from rich.console import Console

from .models.base import AIModel

# Configure logging
logger = logging.getLogger(__name__)
console = Console()

class EssayDrafter:
    """Handles multi-model essay drafting."""

    def __init__(self, models: List[AIModel]):
        """
        Initialize the drafter.

        Args:
            models: List of AIModel instances to use for drafting
        """
        self.models = models

    async def draft_essay(self, topic: str, output_dir: Path) -> List[Dict[str, Any]]:
        """
        Generate essay drafts using all configured models in parallel.

        Args:
            topic: The essay topic
            output_dir: Directory to save drafts

        Returns:
            List of results with model name, status, and file path
        """
        if not self.models:
            logger.warning("No models configured for drafting.")
            return []

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        prompt = (
            f"Write a comprehensive essay about the following topic:\n\n"
            f"Topic: {topic}\n\n"
            "The essay should have a clear introduction, body paragraphs, and conclusion. "
            "Focus on depth, clarity, and logical flow."
        )

        # Create tasks for all models
        tasks = [self._generate_single(model, prompt, output_dir) for model in self.models]
        
        # Run in parallel
        results = await asyncio.gather(*tasks)
        return results

    async def _generate_single(self, model: AIModel, prompt: str, output_dir: Path) -> Dict[str, Any]:
        """
        Generate a single essay draft.

        Args:
            model: The AI model to use
            prompt: The prompt
            output_dir: Output directory

        Returns:
            Dictionary with result details (model, success, error, file, word_count)
        """
        # Sanitize model name for filename (replace slashes and special chars)
        model_name = model.model_id.replace('/', '_').replace(':', '_')
        logger.info(f"Starting draft with {model.model_id}...")

        success, response, error = await model.acall(prompt)

        result = {
            "model": model.model_id,
            "success": success,
            "error": error,
            "file": None,
            "word_count": 0
        }

        if success:
            filename = f"{model_name}.txt"
            filepath = output_dir / filename
            try:
                filepath.write_text(response)
                result["file"] = str(filepath)
                result["word_count"] = len(response.split())
                logger.info(f"Draft saved to {filepath} ({result['word_count']} words)")
            except Exception as e:
                result["error"] = f"Failed to save file to {filepath}: {e}"
                result["success"] = False
        else:
            logger.error(f"Draft failed for {model.model_id}: {error}")

        return result
