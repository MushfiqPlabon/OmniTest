"""Composed OmniTest REST API client for Streamlit views."""

from __future__ import annotations

from api.auth import AuthAPI
from api.chat import ChatAPI
from api.essays import EssaysAPI
from api.http import API_BASE_URL, APIError, APITransport
from api.materials import MaterialsAPI
from api.quizzes import QuizzesAPI


class OmniTestAPIClient:
    """Composes domain-specific API wrappers over one pooled `APITransport`."""

    def __init__(self, base_url: str = API_BASE_URL):
        self.transport = APITransport(base_url=base_url)
        self.auth = AuthAPI(self.transport)
        self.materials = MaterialsAPI(self.transport)
        self.quizzes = QuizzesAPI(self.transport)
        self.essays = EssaysAPI(self.transport)
        self.chat = ChatAPI(self.transport)


api = OmniTestAPIClient()

__all__ = ["APIError", "OmniTestAPIClient", "api"]
