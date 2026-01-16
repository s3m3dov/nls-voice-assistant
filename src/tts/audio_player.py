import sounddevice as sd
import soundfile as sf


def play_audio(file_path: str) -> None:
    """
    Play a WAV file through the default audio output.
    
    Args:
        file_path: Path to the audio file.
    """
    data, sample_rate = sf.read(file_path)
    sd.play(data, sample_rate)
    sd.wait()  # Block until playback finishes


def play_samples(samples, sample_rate: int) -> None:
    """
    Play audio samples directly through the default audio output.
    
    Args:
        samples: Audio samples as numpy array.
        sample_rate: Sample rate in Hz.
    """
    sd.play(samples, sample_rate)
    sd.wait()  # Block until playback finishes
