"""Initial seed data — run once after migrations."""
import os
from app.storage.db import get_conn
from app.models.provider import Provider
from app.models.credential import Credential
from app.models.model import Model, ModelCapability
from app.models.prompt_template import PromptTemplate
from app.storage.repositories.provider_repo import ProviderRepository
from app.storage.repositories.credential_repo import CredentialRepository
from app.storage.repositories.model_repo import ModelRepository
from app.storage.repositories.prompt_template_repo import PromptTemplateRepository


_PROVIDERS = [
    Provider(name="Mock", slug="mock", active=True, base_url="", auth_type="custom",
             notes="Sandbox provider — no real API calls"),
    Provider(name="OpenAI", slug="openai", active=True,
             base_url="https://api.openai.com/v1", auth_type="api_key",
             endpoints={"text": "/chat/completions", "image": "/images/generations", "audio": "/audio"}),
    Provider(name="Anthropic", slug="anthropic", active=True,
             base_url="https://api.anthropic.com", auth_type="api_key",
             endpoints={"text": "/v1/messages"},
             notes="Auth header: x-api-key (not Bearer)"),
    Provider(name="OpenRouter", slug="openrouter", active=True,
             base_url="https://openrouter.ai/api/v1", auth_type="api_key",
             endpoints={"text": "/chat/completions"}),
    Provider(name="Alibaba DashScope (International)", slug="alibaba", active=True,
             base_url="https://dashscope-intl.aliyuncs.com/compatible-mode/v1",
             auth_type="api_key",
             notes="OpenAI-compatible. CN: https://dashscope.aliyuncs.com/compatible-mode/v1"),
    Provider(name="MiniMax (Global)", slug="minimax", active=True,
             base_url="https://api.minimax.io/v1", auth_type="api_key",
             notes="GroupId required — store it in the 'Organisation ID' field of your credential"),
    Provider(name="MiniMax (CN)", slug="minimax_cn", active=False,
             base_url="https://api.minimax.chat/v1", auth_type="api_key",
             notes="China endpoint. GroupId required — store it in 'Organisation ID' of your credential"),
    Provider(name="Z.ai (GLM)", slug="zai", active=True,
             base_url="https://api.z.ai/api/paas/v4", auth_type="api_key",
             notes="[PARTIEL] — API key format: {API_Key_ID}.{secret}"),
]

