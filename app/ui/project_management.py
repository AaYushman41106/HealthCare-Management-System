"""Streamlit Sprints & Epics Project Management Hub.
Pure-Python, Zero HTML, Zero Custom CSS.
"""
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from app.db.database import SessionLocal
from app.models.user import UserRole
from app.services.jira_service import JiraService
from app.ui.auth_state import get_current_user
from app.ui.components import (
    COLOR_BORDER,
    COLOR_NAVY,
    COLOR_SUCCESS,
    COLOR_TEAL,
    COLOR_WARNING,
    apply_plotly_theme,
    empty_state,
    page_header,
    section_heading,
)


def render_project_management() -> None:
    """Render agile sprints velocity, burndown, and epic traceability hub."""
    db = SessionLocal()
    try:
        user = get_current_user(db)
        if not user or user.role != UserRole.ADMIN:
            st.error("Access Forbidden: Only Administrators are authorized to view Project Management telemetry.")
            return

        page_header(
            "Sprints Velocity & Epics Traceability Hub",
            "Track Adaptive SDLC delivery velocity, story point completion, and epic progress across Sprints 1 to 5.",
            badge="Agile SDLC Metrics",
        )

        summary = JiraService.get_project_summary()
        sprints_resp = JiraService.get_sprints()
        sprints = sprints_resp.get("sprints", []) if isinstance(sprints_resp, dict) else sprints_resp
        epics_resp = JiraService.get_epics()
        epics = epics_resp.get("epics", []) if isinstance(epics_resp, dict) else epics_resp

        # High-level Metrics Row
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Total User Stories", summary.get("total_issues", 28))
        m2.metric("Completed Stories", summary.get("resolved_issues", 22))
        m3.metric("Strategic Epics", len(epics))
        m4.metric("Tracked Sprints", len(sprints))

        st.divider()

        tab_velocity, tab_epics = st.tabs([
            "📊 Sprints 1–5 Velocity & Progress",
            "🎯 Epics Traceability & Child Stories",
        ])

        with tab_velocity:
            section_heading("Sprint Velocity: Planned vs Completed Story Points", "Historical throughput across five Adaptive SDLC delivery milestones.")

            sprint_names = [s.get("name", f"Sprint {i+1}") for i, s in enumerate(sprints)]
            planned_points = [s.get("planned_points", 20) for s in sprints]
            completed_points = [s.get("completed_points", 18) for s in sprints]

            fig_vel = go.Figure(data=[
                go.Bar(name="Planned Story Points", x=sprint_names, y=planned_points, marker_color="#CBD5E1"),
                go.Bar(name="Completed Story Points", x=sprint_names, y=completed_points, marker_color=COLOR_TEAL),
            ])
            apply_plotly_theme(fig_vel, height=320)
            fig_vel.update_layout(
                barmode="group",
                xaxis_title="Agile Sprints",
                yaxis_title="Story Points",
            )
            st.plotly_chart(fig_vel, use_container_width=True)

            st.divider()
            section_heading("Sprint Delivery Audit Ledger", "Sprint goals, status, and completion rate breakdown.")

            sprint_table = []
            for s in sprints:
                planned = s.get("planned_points", 0)
                completed = s.get("completed_points", 0)
                rate = f"{int((completed / max(planned, 1)) * 100)}%"
                sprint_table.append({
                    "Sprint Name": s.get("name"),
                    "Sprint Goal": s.get("goal", "Sprint Delivery Objectives"),
                    "Lifecycle State": s.get("state", "CLOSED").upper(),
                    "Planned Points": planned,
                    "Completed Points": completed,
                    "Completion Rate": rate,
                })
            st.dataframe(pd.DataFrame(sprint_table), use_container_width=True, hide_index=True)

        with tab_epics:
            section_heading("Adaptive SDLC Epics Traceability", "Visual progress bars and child story breakdown for each strategic healthcare epic.")

            if epics:
                for epic in epics:
                    name = epic.get("name", "Epic")
                    progress = epic.get("progress", 0.0)
                    child_count = epic.get("child_count", 0)
                    status = epic.get("status", "IN PROGRESS")

                    with st.expander(f"🎯 **{name}** — Status: `{status}` ({int(progress * 100)}% Complete)", expanded=False):
                        st.progress(float(progress))
                        st.caption(f"Child Stories / Verification Items: **{child_count}**")
                        if "description" in epic:
                            st.write(epic["description"])
            else:
                empty_state("No Epics Recorded", "No strategic epics are currently tracked in Jira.")

    finally:
        db.close()
