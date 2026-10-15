"""SecureCare Design System — Native Streamlit UI Primitives & Styling Helpers.
Zero HTML, zero custom CSS, zero JS. Pure Python design system.
"""
from typing import Any, Optional
import streamlit as st


# Brand Palette Constants
COLOR_NAVY = "#102A43"
COLOR_DARK_NAVY = "#0B1F33"
COLOR_TEAL = "#0F9D92"
COLOR_PALE_TEAL = "#E7F7F5"
COLOR_BG = "#F4F7FB"
COLOR_WHITE = "#FFFFFF"
COLOR_TEXT_PRIMARY = "#172B4D"
COLOR_TEXT_MUTED = "#62748A"
COLOR_BORDER = "#DFE7EF"
COLOR_SUCCESS = "#16856B"
COLOR_WARNING = "#C58A26"
COLOR_CRITICAL = "#C84C4C"


def page_header(title: str, subtitle: str, badge: Optional[str] = None) -> None:
    """Render a standardized, premium page header."""
    col_t, col_b = st.columns([4, 1])
    with col_t:
        st.subheader(title)
        st.caption(subtitle)
    with col_b:
        if badge:
            st.info(badge)
    st.divider()


def section_heading(title: str, caption: Optional[str] = None) -> None:
    """Render a distinct, clean section heading."""
    st.markdown(f"#### {title}")
    if caption:
        st.caption(caption)


def empty_state(title: str, message: str, icon: str = "ℹ️") -> None:
    """Render a polite, helpful empty state container."""
    with st.container(border=True):
        st.markdown(f"**{icon} {title}**")
        st.caption(message)


def apply_plotly_theme(fig, height: int = 300, title: Optional[str] = None):
    """Apply consistent, accessible healthcare SaaS palette to Plotly figures."""
    fig.update_layout(
        title=dict(text=title, font=dict(family="sans-serif", size=14, color=COLOR_NAVY)) if title else None,
        height=height,
        margin=dict(l=20, r=20, t=30 if title else 15, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="sans-serif", size=12, color=COLOR_TEXT_PRIMARY),
        xaxis=dict(
            showgrid=True,
            gridcolor=COLOR_BORDER,
            zeroline=False,
            tickfont=dict(color=COLOR_TEXT_MUTED, size=11),
        ),
        yaxis=dict(
            showgrid=True,
            gridcolor=COLOR_BORDER,
            zeroline=False,
            tickfont=dict(color=COLOR_TEXT_MUTED, size=11),
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            font=dict(size=11, color=COLOR_TEXT_MUTED),
        ),
    )
    return fig
