from typing import TypedDict, Any, Optional


class WorkflowState(TypedDict):
    # Project input
    project_id: str
    topic: str
    title: str
    content_type: str
    tone: str
    points_to_cover: list[str]
    target_audience: str
    seo_keywords: list[str]

    # Planning
    outline: dict
    research_tasks: list[dict]

    # Parallel research results (keyed by agent name)
    research_results: dict[str, list[dict]]
    all_sources: list[dict]
    research_summary: str

    # Claims and verification
    claims: list[dict]
    verified_claims: list[dict]

    # Contradiction analysis
    contradictions: list[dict]

    # Content generation
    content_draft: dict
    critique_result: dict
    revision_count: int
    max_revisions: int
    needs_revision: bool
    final_content: dict

    # Self-verification
    audit_result: dict

    # Hyperlinks
    hyperlink_results: list[dict]

    # Workflow telemetry
    workflow_id: str
    steps_completed: list[str]
    errors: list[dict]
    start_time: float
    telemetry: dict


def create_initial_state(
    project_id: str,
    topic: str = "",
    title: str = "",
    content_type: str = "article",
    tone: str = "professional",
    points_to_cover: list[str] | None = None,
    target_audience: str = "",
    seo_keywords: list[str] | None = None,
    workflow_id: str = "",
) -> WorkflowState:
    return {
        "project_id": project_id,
        "topic": topic,
        "title": title,
        "content_type": content_type,
        "tone": tone,
        "points_to_cover": points_to_cover or [],
        "target_audience": target_audience,
        "seo_keywords": seo_keywords or [],
        "outline": {},
        "research_tasks": [],
        "research_results": {},
        "all_sources": [],
        "research_summary": "",
        "claims": [],
        "verified_claims": [],
        "contradictions": [],
        "content_draft": {},
        "critique_result": {},
        "revision_count": 0,
        "max_revisions": 2,
        "needs_revision": False,
        "final_content": {},
        "audit_result": {},
        "hyperlink_results": [],
        "workflow_id": workflow_id,
        "steps_completed": [],
        "errors": [],
        "start_time": 0.0,
        "telemetry": {},
    }
