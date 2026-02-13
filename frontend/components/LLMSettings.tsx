"use client";

import { useEffect, useState, useCallback } from "react";
import {
  llmApi,
  type Provider,
  type ActiveModel,
  type ProviderPreset,
} from "@/lib/llm-api";
import {
  Bot,
  Plus,
  X,
  Loader2,
  CheckCircle2,
  XCircle,
  Trash2,
  Zap,
  Plug,
  Settings2,
  LogOut,
} from "lucide-react";

// --- Provider branding ---

const PROVIDER_COLORS: Record<string, { bg: string; text: string; border: string; icon: string }> = {
  google:        { bg: "bg-blue-500/10",   text: "text-blue-400",   border: "border-blue-500/30",   icon: "🔵" },
  google_vertex: { bg: "bg-indigo-500/10", text: "text-indigo-400", border: "border-indigo-500/30", icon: "☁️" },
  nvidia:        { bg: "bg-green-500/10",  text: "text-green-400",  border: "border-green-500/30",  icon: "🟢" },
  deepseek:      { bg: "bg-cyan-500/10",   text: "text-cyan-400",   border: "border-cyan-500/30",   icon: "🔷" },
  openai:        { bg: "bg-emerald-500/10", text: "text-emerald-400", border: "border-emerald-500/30", icon: "⬛" },
  custom:        { bg: "bg-purple-500/10", text: "text-purple-400", border: "border-purple-500/30", icon: "🔮" },
};

const getColor = (type: string) => PROVIDER_COLORS[type] ?? PROVIDER_COLORS.custom;

interface Props {
  open: boolean;
  onClose: () => void;
  onModelChange?: (model: ActiveModel | null) => void;
}

