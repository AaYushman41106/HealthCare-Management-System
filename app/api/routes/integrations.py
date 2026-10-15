from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.jira import (
    JiraStatusResponse,
    JiraProjectSummaryResponse,
    JiraEpicsResponse,
    JiraIssuesResponse,
    JiraIssueCreateRequest,
    JiraIssueCreateResponse,
    JiraIssueTransitionRequest,
    JiraIssueTransitionResponse,
    JiraSprintsResponse,
    JiraProgressResponse,
    JiraActivityResponse,
)
from app.services.jira_service import JiraService
from app.services.audit_service import log_event

router = APIRouter()


@router.get("/jira/status", response_model=JiraStatusResponse)
def get_jira_status() -> JiraStatusResponse:
    """Retrieve connection and synchronization status with Atlassian Jira Cloud."""
    status_data = JiraService.check_connection()
    return JiraStatusResponse(**status_data)


@router.get("/jira/project", response_model=JiraProjectSummaryResponse)
def get_jira_project_summary() -> JiraProjectSummaryResponse:
    """Retrieve high-level project summary and completion metrics."""
    summary_data = JiraService.get_project_summary()
    return JiraProjectSummaryResponse(**summary_data)


@router.get("/jira/epics", response_model=JiraEpicsResponse)
def get_jira_epics() -> JiraEpicsResponse:
    """Retrieve all epics with their completion rates and story counts."""
    epics_data = JiraService.get_epics()
    return JiraEpicsResponse(**epics_data)


@router.get("/jira/issues", response_model=JiraIssuesResponse)
def get_jira_issues(
    status: Optional[str] = Query(None, description="Filter by status (e.g. 'To Do', 'In Progress', 'Done')"),
    epic_key: Optional[str] = Query(None, description="Filter by parent epic key (e.g. 'SCR-1')"),
    issue_type: Optional[str] = Query(None, description="Filter by issue type (e.g. 'Story', 'Task', 'Bug')"),
    search: Optional[str] = Query(None, description="Text search filter on summary, key, or description"),
) -> JiraIssuesResponse:
    """Retrieve list of Jira issues with optional filtering."""
    issues_data = JiraService.get_issues(
        status=status,
        epic_key=epic_key,
        issue_type=issue_type,
        search=search,
    )
    return JiraIssuesResponse(**issues_data)


@router.post("/jira/issues", response_model=JiraIssueCreateResponse, status_code=status.HTTP_201_CREATED)
def create_jira_issue(
    payload: JiraIssueCreateRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JiraIssueCreateResponse:
    """Create a new User Story, Task, or Bug directly in Jira Cloud.
    
    Protected: Requires authenticated user (Doctor or Admin recommended).
    Audit logged for regulatory compliance.
    """
    res = JiraService.create_issue(
        summary=payload.summary,
        description=payload.description,
        issue_type=payload.issue_type,
        priority=payload.priority,
        parent_key=payload.parent_key,
    )

    if not res.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY if res.get("mode") == "live" else status.HTTP_400_BAD_REQUEST,
            detail=res.get("message", "Failed to create issue in Jira Cloud"),
        )

    # Log audit event for Jira issue creation
    client_ip = request.client.host if request.client else None
    log_event(
        db=db,
        action="JIRA_ISSUE_CREATED",
        resource_type="JIRA_ISSUE",
        user_id=current_user.id,
        resource_id=res.get("key"),
        ip_address=client_ip,
        details=f"Created Jira issue {res.get('key')} ({payload.issue_type}): {payload.summary[:100]}",
    )

    return JiraIssueCreateResponse(**res)


@router.post("/jira/issues/{issue_key}/transition", response_model=JiraIssueTransitionResponse)
def transition_jira_issue(
    issue_key: str,
    payload: JiraIssueTransitionRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> JiraIssueTransitionResponse:
    """Transition Jira issue status (e.g. 'To Do', 'In Progress', 'In Review', 'Done').
    
    Protected: Requires authenticated user (Doctor or Admin recommended).
    Audit logged for regulatory compliance.
    """
    res = JiraService.transition_issue(issue_key=issue_key, target_status=payload.status)

    if not res.get("success", False):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=res.get("message", f"Failed to transition issue {issue_key}"),
        )

    # Log audit event for status transition
    client_ip = request.client.host if request.client else None
    log_event(
        db=db,
        action="JIRA_ISSUE_TRANSITIONED",
        resource_type="JIRA_ISSUE",
        user_id=current_user.id,
        resource_id=issue_key,
        ip_address=client_ip,
        details=f"Transitioned Jira issue {issue_key} to status '{payload.status}'",
    )

    return JiraIssueTransitionResponse(**res)


@router.get("/jira/sprints", response_model=JiraSprintsResponse)
def get_jira_sprints() -> JiraSprintsResponse:
    """Retrieve Sprint 1 through 5 details and agile workflow states."""
    sprints_data = JiraService.get_sprints()
    return JiraSprintsResponse(**sprints_data)


@router.get("/jira/progress", response_model=JiraProgressResponse)
def get_jira_progress() -> JiraProgressResponse:
    """Retrieve aggregated project progression and status distributions."""
    prog_data = JiraService.get_progress()
    return JiraProgressResponse(**prog_data)


@router.get("/jira/activity", response_model=JiraActivityResponse)
def get_jira_activity() -> JiraActivityResponse:
    """Retrieve recent Jira project activity log."""
    act_data = JiraService.get_recent_activity()
    return JiraActivityResponse(**act_data)


@router.post("/jira/refresh")
def refresh_jira_cache() -> dict:
    """Force refresh Jira in-memory cache to sync immediate changes from Jira Cloud."""
    JiraService.clear_cache()
    return {"success": True, "message": "Jira cache cleared successfully."}
