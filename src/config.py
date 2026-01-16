from pydantic_settings import BaseSettings

from src.api.config import APISettings
from src.dialogue.config import DialogueSettings
from src.tts.config import TTSSettings


class Settings(BaseSettings):
    """
    Application-wide settings container.
    """

    # API settings (nested)
    api: APISettings = APISettings(
        calendar_id="team-ezekiel"
    )

    model_config = {
        "extra": "ignore",
    }
    # TTS settings (nested)
    tts: TTSSettings = TTSSettings(
        model_path="kokoro-v1.0.onnx",
        voices_path="voices-v1.0.bin",
        voice="af_heart"
    )

    # Dialogue settings (nested)
    dialogue: DialogueSettings = DialogueSettings(
        llm_model="qwen2.5:7b-instruct"
    )


# Singleton instances
settings = Settings()
