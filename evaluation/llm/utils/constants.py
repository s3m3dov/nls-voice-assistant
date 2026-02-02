QWEN_MODELS = [
    # Qwen 2.5 Series
    "qwen2.5:1.5b",
    "qwen2.5:1.5b-instruct",
    "qwen2.5:3b",
    "qwen2.5:3b-instruct",
    "qwen2.5:7b",
    "qwen2.5:7b-instruct",

    # Qwen 3 Vision-Language Series (acts slower)
    "qwen3-vl:2b-instruct",
    "qwen3-vl:4b-instruct",
    "qwen3-vl:8b-instruct",
]

META_MODELS = [
    "llama3.2:1b-instruct-q4_K_M",
    "llama3.2:3b",
    "llama3.1:8b",
]

MISTRAL_MODELS = [
    "mistral:7b-instruct",
    "mistral-nemo:12b",
]

GOOGLE_MODELS = ["gemma2:2b", "gemma2:9b"]

MICROSOFT_MODELS = ["phi3.5"]

IBM_MODELS = ["granite3-dense:2b"]

HUGGINGFACE_MODELS = ["smollm2:1.7b"]

NOUS_MODELS = ["hermes3:8b"]

COHERE_MODELS = ["command-r7b", "aya:8b"]

TII_MODELS = ["falcon3:1b", "falcon3:7b"]

# =================================================================
# All Models Combined
# =================================================================
DEFAULT_MODELS = (
        QWEN_MODELS +
        META_MODELS +
        MISTRAL_MODELS +
        GOOGLE_MODELS +
        MICROSOFT_MODELS +
        IBM_MODELS +
        HUGGINGFACE_MODELS +
        NOUS_MODELS +
        COHERE_MODELS +
        TII_MODELS
)
