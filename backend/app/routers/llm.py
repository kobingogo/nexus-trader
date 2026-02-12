"""
LLM 管理路由
提供 LLM 提供商的 CRUD、模型切换、连接测试等 API
"""

import logging
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.models.llm_config import (
    AddProviderRequest,
    UpdateProviderRequest,
    SetActiveModelRequest,
    ProviderResponse,
    PROVIDER_PRESETS,
    ProviderType,
)
from app.services.llm_provider import LLMProviderManager
from app.services.google_oauth import GoogleOAuthService

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/providers")
async def list_providers():
    """获取所有已配置的提供商"""
    manager = LLMProviderManager()
    providers = manager.list_providers()
    return {
        "providers": [ProviderResponse.from_config(p) for p in providers],
    }


@router.post("/providers")
async def add_provider(request: AddProviderRequest):
    """添加新提供商"""
    manager = LLMProviderManager()
    config = manager.add_provider(request)
    active = manager.get_active_model()
    return {
        "provider": ProviderResponse.from_config(config),
        "active_model": active.model_dump() if active else None,
    }


@router.put("/providers/{provider_id}")
async def update_provider(provider_id: str, request: UpdateProviderRequest):
    """更新提供商配置"""
    manager = LLMProviderManager()
    config = manager.update_provider(provider_id, request)
    if not config:
        raise HTTPException(status_code=404, detail="Provider not found")
    return {"provider": ProviderResponse.from_config(config)}


@router.delete("/providers/{provider_id}")
async def remove_provider(provider_id: str):
    """删除提供商"""
    manager = LLMProviderManager()
    success = manager.remove_provider(provider_id)
    if not success:
        raise HTTPException(status_code=404, detail="Provider not found")
    active = manager.get_active_model()
    return {
        "success": True,
        "active_model": active.model_dump() if active else None,
    }


@router.post("/providers/{provider_id}/test")
async def test_provider(provider_id: str):
    """测试提供商连接"""
    manager = LLMProviderManager()
    result = await manager.test_connection(provider_id)
    return result


@router.get("/active")
async def get_active_model():
    """获取当前激活的模型"""
    manager = LLMProviderManager()
    active = manager.get_active_model()
    if not active:
        return {"active_model": None, "provider": None}

    provider = manager.get_provider(active.provider_id)
    return {
        "active_model": active.model_dump(),
        "provider": ProviderResponse.from_config(provider) if provider else None,
    }


@router.put("/active")
async def set_active_model(request: SetActiveModelRequest):
    """切换激活模型"""
    manager = LLMProviderManager()
    try:
        active = manager.set_active_model(request.provider_id, request.model_name)
        provider = manager.get_provider(active.provider_id)
        return {
            "active_model": active.model_dump(),
            "provider": ProviderResponse.from_config(provider) if provider else None,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/presets")
async def get_presets():
    """获取提供商预设配置"""
    presets = {}
    for key, value in PROVIDER_PRESETS.items():
        presets[key.value] = {
            "name": value["name"],
            "auth_type": value["auth_type"].value if hasattr(value["auth_type"], "value") else value["auth_type"],
            "base_url": value["base_url"],
            "default_models": value["default_models"],
        }
    return {"presets": presets}


# ---- Google OAuth2 ----

@router.get("/google/auth-url")
async def get_google_auth_url():
    """获取 Google OAuth 授权 URL"""
    try:
        url = GoogleOAuthService.get_auth_url(state="nexus_trader")
        return {"auth_url": url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/google/callback")
async def google_oauth_callback(
    code: str = Query(...),
    state: str = Query(default=""),
):
    """
    Google OAuth 回调
    交换 code 获取 tokens，创建/更新提供商，重定向回前端
    """
    try:
        # 1. 用 code 换取 tokens
        tokens = GoogleOAuthService.exchange_code(code)

        # 2. 获取用户信息
        user_info = GoogleOAuthService.get_user_info(tokens["access_token"])

        # 3. 添加/更新 Google Vertex 提供商
        manager = LLMProviderManager()
        provider = manager.add_google_oauth_provider(
            tokens=tokens,
            user_info=user_info,
        )

        logger.info(f"Google OAuth completed for {user_info.get('email', 'unknown')}")

        # 4. 重定向回前端
        frontend_url = GoogleOAuthService.get_frontend_url()
        return RedirectResponse(
            url=f"{frontend_url}?google_auth=success&email={user_info.get('email', '')}",
            status_code=302,
        )

    except Exception as e:
        logger.error(f"Google OAuth callback error: {e}")
        frontend_url = GoogleOAuthService.get_frontend_url()
        return RedirectResponse(
            url=f"{frontend_url}?google_auth=error&message={str(e)}",
            status_code=302,
        )


@router.post("/google/logout")
async def google_logout():
    """断开 Google 连接，删除 Google Vertex 提供商"""
    manager = LLMProviderManager()
    providers = manager.list_providers()

    for p in providers:
        if p.type == ProviderType.GOOGLE_VERTEX:
            manager.remove_provider(p.id)
            return {"success": True, "message": "Google account disconnected"}

    return {"success": False, "message": "No Google account connected"}

