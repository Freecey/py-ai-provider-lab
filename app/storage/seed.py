"""Initial seed data — run once after migrations."""
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
             base_url="https://api.anthropic.com/v1", auth_type="api_key",
             endpoints={"text": "/messages"}),
    Provider(name="OpenRouter", slug="openrouter", active=True,
             base_url="https://openrouter.ai/api/v1", auth_type="api_key",
             endpoints={"text": "/chat/completions"}),
    Provider(name="Alibaba (DashScope)", slug="alibaba", active=True,
             base_url="https://dashscope.aliyuncs.com/compatible-mode/v1", auth_type="api_key"),
    Provider(name="MiniMax", slug="minimax", active=True,
             base_url="https://api.minimax.chat/v1", auth_type="api_key"),
    Provider(name="Z.ai", slug="zai", active=True,
             base_url="https://api.z.ai/v1", auth_type="api_key",
             notes="[PARTIEL] — documentation en cours"),
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
    m_repo = ModelRepository(conn)
    t_repo = PromptTemplateRepository(conn)

    # Skip if already seeded
    existing = p_repo.list()
    if existing and not force:
        return

    # Insert providers
    provider_map = {}
    for p_data in _PROVIDERS:
        existing_p = p_repo.get_by_slug(p_data.slug)
        if not existing_p:
            p = p_repo.create(p_data)
        else:
            p = existing_p
        provider_map[p.slug] = p

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

    # Insert prompt templates
    for title, content, modality, category in _PROMPT_TEMPLATES:
        t_repo.create(PromptTemplate(title=title, content=content, modality=modality, category=category))
