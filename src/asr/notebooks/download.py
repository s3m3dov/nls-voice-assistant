from __future__ import annotations

import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional, List, Dict, Tuple

from datasets import Dataset, Audio, load_dataset, concatenate_datasets, load_from_disk
from tqdm import tqdm


# ============================================================
# Global settings
# ============================================================
CACHE_DIR = Path("data/cached_datasets")
DEFAULT_SAMPLE_SIZE = 1000        # used for speech datasets
BATCH_SIZE = 50                   # stream → write batches to avoid OOM
SAMPLING_RATE = 16000             # standardize audio


# ============================================================
# Enums
# ============================================================
class Language(str, Enum):
    EN = "en"
    DE = "de"
    FR = "fr"
    ES = "es"
    IT = "it"
    PT = "pt"
    NL = "nl"
    PL = "pl"
    MULTI = "multi"


class DatasetGroup(str, Enum):
    CLEAN = "clean"
    NOISY = "noisy"
    CONVERSATIONAL = "conversational"
    FORMAL = "formal"
    MUSIC = "music"


# ============================================================
# DatasetConfig
# ============================================================
@dataclass
class DatasetConfig:
    name: str
    hf_dataset_name: str
    hf_config: Optional[str] = None
    hf_split: str = "test"

    audio_column: str = "audio"
    text_column: str = "text"

    description: str = ""
    language: Language = Language.EN
    group: DatasetGroup = DatasetGroup.CLEAN

    use_streaming: bool = True
    sample_size: Optional[int] = DEFAULT_SAMPLE_SIZE

    trust_remote_code: bool = True


# ============================================================
# Language map (MLS has NO English)
# ============================================================
LANG_MAP: Dict[Language, Dict[str, str]] = {
    Language.EN: {"fleurs": "en_us"},
    Language.DE: {"mls": "german", "fleurs": "de_de"},
    Language.FR: {"mls": "french", "fleurs": "fr_fr"},
    Language.ES: {"mls": "spanish", "fleurs": "es_es"},
    Language.IT: {"mls": "italian", "fleurs": "it_it"},
    Language.PT: {"mls": "portuguese", "fleurs": "pt_br"},
    Language.NL: {"mls": "dutch", "fleurs": "nl_nl"},
    Language.PL: {"mls": "polish", "fleurs": "pl_pl"},
}


# ============================================================
# Datasets (ONLY what you listed; names unchanged)
# ============================================================
LIBRISPEECH_DATASETS: List[DatasetConfig] = [
    DatasetConfig(
        name="LibriSpeech_Clean",
        hf_dataset_name="openslr/librispeech_asr",
        hf_config="clean",
        description="Clean audiobook recordings",
        language=Language.EN,
        group=DatasetGroup.CLEAN,
    ),
    DatasetConfig(
        name="LibriSpeech_Other",
        hf_dataset_name="openslr/librispeech_asr",
        hf_config="other",
        description="Challenging audiobook recordings",
        language=Language.EN,
        group=DatasetGroup.NOISY,
    ),
]

PEOPLESPEECH_DATASETS: List[DatasetConfig] = [
    DatasetConfig(
        name="PeoplesSpeech_Clean",
        hf_dataset_name="MLCommons/peoples_speech",
        hf_config="clean",
        text_column="text",
        description="Public speeches (clean)",
        language=Language.EN,
        group=DatasetGroup.FORMAL,
    ),
    DatasetConfig(
        name="PeoplesSpeech_Dirty",
        hf_dataset_name="MLCommons/peoples_speech",
        hf_config="dirty",
        text_column="text",
        description="Public speeches (challenging)",
        language=Language.EN,
        group=DatasetGroup.NOISY,
    ),
]

AMI_DATASETS: List[DatasetConfig] = [
    DatasetConfig(
        name="AMI_Meetings",
        hf_dataset_name="edinburghcstr/ami",
        hf_config="ihm",
        description="Meeting recordings – conversational",
        language=Language.EN,
        group=DatasetGroup.CONVERSATIONAL,
    )
]

MLS_DATASETS: List[DatasetConfig] = [
    DatasetConfig(
        name=f"MLS_{lang.value.upper()}",
        hf_dataset_name="facebook/multilingual_librispeech",
        hf_config=cfg["mls"],
        text_column="transcript",
        description="Multilingual LibriSpeech – audiobooks",
        language=lang,
        group=DatasetGroup.CLEAN,
    )
    for lang, cfg in LANG_MAP.items()
    if "mls" in cfg
]

FLEURS_DATASETS: List[DatasetConfig] = [
    DatasetConfig(
        name=f"FLEURS_{lang.value.upper()}",
        hf_dataset_name="google/fleurs",
        hf_config=cfg["fleurs"],
        hf_split="test",
        text_column="transcription",
        description="FLEURS – short, noisy, conversational",
        language=lang,
        group=DatasetGroup.NOISY,
    )
    for lang, cfg in LANG_MAP.items()
    if "fleurs" in cfg
]

JAMENDO_SUBSETS: List[str] = [
    "pure",
    "pure-en",
    "pure-de",
    "pure-es",
    "pure-fr",
    "merged",
    "merged-en",
    "merged-de",
    "merged-es",
    "merged-fr",
]

