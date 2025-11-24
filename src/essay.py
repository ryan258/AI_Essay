"""
Essay Maker Platform CLI.
"""

import fire
from pathlib import Path
import json
import os
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from threading import Thread
from dotenv import load_dotenv

load_dotenv()

from .citations import CitationManager
from .research import ResearchAssistant
from .drafter import EssayDrafter
from .analyzer import EssayAnalyzer
from .improver import EssayImprover
from .outline import OutlineGenerator, OutlineTemplate, ExportFormat
from .optimizer import GrammarOptimizer
from .argument import ArgumentAnalyzer
from .models.openrouter import OpenRouterModel
from .templates import TemplateManager
from .wizard import EssayWizard
from .export import Exporter
from .config import config
import asyncio

console = Console()

class EssayCLI:
    """CLI for the Essay Maker Platform."""

    def _init_model(self, model_name: str = None, role_env: str = None, fallback: str = config.DEFAULT_MODEL) -> OpenRouterModel:
        """
        Initialize AI model with env-aware fallback.

        Args:
            model_name: Explicit model passed via CLI flag
            role_env: Role-specific env var to check (e.g., MODEL_DRAFT)
            fallback: Hardcoded default if nothing else is set
        """
        role_model = os.getenv(role_env) if role_env else None
        env_model = os.getenv("OPENROUTER_MODEL")
        target_model = model_name or role_model or env_model or fallback

        if target_model:
            try:
                console.print(f"[dim]Using {target_model}...[/dim]")
                return OpenRouterModel(model_name=target_model)
            except Exception as e:
                console.print(f"[yellow]Warning: Could not initialize {target_model} ({e}).[/yellow]")
        
        try:
            return OpenRouterModel(model_name=fallback)
        except Exception as e:
            console.print(f"[red]Error initializing fallback model {fallback}: {e}[/red]")
            return None

    def _run_coroutine_in_thread(self, coro):
        """Run an async coroutine in a fresh thread to avoid nested event loop errors."""
        result_holder = {}
        error_holder = {}

        def _runner():
            try:
                result_holder["value"] = asyncio.run(coro)
            except Exception as exc:  # pragma: no cover - defensive
                error_holder["error"] = exc

        thread = Thread(target=_runner, daemon=True)
        thread.start()
        thread.join()

        if "error" in error_holder:
            raise error_holder["error"]

        return result_holder.get("value", [])

    def research(self, input_file: str, min_sources: int = 3, auto_cite: bool = False, gap_analysis: bool = False, model: str = None):
        """
        Research topics for an essay.

        Args:
            input_file: Path to the essay file
            min_sources: Minimum number of sources to find
            auto_cite: Whether to automatically add citations (not implemented yet)
            gap_analysis: Whether to perform research gap analysis
            model: AI model to use (default: anthropic/claude-3-haiku)
        """
        if model is None:
            model = config.DEFAULT_MODEL

        input_path = Path(input_file)
        if not input_path.exists():
            console.print(f"[red]Error: File {input_file} not found.[/red]")
            return

        text = input_path.read_text()

        # Initialize model and assistant
        ai_model = self._init_model(model, role_env="MODEL_RESEARCH")
        if ai_model:
            assistant = ResearchAssistant(model=ai_model)
        else:
            console.print("[yellow]Warning: Research capabilities limited (no AI model).[/yellow]")
            assistant = ResearchAssistant()

        console.print(Panel(f"Researching topics for {input_file}...", title="Research Assistant"))

        # Suggest sources
        console.print("[bold]Searching for relevant sources...[/bold]")
        suggestions = assistant.suggest_sources(text, limit=min_sources)
        
        if not suggestions:
            console.print("[yellow]No sources found.[/yellow]")
            return

        console.print(f"[green]Found {len(suggestions)} relevant sources:[/green]\n")
        
        def _to_csl(paper: dict, idx: int) -> dict:
            """Convert Semantic Scholar paper dict to a CSL-like structure."""
            authors = paper.get("authors") or []
            formatted_authors = []
            for name in authors:
                if isinstance(name, dict) and name.get("family"):
                    formatted_authors.append(name)
                    continue
                parts = name.strip().split() if isinstance(name, str) else []
                if len(parts) >= 2:
                    formatted_authors.append({"family": parts[-1], "given": " ".join(parts[:-1])})
                elif parts:
                    formatted_authors.append({"literal": parts[0]})
            year = paper.get("year") or 0
            csl = {
                "id": paper.get("paperId") or paper.get("id") or f"source-{idx}",
                "type": paper.get("publicationVenue", {}).get("type", "article-journal"),
                "title": paper.get("title", "Untitled"),
                "author": formatted_authors,
                "issued": {"date-parts": [[year]]} if year else {},
                "container-title": paper.get("publicationVenue", {}).get("name", "Semantic Scholar"),
                "URL": paper.get("url", ""),
                "abstract": paper.get("abstract", ""),
            }
            doi = paper.get("externalIds", {}).get("DOI") if isinstance(paper.get("externalIds"), dict) else None
            if doi:
                csl["DOI"] = doi
            return csl

        csl_sources = []
        for i, paper in enumerate(suggestions, 1):
            console.print(f"[bold]{i}. {paper['title']}[/bold]")
            console.print(f"   Authors: {', '.join(paper['authors'][:3])}")
            console.print(f"   Year: {paper['year']}")
            console.print(f"   Citations: {paper['citationCount']}")
            console.print(f"   URL: {paper['url']}")
            console.print()
            csl_sources.append(_to_csl(paper, i))

        # Persist sources for downstream citation steps
        try:
            sources_path = input_path.with_name(f"{input_path.stem}_sources.json")
            sources_path.write_text(json.dumps(csl_sources, indent=2))
            console.print(f"[dim]Saved sources to {sources_path}[/dim]")
        except Exception as e:
            console.print(f"[yellow]Warning: Could not save sources file ({e})[/yellow]")

        # Perform gap analysis if requested
        if gap_analysis:
            console.print(Panel("Analyzing Research Gaps...", title="Gap Analysis"))
            gaps = assistant.find_research_gaps(text)
            if gaps:
                console.print("[bold]Recommended Research Areas:[/bold]")
                for i, gap in enumerate(gaps, 1):
                    console.print(f"{i}. {gap}")
            else:
                console.print("[green]No significant research gaps found.[/green]")

    def cite(
        self,
        input_file: str,
        style: str = "apa",
        generate_bibliography: bool = False,
        model: str = None,
        output_file: str = None,
        annotate_missing: bool = True,
        auto_insert: bool = True,
        switch_to: str = None,
        lenient_fallback: bool = False,
    ):
        """
        Add citation markers and optionally append a bibliography.

        Args:
            input_file: Path to the essay file
            style: Citation style (apa, mla, chicago-author-date, ieee)
            generate_bibliography: Whether to append a bibliography
            output_file: Optional output path for the cited essay
            annotate_missing: Insert inline citation markers for detected claims
            auto_insert: Insert inline citations using available sources
            switch_to: Convert inline citations/bibliography to this style (overrides style)
            lenient_fallback: If True, use the first source when no keywords match (may be less relevant)
            model: AI model to use (default: anthropic/claude-3-haiku)
        """
        if model is None:
            model = config.DEFAULT_MODEL
        input_path = Path(input_file)
        if not input_path.exists():
            console.print(f"[red]Error: File {input_file} not found.[/red]")
            return

        text = input_path.read_text()
        annotated_text = text
        inline_style = switch_to or style
        # Initialize manager
        ai_model = self._init_model(model, role_env="MODEL_CITE")
        if ai_model:
            manager = CitationManager(model=ai_model)
        else:
            console.print("[yellow]Warning: Auto-claim detection disabled (no AI model).[/yellow]")
            manager = CitationManager()

        # Load any saved sources from previous research step
        sources_path = input_path.with_name(f"{input_path.stem}_sources.json")
        if sources_path.exists():
            try:
                raw = sources_path.read_text()
                saved_sources = json.loads(raw)
                if not isinstance(saved_sources, list):
                    raise ValueError("Sources file must contain a list")
                valid_sources = []
                for src in saved_sources:
                    if isinstance(src, dict) and src.get("id"):
                        valid_sources.append(src)
                if valid_sources:
                    manager.sources.extend(valid_sources)
                    console.print(f"[dim]Loaded {len(valid_sources)} source(s) from {sources_path}[/dim]")
            except json.JSONDecodeError as e:
                console.print(f"[yellow]Warning: Corrupt sources file ({e})[/yellow]")
            except Exception as e:
                console.print(f"[yellow]Warning: Could not load saved sources ({e})[/yellow]")

        console.print(Panel(f"Analyzing {input_file} for citations...", title="Citation Generator"))

        # 1. Find claims
        claims = manager.find_claims(text)
        if not claims:
            console.print("[yellow]No specific claims found requiring citation (or model unavailable).[/yellow]")
        else:
            console.print(f"[green]Found {len(claims)} claims needing citation.[/green]")
            for i, claim in enumerate(claims, 1):
                console.print(f"{i}. {claim}")

            inserted = 0
            if auto_insert and manager.sources:
                suggestions = manager.suggest_inline_citations(text, claims, style=inline_style, lenient=lenient_fallback)
                suggested_claims = {s["claim"] for s in suggestions}
                skipped_claims = [c for c in claims if c not in suggested_claims]
                for s in suggestions:
                    claim = s["claim"]
                    citation = s["citation"]
                    claim_with_marker = f"{claim} [citation needed]"
                    if claim_with_marker in annotated_text:
                        annotated_text = annotated_text.replace(
                            claim_with_marker, f"{claim} {citation}", 1
                        )
                        inserted += 1
                    elif claim in annotated_text:
                        annotated_text = annotated_text.replace(
                            claim, f"{claim} {citation}", 1
                        )
                        inserted += 1
                if inserted:
                    console.print(f"[green]Inserted {inserted} inline citation(s) using {inline_style.upper()}.[/green]")
                else:
                    console.print("[yellow]Could not place inline citations (claims not found verbatim in text).[/yellow]")
                if skipped_claims and not lenient_fallback:
                    console.print(f"[yellow]{len(skipped_claims)} claim(s) had no relevant sources (use --lenient-fallback to cite anyway).[/yellow]")
                # Replace any remaining markers with leftover citations in order
                remaining_markers = annotated_text.count("[citation needed]")
                if remaining_markers and manager.sources:
                    for i in range(remaining_markers):
                        source = manager.sources[i % len(manager.sources)]
                        # Defensive check (should exist if manager.sources is non-empty)
                        if not source:
                            continue
                        src_id = source.get("id")
                        if not src_id:
                            continue
                        citation = manager.format_citation(src_id, style=inline_style)
                        annotated_text = annotated_text.replace("[citation needed]", citation, 1)
            elif auto_insert and not manager.sources:
                console.print("[yellow]No sources available to insert inline citations; falling back to markers.[/yellow]")
                if annotate_missing:
                    for claim in claims:
                        if claim in annotated_text:
                            annotated_text = annotated_text.replace(
                                claim, f"{claim} [citation needed]", 1
                            )
                            inserted += 1
                    if inserted:
                        console.print(f"[green]Inserted {inserted} citation marker(s) into the text.[/green]")
            elif annotate_missing:
                for claim in claims:
                    if claim in annotated_text:
                        annotated_text = annotated_text.replace(
                            claim, f"{claim} [citation needed]", 1
                        )
                        inserted += 1
                if inserted:
                    console.print(f"[green]Inserted {inserted} citation marker(s) into the text.[/green]")
                else:
                    console.print("[yellow]Detected claims but could not place markers (claims not found verbatim in text).[/yellow]")
            else:
                console.print("[dim]Inline insertion disabled (auto_insert/annotate_missing False).[/dim]")
        
        # 2. Generate bibliography if requested
        bibliography_block = ""
        if generate_bibliography:
            # Add a dummy source for demonstration if none exist
            if not manager.sources:
                console.print("[yellow]No sources available. Add sources via research before generating a bibliography.[/yellow]")
            
            if manager.sources:
                try:
                    bib_style = inline_style
                    bib = manager.generate_bibliography(style=bib_style)
                    console.print(f"\n[bold]Bibliography ({bib_style.upper()}):[/bold]")
                    console.print(bib)
                    bibliography_block = "\n\n## Bibliography\n" + "\n".join(
                        f"- {line}" for line in bib.splitlines() if line.strip()
                    )
                except Exception as e:
                    console.print(f"[red]Error generating bibliography: {e}[/red]")

            # Demonstrate inline citations
            if manager.sources:
                console.print(f"\n[bold]Inline Citation Examples ({inline_style.upper()}):[/bold]")
                for source in manager.sources:
                    citation = manager.format_citation(source['id'], style=inline_style)
                    title = source.get('title', 'Unknown Title')
                    console.print(f"• {title}: [cyan]{citation}[/cyan]")
        
        # Save annotated output if we made changes
        made_inline_changes = inserted > 0 or (annotate_missing and claims)
        if made_inline_changes or bibliography_block:
            output_path = Path(output_file) if output_file else input_path.with_name(f"{input_path.stem}_cited{input_path.suffix}")
            output_text = annotated_text + bibliography_block
            output_path.write_text(output_text)
            console.print(f"\n[green]Saved cited essay to {output_path}[/green]")
        else:
            console.print("\n[dim]No changes saved (no claims detected and no bibliography generated).[/dim]")

    def check_plagiarism(self, input_file: str, model: str = None):
        """
        Check an essay for potential plagiarism (uncited quotes).

        Args:
            input_file: Path to the essay file
            model: AI model to use
        """
        if model is None:
            model = config.DEFAULT_MODEL

        input_path = Path(input_file)
        if not input_path.exists():
            console.print(f"[red]Error: File {input_file} not found.[/red]")
            return

        text = input_path.read_text()

        ai_model = self._init_model(model, role_env="MODEL_FACTCHECK")
        if not ai_model:
            return

        manager = CitationManager(model=ai_model)

        console.print(Panel(f"Scanning {input_file} for plagiarism...", title="Plagiarism Checker"))
        
        issues = manager.check_plagiarism(text)
        if not issues:
            console.print("[green]No obvious plagiarism detected (all quotes appear cited).[/green]")
        else:
            console.print(f"[yellow]Found {len(issues)} potential issues:[/yellow]")
            for i, issue in enumerate(issues, 1):
                console.print(f"{i}. {issue}")

    def summarize(self, query: str, limit: int = 3, model: str = None):
        """
        Find and summarize sources for a topic.

        Args:
            query: Topic to research
            limit: Number of sources
            model: AI model to use
        """
        if model is None:
            model = config.DEFAULT_MODEL

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

    def check_facts(self, input_file: str, claim: str, model: str = None):
        """
        Verify a specific claim using research from the essay's topic.

        Args:
            input_file: Path to the essay file (to get context/topic)
            claim: The claim to verify
            model: AI model to use
        """
        if model is None:
            model = config.DEFAULT_MODEL

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

    def draft(self, topic: str, models: str = None, output_dir: str = "drafts"):
        """
        Draft an essay using multiple AI models in parallel.

        Args:
            topic: The essay topic
            models: Comma-separated list of model IDs
            output_dir: Directory to save drafts
        """
        from datetime import datetime

        if models is None:
            models = f"{config.DEFAULT_MODEL},openai/gpt-3.5-turbo"

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
            try:
                asyncio.get_running_loop()
                # Already in an event loop (e.g., notebook) – run in a helper thread.
                results = self._run_coroutine_in_thread(drafter.draft_essay(topic, essay_dir))
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
        ai_model = self._init_model(model, role_env="MODEL_ANALYZE")
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

        ai_model = self._init_model(model, role_env="MODEL_ANALYZE")
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
        ai_model = self._init_model(model, role_env="MODEL_OUTLINE") if model else None
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

    def optimize(
        self,
        input_file: str,
        target_grade_level: float = None,
        prefer_active_voice: bool = True,
        apply_fixes: bool = False,
        model: str = None,
        output_file: str = None,
    ):
        """
        Optimize essay for grammar, clarity, and style.

        Args:
            input_file: Path to the essay file.
            target_grade_level: Target Flesch-Kincaid grade level.
            prefer_active_voice: Flag passive voice usage.
            apply_fixes: Whether to apply automatic fixes.
            model: Optional AI model for advanced grammar checking.
            output_file: Optional file to save optimized essay.
        """
        input_path = Path(input_file)
        if not input_path.exists():
            console.print(f"[red]Error: File {input_file} not found.[/red]")
            return

        text = input_path.read_text()

        # Initialize AI model if requested
        ai_model = self._init_model(model, role_env="MODEL_OPTIMIZE") if model else None
        optimizer = GrammarOptimizer(model=ai_model)

        console.print(Panel(f"Analyzing {input_file} for grammar, clarity, and style...", title="Grammar Optimizer"))

        # Run optimization
        result = optimizer.optimize(
            text=text,
            target_grade_level=target_grade_level,
            prefer_active_voice=prefer_active_voice,
            apply_fixes=apply_fixes,
        )

        # Display readability metrics
        console.print("\n[bold]Readability Metrics:[/bold]")
        metrics_table = Table(show_header=False, box=None)
        metrics_table.add_column("Metric", style="cyan")
        metrics_table.add_column("Value", style="white")

        metrics = result.metrics
        metrics_table.add_row("Flesch Reading Ease", f"{metrics.flesch_reading_ease:.1f} / 100")
        metrics_table.add_row("Grade Level", f"{metrics.flesch_kincaid_grade:.1f}")
        metrics_table.add_row("Avg Sentence Length", f"{metrics.avg_sentence_length:.1f} words")
        metrics_table.add_row("Avg Word Length", f"{metrics.avg_word_length:.1f} characters")
        metrics_table.add_row("Passive Voice", f"{metrics.passive_voice_percentage:.1f}%")
        metrics_table.add_row("Total Words", str(metrics.total_words))
        metrics_table.add_row("Total Sentences", str(metrics.total_sentences))
        metrics_table.add_row("Complex Words (>10 chars)", str(metrics.complex_words))

        console.print(metrics_table)

        # Categorize and display issues
        if result.issues:
            console.print(f"\n[bold]Found {len(result.issues)} issues:[/bold]\n")

            # Group by type
            by_type = {}
            for issue in result.issues:
                if issue.type not in by_type:
                    by_type[issue.type] = []
                by_type[issue.type].append(issue)

            # Display by severity
            for issue_type, issues_list in by_type.items():
                console.print(f"[bold]{issue_type.upper()}:[/bold]")
                for issue in issues_list[:10]:  # Limit to 10 per category
                    severity_color = {"error": "red", "warning": "yellow", "suggestion": "blue"}.get(issue.severity, "white")
                    console.print(f"  [{severity_color}]• {issue.message}[/{severity_color}]")
                    if issue.original_text:
                        console.print(f"    [dim]Original: {issue.original_text[:80]}[/dim]")
                    if issue.suggested_text:
                        console.print(f"    [green]Suggested: {issue.suggested_text[:80]}[/green]")

                if len(issues_list) > 10:
                    console.print(f"  [dim]... and {len(issues_list) - 10} more {issue_type} issues[/dim]")
                console.print()
        else:
            console.print("\n[green]No issues found! Essay looks great.[/green]")

        # Display grade level assessment
        if target_grade_level:
            if metrics.flesch_kincaid_grade <= target_grade_level:
                console.print(f"[green]✅ Grade level ({metrics.flesch_kincaid_grade:.1f}) meets target ({target_grade_level})[/green]")
            else:
                console.print(f"[yellow]⚠️  Grade level ({metrics.flesch_kincaid_grade:.1f}) exceeds target ({target_grade_level})[/yellow]")

        # Save optimized text if fixes were applied
        if apply_fixes and result.improvements_applied > 0 and result.optimized_text:
            if output_file:
                output_path = Path(output_file)
            else:
                output_path = input_path.parent / f"{input_path.stem}_optimized{input_path.suffix}"

            output_path.write_text(result.optimized_text)
            console.print(f"\n[green]Applied {result.improvements_applied} automatic fixes[/green]")
            console.print(f"[dim]Saved to {output_path}[/dim]")
        elif apply_fixes and result.improvements_applied == 0:
            console.print("\n[yellow]No automatic fixes available (manual review needed)[/yellow]")

    def analyze_argument(self, input_file: str, model: str = None):
        """
        Analyze the argument strength and structure of an essay.

        Args:
            input_file: Path to the essay file.
            model: Optional AI model to use.
        """
        input_path = Path(input_file)
        if not input_path.exists():
            console.print(f"[red]Error: File {input_file} not found.[/red]")
            return

        text = input_path.read_text()

        # Initialize AI model
        ai_model = self._init_model(model, role_env="MODEL_ARGUMENT")
        
        # Fallback to default model if none specified but required for this feature
        if not ai_model:
             console.print("[red]Error: Argument analysis requires a working AI model configuration.[/red]")
             return

        analyzer = ArgumentAnalyzer(model=ai_model)

        console.print(Panel(f"Analyzing arguments in {input_file}...", title="Argument Analyzer"))

        analysis = analyzer.analyze(text)

        # Display Thesis
        console.print("\n[bold]Thesis Statement:[/bold]")
        if analysis.thesis:
            console.print(f"[italic]{analysis.thesis}[/italic]")
        else:
            console.print("[yellow]No clear thesis statement detected.[/yellow]")

        # Display Claims
        console.print("\n[bold]Supporting Claims:[/bold]")
        if analysis.claims:
            for i, claim in enumerate(analysis.claims, 1):
                strength_color = {
                    "strong": "green",
                    "moderate": "yellow",
                    "weak": "red"
                }.get(claim.strength.lower(), "white")
                
                console.print(f"{i}. [bold]{claim.text}[/bold]")
                console.print(f"   Type: {claim.type}")
                console.print(f"   Strength: [{strength_color}]{claim.strength.upper()}[/{strength_color}]")
                if claim.evidence and claim.evidence.lower() != "none":
                    console.print(f"   Evidence: {claim.evidence}")
                if claim.explanation:
                    console.print(f"   Analysis: [dim]{claim.explanation}[/dim]")
                console.print()
        else:
            console.print("[dim]No distinct supporting claims found.[/dim]")

        # Display Fallacies
        if analysis.fallacies:
            console.print("\n[bold red]Detected Logical Fallacies:[/bold red]")
            for fallacy in analysis.fallacies:
                console.print(f"• [bold]{fallacy.name}[/bold]: {fallacy.text}")
                console.print(f"  [dim]{fallacy.explanation}[/dim]")
        else:
            console.print("\n[green]No logical fallacies detected.[/green]")

        # Display Overall Score & Critique
        console.print("\n[bold]Overall Evaluation:[/bold]")
        score_color = "green" if analysis.overall_strength >= 8 else "yellow" if analysis.overall_strength >= 5 else "red"
        console.print(f"Strength Score: [{score_color}]{analysis.overall_strength}/10[/{score_color}]")
        console.print(f"\n[italic]{analysis.critique}[/italic]")

        # Display Suggestions
        if analysis.suggestions:
            console.print("\n[bold]Suggestions for Improvement:[/bold]")
            for i, suggestion in enumerate(analysis.suggestions, 1):
                console.print(f"{i}. {suggestion}")

    def templates(self, action: str = "list", name: str = None):
        """
        Manage essay templates.

        Args:
            action: Action to perform (list)
            name: Template name (for future use)
        """
        manager = TemplateManager()
        
        if action == "list":
            templates = manager.list_templates()
            console.print(Panel("Available Essay Templates", title="Template Library"))
            
            table = Table(show_header=True, header_style="bold")
            table.add_column("Name", style="cyan")
            table.add_column("Type", style="white")
            table.add_column("Description", style="dim")
            
            for t in templates:
                table.add_row(t["name"], t["type"], t["description"])
            
            console.print(table)
        else:
            console.print(f"[red]Unknown action: {action}[/red]")

    def new(self, topic: str, template: str = "argumentative", output_file: str = None):
        """
        Create a new essay from a template.

        Args:
            topic: Essay topic
            template: Template name
            output_file: Output file path (optional)
        """
        manager = TemplateManager()
        tmpl = manager.get_template(template)
        
        if not tmpl:
            console.print(f"[red]Error: Template '{template}' not found.[/red]")
            console.print("Run 'uv run essay.py templates list' to see available templates.")
            return

        content = manager.render_template(tmpl, topic)
        
        if output_file:
            path = Path(output_file)
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
            console.print(f"[green]Created new essay from template '{template}' at {output_file}[/green]")
        else:
            console.print(content)

    def template_create(self, from_file: str, name: str, description: str = "Custom template"):
        """
        Create a new template from an existing essay file (simplified).
        
        Derives a lightweight structure from the provided essay instead of a static stub.
        """
        manager = TemplateManager()

        source_path = Path(from_file)
        if not source_path.exists():
            console.print(f"[red]Error: Source file '{from_file}' not found.[/red]")
            return

        content = source_path.read_text().strip()
        paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

        def _section_entry(title: str, paragraph: str) -> dict:
            """Create a section definition from a paragraph snippet."""
            words = paragraph.split()
            snippet = " ".join(paragraph.split(".")[0].split()[:15])
            desc = snippet + ("..." if snippet else "")
            return {
                "title": title,
                "description": desc or "Section derived from source essay",
                "word_count": len(words),
            }

        structure = []
        if paragraphs:
            # Intro from first paragraph
            structure.append(_section_entry("Introduction", paragraphs[0]))

            # Body paragraphs
            body_paragraphs = paragraphs[1:-1] if len(paragraphs) > 2 else paragraphs[1:]
            for idx, para in enumerate(body_paragraphs, 1):
                structure.append(_section_entry(f"Body {idx}", para))

            # Conclusion if present
            if len(paragraphs) > 1:
                structure.append(_section_entry("Conclusion", paragraphs[-1]))
        else:
            structure = [
                {"title": "Introduction", "description": "Introduction section", "word_count": "flexible"},
                {"title": "Body", "description": "Main content", "word_count": "flexible"},
                {"title": "Conclusion", "description": "Conclusion section", "word_count": "flexible"},
            ]

        if manager.create_template(name, description, structure):
            console.print(f"[green]Created new template '{name}'[/green]")
        else:
            console.print(f"[red]Failed to create template '{name}'[/red]")

    def wizard(self):
        """
        Start the interactive essay creation wizard.
        """
        wizard = EssayWizard()
        wizard.run()

    def export(self, file: str, format: str = "pdf", output: str = None):
        """
        Export an essay to a different format.

        Args:
            file: Path to the input markdown file.
            format: Target format (pdf, docx, html).
            output: Optional output path.
        """
        input_path = Path(file)
        if not input_path.exists():
            console.print(f"[red]Error: File '{file}' not found.[/red]")
            return

        if not output:
            output = str(input_path.with_suffix(f".{format}"))

        exporter = Exporter()
        console.print(f"[dim]Exporting {file} to {format.upper()}...[/dim]")
        
        if exporter.export(input_path.read_text(), format, output):
            console.print(f"[green]Successfully exported to {output}[/green]")
        else:
            console.print(f"[red]Export failed. Check logs for details.[/red]")


def main():
    fire.Fire(EssayCLI)

if __name__ == "__main__":
    main()
