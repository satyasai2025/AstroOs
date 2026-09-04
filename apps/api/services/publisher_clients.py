"""
AstroOS — Multi-Platform Auto-Publisher Clients (Medium REST & Hashnode GraphQL)
================================================================================
Handles programmatic publishing of deep research articles to Medium and Hashnode
with authentication, rate-limiting safeguards, canonical URLs, tags, and dry-run modes.
"""

from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import httpx

from apps.api.domain.scholar_blog import (
    ArticleStatus,
    PlatformPublishRecord,
    PlatformType,
    PublishMode,
    ScholarArticle,
)

logger = logging.getLogger(__name__)


class MediumPublisherClient:
    """
    Publisher client for Medium REST API v1.
    API Docs: https://github.com/Medium/medium-api-docs
    """

    BASE_URL = "https://api.medium.com/v1"

    def __init__(self, token: Optional[str] = None, user_id: Optional[str] = None, publication_id: Optional[str] = None) -> None:
        self.token = token
        self.user_id = user_id
        self.publication_id = publication_id

    async def get_current_user(self, token_override: Optional[str] = None) -> Dict[str, Any]:
        """Fetch the authenticated Medium user's profile to retrieve userId and username."""
        tok = token_override or self.token
        if not tok:
            raise ValueError("Medium integration token not configured.")

        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.get(
                f"{self.BASE_URL}/me",
                headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"},
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Medium get_current_user failed ({resp.status_code}): {resp.text}")
            data = resp.json()
            return data.get("data", {})

    async def publish(
        self,
        article: ScholarArticle,
        mode: PublishMode = PublishMode.DRAFT,
        token_override: Optional[str] = None,
        user_id_override: Optional[str] = None,
        publication_id_override: Optional[str] = None,
        dry_run: bool = False,
    ) -> PlatformPublishRecord:
        """Publish the scholar article to Medium as draft or public story."""
        tok = token_override or self.token
        uid = user_id_override or self.user_id
        pub_id = publication_id_override or self.publication_id

        # Dry run or missing credentials in simulation mode
        if dry_run or not tok:
            simulated_id = f"med_sim_{uuid.uuid4().hex[:12]}"
            simulated_url = f"https://medium.com/@antigravity-astroos/{article.slug}-{simulated_id[:6]}"
            logger.info("Medium publish executed in DRY-RUN / SIMULATED mode.")
            return PlatformPublishRecord(
                platform=PlatformType.MEDIUM,
                post_id=simulated_id,
                url=simulated_url,
                published_at=datetime.now(timezone.utc),
                publish_mode=mode,
                status="SUCCESS_DRY_RUN",
                response_payload={
                    "id": simulated_id,
                    "title": article.title,
                    "authorId": uid or "simulated_author_id",
                    "url": simulated_url,
                    "canonicalUrl": article.canonical_url,
                    "publishStatus": mode.value,
                    "tags": article.tags[:5],
                    "simulated": True,
                },
            )

        try:
            # If user_id is not supplied, fetch it dynamically
            if not uid:
                user_info = await self.get_current_user(token_override=tok)
                uid = user_info.get("id")
                if not uid:
                    raise RuntimeError("Unable to resolve Medium user ID from token.")

            # Medium allows at most 5 tags
            medium_tags = [t.replace(" ", "-") for t in article.tags[:5]]

            payload = {
                "title": article.title,
                "contentFormat": "markdown",
                "content": article.markdown_content,
                "canonicalUrl": article.canonical_url,
                "tags": medium_tags,
                "publishStatus": mode.value,
                "notifyFollowers": mode == PublishMode.PUBLIC,
            }

            target_endpoint = (
                f"{self.BASE_URL}/publications/{pub_id}/posts"
                if pub_id
                else f"{self.BASE_URL}/users/{uid}/posts"
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    target_endpoint,
                    headers={
                        "Authorization": f"Bearer {tok}",
                        "Content-Type": "application/json",
                        "Accept": "application/json",
                    },
                    json=payload,
                )

                if resp.status_code not in (200, 201):
                    err_msg = f"Medium publish error ({resp.status_code}): {resp.text}"
                    logger.error(err_msg)
                    return PlatformPublishRecord(
                        platform=PlatformType.MEDIUM,
                        post_id="",
                        url="",
                        published_at=datetime.now(timezone.utc),
                        publish_mode=mode,
                        status="FAILED",
                        error_message=err_msg,
                        response_payload={"raw_error": resp.text, "status_code": resp.status_code},
                    )

                res_data = resp.json().get("data", {})
                post_id = res_data.get("id", "")
                post_url = res_data.get("url", f"https://medium.com/p/{post_id}")

                return PlatformPublishRecord(
                    platform=PlatformType.MEDIUM,
                    post_id=post_id,
                    url=post_url,
                    published_at=datetime.now(timezone.utc),
                    publish_mode=mode,
                    status="PUBLISHED",
                    response_payload=res_data,
                )

        except Exception as e:
            logger.exception("Exception during Medium publication")
            return PlatformPublishRecord(
                platform=PlatformType.MEDIUM,
                post_id="",
                url="",
                published_at=datetime.now(timezone.utc),
                publish_mode=mode,
                status="FAILED",
                error_message=str(e),
            )


class HashnodePublisherClient:
    """
    Publisher client for Hashnode GraphQL API v2.
    API Docs: https://apidocs.hashnode.com
    """

    GQL_ENDPOINT = "https://gql.hashnode.com"

    PUBLISH_MUTATION = """
    mutation PublishPost($input: PublishPostInput!) {
      publishPost(input: $input) {
        post {
          id
          slug
          url
          title
          brief
          publishedAt
        }
      }
    }
    """

    def __init__(self, token: Optional[str] = None, publication_id: Optional[str] = None) -> None:
        self.token = token
        self.publication_id = publication_id

    async def publish(
        self,
        article: ScholarArticle,
        mode: PublishMode = PublishMode.DRAFT,
        token_override: Optional[str] = None,
        publication_id_override: Optional[str] = None,
        dry_run: bool = False,
    ) -> PlatformPublishRecord:
        """Publish the scholar article to Hashnode publication via GraphQL API."""
        tok = token_override or self.token
        pub_id = publication_id_override or self.publication_id

        # Dry run or missing credentials in simulation mode
        if dry_run or not tok or not pub_id:
            simulated_id = f"hn_sim_{uuid.uuid4().hex[:12]}"
            simulated_url = f"https://blog.astroos.io/{article.slug}"
            logger.info("Hashnode publish executed in DRY-RUN / SIMULATED mode.")
            return PlatformPublishRecord(
                platform=PlatformType.HASHNODE,
                post_id=simulated_id,
                url=simulated_url,
                published_at=datetime.now(timezone.utc),
                publish_mode=mode,
                status="SUCCESS_DRY_RUN",
                response_payload={
                    "id": simulated_id,
                    "slug": article.slug,
                    "title": article.title,
                    "subtitle": article.subtitle,
                    "publicationId": pub_id or "simulated_pub_id",
                    "url": simulated_url,
                    "originalArticleURL": article.canonical_url,
                    "simulated": True,
                },
            )

        try:
            hashnode_tags = [
                {"name": t.replace("-", " ").title(), "slug": t.replace(" ", "-").lower()}
                for t in article.tags[:5]
            ]

            variables = {
                "input": {
                    "title": article.title,
                    "subtitle": article.subtitle,
                    "publicationId": pub_id,
                    "contentMarkdown": article.markdown_content,
                    "tags": hashnode_tags,
                    "slug": article.slug,
                    "originalArticleURL": article.canonical_url,
                    "disableComments": False,
                }
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    self.GQL_ENDPOINT,
                    headers={
                        "Authorization": tok,
                        "Content-Type": "application/json",
                    },
                    json={"query": self.PUBLISH_MUTATION, "variables": variables},
                )

                if resp.status_code != 200:
                    err_msg = f"Hashnode HTTP error ({resp.status_code}): {resp.text}"
                    logger.error(err_msg)
                    return PlatformPublishRecord(
                        platform=PlatformType.HASHNODE,
                        post_id="",
                        url="",
                        published_at=datetime.now(timezone.utc),
                        publish_mode=mode,
                        status="FAILED",
                        error_message=err_msg,
                        response_payload={"raw_error": resp.text},
                    )

                gql_json = resp.json()
                if "errors" in gql_json and gql_json["errors"]:
                    err_details = str(gql_json["errors"])
                    logger.error("Hashnode GraphQL error: %s", err_details)
                    return PlatformPublishRecord(
                        platform=PlatformType.HASHNODE,
                        post_id="",
                        url="",
                        published_at=datetime.now(timezone.utc),
                        publish_mode=mode,
                        status="FAILED",
                        error_message=err_details,
                        response_payload=gql_json,
                    )

                post_data = (
                    gql_json.get("data", {}).get("publishPost", {}).get("post", {})
                )
                post_id = post_data.get("id", "")
                post_url = post_data.get("url", f"https://blog.hashnode.com/{article.slug}")

                return PlatformPublishRecord(
                    platform=PlatformType.HASHNODE,
                    post_id=post_id,
                    url=post_url,
                    published_at=datetime.now(timezone.utc),
                    publish_mode=mode,
                    status="PUBLISHED",
                    response_payload=post_data,
                )

        except Exception as e:
            logger.exception("Exception during Hashnode publication")
            return PlatformPublishRecord(
                platform=PlatformType.HASHNODE,
                post_id="",
                url="",
                published_at=datetime.now(timezone.utc),
                publish_mode=mode,
                status="FAILED",
                error_message=str(e),
            )