MUSIC_DATASETS: List[DatasetConfig] = [
    DatasetConfig(
        name=f"JamALTLines_{subset}",
        hf_dataset_name="jamendolyrics/jam-alt-lines",
        hf_config=subset,
        description=f"Jam-ALT Lines subset: {subset}",
        language=Language.MULTI,
        group=DatasetGroup.MUSIC,
        sample_size=None,  # full dataset
    )
    for subset in JAMENDO_SUBSETS
]

ALL_DATASETS: List[DatasetConfig] = (
    LIBRISPEECH_DATASETS
    + PEOPLESPEECH_DATASETS
    + AMI_DATASETS
    + MLS_DATASETS
    + FLEURS_DATASETS
    + MUSIC_DATASETS
)


# ============================================================
# Core helpers
# ============================================================
def get_cache_path(dataset_name: str) -> Path:
    clean_name = dataset_name.lower().replace(" ", "_")
    return CACHE_DIR / clean_name


def prepare_streaming_dataset(config: DatasetConfig):
    ds = load_dataset(
        config.hf_dataset_name,
        config.hf_config,
        split=config.hf_split,
        streaming=True,
        trust_remote_code=config.trust_remote_code,
    )

    # normalize audio column -> "audio"
    if config.audio_column != "audio" and config.audio_column in getattr(ds, "column_names", []):
        ds = ds.rename_column(config.audio_column, "audio")

    # force Audio decoding + resampling semantics in the stream
    if "audio" in getattr(ds, "column_names", []):
        ds = ds.cast_column("audio", Audio(sampling_rate=SAMPLING_RATE))

    return ds


def save_batch(batch_examples: List[dict], batch_idx: int, temp_dir: Path) -> Path:
    batch_ds = Dataset.from_list(batch_examples)

    # standardize audio column for saved batch
    if "audio" in batch_ds.column_names:
        batch_ds = batch_ds.cast_column("audio", Audio(sampling_rate=SAMPLING_RATE))

    batch_path = temp_dir / f"batch_{batch_idx:04d}"
    batch_ds.save_to_disk(str(batch_path))
    return batch_path


def stream_and_batch_dataset(
    dataset_stream,
    sample_size: Optional[int],
    batch_size: int,
    temp_dir: Path,
    desc: str,
) -> List[Path]:
    batch_paths: List[Path] = []
    current_batch: List[dict] = []
    total_count = 0

    pbar = tqdm(total=sample_size, desc=desc, unit="ex", leave=False)

    for example in dataset_stream:
        current_batch.append(example)
        total_count += 1
        pbar.update(1)

        if len(current_batch) >= batch_size:
            batch_paths.append(save_batch(current_batch, len(batch_paths), temp_dir))
            current_batch = []

        if sample_size is not None and total_count >= sample_size:
            break

    if current_batch:
        batch_paths.append(save_batch(current_batch, len(batch_paths), temp_dir))

    pbar.close()
    return batch_paths


def concatenate_batches(batch_paths: List[Path], output_path: Path) -> Dataset:
    print(f"   Concatenating {len(batch_paths)} batches...")
    batches = [load_from_disk(str(p)) for p in batch_paths]
    final_ds = concatenate_datasets(batches)
    final_ds.save_to_disk(str(output_path))
    return final_ds


def download_and_cache_dataset(config: DatasetConfig, batch_size: int = BATCH_SIZE) -> Path:
    cache_path = get_cache_path(config.name)

    # ✅ Skip if cache exists
    if cache_path.exists():
        print(f"⏭️  Skipping {config.name} (cache exists at {cache_path})")
        return cache_path

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    sample_info = "ALL" if config.sample_size is None else str(config.sample_size)
    print(
        f"📥 {config.name}\n"
        f"   Dataset: {config.hf_dataset_name} | Config: {config.hf_config} | Split: {config.hf_split}\n"
        f"   Lang: {config.language.value} | Group: {config.group.value} | Samples: {sample_info} | Batch: {batch_size}"
    )

    temp_dir = Path(tempfile.mkdtemp(prefix=f"ds_{config.name}_"))

    try:
        dataset_stream = prepare_streaming_dataset(config)
        batch_paths = stream_and_batch_dataset(
            dataset_stream=dataset_stream,
            sample_size=config.sample_size,
            batch_size=batch_size,
            temp_dir=temp_dir,
            desc=config.name,
        )

        final_ds = concatenate_batches(batch_paths, cache_path)
        print(f"✓ 💾 Cached {len(final_ds)} examples to {cache_path}")
        return cache_path

    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def download_all(datasets: Optional[List[DatasetConfig]] = None) -> None:
    if datasets is None:
        datasets = ALL_DATASETS

    total_start = time.time()
    successes = 0
    failures = 0

    for config in tqdm(datasets, desc="All datasets", unit="ds"):
        start = time.time()
        try:
            download_and_cache_dataset(config)
            elapsed = time.time() - start
            print(f"⏱️  Finished in {elapsed:.1f}s\n")
            successes += 1
        except Exception as e:
            print(f"❌ Failed: {config.name}: {e}\n")
            failures += 1

    total_time = time.time() - total_start
    print(f"\n🏁 Complete! {successes} succeeded, {failures} failed")
    print(f"   Total time: {total_time:.1f}s ({total_time/60:.1f}m)")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    download_all()