export function LLMSettings({ open, onClose, onModelChange }: Props) {
  // State
  const [providers, setProviders] = useState<Provider[]>([]);
  const [activeModel, setActiveModel] = useState<ActiveModel | null>(null);
  const [presets, setPresets] = useState<Record<string, ProviderPreset>>({});
  const [loading, setLoading] = useState(true);

  // Add provider form
  const [showAddForm, setShowAddForm] = useState(false);
  const [addType, setAddType] = useState<string>("");
  const [addApiKey, setAddApiKey] = useState("");
  const [addName, setAddName] = useState("");
  const [addBaseUrl, setAddBaseUrl] = useState("");
  const [addModels, setAddModels] = useState("");
  const [adding, setAdding] = useState(false);

  // Test connection
  const [testingId, setTestingId] = useState<string | null>(null);
  const [testResult, setTestResult] = useState<{ id: string; success: boolean; message: string } | null>(null);
  const [googleLoading, setGoogleLoading] = useState(false);

  // --- Check for OAuth callback on mount ---

  useEffect(() => {
    if (typeof window === "undefined") return;
    const params = new URLSearchParams(window.location.search);
    const googleAuth = params.get("google_auth");
    if (googleAuth === "success") {
      // OAuth completed, clean URL and open panel to show result
      window.history.replaceState({}, "", window.location.pathname);
    }
  }, []);

  // --- Data loading ---

  const loadData = useCallback(async () => {
    try {
      const [providersRes, activeRes, presetsRes] = await Promise.all([
        llmApi.listProviders(),
        llmApi.getActiveModel(),
        llmApi.getPresets(),
      ]);
      setProviders(providersRes.providers);
      setActiveModel(activeRes.active_model);
      setPresets(presetsRes.presets);
    } catch (e) {
      console.error("Failed to load LLM config", e);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (open) {
      setLoading(true);
      loadData();
    }
  }, [open, loadData]);

  // --- Add provider ---

  const handleSelectType = (type: string) => {
    // Google Vertex 使用 OAuth 登录，不走 API Key 表单
    if (type === "google_vertex") {
      handleGoogleLogin();
      return;
    }
    setAddType(type);
    const preset = presets[type];
    if (preset) {
      setAddName(preset.name);
      setAddBaseUrl(preset.base_url);
      setAddModels(preset.default_models.join(", "));
    } else {
      setAddName("");
      setAddBaseUrl("");
      setAddModels("");
    }
  };

  // --- Google OAuth ---

  const handleGoogleLogin = async () => {
    setGoogleLoading(true);
    try {
      const { auth_url } = await llmApi.getGoogleAuthUrl();
      // 直接跳转（回调会重定向回前端）
      window.location.href = auth_url;
    } catch (e) {
      console.error("Failed to get Google auth URL", e);
      setGoogleLoading(false);
    }
  };

  const handleGoogleLogout = async (providerId: string) => {
    try {
      await llmApi.googleLogout();
      setProviders((prev) => prev.filter((p) => p.id !== providerId));
      const activeRes = await llmApi.getActiveModel();
      setActiveModel(activeRes.active_model);
      onModelChange?.(activeRes.active_model);
    } catch (e) {
      console.error("Failed to disconnect Google", e);
    }
  };

  const handleAdd = async () => {
    if (!addType || !addApiKey.trim()) return;
    setAdding(true);
    try {
      const models = addModels
        .split(",")
        .map((m) => m.trim())
        .filter(Boolean);
      const res = await llmApi.addProvider({
        name: addName || presets[addType]?.name || addType,
        type: addType,
        api_key: addApiKey.trim(),
        base_url: addBaseUrl || undefined,
        models: models.length > 0 ? models : undefined,
      });
      setProviders((prev) => [...prev, res.provider]);
      if (res.active_model) {
        setActiveModel(res.active_model);
        onModelChange?.(res.active_model);
      }
      resetAddForm();
    } catch (e) {
      console.error("Failed to add provider", e);
    } finally {
      setAdding(false);
    }
  };

  const resetAddForm = () => {
    setShowAddForm(false);
    setAddType("");
    setAddApiKey("");
    setAddName("");
    setAddBaseUrl("");
    setAddModels("");
  };

  // --- Remove provider ---

  const handleRemove = async (id: string) => {
    try {
      const res = await llmApi.removeProvider(id);
      setProviders((prev) => prev.filter((p) => p.id !== id));
      setActiveModel(res.active_model);
      onModelChange?.(res.active_model);
    } catch (e) {
      console.error("Failed to remove provider", e);
    }
  };

  // --- Test connection ---

  const handleTest = async (id: string) => {
    setTestingId(id);
    setTestResult(null);
    try {
      const res = await llmApi.testConnection(id);
      setTestResult({ id, ...res });
    } catch {
      setTestResult({ id, success: false, message: "Request failed" });
    } finally {
      setTestingId(null);
    }
  };

  // --- Switch model ---

  const handleSwitchModel = async (providerId: string, modelName: string) => {
    try {
      const res = await llmApi.setActiveModel(providerId, modelName);
      setActiveModel(res.active_model);
      onModelChange?.(res.active_model);
    } catch (e) {
      console.error("Failed to switch model", e);
    }
  };

  if (!open) return null;

  const activeProvider = providers.find((p) => p.id === activeModel?.provider_id);

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-full max-w-lg bg-neutral-900 border-l border-neutral-800 z-50 flex flex-col shadow-2xl animate-slide-in">
        {/* Header */}
        <div className="flex items-center justify-between p-5 border-b border-neutral-800">
          <div className="flex items-center gap-2">
            <Bot className="w-5 h-5 text-purple-400" />
            <h2 className="text-lg font-semibold text-gray-100">AI 模型管理</h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-neutral-800 transition-colors"
          >
            <X className="w-5 h-5 text-gray-400" />
          </button>
        </div>

        {/* Active Model Banner */}
        {activeModel && activeProvider && (
          <div className="mx-4 mt-4 p-3 rounded-xl bg-linear-to-r from-purple-500/10 via-blue-500/10 to-cyan-500/10 border border-purple-500/20">
            <div className="flex items-center gap-2">
              <Zap className="w-4 h-4 text-purple-400" />
              <span className="text-xs text-gray-400 uppercase tracking-wider">当前模型</span>
            </div>
            <div className="mt-1.5 flex items-center gap-2">
              <span className="text-sm font-medium text-gray-200">
                {activeProvider.name}
              </span>
              <span className="text-gray-600">/</span>
              <span className="text-sm font-mono text-purple-300">
                {activeModel.model_name}
              </span>
            </div>
          </div>
        )}

        {!activeModel && !loading && (
          <div className="mx-4 mt-4 p-3 rounded-xl bg-yellow-500/5 border border-yellow-500/20">
            <div className="flex items-center gap-2">
              <Settings2 className="w-4 h-4 text-yellow-500" />
              <span className="text-sm text-yellow-400">
                尚未配置任何模型，请添加提供商
              </span>
            </div>
          </div>
        )}

        {/* Provider List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {loading ? (
            <div className="flex items-center justify-center py-16">
              <Loader2 className="w-6 h-6 text-gray-600 animate-spin" />
            </div>
          ) : (
            <>
              {providers.map((provider) => {
                const color = getColor(provider.type);
                const isActive = activeModel?.provider_id === provider.id;

                return (
                  <div
                    key={provider.id}
                    className={`rounded-xl border transition-all ${
                      isActive
                        ? `${color.border} ${color.bg}`
                        : "border-neutral-800 bg-neutral-800/30 hover:border-neutral-700"
                    }`}
                  >
                    {/* Provider Header */}
                    <div className="flex items-center justify-between p-4">
                      <div className="flex items-center gap-3">
                        <span className="text-lg">{color.icon}</span>
                        <div>
                          <div className="flex items-center gap-2">
                            <span className="text-sm font-medium text-gray-200">
                              {provider.name}
                            </span>
                            {isActive && (
                              <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-purple-500/20 text-purple-400 border border-purple-500/30 font-medium">
                                ACTIVE
                              </span>
                            )}
                          </div>
                          <div className="flex items-center gap-2 mt-0.5">
                            {provider.user_email ? (
                              <span className="text-xs text-gray-500">
                                {provider.user_email}
                              </span>
                            ) : (
                              <span className="text-xs text-gray-500 font-mono">
                                {provider.api_key_masked}
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <div className="flex items-center gap-1">
                        {/* Google logout */}
                        {provider.type === "google_vertex" ? (
                          <button
                            onClick={() => handleGoogleLogout(provider.id)}
                            className="p-1.5 rounded-md text-gray-500 hover:text-orange-400 hover:bg-orange-500/10 transition-all"
                            title="断开 Google 连接"
                          >
                            <LogOut className="w-3.5 h-3.5" />
                          </button>
                        ) : (
                          <>
                            {/* Test */}
                            <button
                              onClick={() => handleTest(provider.id)}
                              disabled={testingId === provider.id}
                              className="p-1.5 rounded-md text-gray-500 hover:text-cyan-400 hover:bg-cyan-500/10 transition-all disabled:opacity-40"
                              title="测试连接"
                            >
                              {testingId === provider.id ? (
                                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <Plug className="w-3.5 h-3.5" />
                              )}
                            </button>
                            {/* Remove */}
                            <button
                              onClick={() => handleRemove(provider.id)}
                              className="p-1.5 rounded-md text-gray-500 hover:text-red-400 hover:bg-red-500/10 transition-all"
                              title="删除"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </>
                        )}
                      </div>
                    </div>

                    {/* Test Result */}
                    {testResult && testResult.id === provider.id && (
                      <div
                        className={`mx-4 mb-3 px-3 py-2 rounded-lg text-xs flex items-center gap-2 ${
                          testResult.success
                            ? "bg-green-500/10 text-green-400 border border-green-500/20"
                            : "bg-red-500/10 text-red-400 border border-red-500/20"
                        }`}
                      >
                        {testResult.success ? (
                          <CheckCircle2 className="w-3.5 h-3.5 shrink-0" />
                        ) : (
                          <XCircle className="w-3.5 h-3.5 shrink-0" />
                        )}
                        <span className="truncate">{testResult.message}</span>
                      </div>
                    )}

                    {/* Model List */}
                    <div className="px-4 pb-3">
                      <div className="flex flex-wrap gap-1.5">
                        {provider.models.map((model) => {
                          const isModelActive =
                            isActive && activeModel?.model_name === model;
                          return (
                            <button
                              key={model}
                              onClick={() =>
                                handleSwitchModel(provider.id, model)
                              }
                              className={`text-xs px-2.5 py-1 rounded-lg border transition-all font-mono ${
                                isModelActive
                                  ? "bg-purple-500/20 text-purple-300 border-purple-500/40"
                                  : "bg-neutral-800/80 text-gray-400 border-neutral-700 hover:border-neutral-600 hover:text-gray-300"
                              }`}
                            >
                              {isModelActive && (
                                <CheckCircle2 className="w-3 h-3 inline mr-1 -mt-px" />
                              )}
                              {model}
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  </div>
                );
              })}

              {/* Add Provider */}
              {!showAddForm ? (
                <button
                  onClick={() => setShowAddForm(true)}
                  className="w-full p-4 rounded-xl border-2 border-dashed border-neutral-800 hover:border-purple-500/30 text-gray-500 hover:text-purple-400 transition-all flex items-center justify-center gap-2 group"
                >
                  <Plus className="w-4 h-4 group-hover:scale-110 transition-transform" />
                  <span className="text-sm">添加提供商</span>
                </button>
              ) : (
                <div className="rounded-xl border border-purple-500/30 bg-purple-500/5 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium text-gray-200">
                      添加提供商
                    </span>
                    <button
                      onClick={resetAddForm}
                      className="p-1 rounded-md hover:bg-neutral-800 text-gray-400"
                    >
                      <X className="w-4 h-4" />
                    </button>
                  </div>

                  {/* Step 1: Select type */}
                  {!addType ? (
                    <div className="grid grid-cols-2 gap-2">
                      {Object.entries(presets).map(([type, preset]) => {
                        const color = getColor(type);
                        return (
                          <button
                            key={type}
                            onClick={() => handleSelectType(type)}
                            disabled={type === "google_vertex" && googleLoading}
                            className={`p-3 rounded-lg border ${color.border} ${color.bg} hover:opacity-80 transition-all text-left disabled:opacity-50`}
                          >
                            <span className="text-lg">{color.icon}</span>
                            <div className="text-sm font-medium text-gray-200 mt-1">
                              {preset.name}
                            </div>
                            <div className="text-[10px] text-gray-500 mt-0.5">
                              {type === "google_vertex" ? (
                                googleLoading ? (
                                  <span className="flex items-center gap-1">
                                    <Loader2 className="w-3 h-3 animate-spin" />
                                    跳转中...
                                  </span>
                                ) : (
                                  "Sign in with Google"
                                )
                              ) : (
                                preset.default_models[0] || "Custom"
                              )}
                            </div>
                          </button>
                        );
                      })}
                    </div>
                  ) : (
                    /* Step 2: Fill details */
                    <div className="space-y-3">
                      <div className="flex items-center gap-2">
                        <span className="text-lg">
                          {getColor(addType).icon}
                        </span>
                        <span className="text-sm font-medium text-gray-200">
                          {addName}
                        </span>
                        <button
                          onClick={() => setAddType("")}
                          className="text-xs text-gray-500 hover:text-gray-400 ml-auto"
                        >
                          切换
                        </button>
                      </div>

                      {/* API Key */}
                      <div>
                        <label className="text-xs text-gray-500 block mb-1">
                          API Key
                        </label>
                        <input
                          type="password"
                          value={addApiKey}
                          onChange={(e) => setAddApiKey(e.target.value)}
                          placeholder="sk-..."
                          className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-purple-500/50 font-mono"
                        />
                      </div>

                      {/* Base URL (custom only) */}
                      {addType === "custom" && (
                        <div>
                          <label className="text-xs text-gray-500 block mb-1">
                            Base URL
                          </label>
                          <input
                            type="text"
                            value={addBaseUrl}
                            onChange={(e) => setAddBaseUrl(e.target.value)}
                            placeholder="https://api.example.com/v1"
                            className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-purple-500/50 font-mono"
                          />
                        </div>
                      )}

                      {/* Models (custom only) */}
                      {addType === "custom" && (
                        <div>
                          <label className="text-xs text-gray-500 block mb-1">
                            模型名称 (逗号分隔)
                          </label>
                          <input
                            type="text"
                            value={addModels}
                            onChange={(e) => setAddModels(e.target.value)}
                            placeholder="model-name-1, model-name-2"
                            className="w-full px-3 py-2 bg-neutral-800 border border-neutral-700 rounded-lg text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-purple-500/50 font-mono"
                          />
                        </div>
                      )}

                      {/* Submit */}
                      <button
                        onClick={handleAdd}
                        disabled={adding || !addApiKey.trim()}
                        className="w-full py-2.5 rounded-lg bg-purple-600 hover:bg-purple-500 text-white text-sm font-medium transition-colors disabled:opacity-40 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                      >
                        {adding ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <Plus className="w-4 h-4" />
                        )}
                        添加 {addName}
                      </button>
                    </div>
                  )}
                </div>
              )}
            </>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-neutral-800">
          <p className="text-[10px] text-gray-600 text-center">
            所有 API Key 仅保存在本地 · 支持 OpenAI 兼容协议
          </p>
        </div>
      </div>

      <style jsx>{`
        @keyframes slide-in {
          from {
            transform: translateX(100%);
          }
          to {
            transform: translateX(0);
          }
        }
        .animate-slide-in {
          animation: slide-in 0.3s ease-out;
        }
      `}</style>
    </>
  );
}
