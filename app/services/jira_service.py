import time
import base64
from typing import Dict, Any, List, Optional
import httpx
from ..core.config import settings


class JiraService:
    """
    Service for integrating with Atlassian Jira Cloud REST API v3 and Agile API v1.0.
    Provides live synchronization when configured, and a structured,
    SecureCare-aligned Demo Mode when credentials are not present or network is unreachable.
    """

    CACHE_TTL_SECONDS = 30  # Cache live responses for 30 seconds
    _cache: Dict[str, Any] = {}
    _cache_timestamp: float = 0.0

    # In-memory store for newly created demo issues when in demo mode
    _demo_created_issues: List[Dict[str, Any]] = []

    @classmethod
    def is_configured(cls) -> bool:
        """Check if minimum required credentials for Jira API are present."""
        return bool(settings.JIRA_EMAIL and settings.JIRA_API_TOKEN)

    @classmethod
    def get_auth_header(cls) -> Optional[Dict[str, str]]:
        """Construct HTTP Basic Auth header using email and API token."""
        if not cls.is_configured():
            return None
        token_str = f"{settings.JIRA_EMAIL}:{settings.JIRA_API_TOKEN}"
        encoded = base64.b64encode(token_str.encode("utf-8")).decode("utf-8")
        return {
            "Authorization": f"Basic {encoded}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

    @classmethod
    def clear_cache(cls) -> None:
        """Clear cached responses to force a fresh fetch."""
        cls._cache.clear()
        cls._cache_timestamp = 0.0

    @classmethod
    def check_connection(cls) -> Dict[str, Any]:
        """Test authentication and project accessibility against Jira Cloud."""
        if not cls.is_configured():
            return {
                "is_configured": False,
                "is_connected": False,
                "mode": "demo",
                "message": "Jira integration credentials are not configured. Displaying structured project DEMO DATA.",
                "project_key": settings.JIRA_PROJECT_KEY,
                "base_url": settings.JIRA_BASE_URL,
            }

        headers = cls.get_auth_header()
        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/project/{settings.JIRA_PROJECT_KEY}"

        try:
            with httpx.Client(timeout=8.0) as client:
                resp = client.get(url, headers=headers)
                if resp.status_code == 200:
                    proj_data = resp.json()
                    return {
                        "is_configured": True,
                        "is_connected": True,
                        "mode": "live",
                        "message": f"Successfully connected to Jira Project '{proj_data.get('name', settings.JIRA_PROJECT_KEY)}'.",
                        "project_key": settings.JIRA_PROJECT_KEY,
                        "project_name": proj_data.get("name"),
                        "base_url": settings.JIRA_BASE_URL,
                    }
                elif resp.status_code == 401:
                    return {
                        "is_configured": True,
                        "is_connected": False,
                        "mode": "demo",
                        "message": "Authentication failed: Invalid Jira Email or API Token (HTTP 401). Falling back to Demo Mode.",
                        "project_key": settings.JIRA_PROJECT_KEY,
                        "base_url": settings.JIRA_BASE_URL,
                    }
                elif resp.status_code == 404:
                    return {
                        "is_configured": True,
                        "is_connected": False,
                        "mode": "demo",
                        "message": f"Project key '{settings.JIRA_PROJECT_KEY}' not found in Jira instance (HTTP 404). Falling back to Demo Mode.",
                        "project_key": settings.JIRA_PROJECT_KEY,
                        "base_url": settings.JIRA_BASE_URL,
                    }
                else:
                    return {
                        "is_configured": True,
                        "is_connected": False,
                        "mode": "demo",
                        "message": f"Jira API returned HTTP {resp.status_code}. Falling back to Demo Mode.",
                        "project_key": settings.JIRA_PROJECT_KEY,
                        "base_url": settings.JIRA_BASE_URL,
                    }
        except Exception as e:
            return {
                "is_configured": True,
                "is_connected": False,
                "mode": "demo",
                "message": f"Failed to reach Jira server ({type(e).__name__}). Falling back to Demo Mode.",
                "project_key": settings.JIRA_PROJECT_KEY,
                "base_url": settings.JIRA_BASE_URL,
            }

    @classmethod
    def _fetch_live_issues(cls) -> Optional[List[Dict[str, Any]]]:
        """Fetch all issues from live Jira using REST API v3 search/jql endpoint."""
        if not cls.is_configured():
            return None

        now = time.time()
        if "issues" in cls._cache and (now - cls._cache_timestamp < cls.CACHE_TTL_SECONDS):
            return cls._cache["issues"]

        headers = cls.get_auth_header()
        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/search/jql"
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(
                    url,
                    headers=headers,
                    json={
                        "jql": f"project = {settings.JIRA_PROJECT_KEY} ORDER BY key ASC",
                        "fields": [
                            "summary",
                            "status",
                            "issuetype",
                            "parent",
                            "priority",
                            "assignee",
                            "created",
                            "updated",
                            "description",
                        ],
                        "maxResults": 100,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    issues = data.get("issues", [])
                    cls._cache["issues"] = issues
                    cls._cache_timestamp = now
                    return issues
        except Exception as e:
            print(f"[JiraService] Failed to query live issues: {e}")
        return None

    @classmethod
    def _fetch_live_sprints(cls) -> Optional[List[Dict[str, Any]]]:
        """Fetch agile sprints from live Jira Agile API."""
        if not cls.is_configured():
            return None

        now = time.time()
        if "sprints" in cls._cache and (now - cls._cache_timestamp < cls.CACHE_TTL_SECONDS):
            return cls._cache["sprints"]

        headers = cls.get_auth_header()
        try:
            with httpx.Client(timeout=10.0) as client:
                # 1. Get board ID
                boards_url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/agile/1.0/board?projectKeyOrId={settings.JIRA_PROJECT_KEY}"
                b_resp = client.get(boards_url, headers=headers)
                if b_resp.status_code != 200:
                    return None
                b_data = b_resp.json()
                boards = b_data.get("values", [])
                if not boards:
                    return None
                board_id = boards[0].get("id")

                # 2. Get sprints for board
                sprints_url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/agile/1.0/board/{board_id}/sprint"
                s_resp = client.get(sprints_url, headers=headers)
                if s_resp.status_code == 200:
                    s_data = s_resp.json()
                    sprints = s_data.get("values", [])
                    cls._cache["sprints"] = sprints
                    return sprints
        except Exception as e:
            print(f"[JiraService] Failed to query live sprints: {e}")
        return None

    @classmethod
    def _normalize_issue(cls, raw: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize raw Jira API issue into clean dictionary format."""
        fields = raw.get("fields", {})
        status_obj = fields.get("status", {}) or {}
        status_category = status_obj.get("statusCategory", {}).get("name", "To Do")
        status_name = status_obj.get("name", "To Do")
        
        # Normalize status into 3 standard states: To Do, In Progress, Done
        cat_key = status_obj.get("statusCategory", {}).get("key", "").lower()
        if cat_key == "done" or status_name.lower() in ("done", "closed", "resolved"):
            std_status = "Done"
        elif cat_key == "indeterminate" or status_name.lower() in ("in progress", "in review", "testing"):
            std_status = "In Progress"
        else:
            std_status = "To Do"

        issue_type_obj = fields.get("issuetype", {}) or {}
        priority_obj = fields.get("priority", {}) or {}
        assignee_obj = fields.get("assignee", {}) or {}
        parent_obj = fields.get("parent", {}) or {}

        # Parse text description if present
        raw_desc = fields.get("description")
        desc_text = ""
        if isinstance(raw_desc, dict):
            # Extract text from ADF
            paragraphs = []
            for block in raw_desc.get("content", []):
                for inline in block.get("content", []):
                    if inline.get("type") == "text":
                        paragraphs.append(inline.get("text", ""))
            desc_text = " ".join(paragraphs)
        elif isinstance(raw_desc, str):
            desc_text = raw_desc

        key = raw.get("key", "")
        return {
            "key": key,
            "id": str(raw.get("id", "")),
            "summary": fields.get("summary", ""),
            "description": desc_text,
            "status": std_status,
            "raw_status": status_name,
            "status_category": status_category,
            "issue_type": issue_type_obj.get("name", "Task"),
            "priority": priority_obj.get("name", "Medium"),
            "assignee": {
                "name": assignee_obj.get("displayName", "Unassigned"),
                "email": assignee_obj.get("emailAddress", ""),
                "avatar": assignee_obj.get("avatarUrls", {}).get("24x24", ""),
            },
            "parent_key": parent_obj.get("key"),
            "parent_summary": parent_obj.get("fields", {}).get("summary") if isinstance(parent_obj.get("fields"), dict) else None,
            "created": fields.get("created", ""),
            "updated": fields.get("updated", ""),
            "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/{key}" if key else "#",
        }

    # =========================================================================
    # PUBLIC API METHODS
    # =========================================================================

    @classmethod
    def get_project_summary(cls) -> Dict[str, Any]:
        """Retrieve overall project status and story completion statistics."""
        live_issues = cls._fetch_live_issues()
        if live_issues is not None:
            epics = [i for i in live_issues if i.get("fields", {}).get("issuetype", {}).get("name") == "Epic"]
            stories_and_tasks = [i for i in live_issues if i.get("fields", {}).get("issuetype", {}).get("name") != "Epic"]

            total_items = len(stories_and_tasks)
            done_items = sum(
                1 for s in stories_and_tasks
                if (s.get("fields", {}).get("status", {}).get("statusCategory", {}).get("key") == "done"
                    or s.get("fields", {}).get("status", {}).get("name", "").lower() in ("done", "closed", "resolved"))
            )
            in_progress_items = sum(
                1 for s in stories_and_tasks
                if (s.get("fields", {}).get("status", {}).get("statusCategory", {}).get("key") == "indeterminate"
                    or s.get("fields", {}).get("status", {}).get("name", "").lower() in ("in progress", "in review"))
            )
            todo_items = total_items - done_items - in_progress_items

            completion_pct = round((done_items / total_items * 100), 1) if total_items > 0 else 0.0

            return {
                "is_live": True,
                "mode": "live",
                "data_source": f"LIVE JIRA CLOUD ({settings.JIRA_PROJECT_KEY})",
                "project_key": settings.JIRA_PROJECT_KEY,
                "project_name": "SecureCare – Healthcare Management System",
                "base_url": settings.JIRA_BASE_URL,
                "total_issues": len(live_issues),
                "total_epics": len(epics),
                "total_stories": total_items,
                "done_stories": done_items,
                "in_progress_stories": in_progress_items,
                "todo_stories": max(0, todo_items),
                "completion_percentage": completion_pct,
                "lead": "AaYushman Parab",
            }

        # Fallback to Demo Data
        demo_issues = cls._get_demo_issues()
        epics = [i for i in demo_issues if i.get("issue_type") == "Epic"]
        non_epics = [i for i in demo_issues if i.get("issue_type") != "Epic"]
        done_count = sum(1 for i in non_epics if i.get("status") == "Done")
        prog_count = sum(1 for i in non_epics if i.get("status") == "In Progress")
        todo_count = len(non_epics) - done_count - prog_count

        return {
            "is_live": False,
            "mode": "demo",
            "data_source": "DEMO DATA (Offline / Standalone Mode)",
            "project_key": settings.JIRA_PROJECT_KEY,
            "project_name": "SecureCare – Healthcare Management System",
            "base_url": settings.JIRA_BASE_URL,
            "total_issues": len(demo_issues),
            "total_epics": len(epics),
            "total_stories": len(non_epics),
            "done_stories": done_count,
            "in_progress_stories": prog_count,
            "todo_stories": todo_count,
            "completion_percentage": round(done_count / len(non_epics) * 100, 1) if non_epics else 0.0,
            "lead": "AaYushman Parab",
        }

    @classmethod
    def get_epics(cls) -> Dict[str, Any]:
        """Retrieve all epics with their completion rates and story counts."""
        live_issues = cls._fetch_live_issues()
        if live_issues is not None:
            raw_epics = [i for i in live_issues if i.get("fields", {}).get("issuetype", {}).get("name") == "Epic"]
            stories = [i for i in live_issues if i.get("fields", {}).get("issuetype", {}).get("name") != "Epic"]

            epics_data = []
            for e in raw_epics:
                e_key = e.get("key")
                e_fields = e.get("fields", {})
                e_summary = e_fields.get("summary", "").strip()

                # Find child stories for this epic
                child_stories = [
                    s for s in stories
                    if s.get("fields", {}).get("parent", {}).get("key") == e_key
                ]
                total_c = len(child_stories)
                done_c = sum(
                    1 for s in child_stories
                    if (s.get("fields", {}).get("status", {}).get("statusCategory", {}).get("key") == "done"
                        or s.get("fields", {}).get("status", {}).get("name", "").lower() in ("done", "closed", "resolved"))
                )
                progress_pct = round((done_c / total_c * 100), 1) if total_c > 0 else 0.0

                epics_data.append({
                    "key": e_key,
                    "summary": e_summary,
                    "name": e_summary,
                    "status": e_fields.get("status", {}).get("name", "To Do"),
                    "total_stories": total_c,
                    "completed_stories": done_c,
                    "progress_percentage": progress_pct,
                    "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/{e_key}",
                })

            epics_data.sort(key=lambda x: x["key"])
            return {
                "is_live": True,
                "mode": "live",
                "count": len(epics_data),
                "epics": epics_data,
            }

        # Fallback to structured demo epics
        demo_epics = cls._get_demo_epics()
        return {
            "is_live": False,
            "mode": "demo",
            "count": len(demo_epics),
            "epics": demo_epics,
        }

    @classmethod
    def get_issues(
        cls,
        status: Optional[str] = None,
        epic_key: Optional[str] = None,
        issue_type: Optional[str] = None,
        search: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Retrieve issues with optional filters."""
        live_issues = cls._fetch_live_issues()
        if live_issues is not None:
            normalized = [cls._normalize_issue(i) for i in live_issues]
            is_live = True
        else:
            normalized = list(cls._get_demo_issues())
            is_live = False

        # Apply filters
        filtered = normalized
        if status:
            s_low = status.lower()
            filtered = [i for i in filtered if i.get("status", "").lower() == s_low]

        if epic_key:
            filtered = [
                i for i in filtered
                if i.get("parent_key") == epic_key or (i.get("issue_type") == "Epic" and i.get("key") == epic_key)
            ]

        if issue_type:
            it_low = issue_type.lower()
            filtered = [i for i in filtered if i.get("issue_type", "").lower() == it_low]

        if search:
            q = search.lower()
            filtered = [
                i for i in filtered
                if q in i.get("summary", "").lower() or q in i.get("key", "").lower() or q in i.get("description", "").lower()
            ]

        return {
            "is_live": is_live,
            "mode": "live" if is_live else "demo",
            "total": len(filtered),
            "issues": filtered,
        }

    @classmethod
    def get_sprints(cls) -> Dict[str, Any]:
        """Retrieve Sprint 1 through 5 details and progress."""
        live_sprints = cls._fetch_live_sprints()
        if live_sprints is not None:
            sprints_out = []
            for s in live_sprints:
                sprints_out.append({
                    "id": s.get("id"),
                    "name": s.get("name"),
                    "state": s.get("state"),  # 'closed', 'active', 'future'
                    "goal": s.get("goal", ""),
                    "startDate": s.get("startDate"),
                    "endDate": s.get("endDate"),
                    "completeDate": s.get("completeDate"),
                    "originBoardId": s.get("originBoardId"),
                })
            return {
                "is_live": True,
                "mode": "live",
                "count": len(sprints_out),
                "sprints": sprints_out,
            }

        # Fallback demo sprints
        demo_sprints = cls._get_demo_sprints()
        return {
            "is_live": False,
            "mode": "demo",
            "count": len(demo_sprints),
            "sprints": demo_sprints,
        }

    @classmethod
    def get_progress(cls) -> Dict[str, Any]:
        """Compute comprehensive project progression metrics."""
        summary = cls.get_project_summary()
        epics_resp = cls.get_epics()
        sprints_resp = cls.get_sprints()

        todo = summary.get("todo_stories", 0)
        in_prog = summary.get("in_progress_stories", 0)
        done = summary.get("done_stories", 0)
        total = summary.get("total_stories", 1)

        return {
            "is_live": summary.get("is_live", False),
            "mode": summary.get("mode", "demo"),
            "completion_percentage": summary.get("completion_percentage", 0.0),
            "health_status": "Healthy / On Track" if summary.get("completion_percentage", 0) > 60 else "In Progress",
            "status_distribution": {
                "To Do": todo,
                "In Progress": in_prog,
                "Done": done,
            },
            "total_items": total,
            "epics": epics_resp.get("epics", []),
            "sprints": sprints_resp.get("sprints", []),
        }

    @classmethod
    def get_recent_activity(cls) -> Dict[str, Any]:
        """Retrieve recent activity log across Jira project."""
        live_issues = cls._fetch_live_issues()
        if live_issues is not None:
            sorted_issues = sorted(
                live_issues,
                key=lambda x: x.get("fields", {}).get("updated", ""),
                reverse=True
            )[:10]

            activities = []
            for idx, item in enumerate(sorted_issues):
                fields = item.get("fields", {})
                updated_ts = fields.get("updated", "")[:16].replace("T", " ")
                assignee_name = fields.get("assignee", {}).get("displayName", "Team Member") if fields.get("assignee") else "SecureCare Lead"
                status_name = fields.get("status", {}).get("name", "Updated")

                activities.append({
                    "id": f"ACT-{idx + 1}",
                    "timestamp": updated_ts,
                    "author": assignee_name,
                    "type": "STATUS_UPDATE",
                    "issue_key": item.get("key"),
                    "summary": fields.get("summary", ""),
                    "status": status_name,
                    "details": f"Issue {item.get('key')} status: {status_name}.",
                    "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/{item.get('key')}",
                })

            return {
                "is_live": True,
                "mode": "live",
                "count": len(activities),
                "activities": activities,
            }

        # Fallback demo activity
        demo_acts = cls._get_demo_activities()
        return {
            "is_live": False,
            "mode": "demo",
            "count": len(demo_acts),
            "activities": demo_acts,
        }

    @classmethod
    def create_issue(
        cls,
        summary: str,
        description: Optional[str] = None,
        issue_type: str = "Task",
        priority: Optional[str] = "Medium",
        parent_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new issue directly in Jira Cloud project SCR."""
        if not cls.is_configured():
            # In demo mode, simulate successful creation
            new_id = len(cls._demo_created_issues) + 60
            demo_key = f"SCR-{new_id}"
            new_issue = {
                "key": demo_key,
                "id": str(new_id),
                "summary": summary,
                "description": description or f"SecureCare Task: {summary}",
                "status": "To Do",
                "raw_status": "To Do",
                "status_category": "To Do",
                "issue_type": issue_type,
                "priority": priority or "Medium",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": parent_key,
                "parent_summary": f"Epic {parent_key}" if parent_key else None,
                "created": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "updated": time.strftime("%Y-%m-%dT%H:%M:%S.000Z"),
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/{demo_key}",
            }
            cls._demo_created_issues.insert(0, new_issue)
            return {
                "success": True,
                "is_live": False,
                "mode": "demo",
                "key": demo_key,
                "id": str(new_id),
                "url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/{demo_key}",
                "message": f"[Demo Mode] Created Jira issue {demo_key} in project {settings.JIRA_PROJECT_KEY}.",
            }

        headers = cls.get_auth_header()
        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/issue"

        desc_node = {
            "type": "doc",
            "version": 1,
            "content": [
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": description or f"Created via SecureCare Platform: {summary}",
                        }
                    ],
                }
            ],
        }

        fields: Dict[str, Any] = {
            "project": {"key": settings.JIRA_PROJECT_KEY},
            "summary": summary,
            "description": desc_node,
            "issuetype": {"name": issue_type},
        }

        if priority:
            fields["priority"] = {"name": priority}

        if parent_key:
            fields["parent"] = {"key": parent_key}

        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.post(url, headers=headers, json={"fields": fields})
                if resp.status_code in (200, 201):
                    data = resp.json()
                    cls.clear_cache()  # Invalidate cache so newly created issue shows immediately
                    return {
                        "success": True,
                        "is_live": True,
                        "mode": "live",
                        "key": data.get("key"),
                        "id": data.get("id"),
                        "url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/{data.get('key')}",
                        "message": f"Successfully created Jira issue {data.get('key')} in project {settings.JIRA_PROJECT_KEY}.",
                    }
                else:
                    return {
                        "success": False,
                        "is_live": False,
                        "mode": "live",
                        "status_code": resp.status_code,
                        "message": f"Jira API error ({resp.status_code}): {resp.text}",
                    }
        except Exception as e:
            return {
                "success": False,
                "is_live": False,
                "mode": "live",
                "message": f"Failed to connect to Jira Cloud: {str(e)}",
            }

    @classmethod
    def transition_issue(cls, issue_key: str, target_status: str) -> Dict[str, Any]:
        """
        Transition a Jira issue to a new status (e.g. 'To Do', 'In Progress', 'In Review', 'Done').
        Handles live Jira API transitions when configured, or updates demo state in memory.
        """
        valid_statuses = ["To Do", "In Progress", "In Review", "Done"]
        normalized_target = None
        for s in valid_statuses:
            if s.lower() == target_status.lower():
                normalized_target = s
                break
        if not normalized_target:
            normalized_target = target_status

        if not cls.is_configured():
            # In demo mode, update demo issue status
            all_issues = cls._get_demo_issues()
            found = False
            for iss in all_issues:
                if iss.get("key") == issue_key:
                    iss["status"] = normalized_target
                    iss["raw_status"] = normalized_target
                    iss["status_category"] = normalized_target
                    iss["updated"] = time.strftime("%Y-%m-%dT%H:%M:%S.000Z")
                    found = True
                    break
            cls.clear_cache()
            return {
                "success": True,
                "is_live": False,
                "mode": "demo",
                "key": issue_key,
                "status": normalized_target,
                "message": f"[Demo Mode] Successfully transitioned {issue_key} to '{normalized_target}'.",
            }

        headers = cls.get_auth_header()
        url = f"{settings.JIRA_BASE_URL.rstrip('/')}/rest/api/3/issue/{issue_key}/transitions"

        try:
            with httpx.Client(timeout=10.0) as client:
                # 1. Fetch available transitions
                t_resp = client.get(url, headers=headers)
                if t_resp.status_code != 200:
                    return {
                        "success": False,
                        "is_live": False,
                        "mode": "live",
                        "key": issue_key,
                        "status": target_status,
                        "message": f"Failed to fetch available transitions for {issue_key} ({t_resp.status_code})",
                    }
                transitions = t_resp.json().get("transitions", [])
                matching_transition = None
                for t in transitions:
                    t_name = t.get("name", "")
                    to_status = t.get("to", {}).get("name", "")
                    if t_name.lower() == normalized_target.lower() or to_status.lower() == normalized_target.lower():
                        matching_transition = t
                        break

                if not matching_transition:
                    avail_names = [t.get("name") for t in transitions]
                    return {
                        "success": False,
                        "is_live": False,
                        "mode": "live",
                        "key": issue_key,
                        "status": target_status,
                        "message": f"Transition '{normalized_target}' is not permitted by Jira workflow. Available transitions: {avail_names}",
                    }

                # 2. Post transition
                p_resp = client.post(url, headers=headers, json={"transition": {"id": matching_transition["id"]}})
                if p_resp.status_code in (200, 204):
                    cls.clear_cache()
                    return {
                        "success": True,
                        "is_live": True,
                        "mode": "live",
                        "key": issue_key,
                        "status": normalized_target,
                        "message": f"Successfully transitioned {issue_key} to '{normalized_target}' in Jira Cloud.",
                    }
                else:
                    return {
                        "success": False,
                        "is_live": False,
                        "mode": "live",
                        "key": issue_key,
                        "status": target_status,
                        "message": f"Jira transition API error ({p_resp.status_code}): {p_resp.text}",
                    }
        except Exception as e:
            return {
                "success": False,
                "is_live": False,
                "mode": "live",
                "key": issue_key,
                "status": target_status,
                "message": f"Failed to connect to Jira Cloud: {str(e)}",
            }

    # =========================================================================
    # STRUCTURED SECURECARE DEMO DATASETS (FALLBACK)
    # =========================================================================

    @classmethod
    def _get_demo_epics(cls) -> List[Dict[str, Any]]:
        return [
            {
                "key": "SCR-1",
                "summary": "Secure Foundation & Authentication",
                "name": "Secure Foundation & Authentication",
                "status": "Done",
                "total_stories": 9,
                "completed_stories": 9,
                "progress_percentage": 100.0,
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-1",
            },
            {
                "key": "SCR-2",
                "summary": "Appointment Management",
                "name": "Appointment Management",
                "status": "Done",
                "total_stories": 11,
                "completed_stories": 11,
                "progress_percentage": 100.0,
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-2",
            },
            {
                "key": "SCR-3",
                "summary": "Medical Records & Security",
                "name": "Medical Records & Security",
                "status": "Done",
                "total_stories": 10,
                "completed_stories": 10,
                "progress_percentage": 100.0,
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-3",
            },
            {
                "key": "SCR-4",
                "summary": "Adaptive SDLC & Quality Assurance",
                "name": "Adaptive SDLC & Quality Assurance",
                "status": "Done",
                "total_stories": 8,
                "completed_stories": 8,
                "progress_percentage": 100.0,
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-4",
            },
            {
                "key": "SCR-5",
                "summary": "CIAP Documentation & Demonstration",
                "name": "CIAP Documentation & Demonstration",
                "status": "In Progress",
                "total_stories": 6,
                "completed_stories": 5,
                "progress_percentage": 83.3,
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-5",
            },
        ]

    @classmethod
    def _get_demo_sprints(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": 72,
                "name": "SCR Sprint 1",
                "state": "closed",
                "goal": "Establish secure application architecture, database models and JWT authentication.",
                "startDate": "2026-10-05T05:51:25.069Z",
                "endDate": "2026-10-19T05:51:03.000Z",
                "completeDate": "2026-10-05T06:05:50.150Z",
                "originBoardId": 67,
            },
            {
                "id": 73,
                "name": "SCR Sprint 2",
                "state": "closed",
                "goal": "Implement secure appointment scheduling with RBAC and workflow controls.",
                "startDate": "2026-10-05T06:06:14.184Z",
                "endDate": "2026-10-19T06:06:09.000Z",
                "completeDate": "2026-10-05T06:13:34.557Z",
                "originBoardId": 67,
            },
            {
                "id": 74,
                "name": "SCR Sprint 3",
                "state": "closed",
                "goal": "Implement secure medical records, audit logging and collision prevention.",
                "startDate": "2026-10-05T06:16:57.950Z",
                "endDate": "2026-10-19T06:16:55.000Z",
                "completeDate": "2026-10-05T06:21:44.043Z",
                "originBoardId": 67,
            },
            {
                "id": 75,
                "name": "SCR Sprint 4",
                "state": "closed",
                "goal": "Evaluate security risks, perform iterative improvement and validate the integrated system.",
                "startDate": "2026-10-05T06:21:59.675Z",
                "endDate": "2026-10-19T06:21:56.000Z",
                "completeDate": "2026-10-05T06:44:18.917Z",
                "originBoardId": 67,
            },
            {
                "id": 76,
                "name": "SCR Sprint 5",
                "state": "active",
                "goal": "Complete diagrams, documentation, presentation and working-model evidence.",
                "startDate": "2026-10-05T06:57:47.887Z",
                "endDate": "2026-10-19T06:57:45.000Z",
                "completeDate": None,
                "originBoardId": 67,
            },
        ]

    @classmethod
    def _get_demo_issues(cls) -> List[Dict[str, Any]]:
        base_issues = [
            # Epics
            {
                "key": "SCR-1",
                "id": "10001",
                "summary": "Secure Foundation & Authentication",
                "description": "Establish core security, user accounts, and authentication.",
                "status": "Done",
                "raw_status": "Done",
                "status_category": "Done",
                "issue_type": "Epic",
                "priority": "High",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": None,
                "parent_summary": None,
                "created": "2026-10-04T10:00:00.000Z",
                "updated": "2026-10-05T06:05:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-1",
            },
            {
                "key": "SCR-2",
                "id": "10002",
                "summary": "Appointment Management",
                "description": "State machine workflow for appointments with double-booking prevention.",
                "status": "Done",
                "raw_status": "Done",
                "status_category": "Done",
                "issue_type": "Epic",
                "priority": "High",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": None,
                "parent_summary": None,
                "created": "2026-10-04T10:00:00.000Z",
                "updated": "2026-10-05T06:13:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-2",
            },
            {
                "key": "SCR-3",
                "id": "10003",
                "summary": "Medical Records & Security",
                "description": "Doctor-authored clinical records, prescription privacy, and audit logging.",
                "status": "Done",
                "raw_status": "Done",
                "status_category": "Done",
                "issue_type": "Epic",
                "priority": "High",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": None,
                "parent_summary": None,
                "created": "2026-10-04T10:00:00.000Z",
                "updated": "2026-10-05T06:21:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-3",
            },
            {
                "key": "SCR-4",
                "id": "10004",
                "summary": "Adaptive SDLC & Quality Assurance",
                "description": "Security testing, audit logs dashboard, and regression suites.",
                "status": "Done",
                "raw_status": "Done",
                "status_category": "Done",
                "issue_type": "Epic",
                "priority": "High",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": None,
                "parent_summary": None,
                "created": "2026-10-04T10:00:00.000Z",
                "updated": "2026-10-05T06:44:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-4",
            },
            {
                "key": "SCR-5",
                "id": "10005",
                "summary": "CIAP Documentation & Demonstration",
                "description": "Demonstration readiness, API integration, and architectural documentation.",
                "status": "In Progress",
                "raw_status": "In Progress",
                "status_category": "In Progress",
                "issue_type": "Epic",
                "priority": "Medium",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": None,
                "parent_summary": None,
                "created": "2026-10-04T10:00:00.000Z",
                "updated": "2026-10-05T06:57:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-5",
            },
            # Stories / Tasks
            {
                "key": "SCR-10",
                "id": "10010",
                "summary": "Implement JWT authentication and bcrypt password hashing",
                "description": "Secure access tokens with expiration and rate limiting.",
                "status": "Done",
                "raw_status": "Done",
                "status_category": "Done",
                "issue_type": "Story",
                "priority": "Highest",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": "SCR-1",
                "parent_summary": "Secure Foundation & Authentication",
                "created": "2026-10-04T11:00:00.000Z",
                "updated": "2026-10-05T06:00:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-10",
            },
            {
                "key": "SCR-11",
                "id": "10011",
                "summary": "Implement Role-Based Access Control (RBAC) dependencies",
                "description": "Patient, Doctor, and Admin enforcement filters.",
                "status": "Done",
                "raw_status": "Done",
                "status_category": "Done",
                "issue_type": "Story",
                "priority": "High",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": "SCR-1",
                "parent_summary": "Secure Foundation & Authentication",
                "created": "2026-10-04T11:30:00.000Z",
                "updated": "2026-10-05T06:05:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-11",
            },
            {
                "key": "SCR-20",
                "id": "10020",
                "summary": "Build Appointment Booking and Collision Prevention Engine",
                "description": "Prevent concurrent bookings and enforce doctor schedule slot checks.",
                "status": "Done",
                "raw_status": "Done",
                "status_category": "Done",
                "issue_type": "Story",
                "priority": "High",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": "SCR-2",
                "parent_summary": "Appointment Management",
                "created": "2026-10-04T12:00:00.000Z",
                "updated": "2026-10-05T06:12:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-20",
            },
            {
                "key": "SCR-30",
                "id": "10030",
                "summary": "Implement Medical Record CRUD with IDOR Protection",
                "description": "Only authorized doctors and owner patients can view medical records.",
                "status": "Done",
                "raw_status": "Done",
                "status_category": "Done",
                "issue_type": "Story",
                "priority": "Highest",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": "SCR-3",
                "parent_summary": "Medical Records & Security",
                "created": "2026-10-04T13:00:00.000Z",
                "updated": "2026-10-05T06:20:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-30",
            },
            {
                "key": "SCR-40",
                "id": "10040",
                "summary": "Admin Audit Log Dashboard and Account Lockout Monitoring",
                "description": "Track login attempts, security events, and audit trails in real time.",
                "status": "Done",
                "raw_status": "Done",
                "status_category": "Done",
                "issue_type": "Story",
                "priority": "High",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": "SCR-4",
                "parent_summary": "Adaptive SDLC & Quality Assurance",
                "created": "2026-10-04T14:00:00.000Z",
                "updated": "2026-10-05T06:40:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-40",
            },
            {
                "key": "SCR-50",
                "id": "10050",
                "summary": "Jira Cloud Bidirectional Integration Service & Kanban Board",
                "description": "Live sync with Atlassian Jira Cloud REST API v3 and Agile board.",
                "status": "Done",
                "raw_status": "Done",
                "status_category": "Done",
                "issue_type": "Story",
                "priority": "Highest",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": "SCR-5",
                "parent_summary": "CIAP Documentation & Demonstration",
                "created": "2026-10-05T07:00:00.000Z",
                "updated": "2026-10-05T08:00:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-50",
            },
            {
                "key": "SCR-51",
                "id": "10051",
                "summary": "Final CIAP Micro-Project Demonstration and Evidence Package",
                "description": "Compile academic evidence, test logs, and live Jira workflow verification.",
                "status": "In Progress",
                "raw_status": "In Progress",
                "status_category": "In Progress",
                "issue_type": "Task",
                "priority": "High",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": "SCR-5",
                "parent_summary": "CIAP Documentation & Demonstration",
                "created": "2026-10-05T07:15:00.000Z",
                "updated": "2026-10-05T08:15:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-51",
            },
            {
                "key": "SCR-52",
                "id": "10052",
                "summary": "Conduct Final Security & Quality Review",
                "description": "Complete 64+ automated test verification and static analysis audit.",
                "status": "To Do",
                "raw_status": "To Do",
                "status_category": "To Do",
                "issue_type": "Task",
                "priority": "Medium",
                "assignee": {"name": "AaYushman Parab", "email": "admin@securecare.local", "avatar": ""},
                "parent_key": "SCR-5",
                "parent_summary": "CIAP Documentation & Demonstration",
                "created": "2026-10-05T07:30:00.000Z",
                "updated": "2026-10-05T08:20:00.000Z",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-52",
            },
        ]
        return cls._demo_created_issues + base_issues

    @classmethod
    def _get_demo_activities(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": "ACT-1",
                "timestamp": "2026-10-05 08:15",
                "author": "AaYushman Parab",
                "type": "STATUS_UPDATE",
                "issue_key": "SCR-51",
                "summary": "Final CIAP Micro-Project Demonstration and Evidence Package",
                "status": "In Progress",
                "details": "Compiled complete architectural evidence and Jira integration demo.",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-51",
            },
            {
                "id": "ACT-2",
                "timestamp": "2026-10-05 08:00",
                "author": "AaYushman Parab",
                "type": "STATUS_UPDATE",
                "issue_key": "SCR-50",
                "summary": "Jira Cloud Bidirectional Integration Service & Kanban Board",
                "status": "Done",
                "details": "Verified REST API v3 search/jql and agile sprint synchronizer.",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-50",
            },
            {
                "id": "ACT-3",
                "timestamp": "2026-10-05 06:44",
                "author": "AaYushman Parab",
                "type": "SPRINT_COMPLETION",
                "issue_key": "SCR-4",
                "summary": "Adaptive SDLC & Quality Assurance",
                "status": "Done",
                "details": "Completed Sprint 4 with 47 automated security and integration tests passing.",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-4",
            },
            {
                "id": "ACT-4",
                "timestamp": "2026-10-05 06:21",
                "author": "AaYushman Parab",
                "type": "SPRINT_COMPLETION",
                "issue_key": "SCR-3",
                "summary": "Medical Records & Security",
                "status": "Done",
                "details": "Completed Sprint 3 medical records, prescriptions and HIPAA audit logging.",
                "jira_url": f"{settings.JIRA_BASE_URL.rstrip('/')}/browse/SCR-3",
            },
        ]
