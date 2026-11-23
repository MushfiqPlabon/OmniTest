"""Application-wide constants — single source of truth across backend and scripts."""

# Embedding & text chunking
EMBEDDING_DIM = 384
CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
GEMINI_BATCH_SIZE = 100
# Gemini 384-d cosine similarity floor: unrelated text scores ~0.55-0.67; relevant matches >= 0.71.
MIN_RAG_SIMILARITY = 0.70

# Chat & LLM limits
MAX_HISTORY_TURNS = 20
MAX_CHAT_OUTPUT_TOKENS = 1536
MAX_STRUCTURED_OUTPUT_TOKENS = 8192

# Upload & list query limits
MAX_UPLOAD_BYTES = 2 * 1024 * 1024
ALLOWED_UPLOAD_EXTENSIONS = frozenset({".md", ".txt"})
DEFAULT_HISTORY_LIMIT = 50
MAX_HISTORY_LIMIT = 100
