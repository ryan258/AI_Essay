"""
Interactive Essay Wizard.
"""
import asyncio
import os
from rich.console import Console
from rich.prompt import Prompt, Confirm, IntPrompt
from rich.panel import Panel
from pathlib import Path
from datetime import datetime

from .templates import TemplateManager
from .research import ResearchAssistant
from .drafter import EssayDrafter
from .models.openrouter import OpenRouterModel
from .config import config

console = Console()

class EssayWizard:
    """Interactive wizard for essay creation."""

    def __init__(self):
        # Initialize with a default model for research/drafting
        self.model_name = os.getenv("OPENROUTER_MODEL", config.DEFAULT_MODEL)
        self.template_manager = TemplateManager()

    def run(self):
        """Run the interactive wizard."""
        console.clear()
        console.print(Panel.fit(
            "[bold]Welcome to the Essay Wizard! 🧙‍♂️[/bold]\n"
            "I'll guide you through creating your essay step-by-step.",
            title="Essay Wizard",
            border_style="blue"
        ))

        # --- Step 1: Collect Inputs ---
        
        # Topic
        topic = Prompt.ask("\n📝 What is the [bold cyan]topic[/bold cyan] of your essay?")
        
        # Template
        templates = self.template_manager.list_templates()
        template_choices = [t["name"] for t in templates]
        template_name = Prompt.ask(
            "📋 Choose a [bold cyan]template[/bold cyan]", 
            choices=template_choices, 
            default="argumentative"
        )
        
        # Word Count
        word_count = IntPrompt.ask("📏 Target [bold cyan]word count[/bold cyan]", default=1000)
        
        # Research
        do_research = Confirm.ask("🔍 Do you want to [bold cyan]find sources[/bold cyan] for this topic?")
        
        # --- Step 2: Confirm Plan ---
        
        console.print("\n[bold]Here's the plan:[/bold]")
        console.print(f"• Topic: {topic}")
        console.print(f"• Template: {template_name}")
        console.print(f"• Length: {word_count} words")
        console.print(f"• Research: {'Yes' if do_research else 'No'}")
        
        if not Confirm.ask("\nReady to start?", default=True):
            console.print("[yellow]Aborted.[/yellow]")
            return

        # --- Step 3: Execution ---
        
        # Create output directory
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_topic = "".join(c if c.isalnum() else "_" for c in topic)[:30]
        output_dir = Path("wizard_output") / f"{timestamp}_{safe_topic}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        console.print(f"\n[dim]Working directory: {output_dir}[/dim]")

        # Initialize AI Model
        try:
            model = OpenRouterModel(model_name=self.model_name)
        except Exception as e:
            console.print(f"[red]Error initializing AI model: {e}[/red]")
            return

        # A. Research
        sources = []
        if do_research:
            with console.status("[bold green]Researching topic...[/bold green]"):
                assistant = ResearchAssistant(model=model)
                sources = assistant.suggest_sources(topic, limit=3)
            
            if sources:
                console.print(f"\n[green]Found {len(sources)} sources:[/green]")
                for s in sources:
                    console.print(f"• {s.get('title', 'Unknown')} ({s.get('year', 'n.d.')})")
            else:
                console.print("\n[yellow]No sources found.[/yellow]")

        # B. Outline
        with console.status("[bold green]Generating outline...[/bold green]"):
            tmpl = self.template_manager.get_template(template_name)
            if tmpl:
                outline_content = self.template_manager.render_template(tmpl, topic)
                
                # Append sources if any
                if sources:
                    outline_content += "\n\n## References\n"
                    for s in sources:
                        title = s.get('title', 'Unknown')
                        url = s.get('url', '')
                        outline_content += f"- {title} {f'({url})' if url else ''}\n"
                
                outline_path = output_dir / "outline.md"
                outline_path.write_text(outline_content)
                console.print(f"\n[green]✅ Outline created at {outline_path}[/green]")
            else:
                console.print(f"[red]Error: Template {template_name} not found.[/red]")

        # C. Draft
        if Confirm.ask("\nDo you want to [bold cyan]generate a full draft[/bold cyan] now?"):
            console.print("[dim]Starting drafting process (this may take a minute)...[/dim]")
            
            drafter = EssayDrafter(models=[model])
            
            # Run async drafting
            try:
                results = asyncio.run(drafter.draft_essay(topic, output_dir))
                
                success_count = sum(1 for r in results if r['success'])
                if success_count > 0:
                    console.print(f"\n[green]✅ Draft generated successfully![/green]")
                    for res in results:
                        if res['success']:
                            console.print(f"• {res['file']} ({res.get('word_count', 0)} words)")
                else:
                    console.print("\n[red]Drafting failed.[/red]")
                    
            except Exception as e:
                console.print(f"[red]Error during drafting: {e}[/red]")

        console.print(f"\n[bold blue]Wizard complete! 🧙‍♂️[/bold blue]")
        console.print(f"Open [bold]{output_dir}[/bold] to see your files.")
