"""Citation management module."""

import json
import logging
from pathlib import Path
from typing import List, Dict, Optional, Any
from habanero import Crossref
from citeproc import CitationStylesStyle, CitationStylesBibliography
from citeproc import Citation, CitationItem
from citeproc import formatter
from citeproc.source.json import CiteProcJSON

from .models.base import AIModel

# Configure logging
logger = logging.getLogger(__name__)

class CitationManager:
    """Manages citations, source lookups, and bibliography generation."""

    def __init__(self, model: Optional[AIModel] = None):
        """
        Initialize citation manager.

        Args:
            model: AIModel instance for claim detection
        """
        self.model = model
        self.cr = Crossref()
        self.sources: List[Dict[str, Any]] = []

    def find_claims(self, text: str) -> List[str]:
        """
        Identify sentences that require citations.

        Args:
            text: The essay text

        Returns:
            List of sentences needing citations
        """
        if not self.model:
            logger.warning("No AI model available for claim detection.")
            return []

        prompt = (
            "Identify sentences in the following text that contain specific claims, "
            "facts, or data that require a citation. Return ONLY the sentences, "
            "one per line. Do not include general knowledge or topic sentences.\n\n"
            f"Text:\n{text}"
        )

        success, response, error = self.model.call(prompt)
        if not success:
            logger.error(f"Failed to find claims: {error}")
            return []

        claims = [line.strip() for line in response.split('\n') if line.strip()]
        return claims

    def lookup_source(self, query: str, limit: int = 1) -> List[Dict[str, Any]]:
        """
        Find sources using CrossRef.

        Args:
            query: Search query (title, author, etc.)
            limit: Max number of results

        Returns:
            List of source metadata in CSL JSON format
        """
        try:
            results = self.cr.works(query=query, limit=limit)
            items = results['message']['items']
            return items
        except Exception as e:
            logger.error(f"Error looking up source '{query}': {e}")
            return []

    def add_source(self, source_data: Dict[str, Any]):
        """Add a source to the manager."""
        # Ensure it has an ID
        if 'id' not in source_data:
            # Use a simple counter for now, but could be improved
            source_data['id'] = f"source-{len(self.sources) + 1}"
        self.sources.append(source_data)

    def generate_bibliography(self, style: str = "apa") -> str:
        """
        Generate bibliography for added sources.

        Args:
            style: Citation style (apa, mla, chicago-author-date, ieee)

        Returns:
            Formatted bibliography string
        
        Raises:
            FileNotFoundError: If style file is missing
            ValueError: If style is invalid
        """
        supported_styles = ["apa", "mla", "chicago-author-date", "ieee"]
        if style not in supported_styles:
            raise ValueError(f"Unsupported style: {style}. Choose from {supported_styles}")

        if not self.sources:
            return ""

        # Create a bibliography source
        bib_source = CiteProcJSON(self.sources)
        
        # Check for local CSL file
        # Fix: Use absolute path relative to this file
        styles_dir = Path(__file__).parent.parent / "styles"
        style_path = styles_dir / f"{style}.csl"
        
        if not style_path.exists():
            # Try to find it in the current directory as fallback
            if Path(f"styles/{style}.csl").exists():
                 style_path = Path(f"styles/{style}.csl")
            else:
                # List available styles
                available = [f.stem for f in styles_dir.glob("*.csl")]
                raise FileNotFoundError(
                    f"Style file {style}.csl not found in {styles_dir}. "
                    f"Available styles: {', '.join(available)}"
                )

        try:
            bib_style = CitationStylesStyle(str(style_path), validate=False)
        except Exception as e:
            raise ValueError(f"Error loading style {style}: {e}")

        bibliography = CitationStylesBibliography(bib_style, bib_source, formatter.plain)

        # Register all items
        for source in self.sources:
            citation = Citation([CitationItem(source['id'])])
            bibliography.register(citation)

        # Generate
        return "\n".join(str(item) for item in bibliography.bibliography())

    def format_citation(self, source_id: str, style: str = "apa") -> str:
        """
        Generate an inline citation.

        Args:
            source_id: ID of the source
            style: Citation style

        Returns:
            Formatted inline citation
        """
        # This is tricky with citeproc-py as it's designed for whole documents.
        # We might need a simplified approach for inline citations or use the bibliography engine.
        # For now, a simple placeholder or basic author-year if possible.
        
        source = next((s for s in self.sources if s['id'] == source_id), None)
        if not source:
            return "(Source not found)"

        # Simple fallback for now
        author = "Unknown"
        if 'author' in source and source['author']:
            author = source['author'][0].get('family', 'Unknown')
        
        year = "n.d."
        if 'issued' in source and 'date-parts' in source['issued']:
             year = source['issued']['date-parts'][0][0]

        return f"({author}, {year})"

    def check_plagiarism(self, text: str) -> List[str]:
        """
        Identify potential plagiarism (quotes without nearby citations).

        Args:
            text: The essay text

        Returns:
            List of potential plagiarism instances (sentences or phrases)
        """
        if not self.model:
            logger.warning("No AI model available for plagiarism check.")
            return []

        prompt = (
            "Analyze the following text for potential plagiarism. "
            "Identify direct quotes or specific data points that do NOT have "
            "an accompanying citation (e.g., (Smith, 2023) or [1]). "
            "Return ONLY the specific sentences or phrases that are missing citations, "
            "one per line. If none, return nothing.\n\n"
            f"Text:\n{text}"
        )

        success, response, error = self.model.call(prompt)
        if not success:
            logger.error(f"Failed to check plagiarism: {error}")
            return []

        issues = [line.strip() for line in response.split('\n') if line.strip()]
        return issues
