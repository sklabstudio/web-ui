"""Other SKLab integrations: thin detectors, graceful degradation."""
from __future__ import annotations

from sklab_web.integrations import component_state


def agent_catalog(mock_mode: bool) -> tuple[list[dict], str | None]:
    st = component_state("agent_adapters", mock_mode)
    return [], st.get("version")


def provider_statuses(mock_mode: bool) -> tuple[list[dict], str | None]:
    st = component_state("provider_connections", mock_mode)
    return [], st.get("version")
