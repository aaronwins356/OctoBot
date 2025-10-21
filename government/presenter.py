"""Portfolio presentation tooling for Grounded Lifestyle."""
from __future__ import annotations

from pathlib import Path
from typing import Dict, List

from jinja2 import Environment, FileSystemLoader, select_autoescape

from government.proposal_manager import VentureProposal, filter_approved, load_proposals
from utils.logger import get_logger

LOGGER = get_logger(__name__)


class PortfolioPresenter:
    """Build static HTML views summarising approved ventures."""

    def __init__(self, template_dir: Path, output_dir: Path) -> None:
        self.template_dir = template_dir
        self.output_dir = output_dir
        self.env = Environment(
            loader=FileSystemLoader(str(template_dir)),
            autoescape=select_autoescape(["html", "xml"]),
        )
        self.env.globals['url_for'] = self._url_for

    def _url_for(self, endpoint: str, **values: object) -> str:
        if endpoint == 'static':
            filename = values.get('filename', '')
            return f'static/{filename}'
        if endpoint == 'home':
            return 'index.html'
        if endpoint == 'about':
            return 'about.html'
        if endpoint == 'contact':
            return 'contact.html'
        if endpoint == 'venture_detail':
            proposal_id = values.get('proposal_id', '')
            return f'ventures/{proposal_id}.html'
        return 'index.html'

    def _render_template(self, name: str, context: Dict[str, object]) -> str:
        template = self.env.get_template(name)
        return template.render(**context)

    def build_homepage(self, proposals: List[VentureProposal]) -> Path:
        LOGGER.info("Rendering portfolio homepage with %d ventures", len(proposals))
        html = self._render_template(
            "home.html",
            {
                "ventures": proposals,
                "placeholder_mode": not proposals,
            },
        )
        target = self.output_dir / "index.html"
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(html, encoding="utf-8")
        return target

    def build_reference_pages(self) -> List[Path]:
        pages = {
            'about.html': {
                'proposal_id': 'about',
                'proposal_name': 'Human-Supervised AI Entrepreneurship',
                'author_agent': 'presenter',
                'description': 'Grounded Lifestyle pairs AI ideation with human judgment to explore ethical ventures.',
                'expected_cost': 'Variable',
                'expected_revenue': 'Long-term goodwill',
                'strategy': 'Propose, refine, and release only with Aaron’s explicit approval.',
                'ethical_statement': 'Every deployment is initiated by a human.',
                'files_created': [],
                'status': 'reference',
                'require_human_approval': True,
            },
            'contact.html': {
                'proposal_id': 'contact',
                'proposal_name': 'Collaborate with Grounded Lifestyle',
                'author_agent': 'presenter',
                'description': 'Reach out to discuss mindful digital ventures.',
                'expected_cost': 'N/A',
                'expected_revenue': 'Relationship building',
                'strategy': 'Email hello@groundedlifestyle.org with your ideas.',
                'ethical_statement': 'All conversations begin with mutual consent.',
                'files_created': [],
                'status': 'reference',
                'require_human_approval': True,
            },
        }
        created: List[Path] = []
        for filename, data in pages.items():
            venture = VentureProposal(**data)
            html = self._render_template('venture_page.html', {'venture': venture})
            target = self.output_dir / filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding='utf-8')
            created.append(target)
        return created

    def build_venture_pages(self, proposals: List[VentureProposal]) -> List[Path]:
        created: List[Path] = []
        for proposal in proposals:
            html = self._render_template(
                "venture_page.html",
                {
                    "venture": proposal,
                },
            )
            target = self.output_dir / "ventures" / f"{proposal.slug}.html"
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(html, encoding="utf-8")
            created.append(target)
        LOGGER.info("Rendered %d venture detail pages", len(created))
        return created


def build_portfolio(output_dir: Path | None = None, template_dir: Path | None = None) -> List[Path]:
    """Render the Grounded Lifestyle portfolio without deploying it."""

    template_path = template_dir or Path("website/templates")
    output_path = output_dir or Path("website/public")
    presenter = PortfolioPresenter(template_path, output_path)
    proposals = filter_approved(load_proposals())
    created_files = [presenter.build_homepage(proposals)]
    created_files.extend(presenter.build_venture_pages(proposals))
    created_files.extend(presenter.build_reference_pages())
    LOGGER.info("Portfolio build complete (%d files)", len(created_files))
    return created_files


__all__ = ["PortfolioPresenter", "build_portfolio"]
