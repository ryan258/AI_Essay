"""
Essay Maker Platform CLI.
"""

import fire
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .citations import CitationManager
from .research import ResearchAssistant
from .drafter import EssayDrafter
from .analyzer import EssayAnalyzer
from .improver import EssayImprover
from .outline import OutlineGenerator, OutlineTemplate, ExportFormat
from .models.openrouter import OpenRouterModel
import asyncio

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

    def draft(self, topic: str, models: str = "anthropic/claude-3-haiku,openai/gpt-3.5-turbo", output_dir: str = "drafts"):
        """
        Draft an essay using multiple AI models in parallel.

        Args:
            topic: The essay topic
            models: Comma-separated list of model IDs
            output_dir: Directory to save drafts
        """
        from datetime import datetime

        model_list = [m.strip() for m in models.split(',')]
        console.print(Panel(f"Drafting essay on '{topic}' using {len(model_list)} models...", title="Essay Drafter"))

        # Initialize models
        ai_models = []
        for m in model_list:
            try:
                ai_models.append(OpenRouterModel(model_name=m))
            except Exception as e:
                console.print(f"[red]Error initializing {m}: {e}[/red]")

        if not ai_models:
            console.print("[red]No valid models available. Aborting.[/red]")
            return

        drafter = EssayDrafter(models=ai_models)

        # Create timestamped output directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        topic_slug = topic.replace(" ", "_")[:50]  # Limit length
        essay_dir = Path(output_dir) / f"{timestamp}_{topic_slug}"

        # Run async drafting with proper event loop handling
        try:
            # Check if there's already a running event loop
            try:
                loop = asyncio.get_running_loop()
                # We're in an async context, can't use asyncio.run()
                console.print("[yellow]Warning: Cannot run in existing event loop context[/yellow]")
                return
            except RuntimeError:
                # No running loop, safe to use asyncio.run()
                results = asyncio.run(drafter.draft_essay(topic, essay_dir))
        except Exception as e:
            console.print(f"[red]Error during drafting: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return

        # Report results
        console.print(f"\n[bold]Drafting Complete![/bold]")
        console.print(f"[dim]Output directory: {essay_dir}[/dim]\n")

        for res in results:
            model_name = res['model']
            if res['success']:
                word_count = res.get('word_count', 0)
                console.print(f"[green]✅ {model_name}: {word_count} words → {res['file']}[/green]")
            else:
                console.print(f"[red]❌ {model_name}: Failed ({res['error']})[/red]")

    def analyze(self, input_file: str, model: str = None):
        """
        Analyze essay structure and provide recommendations.

        Args:
            input_file: Path to the essay file
            model: Optional AI model for advanced thesis extraction
        """
        input_path = Path(input_file)
        if not input_path.exists():
            console.print(f"[red]Error: File {input_file} not found.[/red]")
            return

        essay_text = input_path.read_text()

        # Initialize analyzer
        ai_model = None
        if model:
            try:
                ai_model = OpenRouterModel(model_name=model)
                console.print(f"[dim]Using {model} for advanced analysis[/dim]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not initialize AI model ({e}). Using basic analysis.[/yellow]")

        analyzer = EssayAnalyzer(model=ai_model)

        console.print(Panel(f"Analyzing structure of {input_file}...", title="Essay Analyzer"))

        # Analyze
        structure = analyzer.analyze(essay_text)

        # Print results
        analyzer.print_analysis(structure)

    def improve(
        self,
        input_file: str,
        cycles: int = 3,
        target_score: int = 85,
        model: str = None,
        output_dir: str = "improvements"
    ):
        """
        Iteratively improve an essay.

        Args:
            input_file: Path to the essay file.
            cycles: Maximum number of improvement cycles.
            target_score: Stop early once this score is met.
            model: Optional model ID for AI-powered improvements.
            output_dir: Directory to save the improved essay.
        """
        from datetime import datetime

        input_path = Path(input_file)
        if not input_path.exists():
            console.print(f"[red]Error: File {input_file} not found.[/red]")
            return

        essay_text = input_path.read_text()

        ai_model = None
        if model:
            try:
                ai_model = OpenRouterModel(model_name=model)
                console.print(f"[dim]Using {model} for improvements[/dim]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not initialize AI model ({e}). Falling back to heuristics.[/yellow]")

        improver = EssayImprover(model=ai_model)

        console.print(Panel(f"Improving {input_file} for clarity, grammar, and argument strength...", title="Essay Improver"))

        def _progress(iteration: int, total: int) -> None:
            console.print(f"[dim]Running improvement cycle {iteration}/{total}...[/dim]")

        result = improver.improve(
            essay_text,
            cycles=cycles,
            target_score=target_score,
            progress_callback=_progress,
        )

        if not result.iterations:
            console.print("[green]Essay already meets the target score. No changes applied.[/green]")
            return

        # Show score deltas per iteration
        table = Table(show_header=True, header_style="bold")
        table.add_column("Iter", width=6)
        table.add_column("Clarity", width=14)
        table.add_column("Grammar", width=14)
        table.add_column("Argument", width=14)
        table.add_column("Overall", width=14)
        table.add_column("Model", width=10)

        for step in result.iterations:
            table.add_row(
                str(step.iteration),
                f"{step.scores_before.clarity:.1f} → {step.scores_after.clarity:.1f}",
                f"{step.scores_before.grammar:.1f} → {step.scores_after.grammar:.1f}",
                f"{step.scores_before.argument_strength:.1f} → {step.scores_after.argument_strength:.1f}",
                f"{step.scores_before.overall:.1f} → {step.scores_after.overall:.1f}",
                step.applied_model or "heuristic"
            )

        console.print(table)

        # Show before/after snippets
        def _snippet(text: str, length: int = 180) -> str:
            return text[:length].strip() + ("..." if len(text) > length else "")

        for step in result.iterations:
            console.print(f"\n[bold]Iteration {step.iteration} preview[/bold]")
            console.print(f"[dim]Before:[/dim] {_snippet(step.before_text)}")
            console.print(f"[green]After:[/green] {_snippet(step.after_text)}")

        # Save final essay
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        final_file = output_path / f"{input_path.stem}_improved_{timestamp}.txt"
        final_file.write_text(result.final_text)

        status_color = "green" if result.reached_target else "yellow"
        console.print(f"\n[{status_color}]Final overall score: {result.final_scores.overall:.1f} / 100 (target {target_score})[/{status_color}]")
        console.print(f"[dim]Saved to {final_file}[/dim]\n")

    def outline(
        self,
        topic: str = None,
        notes_file: str = None,
        template: str = "5-paragraph",
        word_count: int = 1000,
        model: str = None,
        format: str = "markdown",
        output_file: str = None,
    ):
        """
        Generate a structured essay outline.

        Args:
            topic: Essay topic (required if notes_file not provided).
            notes_file: Path to rough notes file (alternative to topic).
            template: Outline template (5-paragraph, analytical, comparative, argumentative).
            word_count: Target word count for the essay.
            model: Optional AI model for intelligent outline generation.
            format: Export format (markdown, json, plain).
            output_file: Optional file to save the outline.
        """
        # Validate inputs
        if not topic and not notes_file:
            console.print("[red]Error: Either --topic or --notes-file must be provided.[/red]")
            return

        # Parse template
        try:
            template_enum = OutlineTemplate(template)
        except ValueError:
            console.print(f"[red]Error: Unknown template '{template}'. Valid options: 5-paragraph, analytical, comparative, argumentative[/red]")
            return

        # Parse format
        try:
            format_enum = ExportFormat(format)
        except ValueError:
            console.print(f"[red]Error: Unknown format '{format}'. Valid options: markdown, json, plain[/red]")
            return

        # Initialize AI model if requested
        ai_model = None
        if model:
            try:
                ai_model = OpenRouterModel(model_name=model)
                console.print(f"[dim]Using {model} for intelligent outline generation[/dim]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not initialize AI model ({e}). Using template-based generation.[/yellow]")

        generator = OutlineGenerator(model=ai_model)

        console.print(Panel(f"Generating {template} outline...", title="Outline Generator"))

        # Generate outline
        if notes_file:
            # Convert notes to outline
            notes_path = Path(notes_file)
            if not notes_path.exists():
                console.print(f"[red]Error: Notes file {notes_file} not found.[/red]")
                return

            notes = notes_path.read_text()
            outline = generator.convert_notes_to_outline(
                notes=notes,
                template=template_enum,
                word_count=word_count,
            )
        else:
            # Generate from topic
            outline = generator.generate(
                topic=topic,
                template=template_enum,
                word_count=word_count,
            )

        # Export outline
        output = generator.export(outline, format_enum)

        # Save or print
        if output_file:
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(output)
            console.print(f"[green]Outline saved to {output_file}[/green]")
        else:
            console.print("\n" + output)

        # Show summary
        console.print(f"\n[bold]Outline Summary:[/bold]")
        console.print(f"  Topic: {outline.topic}")
        console.print(f"  Template: {outline.template_type}")
        console.print(f"  Sections: {len(outline.sections)}")
        console.print(f"  Total word count: {outline.total_word_count}")

def main():
    fire.Fire(EssayCLI)

if __name__ == "__main__":
    main()
