"""Compatibility wrapper around ``st.session_state``.

This keeps the app's existing ``SessionState.get(...)`` call sites working
while using Streamlit's built-in session state on modern versions.
"""

import streamlit as st


class SessionState:
    def __init__(self, state):
        object.__setattr__(self, "_state", state)

    def __getattr__(self, name):
        try:
            return self._state[name]
        except KeyError as exc:
            raise AttributeError(name) from exc

    def __setattr__(self, name, value):
        self._state[name] = value

    def __delattr__(self, name):
        try:
            del self._state[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


def get(**kwargs):
    for key, value in kwargs.items():
        if key not in st.session_state:
            st.session_state[key] = value
    return SessionState(st.session_state)
