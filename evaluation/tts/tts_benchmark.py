import os
import time
import shutil
import subprocess
from pathlib import Path
from collections import defaultdict
import soundfile as sf


import numpy as np
import matplotlib
matplotlib.use("TkAgg")  # force GUI backend on Windows
import matplotlib.pyplot as plt
import librosa
import re

def safe_name(s: str) -> str:
    return re.sub(r"[^A-Za-z0-9_\-]+", "_", s)


# --- Your Kokoro engine ---
from src.tts.kokoro_engine import KokoroTTS

# ---------------- CONFIG ----------------
OUT_DIR = Path("tmp_tts_audio").resolve()
OUT_DIR.mkdir(parents=True, exist_ok=True)


TEXTS = [
    "What is the weather in Marburg tomorrow?",
    "Your meeting has been added to the calendar.",
    "Please confirm the deletion of the event.",
    "The temperature will be around twelve degrees.",
    "You have no events scheduled for today."
]

KOKORO_MODEL = r"C:\Users\ASUS\nls-voice-assistant\src\tts\kokoro-v1.0.onnx"
KOKORO_VOICES = r"C:\Users\ASUS\nls-voice-assistant\src\tts\voices-v1.0.bin"
KOKORO_VOICE = "af_heart"  # <-- set this to whatever voice you use


# ---------------- METRICS ----------------
def audio_duration_sec(wav_path: Path) -> float:
    info = sf.info(str(wav_path))
    return float(info.frames / info.samplerate)

def rms_energy(wav_path: Path) -> float:
    y, sr = sf.read(str(wav_path), always_2d=False)
    y = y.astype(np.float32)
    if y.ndim > 1:
        y = y.mean(axis=1)
    return float(np.sqrt(np.mean(y**2)))


# ---------------- LOAD MODELS ----------------
def load_models():
    models = {}

    # Kokoro (your chosen model)
    kokoro = KokoroTTS(model_path=KOKORO_MODEL, voices_path=KOKORO_VOICES, voice=KOKORO_VOICE)
    models["Kokoro"] = lambda text, out_wav: kokoro.speak(text, out_wav)

    # Windows SAPI (offline baseline)
    try:
        import pyttsx3
        engine = pyttsx3.init()
        engine.setProperty("rate", 175)

        def sapi_tts(text, out_wav):
            import pyttsx3
            engine = pyttsx3.init()
            engine.setProperty("rate", 175)
            engine.save_to_file(text, out_wav)
            engine.runAndWait()
            engine.stop()

        models["WindowsSAPI(pyttsx3)"] = sapi_tts
    except Exception as e:
        print(f"⚠️ Skipping WindowsSAPI(pyttsx3): {e}")

    # eSpeak (if installed)
    ESPEAK_EXE = Path(r"C:\Program Files (x86)\eSpeak\command_line\espeak.exe")

    if ESPEAK_EXE.exists():
        def espeak_tts(text, out_wav):
            out_wav = str(Path(out_wav).resolve())
            cmd = [str(ESPEAK_EXE), "--stdin", "-w", out_wav]
            subprocess.run(cmd, input=text.encode("utf-8"), check=True)

        models["eSpeak"] = espeak_tts
    else:
        print(f"⚠️ Skipping eSpeak (not found at: {ESPEAK_EXE})")

    return models


# ---------------- RUN BENCHMARK ----------------
def main():
    models = load_models()

    lat = defaultdict(list)
    dur = defaultdict(list)
    rms = defaultdict(list)

    for model_name, tts_fn in models.items():
        print(f"\n🔊 Evaluating {model_name}")
        for i, text in enumerate(TEXTS):
            wav_path = OUT_DIR / f"{safe_name(model_name)}_{i}.wav"


            t0 = time.perf_counter()
            tts_fn(text, str(wav_path))
            t1 = time.perf_counter()

            lat[model_name].append(t1 - t0)
            dur[model_name].append(audio_duration_sec(wav_path))
            rms[model_name].append(rms_energy(wav_path))

            print(f"  [{i}] latency={t1-t0:.2f}s | duration={dur[model_name][-1]:.2f}s")

    # Aggregate
    names = list(lat.keys())
    avg_lat = [np.mean(lat[n]) for n in names]
    avg_dur = [np.mean(dur[n]) for n in names]
    avg_rms = [np.mean(rms[n]) for n in names]

    # Plot
    fig, axes = plt.subplots(1, 3, figsize=(15, 4))

    axes[0].bar(names, avg_lat)
    axes[0].set_title("Average TTS Latency")
    axes[0].set_ylabel("Seconds")

    axes[1].bar(names, avg_dur)
    axes[1].set_title("Average Audio Duration")
    axes[1].set_ylabel("Seconds")

    axes[2].bar(names, avg_rms)
    axes[2].set_title("Average RMS Energy (proxy)")
    axes[2].set_ylabel("Amplitude")

    for ax in axes:
        ax.set_xticklabels(names, rotation=15, ha="right")

    plt.tight_layout()

    # Save to file so you always get an artifact even if GUI doesn't pop up
    out_path = Path("plots/tts_benchmark.png")
    Path("plots").mkdir(exist_ok=True)
    plt.savefig(out_path, dpi=200)
    print(f"\n✅ Plot saved to: {out_path.resolve()}")

    # Try to show interactively too
    plt.show(block=True)

    input("Press Enter to exit...")


if __name__ == "__main__":
    main()
