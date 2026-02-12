"""
LLM 提供商管理器
负责配置读写、提供商 CRUD、模型切换、连接测试
"""

import json
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Tuple

from openai import OpenAI

from app.models.llm_config import (
    LLMConfigFile,
    ProviderConfig,
    ProviderType,
    AuthType,
    ActiveModel,
    AddProviderRequest,
    UpdateProviderRequest,
    OAuthTokens,
    PROVIDER_PRESETS,
)

logger = logging.getLogger(__name__)

# 配置文件路径
CONFIG_DIR = Path(__file__).parent.parent
CONFIG_FILE = CONFIG_DIR / "llm_config.json"


class LLMProviderManager:
    """LLM 提供商管理器 (单例模式)"""

    _instance: Optional["LLMProviderManager"] = None
    _config: Optional[LLMConfigFile] = None

    def __new__(cls) -> "LLMProviderManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if self._config is None:
            self._config = self._load_config()

    # ---- 配置读写 ----

    def _load_config(self) -> LLMConfigFile:
        """从 JSON 文件加载配置"""
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
                return LLMConfigFile(**data)
            except Exception as e:
                logger.error(f"Failed to load LLM config: {e}")
        return LLMConfigFile()

    def _save_config(self) -> None:
        """保存配置到 JSON 文件"""
        try:
            CONFIG_FILE.write_text(
                self._config.model_dump_json(indent=2),
                encoding="utf-8",
            )
        except Exception as e:
            logger.error(f"Failed to save LLM config: {e}")
            raise

    def reload_config(self) -> None:
        """重新加载配置"""
        self._config = self._load_config()

    # ---- 提供商管理 ----

    def list_providers(self) -> list[ProviderConfig]:
        """获取所有已配置的提供商"""
        return self._config.providers

    def get_provider(self, provider_id: str) -> Optional[ProviderConfig]:
        """按 ID 获取提供商"""
        for p in self._config.providers:
            if p.id == provider_id:
                return p
        return None

    def add_provider(self, request: AddProviderRequest) -> ProviderConfig:
        """添加新提供商"""
        preset = PROVIDER_PRESETS.get(request.type, {})

        config = ProviderConfig(
            name=request.name or preset.get("name", "Custom"),
            type=request.type,
            auth_type=preset.get("auth_type", "api_key"),
            api_key=request.api_key,
            base_url=request.base_url or preset.get("base_url", ""),
            models=request.models or preset.get("default_models", []),
            enabled=True,
        )

        self._config.providers.append(config)

        # 如果是第一个提供商，自动设为激活
        if self._config.active_model is None and config.models:
            self._config.active_model = ActiveModel(
                provider_id=config.id,
                model_name=config.models[0],
            )

        self._save_config()
        return config

    def update_provider(self, provider_id: str, request: UpdateProviderRequest) -> Optional[ProviderConfig]:
        """更新提供商配置"""
        provider = self.get_provider(provider_id)
        if not provider:
            return None

        if request.name is not None:
            provider.name = request.name
        if request.api_key is not None:
            provider.api_key = request.api_key
        if request.base_url is not None:
            provider.base_url = request.base_url
        if request.models is not None:
            provider.models = request.models
        if request.enabled is not None:
            provider.enabled = request.enabled

        self._save_config()
        return provider

    def remove_provider(self, provider_id: str) -> bool:
        """删除提供商"""
        provider = self.get_provider(provider_id)
        if not provider:
            return False

        self._config.providers = [
            p for p in self._config.providers if p.id != provider_id
        ]

        # 如果删除的是当前激活的提供商，清除激活状态
        if (
            self._config.active_model
            and self._config.active_model.provider_id == provider_id
        ):
            # 尝试切换到下一个可用的提供商
            for p in self._config.providers:
                if p.enabled and p.models:
                    self._config.active_model = ActiveModel(
                        provider_id=p.id, model_name=p.models[0]
                    )
                    break
            else:
                self._config.active_model = None

        self._save_config()
        return True

    def add_google_oauth_provider(
        self, tokens: dict, user_info: dict, gcp_project_id: str = ""
    ) -> ProviderConfig:
        """通过 OAuth 授权添加 Google Vertex AI 提供商"""
        preset = PROVIDER_PRESETS[ProviderType.GOOGLE_VERTEX]

        # 检查是否已存在 Google Vertex 提供商
        for p in self._config.providers:
            if p.type == ProviderType.GOOGLE_VERTEX:
                # 更新现有的 tokens
                p.oauth_tokens = OAuthTokens(
                    access_token=tokens.get("access_token", ""),
                    refresh_token=tokens.get("refresh_token", p.oauth_tokens.refresh_token if p.oauth_tokens else ""),
                    token_expiry=self._calc_expiry(tokens.get("expires_in", 3600)),
                    id_token=tokens.get("id_token", ""),
                )
                p.user_email = user_info.get("email", p.user_email)
                p.user_avatar = user_info.get("picture", p.user_avatar)
                if gcp_project_id:
                    p.gcp_project_id = gcp_project_id
                p.enabled = True
                self._save_config()
                return p

        # 新建
        config = ProviderConfig(
            name=preset["name"],
            type=ProviderType.GOOGLE_VERTEX,
            auth_type=AuthType.OAUTH,
            models=preset["default_models"],
            enabled=True,
            oauth_tokens=OAuthTokens(
                access_token=tokens.get("access_token", ""),
                refresh_token=tokens.get("refresh_token", ""),
                token_expiry=self._calc_expiry(tokens.get("expires_in", 3600)),
                id_token=tokens.get("id_token", ""),
            ),
            user_email=user_info.get("email", ""),
            user_avatar=user_info.get("picture", ""),
            gcp_project_id=gcp_project_id,
        )

        self._config.providers.append(config)

        # 自动设为激活
        if config.models:
            self._config.active_model = ActiveModel(
                provider_id=config.id,
                model_name=config.models[0],
            )

        self._save_config()
        return config

    @staticmethod
    def _calc_expiry(expires_in: int) -> str:
        """计算 token 过期时间"""
        from datetime import timedelta
        expiry = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        return expiry.isoformat()

    def _ensure_oauth_token_fresh(self, provider: ProviderConfig) -> bool:
        """检查并刷新 OAuth token"""
        if not provider.oauth_tokens or not provider.oauth_tokens.refresh_token:
            return False

        # 检查是否过期
        if provider.oauth_tokens.token_expiry:
            try:
                expiry = datetime.fromisoformat(provider.oauth_tokens.token_expiry)
                now = datetime.now(timezone.utc)
                if now < expiry:
                    return True  # 还未过期
            except (ValueError, TypeError):
                pass

        # 刷新 token
        try:
            from app.services.google_oauth import GoogleOAuthService
            new_tokens = GoogleOAuthService.refresh_access_token(
                provider.oauth_tokens.refresh_token
            )
            provider.oauth_tokens.access_token = new_tokens["access_token"]
            provider.oauth_tokens.token_expiry = self._calc_expiry(
                new_tokens.get("expires_in", 3600)
            )
            self._save_config()
            logger.info(f"Refreshed OAuth token for {provider.name}")
            return True
        except Exception as e:
            logger.error(f"Failed to refresh OAuth token: {e}")
            return False

    # ---- 模型切换 ----

    def get_active_model(self) -> Optional[ActiveModel]:
        """获取当前激活的模型"""
        return self._config.active_model

    def set_active_model(self, provider_id: str, model_name: str) -> ActiveModel:
        """设置激活模型"""
        provider = self.get_provider(provider_id)
        if not provider:
            raise ValueError(f"Provider {provider_id} not found")
        if not provider.enabled:
            raise ValueError(f"Provider {provider.name} is disabled")

        self._config.active_model = ActiveModel(
            provider_id=provider_id,
            model_name=model_name,
        )
        self._save_config()
        return self._config.active_model

    # ---- 连接测试 ----

    async def test_connection(self, provider_id: str) -> dict:
        """测试提供商连接"""
        provider = self.get_provider(provider_id)
        if not provider:
            return {"success": False, "message": "Provider not found"}

        try:
            client = OpenAI(
                api_key=provider.api_key,
                base_url=provider.base_url or None,
                timeout=10,
            )
            test_model = provider.models[0] if provider.models else "gpt-3.5-turbo"

            response = client.chat.completions.create(
                model=test_model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=5,
            )

            return {
                "success": True,
                "message": f"Connected to {provider.name} successfully. Model: {test_model}",
                "model_used": test_model,
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"Connection failed: {str(e)}",
            }

    # ---- 获取客户端 ----

    def get_client(self) -> Tuple[Optional[OpenAI], Optional[str]]:
        """
        获取当前激活模型的 OpenAI 客户端
        返回 (client, model_name) 元组
        """
        active = self._config.active_model
        if not active:
            # 回退到环境变量
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
                return OpenAI(api_key=api_key, base_url=base_url), "gpt-3.5-turbo"
            return None, None

        provider = self.get_provider(active.provider_id)
        if not provider:
            return None, None

        # OAuth 提供商 (Google Vertex AI)
        if provider.auth_type == AuthType.OAUTH:
            return self._get_vertex_client(provider, active.model_name)

        # API Key 提供商
        if not provider.api_key:
            return None, None

        client = OpenAI(
            api_key=provider.api_key,
            base_url=provider.base_url or None,
        )
        return client, active.model_name

    def _get_vertex_client(
        self, provider: ProviderConfig, model_name: str
    ) -> Tuple[Optional[OpenAI], Optional[str]]:
        """
        为 Vertex AI 创建 OpenAI 兼容客户端
        Vertex AI 提供 OpenAI 兼容端点
        """
        if not self._ensure_oauth_token_fresh(provider):
            logger.error("OAuth token expired and refresh failed")
            return None, None

        access_token = provider.oauth_tokens.access_token
        project_id = provider.gcp_project_id or os.getenv("GCP_PROJECT_ID", "")
        location = provider.gcp_location or "us-central1"

        if not project_id:
            logger.error("GCP project ID not configured")
            return None, None

        # Vertex AI OpenAI-compatible endpoint
        base_url = (
            f"https://{location}-aiplatform.googleapis.com/v1beta1/"
            f"projects/{project_id}/locations/{location}/endpoints/openapi"
        )

        client = OpenAI(
            api_key=access_token,  # OAuth token 作为 API key
            base_url=base_url,
        )
        return client, model_name

    # ---- 提供商预设 ----

    @staticmethod
    def get_presets() -> dict:
        """获取所有提供商预设配置"""
        return {
            k.value: v for k, v in PROVIDER_PRESETS.items()
        }
