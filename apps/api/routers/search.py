"""
AstroOS — Unified Search Router (Phase 9)

Provides a single search endpoint that returns results from all domains:
- Saved birth charts (subject_name, place_name, lagna_rashi, moon_nakshatra, notes)
- Knowledge base (books, verses, rules, karakatvas)
- Research projects (title, description)

All searches are case-insensitive substring matches.

When OPENAI_API_KEY is configured, the endpoint first calls
AISearchAssistant.expand_query() to enrich the user's plain-language query
with domain-specific astrological terms before matching. When the key is
absent or the call fails, it degrades silently to single-term keyword search.
"""

import logging
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.dependencies import get_current_user_from_bearer, get_db_session
from apps.api.domain.user import User
from apps.api.repositories.birth_chart_repository import BirthChartRepository
from apps.api.repositories.knowledge_repository import KnowledgeRepository
from apps.api.repositories.research_repository import ResearchRepository
from apps.api.schemas.search import (
    UnifiedSearchRequest,
    UnifiedSearchResponse,
    SearchResultChart,
    SearchResultKnowledge,
    SearchResultProject,
)
from apps.api.domain.knowledge import KnowledgeSearchQuery, KnowledgeSearchResult
from apps.api.services.ai_search_assistant import AISearchAssistant, AISearchError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/search", tags=["Search"])


def _make_chart_href(chart_id: uuid.UUID) -> str:
    """Generate frontend href for a chart result."""
    return f"/charts/{chart_id}"


def _make_knowledge_href(entity_type: str, entity_id: uuid.UUID) -> str:
    """Generate frontend href for a knowledge result."""
    if entity_type == "book":
        return f"/knowledge/browse/{entity_id}"
    elif entity_type == "verse":
        return f"/knowledge/browse/{entity_id}"
    elif entity_type == "rule":
        return f"/research/rules/{entity_id}"
    elif entity_type == "karakatva":
        return f"/karakatva/{entity_id}"
    return "/knowledge"


def _make_project_href(project_id: uuid.UUID) -> str:
    """Generate frontend href for a research project result."""
    return f"/research/projects/{project_id}"


async def _search_charts(
    user_id: uuid.UUID,
    terms: list[str],
    limit: int,
    session: AsyncSession,
) -> List[SearchResultChart]:
    """Search user's saved birth charts across all expanded terms, deduplicating."""
    repo = BirthChartRepository(session)
    seen_ids: set[uuid.UUID] = set()
    results: List[SearchResultChart] = []
    for term in terms:
        charts = await repo.search_for_user(user_id, term, limit=limit)
        for chart in charts:
            if chart.id in seen_ids or len(results) >= limit:
                continue
            seen_ids.add(chart.id)
            snippet_parts = []
            if chart.lagna_rashi:
                snippet_parts.append(f"Lagna: {chart.lagna_rashi}")
            if chart.moon_nakshatra:
                snippet_parts.append(f"Moon: {chart.moon_nakshatra}")
            snippet = " · ".join(snippet_parts) if snippet_parts else "No details"
            results.append(SearchResultChart(
                id=chart.id,
                title=chart.subject_name,
                subtitle=chart.place_name,
                snippet=snippet,
                created_at=chart.created_at,
                href=_make_chart_href(chart.id),
            ))
        if len(results) >= limit:
            break
    return results


async def _search_knowledge(
    terms: list[str],
    limit: int,
    session: AsyncSession,
) -> List[SearchResultKnowledge]:
    """Search knowledge base across all expanded terms, deduplicating."""
    repo = KnowledgeRepository(session)
    seen_ids: set[uuid.UUID] = set()
    results: List[SearchResultKnowledge] = []
    for term in terms:
        knowledge_query = KnowledgeSearchQuery(text=term, entity_type=None, limit=limit)
        search_results = await repo.search(knowledge_query)
        for result in search_results:
            if not isinstance(result, KnowledgeSearchResult):
                continue
            if result.entity_id in seen_ids or len(results) >= limit:
                continue
            seen_ids.add(result.entity_id)
            results.append(SearchResultKnowledge(
                type=result.entity_type,
                id=result.entity_id,
                title=result.title,
                snippet=result.snippet,
                relevance=result.relevance,
                book_title=result.book_title,
                tradition=result.tradition,
                href=_make_knowledge_href(result.entity_type, result.entity_id),
            ))
        if len(results) >= limit:
            break
    return results


async def _search_projects(
    user_id: uuid.UUID,
    terms: list[str],
    limit: int,
    session: AsyncSession,
) -> List[SearchResultProject]:
    """Search research projects across all expanded terms, deduplicating."""
    repo = ResearchRepository(session)
    projects = await repo.list_projects(user_id)
    seen_ids: set[uuid.UUID] = set()
    results: List[SearchResultProject] = []
    for term in terms:
        term_lower = term.lower()
        for project in projects:
            if project.id in seen_ids or len(results) >= limit:
                continue
            if (
                term_lower in project.title.lower()
                or (project.description and term_lower in project.description.lower())
            ):
                seen_ids.add(project.id)
                snippet = project.description[:150] + "..." if project.description else "No description"
                results.append(SearchResultProject(
                    id=project.id,
                    title=project.title,
                    snippet=snippet,
                    created_at=project.created_at or project.updated_at,
                    href=_make_project_href(project.id),
                ))
    return results


@router.post("", response_model=UnifiedSearchResponse)
async def unified_search(
    request: UnifiedSearchRequest,
    http_request: Request,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> UnifiedSearchResponse:
    """
    Unified search across charts, knowledge base, and research projects.

    When OPENAI_API_KEY is configured, the query is first expanded by the
    LLM into related astrological terms before keyword matching. On any
    LLM failure the endpoint degrades to plain single-term keyword search.
    """
    try:
        from apps.api.config import get_settings
        settings = get_settings()

        user_id = current_user.id.value

        # ── AI query expansion (optional) ──────────────────────────────────
        http_client = http_request.app.state.http_client
        ai_assistant = AISearchAssistant(
            http_client=http_client,
            api_key=settings.OPENAI_API_KEY,
            model=settings.OPENAI_MODEL,
            base_url=settings.OPENAI_BASE_URL,
        )

        ai_enhanced = False
        expanded_terms = [request.query.strip().lower()]

        if ai_assistant.is_configured:
            try:
                expanded_terms = await ai_assistant.expand_query(request.query)
                ai_enhanced = True
            except (AISearchError, Exception) as exc:
                logger.warning("AI search expansion failed, falling back to keyword: %s", exc)
                expanded_terms = [request.query.strip().lower()]

        # ── Keyword search across all domains ──────────────────────────────
        chart_limit = max(1, min(6, request.limit // 3))
        knowledge_limit = max(1, min(6, request.limit // 3))
        project_limit = max(1, min(3, request.limit // 3))

        charts = await _search_charts(user_id, expanded_terms, chart_limit, session)
        knowledge = await _search_knowledge(expanded_terms, knowledge_limit, session)
        projects = await _search_projects(user_id, expanded_terms, project_limit, session)

        all_results = []
        all_results.extend(charts)
        all_results.extend(knowledge)
        all_results.extend(projects)

        return UnifiedSearchResponse(
            results=all_results,
            total=len(all_results),
            query=request.query,
            ai_enhanced=ai_enhanced,
            expanded_terms=expanded_terms if ai_enhanced else [],
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail="Search failed") from e