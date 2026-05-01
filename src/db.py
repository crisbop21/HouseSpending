"""Supabase client wrapper. Reads credentials from Streamlit secrets."""

from __future__ import annotations

import streamlit as st
from supabase import Client, create_client


@st.cache_resource
def get_client() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)
