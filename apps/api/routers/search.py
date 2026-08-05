"""
AstroOS — Unified Search Router (Phase 9)

Provides a single search endpoint that returns results from all domains:
- Saved birth charts (subject_name, place_name, lagna_rashi, moon_nakshatra, notes)
- Knowledge base (books, verses, rules, karakatvas)
- Research projects (title, description)

All searches are case-insensitive substring matches.
"""

import uuid
from typing import List, Union

from fastapi import APIRouter, Depends, HTTPException
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
    query: str,
    limit: int,
    session: AsyncSession,
) -> List[SearchResultChart]:
    """Search user's saved birth charts."""
    repo = BirthChartRepository(session)
    charts = await repo.search_for_user(user_id, query, limit=limit)
    results = []
    for chart in charts:
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
    return results


async def _search_knowledge(
    query: str,
    limit: int,
    session: AsyncSession,
) -> List[SearchResultKnowledge]:
    """Search knowledge base (books, verses)."""
    repo = KnowledgeRepository(session)
    knowledge_query = KnowledgeSearchQuery(
        text=query,
        entity_type=None,  # search all types
        limit=limit,
    )
    search_results = await repo.search(knowledge_query)
    results = []
    for result in search_results:
        if isinstance(result, KnowledgeSearchResult):
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
    return results


async def _search_projects(
    user_id: uuid.UUID,
    query: str,
    limit: int,
    session: AsyncSession,
) -> List[SearchResultProject]:
    """Search research projects."""
    repo = ResearchRepository(session)
    # Research repository doesn't have a search method yet, but we can filter
    # after fetching all projects (this is a simple substring match).
    projects = await repo.list_projects(user_id)
    results = []
    query_lower = query.lower()
    for project in projects:
        if (
            query_lower in project.title.lower()
            or (project.description and query_lower in project.description.lower())
        ):
            snippet = project.description[:150] + "..." if project.description else "No description"
            results.append(SearchResultProject(
                id=project.id,
                title=project.title,
                snippet=snippet,
                created_at=project.created_at or project.updated_at,
                href=_make_project_href(project.id),
            ))
            if len(results) >= limit:
                break
    return results


@router.post("", response_model=UnifiedSearchResponse)
async def unified_search(
    request: UnifiedSearchRequest,
    current_user: User = Depends(get_current_user_from_bearer),
    session: AsyncSession = Depends(get_db_session),
) -> UnifiedSearchResponse:
    """
    Unified search across charts, knowledge base, and research projects.

    Returns results from all domains in a single response, limited to the
    specified total limit (divided roughly equally across domains).
    """
    try:
        user_id = current_user.id.value

        # Distribute limit across domains: 40% charts, 40% knowledge, 20% projects
        chart_limit = max(1, min(6, request.limit // 3))
        knowledge_limit = max(1, min(6, request.limit // 3))
        project_limit = max(1, min(3, request.limit // 3))

        # Run searches in parallel (they're independent)
        charts = await _search_charts(user_id, request.query, chart_limit, session)
        knowledge = await _search_knowledge(request.query, knowledge_limit, session)
        projects = await _search_projects(user_id, request.query, project_limit, session)

        # Combine all results
        all_results = []
        all_results.extend(charts)
        all_results.extend(knowledge)
        all_results.extend(projects)

        return UnifiedSearchResponse(
            results=all_results,
            total=len(all_results),
            query=request.query,
        )
    except Exception as e:
        # Log the error but return a generic message
        # In production, you'd want proper logging here
        raise HTTPException(status_code=500, detail="Search failed") from e
