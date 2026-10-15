from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class JiraStatusResponse(BaseModel):
    is_configured: bool
    is_connected: bool
    mode: str  # "live" or "demo"
    message: str
    project_key: str
    project_name: Optional[str] = None
    base_url: str


class JiraProjectSummaryResponse(BaseModel):
    is_live: bool
    mode: str
    data_source: str
    project_key: str
    project_name: str
    base_url: str
    total_issues: int
    total_epics: int
    total_stories: int
    done_stories: int
    in_progress_stories: int
    todo_stories: int
    completion_percentage: float
    lead: Optional[str] = None


class JiraEpicItem(BaseModel):
    key: str
    summary: str
    name: str
    status: str
    total_stories: int
    completed_stories: int
    progress_percentage: float
    jira_url: str


class JiraEpicsResponse(BaseModel):
    is_live: bool
    mode: str
    count: int
    epics: List[JiraEpicItem]


class JiraIssueItem(BaseModel):
    key: str
    id: str
    summary: str
    description: Optional[str] = ""
    status: str
    raw_status: Optional[str] = None
    status_category: Optional[str] = None
    issue_type: str
    priority: str
    assignee: Dict[str, Any]
    parent_key: Optional[str] = None
    parent_summary: Optional[str] = None
    created: str
    updated: str
    jira_url: str


class JiraIssuesResponse(BaseModel):
    is_live: bool
    mode: str
    total: int
    issues: List[JiraIssueItem]


class JiraIssueCreateRequest(BaseModel):
    summary: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    issue_type: str = Field(default="Task")
    priority: Optional[str] = Field(default="Medium")
    parent_key: Optional[str] = None


class JiraIssueCreateResponse(BaseModel):
    success: bool
    is_live: bool
    mode: str
    key: Optional[str] = None
    id: Optional[str] = None
    url: Optional[str] = None
    message: str


class JiraSprintItem(BaseModel):
    id: Optional[int] = None
    name: str
    state: Optional[str] = None
    goal: Optional[str] = ""
    startDate: Optional[str] = None
    endDate: Optional[str] = None
    completeDate: Optional[str] = None
    originBoardId: Optional[int] = None


class JiraSprintsResponse(BaseModel):
    is_live: bool
    mode: str
    count: int
    sprints: List[JiraSprintItem]


class JiraProgressResponse(BaseModel):
    is_live: bool
    mode: str
    completion_percentage: float
    health_status: str
    status_distribution: Dict[str, int]
    total_items: int
    epics: List[JiraEpicItem]
    sprints: List[JiraSprintItem]


class JiraActivityItem(BaseModel):
    id: str
    timestamp: str
    author: str
    type: str
    issue_key: Optional[str] = None
    summary: str
    status: Optional[str] = None
    details: str
    jira_url: Optional[str] = None


class JiraActivityResponse(BaseModel):
    is_live: bool
    mode: str
    count: int
    activities: List[JiraActivityItem]


class JiraIssueTransitionRequest(BaseModel):
    status: str = Field(..., description="Target status, e.g. 'To Do', 'In Progress', 'In Review', 'Done'")


class JiraIssueTransitionResponse(BaseModel):
    success: bool
    is_live: bool
    mode: str
    key: str
    status: str
    message: str