_MODELS = {
    "openai": [
        {"technical_name": "gpt-4o", "display_name": "GPT-4o", "type": "text",
         "capabilities": ["chat", "vision", "tool_calling", "json_output", "streaming"]},
        {"technical_name": "gpt-4o-mini", "display_name": "GPT-4o Mini", "type": "text",
         "capabilities": ["chat", "vision", "tool_calling", "json_output", "streaming"]},
        {"technical_name": "gpt-4-turbo", "display_name": "GPT-4 Turbo", "type": "text",
         "capabilities": ["chat", "vision", "tool_calling", "json_output", "streaming"]},
        {"technical_name": "o1", "display_name": "o1 (reasoning)", "type": "text",
         "capabilities": ["chat", "reasoning", "vision"]},
        {"technical_name": "o3-mini", "display_name": "o3-mini (reasoning)", "type": "text",
         "capabilities": ["chat", "reasoning", "tool_calling", "json_output"]},
        {"technical_name": "dall-e-3", "display_name": "DALL·E 3", "type": "image",
         "capabilities": ["image_gen"]},
        {"technical_name": "whisper-1", "display_name": "Whisper v1", "type": "audio",
         "capabilities": ["transcription"]},
        {"technical_name": "tts-1", "display_name": "TTS-1", "type": "audio",
         "capabilities": ["speech"]},
    ],
    "anthropic": [
        {"technical_name": "claude-opus-4-7", "display_name": "Claude Opus 4.7", "type": "text",
         "capabilities": ["chat", "vision", "tool_calling", "json_output", "streaming", "reasoning"]},
        {"technical_name": "claude-sonnet-4-6", "display_name": "Claude Sonnet 4.6", "type": "text",
         "capabilities": ["chat", "vision", "tool_calling", "json_output", "streaming"]},
        {"technical_name": "claude-haiku-4-5-20251001", "display_name": "Claude Haiku 4.5", "type": "text",
         "capabilities": ["chat", "vision", "tool_calling", "json_output", "streaming"]},
    ],
    "alibaba": [
        {"technical_name": "qwen-max", "display_name": "Qwen Max", "type": "text",
         "capabilities": ["chat", "tool_calling", "json_output", "streaming"]},
        {"technical_name": "qwen-plus", "display_name": "Qwen Plus", "type": "text",
         "capabilities": ["chat", "tool_calling", "json_output", "streaming"]},
        {"technical_name": "qwen-turbo", "display_name": "Qwen Turbo", "type": "text",
         "capabilities": ["chat", "streaming"]},
        {"technical_name": "qwen-vl-plus", "display_name": "Qwen VL Plus (vision)", "type": "text",
         "capabilities": ["chat", "vision", "streaming"]},
        {"technical_name": "qwen-vl-max", "display_name": "Qwen VL Max (vision)", "type": "text",
         "capabilities": ["chat", "vision", "tool_calling", "streaming"]},
    ],
    "minimax": [
        {"technical_name": "minimax-m2.7", "display_name": "MiniMax M2.7", "type": "text",
         "capabilities": ["chat", "streaming", "tool_calling", "json_output", "vision"]},
        {"technical_name": "minimax-m2.5", "display_name": "MiniMax M2.5", "type": "text",
         "capabilities": ["chat", "streaming", "tool_calling", "json_output"]},
        {"technical_name": "minimax-m2.5-highspeed", "display_name": "MiniMax M2.5 High Speed", "type": "text",
         "capabilities": ["chat", "streaming"]},
        {"technical_name": "abab6.5s", "display_name": "abab6.5s (200k ctx)", "type": "text",
         "capabilities": ["chat", "streaming", "tool_calling"]},
        {"technical_name": "coding-plan-vlm", "display_name": "Coding Plan VLM", "type": "text",
         "capabilities": ["chat", "vision", "streaming", "tool_calling"]},
        {"technical_name": "coding-plan-search", "display_name": "Coding Plan Search", "type": "text",
         "capabilities": ["chat", "streaming"]},
        {"technical_name": "speech-02-hd", "display_name": "Text to Speech HD", "type": "audio",
         "capabilities": ["speech"]},
        {"technical_name": "music-2.6", "display_name": "Music 2.6", "type": "audio",
         "capabilities": ["speech"]},
        {"technical_name": "music-cover", "display_name": "Music Cover", "type": "audio",
         "capabilities": ["speech"]},
        {"technical_name": "lyrics_generation", "display_name": "Lyrics Generation", "type": "text",
         "capabilities": ["chat"]},
        {"technical_name": "image-01", "display_name": "Image-01", "type": "image",
         "capabilities": ["image_gen"]},
        {"technical_name": "video-01", "display_name": "Video-01", "type": "video",
         "capabilities": ["video_gen"]},
    ],
    "zai": [
        {"technical_name": "glm-4-plus", "display_name": "GLM-4 Plus", "type": "text",
         "capabilities": ["chat", "tool_calling", "json_output", "streaming"]},
        {"technical_name": "glm-4-air", "display_name": "GLM-4 Air", "type": "text",
         "capabilities": ["chat", "streaming"]},
        {"technical_name": "glm-4v-plus", "display_name": "GLM-4V Plus (vision)", "type": "text",
         "capabilities": ["chat", "vision", "streaming"]},
        {"technical_name": "cogvideox-2", "display_name": "CogVideoX-2 (vidéo)", "type": "video",
         "capabilities": ["video_gen"]},
    ],
    "openrouter": [
        {"technical_name": "openai/gpt-4o", "display_name": "GPT-4o (via OR)", "type": "text",
         "capabilities": ["chat", "vision", "tool_calling", "streaming"]},
        {"technical_name": "anthropic/claude-sonnet-4-6", "display_name": "Claude Sonnet 4.6 (via OR)", "type": "text",
         "capabilities": ["chat", "vision", "tool_calling", "streaming"]},
        {"technical_name": "google/gemini-2.0-flash-exp:free", "display_name": "Gemini 2.0 Flash (free)", "type": "text",
         "capabilities": ["chat", "vision", "streaming"]},
        {"technical_name": "meta-llama/llama-3.3-70b-instruct", "display_name": "Llama 3.3 70B", "type": "text",
         "capabilities": ["chat", "streaming", "tool_calling"]},
    ],
}

