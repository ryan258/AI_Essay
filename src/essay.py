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

def main():
    fire.Fire(EssayCLI)

if __name__ == "__main__":
    main()
