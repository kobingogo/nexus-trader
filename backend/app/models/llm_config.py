"""
LLM 配置数据模型
定义提供商类型、认证方式、配置结构等
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
import uuid


class ProviderType(str, Enum):
    """支持的 LLM 提供商类型"""
    GOOGLE = "google"
    GOOGLE_VERTEX = "google_vertex"
    NVIDIA = "nvidia"
    DEEPSEEK = "deepseek"
    OPENAI = "openai"
    CUSTOM = "custom"


class AuthType(str, Enum):
    """认证方式"""
    API_KEY = "api_key"
    OAUTH = "oauth"


# --- 提供商预设配置 ---

PROVIDER_PRESETS = {
    ProviderType.GOOGLE: {
        "name": "Google Gemini",
        "auth_type": AuthType.API_KEY,
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai/",
        "default_models": [
            "gemini-2.0-flash",
            "gemini-2.0-flash-lite",
            "gemini-1.5-pro",
            "gemini-1.5-flash",
        ],
    },
    ProviderType.GOOGLE_VERTEX: {
        "name": "Google Cloud (OAuth)",
        "auth_type": AuthType.OAUTH,
        "base_url": "",  # 通过 Vertex AI SDK 访问
        "default_models": [
            "gemini-3-pro",
            "gemini-2.0-flash",
            "claude-opus-4-6-think",
            "claude-sonnet-4",
        ],
    },
    ProviderType.NVIDIA: {
        "name": "Nvidia Build",
        "auth_type": AuthType.API_KEY,
        "base_url": "https://integrate.api.nvidia.com/v1",
        "default_models": [
            "moonshotai/kimi-k2.5",
            "deepseek-ai/deepseek-r1",
            "deepseek-ai/deepseek-v3.2",
            "qwen/qwen3-next",
            "z-ai/glm4.7",
            "nvidia/nemotron-3-nano-30b-a3b",
            "meta/llama-3.1-405b-instruct",
            "mistralai/devstral-2-123b-instruct-2512",
        ],
    },
    ProviderType.DEEPSEEK: {
        "name": "DeepSeek",
        "auth_type": AuthType.API_KEY,
        "base_url": "https://api.deepseek.com",
        "default_models": [
            "deepseek-chat",
            "deepseek-reasoner",
        ],
    },
    ProviderType.OPENAI: {
        "name": "OpenAI",
        "auth_type": AuthType.API_KEY,
        "base_url": "https://api.openai.com/v1",
        "default_models": [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4-turbo",
            "gpt-3.5-turbo",
        ],
    },
    ProviderType.CUSTOM: {
        "name": "Custom (OpenAI Compatible)",
        "auth_type": AuthType.API_KEY,
        "base_url": "",
        "default_models": [],
    },
}


# --- Pydantic Models ---

class OAuthTokens(BaseModel):
    """OAuth2 token 存储"""
    access_token: str = ""
    refresh_token: str = ""
    token_expiry: Optional[str] = None  # ISO format
    id_token: Optional[str] = None


class ProviderConfig(BaseModel):
    """单个提供商的完整配置"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str
    type: ProviderType
    auth_type: AuthType = AuthType.API_KEY
    api_key: str = ""
    base_url: str = ""
    models: list[str] = Field(default_factory=list)
    enabled: bool = True
    # OAuth 相关字段
    oauth_tokens: Optional[OAuthTokens] = None
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None
    gcp_project_id: Optional[str] = None
    gcp_location: str = "us-central1"

    def get_masked_key(self) -> str:
        """返回掩码后的 API Key"""
        if self.auth_type == AuthType.OAUTH:
            return f"OAuth ({self.user_email or 'connected'})"
        if not self.api_key or len(self.api_key) < 8:
            return "***"
        return f"{self.api_key[:4]}...{self.api_key[-4:]}"


class ActiveModel(BaseModel):
    """当前激活的模型"""
    provider_id: str
    model_name: str


class LLMConfigFile(BaseModel):
    """完整的 LLM 配置文件结构"""
    providers: list[ProviderConfig] = Field(default_factory=list)
    active_model: Optional[ActiveModel] = None


# --- API Request / Response Models ---

class AddProviderRequest(BaseModel):
    """添加提供商请求"""
    name: str
    type: ProviderType
    api_key: str = ""  # OAuth 类型可为空
    base_url: Optional[str] = None
    models: Optional[list[str]] = None


class UpdateProviderRequest(BaseModel):
    """更新提供商请求"""
    name: Optional[str] = None
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    models: Optional[list[str]] = None
    enabled: Optional[bool] = None


class SetActiveModelRequest(BaseModel):
    """设置激活模型请求"""
    provider_id: str
    model_name: str


class ProviderResponse(BaseModel):
    """提供商响应 (掩码 API Key)"""
    id: str
    name: str
    type: ProviderType
    auth_type: AuthType
    api_key_masked: str
    base_url: str
    models: list[str]
    enabled: bool
    user_email: Optional[str] = None
    user_avatar: Optional[str] = None

    @classmethod
    def from_config(cls, config: ProviderConfig) -> "ProviderResponse":
        return cls(
            id=config.id,
            name=config.name,
            type=config.type,
            auth_type=config.auth_type,
            api_key_masked=config.get_masked_key(),
            base_url=config.base_url,
            models=config.models,
            enabled=config.enabled,
            user_email=config.user_email,
            user_avatar=config.user_avatar,
        )
