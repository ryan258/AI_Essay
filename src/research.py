import logging
from typing import List, Dict, Any, Optional

# Configure logging
logger = logging.getLogger(__name__)

from semanticscholar import SemanticScholar
from semanticscholar.PaginatedResults import PaginatedResults

from .models.base import AIModel

# Constants
MAX_ESSAY_LENGTH = 2000  # Token limit for API call
DEFAULT_SEARCH_LIMIT = 5

class ResearchAssistant:
    """Assists with finding sources and research."""

    def __init__(self, model: Optional[AIModel] = None):
        """
        Initialize research assistant.

        Args:
            model: AIModel instance for analysis
        """
        self.model = model
        self.sch = SemanticScholar()

    def search_papers(self, query: str, limit: int = DEFAULT_SEARCH_LIMIT) -> List[Dict[str, Any]]:
        """
        Search for academic papers.

        Args:
            query: Search query
            limit: Max results

        Returns:
            List of paper details
        """
        try:
            results = self.sch.search_paper(query, limit=limit)
            papers = []
            
            # Handle PaginatedResults or list
            items = results if isinstance(results, list) else results
            
            for item in items:
                papers.append({
                    "title": item.title,
                    "url": item.url,
                    "abstract": item.abstract,
                    "year": item.year,
                    "authors": [author.name for author in item.authors] if item.authors else [],
                    "citationCount": item.citationCount,
                    "paperId": item.paperId
                })
            return papers
        except Exception as e:
            logger.error(f"Error searching papers for '{query}': {e}")
            return []

    def suggest_sources(self, essay_text: str, limit: int = 3, max_queries: int = 2, search_limit: int = 2) -> List[Dict[str, Any]]:
        """
        Analyze essay and suggest relevant sources.

        Args:
            essay_text: The essay content
            limit: Number of final suggestions to return
            max_queries: Number of search queries to generate
            search_limit: Number of papers to fetch per query

        Returns:
            List of suggested papers
        """
        if not self.model:
            # Fallback: Use simple keyword extraction or just the first sentence
            # For MVP, let's just use "Artificial Intelligence Education" as a fallback query
            # based on the likely content, or extract from text.
            # A simple heuristic: take the first 5 words.
            words = essay_text.split()[:5]
            query = " ".join(words)
            logger.warning(f"Model unavailable. Using fallback query: '{query}'")
            return self.search_papers(query, limit=limit)

        # 1. Extract key topics/queries from essay
        # Truncate for token limits if needed
        truncated_text = essay_text[:MAX_ESSAY_LENGTH] 
        prompt = (
            "Analyze the following essay and generate 3 specific search queries "
            "to find academic papers that would support its arguments. "
            "Return ONLY the queries, one per line.\n\n"
            f"Essay:\n{truncated_text}..." 
        )

        success, response, error = self.model.call(prompt)
        if not success:
            logger.error(f"Failed to generate search queries: {error}")
            return []

        queries = [line.strip() for line in response.split('\n') if line.strip()]
        
        all_suggestions = []
        for query in queries[:max_queries]: # Search top queries
            papers = self.search_papers(query, limit=search_limit)
            all_suggestions.extend(papers)

        # Deduplicate by paperId
        seen = set()
        unique_suggestions = []
        for paper in all_suggestions:
            if paper['paperId'] not in seen:
                seen.add(paper['paperId'])
                unique_suggestions.append(paper)

        return unique_suggestions[:limit]

    def find_quotes(self, paper_id: str, topic: str) -> List[str]:
        """
        Find relevant quotes from a paper (simulated since we can't always get full text).
        
        In a real app, we might try to fetch open access full text or use abstract.
        """
        # For MVP, we'll just return the abstract if it matches the topic
        # or use the model to extract a "quote" from the abstract.
        try:
            paper = self.sch.get_paper(paper_id)
            if not paper or not paper.abstract:
                return []
            
            if not self.model:
                return [paper.abstract[:200] + "..."]

            prompt = (
                f"Extract a relevant quote (1-2 sentences) from the following abstract "
                f"that relates to '{topic}'. If none, return nothing.\n\n"
                f"Abstract:\n{paper.abstract}"
            )
            
            success, response, _ = self.model.call(prompt)
            if success and len(response) > 10:
                return [response]
            return []
            
        except Exception:
            return []

    def fact_check(self, claim: str, sources: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Verify if a claim is supported by the provided sources.

        Args:
            claim: The claim to verify
            sources: List of source dictionaries (must contain 'abstract' or 'title')

        Returns:
            Dictionary with 'supported' (bool), 'confidence' (float), and 'explanation' (str)
        """
        if not self.model:
            return {"supported": False, "confidence": 0.0, "explanation": "No AI model available."}

        # Prepare source context
        context = ""
        for i, source in enumerate(sources, 1):
            title = source.get('title', 'Unknown')
            abstract = source.get('abstract', '')
            if abstract:
                context += f"Source {i} ({title}):\n{abstract}\n\n"

        if not context:
            return {"supported": False, "confidence": 0.0, "explanation": "No source context available."}

        prompt = (
            f"Verify the following claim based ONLY on the provided sources.\n\n"
            f"Claim: {claim}\n\n"
            f"Sources:\n{context}\n"
            "Is the claim supported by the sources? Answer with JSON format:\n"
            "{\n"
            '  "supported": true/false,\n'
            '  "confidence": 0.0-1.0,\n'
            '  "explanation": "Brief explanation citing specific sources"\n'
            "}"
        )

        success, response, error = self.model.call(prompt)
        if not success:
            return {"supported": False, "confidence": 0.0, "explanation": f"AI Error: {error}"}

        try:
            # Clean up response to ensure valid JSON (sometimes models add markdown)
            clean_response = response.replace("```json", "").replace("```", "").strip()
            import json
            return json.loads(clean_response)
        except Exception as e:
            logger.error(f"Failed to parse fact check response: {e}")
            return {"supported": False, "confidence": 0.0, "explanation": "Failed to parse AI response."}

    def summarize_source(self, source: Dict[str, Any]) -> str:
        """
        Generate a concise summary of a source.

        Args:
            source: Source dictionary

        Returns:
            Summary string
        """
        if not self.model:
            return source.get('abstract', 'No abstract available.')[:200] + "..."

        title = source.get('title', 'Unknown Title')
        abstract = source.get('abstract', '')
        
        if not abstract:
            return f"{title}: No abstract available to summarize."

        prompt = (
            f"Summarize the following academic paper in 2-3 sentences for a general audience.\n\n"
            f"Title: {title}\n"
            f"Abstract: {abstract}"
        )

        success, response, error = self.model.call(prompt)
        if success:
            return response.strip()
        return "Failed to generate summary."
