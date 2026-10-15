"""Streamlit Interactive Jira Agile Kanban Board.
Pure-Python, Zero HTML, Zero Custom CSS.
"""
import streamlit as st
from app.db.database import SessionLocal
from app.models.user import UserRole
from app.services.jira_service import JiraService
from app.ui.auth_state import get_current_user
from app.ui.components import (
    COLOR_CRITICAL,
    COLOR_DARK_NAVY,
    COLOR_NAVY,
    COLOR_SUCCESS,
    COLOR_TEAL,
    COLOR_WARNING,
    empty_state,
    page_header,
    section_heading,
)


def render_jira_board() -> None:
    """Render interactive 4-column Agile Kanban board synchronized with Jira Cloud."""
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if not user or user.role != UserRole.ADMIN:
            st.error("Access Forbidden: Only Administrators are authorized to view and interact with Jira Agile Boards.")
            return

        page_header(
            "Jira Cloud Agile Kanban Board",
            "Live synchronization with Atlassian Jira Cloud (REST API v3). Track tasks, transition issues, and author new user stories.",
            badge="Atlassian Agile",
        )

        # Connection status bar & board controls
        conn = JiraService.check_connection()
        col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
        with col_c1:
            if conn.get("is_connected"):
                st.success(f"🟢 **Jira Cloud**: Connected to `{conn.get('project_key', 'SCR')}`")
            else:
                st.info(f"🟡 **Jira Cloud Offline Mode**: Operating on schema for `{conn.get('project_key', 'SCR')}`")
        with col_c2:
            if st.button("🔄 Sync & Refresh Board", use_container_width=True):
                JiraService.clear_cache()
                st.rerun()
        with col_c3:
            show_creator = st.checkbox("➕ New Issue", value=False)

        # Issue Creator Container
        if show_creator:
            with st.container(border=True):
                st.subheader("Create Jira Cloud User Story / Task")
                st.caption(f"Push a new development or security story into `{conn.get('project_key', 'SCR')}` backlog.")
                with st.form("create_jira_issue_form"):
                    new_summary = st.text_input("Summary / Title *", placeholder="e.g. Implement automated vulnerability scanning")
                    new_desc = st.text_area("Description & Acceptance Criteria", placeholder="Given a medical practitioner, when accessing lab results...")
                    col_type, col_pri = st.columns(2)
                    with col_type:
                        new_type = st.selectbox("Issue Type", options=["Story", "Task", "Bug", "Improvement"])
                    with col_pri:
                        new_pri = st.selectbox("Priority", options=["Highest", "High", "Medium", "Low", "Lowest"], index=2)

                    submit_issue = st.form_submit_button("Push Issue to Jira Cloud", type="primary", use_container_width=True)

                if submit_issue:
                    if not new_summary or not new_summary.strip():
                        st.warning("Issue summary is required.")
                    else:
                        created_issue = JiraService.create_issue({
                            "summary": new_summary.strip(),
                            "description": new_desc.strip() if new_desc else "",
                            "issue_type": new_type,
                            "priority": new_pri,
                        })
                        if created_issue:
                            st.success(f"Issue **{created_issue.get('key', 'SCR-NEW')}** successfully created!")
                            st.rerun()
                        else:
                            st.error("Failed to push issue to Jira Cloud API.")

        st.divider()

        # Fetch issues
        issues_resp = JiraService.get_issues()
        issues = issues_resp.get("issues", []) if isinstance(issues_resp, dict) else issues_resp

        # Group issues into 4 Kanban columns
        cols_map = {
            "To Do": [],
            "In Progress": [],
            "In Review": [],
            "Done": [],
        }

        for issue in issues:
            status = issue.get("status", "To Do")
            if status in ("To Do", "Open", "Backlog", "Selected for Development"):
                cols_map["To Do"].append(issue)
            elif status in ("In Progress",):
                cols_map["In Progress"].append(issue)
            elif status in ("In Review", "Review", "Under Review", "Code Review"):
                cols_map["In Review"].append(issue)
            else:
                cols_map["Done"].append(issue)

        col_todo, col_prog, col_rev, col_done = st.columns(4)

        def _render_column(column_title: str, items: list, badge_text: str):
            st.markdown(f"##### {column_title}")
            st.caption(f"{len(items)} story card(s)")
            if not items:
                empty_state("No Issues", f"No items in {column_title}.")
                return

            for it in items:
                key = it.get("key", "SCR-?")
                summary = it.get("summary", "No Summary")
                priority = it.get("priority", "Medium")
                itype = it.get("issue_type", "Story")
                assignee = it.get("assignee", "Unassigned")

                with st.container(border=True):
                    st.markdown(f"**`{key}`**")
                    st.write(summary)
                    c_meta1, c_meta2 = st.columns(2)
                    with c_meta1:
                        st.caption(f"Type: **{itype}**")
                    with c_meta2:
                        st.caption(f"Priority: **{priority}**")
                    st.caption(f"👤 {assignee}")

                    # Transition controls
                    other_cols = [c for c in ["To Do", "In Progress", "In Review", "Done"] if c != column_title]
                    next_status = st.selectbox(
                        "Move To:",
                        options=other_cols,
                        key=f"sel_move_{key}",
                        label_visibility="collapsed",
                    )
                    if st.button("Move", key=f"btn_move_{key}", use_container_width=True):
                        res = JiraService.transition_issue(key, next_status)
                        if res.get("success"):
                            st.success(f"{key} → {next_status}")
                            st.rerun()
                        else:
                            st.error(res.get("error", "Transition failed"))

        with col_todo:
            _render_column("📋 To Do", cols_map["To Do"], "Backlog")

        with col_prog:
            _render_column("⚡ In Progress", cols_map["In Progress"], "Active")

        with col_rev:
            _render_column("🔍 In Review", cols_map["In Review"], "Verification")

        with col_done:
            _render_column("✅ Done", cols_map["Done"], "Accepted")

    finally:
        db.close()