# Default credentials seeded from environment variables.
# Each entry: (provider_slug, credential_name, {field: env_var_name})
_DEFAULT_CREDENTIALS: list[tuple[str, str, dict]] = [
    ("openai",     "Default (env)",  {"api_key": "OPENAI_API_KEY", "org_id": "OPENAI_ORG_ID", "project_id": "OPENAI_PROJECT_ID"}),
    ("anthropic",  "Default (env)",  {"api_key": "ANTHROPIC_API_KEY"}),
    ("openrouter", "Default (env)",  {"api_key": "OPENROUTER_API_KEY"}),
    ("alibaba",    "Default (env)",  {"api_key": "DASHSCOPE_API_KEY"}),
    ("minimax",    "Default (env)",  {"api_key": "MINIMAX_API_KEY", "org_id": "MINIMAX_GROUP_ID"}),
    ("minimax_cn", "Default (env)",  {"api_key": "MINIMAX_API_KEY", "org_id": "MINIMAX_GROUP_ID"}),
    ("zai",        "Default (env)",  {"api_key": "ZAI_API_KEY"}),
]

_PROMPT_TEMPLATES = [
    ("Résumé", "Résume le texte suivant en 3 points clés :\n\n{texte}", "text", "general"),
    ("Extraction JSON", "Extrait les informations suivantes du texte sous forme JSON : {champs}\n\nTexte :\n{texte}", "text", "extraction"),
    ("Traduction FR→EN", "Translate the following French text to English:\n\n{texte}", "text", "translation"),
    ("Classification", "Classe le texte suivant dans une des catégories : {categories}\n\nTexte :\n{texte}", "text", "classification"),
    ("Génération image", "A photorealistic image of {description}, high quality, 4K", "image", "generation"),
    ("Transcription audio", "Transcribe the following audio file accurately.", "audio", "transcription"),
]


def seed(force: bool = False) -> None:
    conn = get_conn()
    p_repo = ProviderRepository(conn)
    c_repo = CredentialRepository(conn)
    m_repo = ModelRepository(conn)
    t_repo = PromptTemplateRepository(conn)

    existing = p_repo.list()
    if existing and not force:
        return

    provider_map: dict = {}
    for p_data in _PROVIDERS:
        existing_p = p_repo.get_by_slug(p_data.slug)
        p = existing_p if existing_p else p_repo.create(p_data)
        provider_map[p_data.slug] = p

    # Seed default credentials from environment variables (only if env var is set)
    for slug, cred_name, field_map in _DEFAULT_CREDENTIALS:
        prov = provider_map.get(slug)
        if not prov:
            continue
        values = {field: os.environ.get(env_var, "") for field, env_var in field_map.items()}
        if not any(values.values()):
            continue
        existing_creds = c_repo.list(provider_id=prov.id)
        if any(c.name == cred_name for c in existing_creds):
            continue
        c_repo.create(Credential(
            provider_id=prov.id,
            name=cred_name,
            active=True,
            validity="untested",
            **values,
        ))

    # Insert Mock models
    mock_provider = provider_map.get("mock")
    if mock_provider:
        mock_models = [
            Model(provider_id=mock_provider.id, technical_name="mock-text-v1",
                  display_name="Mock Text v1", type="text", active=True,
                  capabilities=[ModelCapability(capability=c) for c in ["chat", "streaming", "json_output"]]),
            Model(provider_id=mock_provider.id, technical_name="mock-image-v1",
                  display_name="Mock Image v1", type="image", active=True,
                  capabilities=[ModelCapability(capability="image_gen")]),
            Model(provider_id=mock_provider.id, technical_name="mock-audio-v1",
                  display_name="Mock Audio v1", type="audio", active=True,
                  capabilities=[ModelCapability(capability=c) for c in ["transcription", "speech"]]),
        ]
        for m in mock_models:
            m_repo.create(m)

    # Insert pre-seeded models for real providers
    for slug in ("openai", "anthropic", "alibaba", "minimax", "minimax_cn", "zai", "openrouter"):
        prov = provider_map.get(slug)
        if not prov:
            continue
        model_key = "minimax" if slug == "minimax_cn" else slug
        for m_data in _MODELS.get(model_key, []):
            caps = [ModelCapability(capability=c) for c in m_data.get("capabilities", [])]
            m_repo.create(Model(
                provider_id=prov.id,
                technical_name=m_data["technical_name"],
                display_name=m_data["display_name"],
                type=m_data.get("type", "text"),
                active=True,
                capabilities=caps,
            ))

    # Insert prompt templates
    for title, content, modality, category in _PROMPT_TEMPLATES:
        t_repo.create(PromptTemplate(title=title, content=content,
                                     modality=modality, category=category))
