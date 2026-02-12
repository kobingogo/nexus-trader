"""
Google OAuth2 服务
处理 OAuth 授权流程、token 管理
"""

import os
import logging
from typing import Optional
from urllib.parse import urlencode

import requests

logger = logging.getLogger(__name__)

# OAuth2 配置
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET", "")
REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", "http://localhost:8000/api/v1/llm/google/callback")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

# Google OAuth endpoints
AUTH_ENDPOINT = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_ENDPOINT = "https://oauth2.googleapis.com/token"
USERINFO_ENDPOINT = "https://www.googleapis.com/oauth2/v2/userinfo"

# 请求的 scope
SCOPES = [
    "openid",
    "email",
    "profile",
    "https://www.googleapis.com/auth/cloud-platform",  # Vertex AI 访问
]


class GoogleOAuthService:
    """Google OAuth2 处理服务"""

    @staticmethod
    def get_auth_url(state: str = "") -> str:
        """
        生成 Google OAuth 授权 URL
        state 参数可用于防 CSRF
        """
        if not GOOGLE_CLIENT_ID:
            raise ValueError(
                "GOOGLE_CLIENT_ID not configured. "
                "Set it as an environment variable."
            )

        params = {
            "client_id": GOOGLE_CLIENT_ID,
            "redirect_uri": REDIRECT_URI,
            "response_type": "code",
            "scope": " ".join(SCOPES),
            "access_type": "offline",  # 获取 refresh_token
            "prompt": "consent",  # 强制显示同意页面以获取 refresh_token
            "include_granted_scopes": "true",
        }
        if state:
            params["state"] = state

        return f"{AUTH_ENDPOINT}?{urlencode(params)}"

    @staticmethod
    def exchange_code(code: str) -> dict:
        """
        用授权码换取 access_token / refresh_token
        返回 { access_token, refresh_token, expires_in, id_token, ... }
        """
        if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
            raise ValueError("Google OAuth credentials not configured.")

        response = requests.post(
            TOKEN_ENDPOINT,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": REDIRECT_URI,
            },
            timeout=15,
        )

        if response.status_code != 200:
            logger.error(f"Token exchange failed: {response.text}")
            raise ValueError(f"Token exchange failed: {response.status_code}")

        return response.json()

    @staticmethod
    def refresh_access_token(refresh_token: str) -> dict:
        """
        使用 refresh_token 获取新的 access_token
        返回 { access_token, expires_in, ... }
        """
        response = requests.post(
            TOKEN_ENDPOINT,
            data={
                "client_id": GOOGLE_CLIENT_ID,
                "client_secret": GOOGLE_CLIENT_SECRET,
                "refresh_token": refresh_token,
                "grant_type": "refresh_token",
            },
            timeout=15,
        )

        if response.status_code != 200:
            logger.error(f"Token refresh failed: {response.text}")
            raise ValueError(f"Token refresh failed: {response.status_code}")

        return response.json()

    @staticmethod
    def get_user_info(access_token: str) -> dict:
        """
        获取 Google 用户信息
        返回 { id, email, name, picture, ... }
        """
        response = requests.get(
            USERINFO_ENDPOINT,
            headers={"Authorization": f"Bearer {access_token}"},
            timeout=10,
        )

        if response.status_code != 200:
            logger.error(f"Failed to get user info: {response.text}")
            raise ValueError("Failed to get user info")

        return response.json()

    @staticmethod
    def get_frontend_url() -> str:
        """返回前端 URL"""
        return FRONTEND_URL
