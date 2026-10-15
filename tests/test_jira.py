import pytest
from unittest.mock import patch
from app.core.security import create_access_token, hash_password
from app.models.user import User, UserRole
from app.services.jira_service import JiraService


@pytest.fixture
def test_admin_user(db_session):
    admin = User(
        username="jira_admin",
        email="jira_admin@securecare.org",
        hashed_password=hash_password("AdminSecure123!"),
        role=UserRole.ADMIN,
        is_active=True,
    )
    db_session.add(admin)
    db_session.commit()
    db_session.refresh(admin)
    return admin


@pytest.fixture
def admin_headers(test_admin_user):
    token = create_access_token(
        subject=test_admin_user.id,
        claims={"username": test_admin_user.username, "role": test_admin_user.role.value},
    )
    return {"Authorization": f"Bearer {token}"}


def test_jira_status_endpoint(client):
    """GET /api/integrations/jira/status returns 200 with connection and project details."""
    response = client.get("/api/integrations/jira/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_configured" in data
    assert "is_connected" in data
    assert data["project_key"] == "SCR"
    assert "atlassian.net" in data["base_url"]
    assert data["mode"] in ("live", "demo")


def test_jira_project_summary_endpoint(client):
    """GET /api/integrations/jira/project returns 200 with summary KPIs."""
    response = client.get("/api/integrations/jira/project")
    assert response.status_code == 200
    data = response.json()
    assert data["project_key"] == "SCR"
    assert data["total_issues"] >= 5
    assert data["total_epics"] == 5
    assert 0 <= data["completion_percentage"] <= 100.0


def test_jira_epics_endpoint(client):
    """GET /api/integrations/jira/epics returns 200 with all 5 SecureCare Epics."""
    response = client.get("/api/integrations/jira/epics")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 5
    epic_keys = [e["key"] for e in data["epics"]]
    assert "SCR-1" in epic_keys
    assert "SCR-2" in epic_keys
    assert "SCR-3" in epic_keys
    assert "SCR-4" in epic_keys
    assert "SCR-5" in epic_keys


def test_jira_issues_endpoint_and_filters(client):
    """GET /api/integrations/jira/issues returns normalized issues and respects filters."""
    # 1. Fetch all
    response = client.get("/api/integrations/jira/issues")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] > 0
    first_issue = data["issues"][0]
    assert "key" in first_issue
    assert "summary" in first_issue
    assert "status" in first_issue

    # 2. Filter by status
    res_done = client.get("/api/integrations/jira/issues?status=Done")
    assert res_done.status_code == 200
    for item in res_done.json()["issues"]:
        assert item["status"] == "Done"

    # 3. Filter by epic_key
    res_epic = client.get("/api/integrations/jira/issues?epic_key=SCR-1")
    assert res_epic.status_code == 200
    assert "issues" in res_epic.json()


def test_jira_sprints_endpoint(client):
    """GET /api/integrations/jira/sprints returns Sprint 1 through Sprint 5."""
    response = client.get("/api/integrations/jira/sprints")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] == 5
    sprint_names = [s["name"] for s in data["sprints"]]
    assert any("Sprint 1" in name for name in sprint_names)
    assert any("Sprint 5" in name for name in sprint_names)


def test_jira_progress_endpoint(client):
    """GET /api/integrations/jira/progress returns SDLC progress metrics."""
    response = client.get("/api/integrations/jira/progress")
    assert response.status_code == 200
    data = response.json()
    assert "completion_percentage" in data
    assert "health_status" in data
    assert "status_distribution" in data
    assert "epics" in data
    assert "sprints" in data


def test_jira_activity_endpoint(client):
    """GET /api/integrations/jira/activity returns recent activity log."""
    response = client.get("/api/integrations/jira/activity")
    assert response.status_code == 200
    data = response.json()
    assert data["count"] > 0
    assert len(data["activities"]) > 0


def test_jira_refresh_endpoint(client):
    """POST /api/integrations/jira/refresh clears in-memory cache."""
    response = client.post("/api/integrations/jira/refresh")
    assert response.status_code == 200
    assert response.json()["success"] is True


def test_jira_create_issue_unauthenticated_forbidden(client):
    """POST /api/integrations/jira/issues requires authentication."""
    response = client.post(
        "/api/integrations/jira/issues",
        json={"summary": "Unauthenticated test issue", "issue_type": "Task"},
    )
    assert response.status_code == 401


def test_jira_create_issue_authenticated_validation(client, admin_headers):
    """POST /api/integrations/jira/issues validates minimum summary length."""
    response = client.post(
        "/api/integrations/jira/issues",
        headers=admin_headers,
        json={"summary": "ab", "issue_type": "Task"},  # Less than min 3 chars
    )
    assert response.status_code == 422


def test_jira_create_issue_mocked_success(client, admin_headers):
    """POST /api/integrations/jira/issues creates issue and records audit log."""
    mock_res = {
        "success": True,
        "is_live": True,
        "mode": "live",
        "key": "SCR-99",
        "id": "10099",
        "url": "https://sakec-team-bcq481n1.atlassian.net/browse/SCR-99",
        "message": "Successfully created Jira issue SCR-99 in project SCR.",
    }

    with patch.object(JiraService, "create_issue", return_value=mock_res):
        response = client.post(
            "/api/integrations/jira/issues",
            headers=admin_headers,
            json={
                "summary": "Implement automated penetration testing harness",
                "issue_type": "Task",
                "priority": "High",
                "parent_key": "SCR-4",
                "description": "Integration with automated test execution pipeline.",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["success"] is True
        assert data["key"] == "SCR-99"


def test_jira_service_demo_fallback():
    """Verify JiraService structured demo mode behaves correctly when unconfigured."""
    with patch.object(JiraService, "is_configured", return_value=False):
        conn = JiraService.check_connection()
        assert conn["is_connected"] is False
        assert conn["mode"] == "demo"

        summary = JiraService.get_project_summary()
        assert summary["mode"] == "demo"
        assert summary["total_issues"] > 0
        assert summary["total_epics"] == 5

        epics = JiraService.get_epics()
        assert epics["mode"] == "demo"
        assert len(epics["epics"]) == 5

        sprints = JiraService.get_sprints()
        assert sprints["mode"] == "demo"
        assert len(sprints["sprints"]) == 5

        demo_issue = JiraService.create_issue(
            summary="Demo Test Task",
            description="Testing demo fallback",
            issue_type="Task",
        )
        assert demo_issue["success"] is True
        assert demo_issue["mode"] == "demo"
        assert "SCR-" in demo_issue["key"]


def test_jira_transition_issue_endpoint(client, admin_headers):
    """POST /api/integrations/jira/issues/{key}/transition transitions an issue."""
    # Test transition in demo mode
    response = client.post(
        "/api/integrations/jira/issues/SCR-52/transition",
        headers=admin_headers,
        json={"status": "In Progress"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["key"] == "SCR-52"
    assert data["status"] == "In Progress"
