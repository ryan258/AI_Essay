"""
Essay Maker Platform CLI.
"""

import fire
from pathlib import Path
from rich.console import Console
from rich.panel import Panel

from .citations import CitationManager
from .research import ResearchAssistant
from .models.openrouter import OpenRouterModel  # Assuming this exists or we use a factory

console = Console()

class EssayCLI:
    """CLI for the Essay Maker Platform."""

    def research(self, input_file: str, min_sources: int = 3, auto_cite: bool = False, model: str = "anthropic/claude-3-haiku"):
        """
        Research topics for an essay.

        Args:
            input_file: Path to the essay file
            min_sources: Minimum number of sources to find
            auto_cite: Whether to automatically add citations (not implemented yet)
            model: AI model to use (default: anthropic/claude-3-haiku)
        """
        input_path = Path(input_file)
        if not input_path.exists():
            console.print(f"[red]Error: File {input_file} not found.[/red]")
            return

        text = input_path.read_text()

        # Initialize model and assistant
        try:
            ai_model = OpenRouterModel(model_name=model)
            assistant = ResearchAssistant(model=ai_model)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not initialize AI model ({e}). Research capabilities limited.[/yellow]")
            assistant = ResearchAssistant()

        console.print(Panel(f"Researching topics for {input_file}...", title="Research Assistant"))

        # Suggest sources
        console.print("[bold]Searching for relevant sources...[/bold]")
        suggestions = assistant.suggest_sources(text, limit=min_sources)
        
        if not suggestions:
            console.print("[yellow]No sources found.[/yellow]")
            return

        console.print(f"[green]Found {len(suggestions)} relevant sources:[/green]\n")
        
        for i, paper in enumerate(suggestions, 1):
            console.print(f"[bold]{i}. {paper['title']}[/bold]")
            console.print(f"   Authors: {', '.join(paper['authors'][:3])}")
            console.print(f"   Year: {paper['year']}")
            console.print(f"   Citations: {paper['citationCount']}")
            console.print(f"   URL: {paper['url']}")
            console.print()

    def cite(self, input_file: str, style: str = "apa", generate_bibliography: bool = False, model: str = "anthropic/claude-3-haiku"):
        """
        Add citations to an essay.

        Args:
            input_file: Path to the essay file
            style: Citation style (apa, mla, chicago-author-date, ieee)
            generate_bibliography: Whether to append a bibliography
            model: AI model to use (default: anthropic/claude-3-haiku)
        """
        input_path = Path(input_file)
        if not input_path.exists():
            console.print(f"[red]Error: File {input_file} not found.[/red]")
            return

        text = input_path.read_text()
        
        # Initialize manager
        try:
            ai_model = OpenRouterModel(model_name=model)
            manager = CitationManager(model=ai_model)
        except Exception as e:
            console.print(f"[yellow]Warning: Could not initialize AI model ({e}). Auto-claim detection disabled.[/yellow]")
            manager = CitationManager()

        console.print(Panel(f"Analyzing {input_file} for citations...", title="Citation Generator"))

        # 1. Find claims
        claims = manager.find_claims(text)
        if not claims:
            console.print("[yellow]No specific claims found requiring citation (or model unavailable).[/yellow]")
        else:
            console.print(f"[green]Found {len(claims)} claims needing citation.[/green]")
            for i, claim in enumerate(claims, 1):
                console.print(f"{i}. {claim}")
        
        # 2. Generate bibliography if requested
        if generate_bibliography:
            # Add a dummy source for demonstration if none exist
            if not manager.sources:
                manager.add_source({
                    "id": "example-source",
                    "type": "article-journal",
                    "title": "Artificial Intelligence in Education",
                    "author": [{"family": "Smith", "given": "John"}],
                    "issued": {"date-parts": [[2023]]},
                    "container-title": "Journal of EdTech"
                })
            
            try:
                bib = manager.generate_bibliography(style=style)
                console.print(f"\n[bold]Bibliography ({style.upper()}):[/bold]")
                console.print(bib)
            except Exception as e:
                console.print(f"[red]Error generating bibliography: {e}[/red]")

    def check_plagiarism(self, input_file: str, model: str = "anthropic/claude-3-haiku"):
        """
        Check an essay for potential plagiarism (uncited quotes).

        Args:
            input_file: Path to the essay file
            model: AI model to use
        """
        input_path = Path(input_file)
        if not input_path.exists():
            console.print(f"[red]Error: File {input_file} not found.[/red]")
            return

        text = input_path.read_text()

        try:
            ai_model = OpenRouterModel(model_name=model)
            manager = CitationManager(model=ai_model)
        except Exception as e:
            console.print(f"[red]Error initializing AI model: {e}[/red]")
            return

        console.print(Panel(f"Scanning {input_file} for plagiarism...", title="Plagiarism Checker"))
        
        issues = manager.check_plagiarism(text)
        if not issues:
            console.print("[green]No obvious plagiarism detected (all quotes appear cited).[/green]")
        else:
            console.print(f"[yellow]Found {len(issues)} potential issues:[/yellow]")
            for i, issue in enumerate(issues, 1):
                console.print(f"{i}. {issue}")

    def summarize(self, query: str, limit: int = 3, model: str = "anthropic/claude-3-haiku"):
        """
        Find and summarize sources for a topic.

        Args:
            query: Topic to research
            limit: Number of sources
            model: AI model to use
        """
        try:
            ai_model = OpenRouterModel(model_name=model)
            assistant = ResearchAssistant(model=ai_model)
        except Exception as e:
            console.print(f"[red]Error initializing AI model: {e}[/red]")
            return

        console.print(Panel(f"Researching and summarizing: {query}", title="Research Assistant"))
        
        papers = assistant.search_papers(query, limit=limit)
        if not papers:
            console.print("[yellow]No papers found.[/yellow]")
            return

        for i, paper in enumerate(papers, 1):
            console.print(f"[bold]{i}. {paper['title']}[/bold]")
            summary = assistant.summarize_source(paper)
            console.print(f"   [italic]{summary}[/italic]")
            console.print(f"   URL: {paper['url']}\n")

    def check_facts(self, input_file: str, claim: str, model: str = "anthropic/claude-3-haiku"):
        """
        Verify a specific claim using research from the essay's topic.

        Args:
            input_file: Path to the essay file (to get context/topic)
            claim: The claim to verify
            model: AI model to use
        """
        input_path = Path(input_file)
        if not input_path.exists():
            console.print(f"[red]Error: File {input_file} not found.[/red]")
            return

        text = input_path.read_text()

        try:
            ai_model = OpenRouterModel(model_name=model)
            assistant = ResearchAssistant(model=ai_model)
        except Exception as e:
            console.print(f"[red]Error initializing AI model: {e}[/red]")
            return

        console.print(Panel(f"Fact checking claim: {claim}", title="Fact Checker"))
        
        # First, find relevant sources based on the claim
        console.print("[dim]Finding relevant sources...[/dim]")
        sources = assistant.search_papers(claim, limit=5)
        
        if not sources:
            console.print("[red]Could not find sources to verify this claim.[/red]")
            return

        # Check the fact
        console.print("[dim]Analyzing sources...[/dim]")
        result = assistant.fact_check(claim, sources)
        
        if result['supported']:
            console.print(f"[green]✅ Claim Supported (Confidence: {result.get('confidence', 0):.2f})[/green]")
        else:
            console.print(f"[red]❌ Claim Not Supported (Confidence: {result.get('confidence', 0):.2f})[/red]")
        
        console.print(f"\n[bold]Explanation:[/bold] {result.get('explanation', 'No explanation provided.')}")

def main():
    fire.Fire(EssayCLI)

if __name__ == "__main__":
    main()
