"""Couple Expense Tracker entry point.

Pre-Phase scaffolding only. Auth, navigation, and the dashboard land in Phase 1.B and 1.F.
"""

from __future__ import annotations

import streamlit as st

st.set_page_config(
    page_title="Couple Expense Tracker",
    page_icon="$",
    layout="wide",
    initial_sidebar_state="auto",
)


def main() -> None:
    st.title("Couple Expense Tracker")
    st.caption("Pre-Phase scaffolding. See IMPLEMENTATION_PLAN.md for what comes next.")

    with st.expander("Secrets check"):
        try:
            supabase_url = st.secrets["supabase"]["url"]
            st.success(f"Supabase URL loaded: {supabase_url[:30]}...")
        except (KeyError, FileNotFoundError):
            st.warning(
                "No Supabase secrets found. Copy "
                "`.streamlit/secrets.toml.example` to `.streamlit/secrets.toml` "
                "and fill in your values."
            )


if __name__ == "__main__":
    main()
