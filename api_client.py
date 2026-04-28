import os
from typing import Any, Dict, Optional

import requests
import streamlit as st

from config import settings
from response_utils import unwrap_payload


API_BASE_URL = os.getenv("AQUA_API_BASE_URL", settings.api_base_url)


def auth_headers() -> Dict[str, str]:
    token = st.session_state.get("auth_token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}


def api_get(endpoint: str) -> Optional[Dict[str, Any]]:
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.get(url, headers=auth_headers(), timeout=settings.request_timeout_seconds)
        response.raise_for_status()
        return unwrap_payload(response.json())
    except requests.exceptions.ConnectionError:
        st.warning("Backend service is offline. The dashboard can continue in local AI mode.")
    except requests.exceptions.Timeout:
        st.warning("The backend took too long to respond. Please try again.")
    except requests.exceptions.HTTPError as exc:
        st.warning(f"The backend returned an error: {exc}")
    except ValueError:
        st.warning("The backend returned an unreadable response.")
    except requests.exceptions.RequestException as exc:
        st.warning(f"Unexpected backend error: {exc}")
    return None


def api_post(endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.post(url, json=payload, headers=auth_headers(), timeout=settings.request_timeout_seconds)
        response.raise_for_status()
        return unwrap_payload(response.json())
    except requests.exceptions.ConnectionError:
        st.warning("Backend service is offline. The dashboard can continue in local AI mode.")
    except requests.exceptions.Timeout:
        st.warning("The backend took too long to respond. Please try again.")
    except requests.exceptions.HTTPError as exc:
        st.warning(f"The backend returned an error: {exc}")
    except ValueError:
        st.warning("The backend returned an unreadable response.")
    except requests.exceptions.RequestException as exc:
        st.warning(f"Unexpected backend error: {exc}")
    return None


def api_patch(endpoint: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    url = f"{API_BASE_URL}{endpoint}"
    try:
        response = requests.patch(url, json=payload, headers=auth_headers(), timeout=settings.request_timeout_seconds)
        response.raise_for_status()
        return unwrap_payload(response.json())
    except requests.exceptions.ConnectionError:
        st.warning("Backend service is offline. Please try again when the city service is online.")
    except requests.exceptions.Timeout:
        st.warning("The backend took too long to respond. Please try again.")
    except requests.exceptions.HTTPError as exc:
        st.warning(f"The backend returned an error: {exc}")
    except ValueError:
        st.warning("The backend returned an unreadable response.")
    except requests.exceptions.RequestException as exc:
        st.warning(f"Unexpected backend error: {exc}")
    return None
