from pydantic_settings import BaseSettings

from src.api.config import APISettings
from src.asr.config import ASRSettings
from src.dialogue.config import DialogueSettings
from src.tts.config import TTSSettings
from src.interface.ui.config import UISettings


class Settings(BaseSettings):
    """
    Application-wide settings container.
    """

    # API settings (nested)
    api: APISettings = APISettings(
        calendar_id="team-ezekiel"
    )

    # ASR settings (nested)
    asr: ASRSettings = ASRSettings(
        model_name="medium.en",
    )

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

    # UI settings (nested)
    ui: UISettings = UISettings()


# Singleton instances
settings = Settings()
