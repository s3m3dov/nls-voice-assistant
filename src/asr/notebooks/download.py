from __future__ import annotations

import os
import shutil
import tempfile
import time
from dataclasses import dataclass
from typing import Optional, List

from datasets import Dataset, load_dataset, Audio, concatenate_datasets
from tqdm import tqdm


# ============================================================
# Configuration
# ============================================================
CACHE_DIR = "data/cached_datasets"
DEFAULT_SAMPLE_SIZE = 1000
BATCH_SIZE = 50
SAMPLING_RATE = 16000


# ============================================================
# Dataset Configurations
# ============================================================
@dataclass
class DatasetConfig:
    """Configuration for a HuggingFace dataset."""
    name: str
    hf_dataset_name: str
    hf_config: Optional[str] = None
    hf_split: str = "test"
    audio_column: str = "audio"
    text_column: str = "text"
    description: str = ""
    language: str = "en"
    sample_size: Optional[int] = DEFAULT_SAMPLE_SIZE
    trust_remote_code: bool = True


def create_dataset_configs() -> List[DatasetConfig]:
    """Create all dataset configurations."""
    
    # English datasets
    english = [
        DatasetConfig(
            name="LibriSpeech_Clean",
            hf_dataset_name="openslr/librispeech_asr",
            hf_config="clean",
            description="Clean audiobook recordings",
        ),
        DatasetConfig(
            name="LibriSpeech_Other",
            hf_dataset_name="openslr/librispeech_asr",
            hf_config="other",
            description="Challenging audiobook recordings",
        ),
        DatasetConfig(
            name="PeoplesSpeech_Clean",
            hf_dataset_name="MLCommons/peoples_speech",
            hf_config="clean",
            description="Public speeches (clean audio)",
        ),
        DatasetConfig(
            name="PeoplesSpeech_Dirty",
            hf_dataset_name="MLCommons/peoples_speech",
            hf_config="dirty",
            description="Public speeches (challenging audio)",
        ),
        DatasetConfig(
            name="AMI_Meetings",
            hf_dataset_name="edinburghcstr/ami",
            hf_config="ihm",
            description="Meeting recordings - conversational speech",
        ),
    ]
    
    # Multilingual datasets
    mls_configs = [
        ("German", "german"), ("Spanish", "spanish"), ("French", "french"), 
        ("Italian", "italian"), ("Dutch", "dutch"), ("Portuguese", "portuguese"), ("Polish", "polish")
    ]
    multilingual = [
        DatasetConfig(
            name=f"MLS_{lang}",
            hf_dataset_name="facebook/multilingual_librispeech",
            hf_config=code.lower(),
            text_column="transcript",
            description=f"Multilingual LibriSpeech - {lang} audiobooks",
            language=code,
        )
        for lang, code in mls_configs
    ]
    
    # Music datasets
    jam_subsets = [
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
    music = [
        DatasetConfig(
            name=f"JamALTLines_{subset}",
            hf_dataset_name="jamendolyrics/jam-alt-lines",
            hf_config=subset,
            description=f"Jam-ALT Lines subset: {subset}",
            language="multi",
            sample_size=None,  # Full dataset
        )
        for subset in jam_subsets
    ]
    
    return english + multilingual + music


# ============================================================
# Core Functions
# ============================================================
def get_cache_path(dataset_name: str) -> str:
    """Get cache path for a dataset."""
    clean_name = dataset_name.lower().replace(' ', '_')
    return os.path.join(CACHE_DIR, clean_name)


def prepare_streaming_dataset(config: DatasetConfig):
    """Load and prepare streaming dataset."""
    ds = load_dataset(
        config.hf_dataset_name,
        config.hf_config,
        split=config.hf_split,
        streaming=True,
        trust_remote_code=config.trust_remote_code,
    )
    
    # Normalize column name if needed
    if config.audio_column != "audio" and config.audio_column in ds.column_names:
        ds = ds.rename_column(config.audio_column, "audio")
    
    return ds


def save_batch(batch_examples: List[dict], batch_idx: int, temp_dir: str) -> str:
    """Save a batch of examples to disk."""
    batch_ds = Dataset.from_list(batch_examples)
    
    if "audio" in batch_ds.column_names:
        batch_ds = batch_ds.cast_column("audio", Audio(sampling_rate=SAMPLING_RATE))
    
    batch_path = os.path.join(temp_dir, f"batch_{batch_idx:04d}")
    batch_ds.save_to_disk(batch_path)
    
    return batch_path


def stream_and_batch_dataset(
    dataset_stream, 
    sample_size: Optional[int],
    batch_size: int,
    temp_dir: str,
    desc: str
) -> List[str]:
    """Stream dataset and save in batches. Returns list of batch paths."""
    batch_paths = []
    current_batch = []
    total_count = 0
    
    pbar = tqdm(total=sample_size, desc=desc, unit="ex", leave=False)
    
    for example in dataset_stream:
        current_batch.append(example)
        total_count += 1
        pbar.update(1)
        
        # Save when batch is full
        if len(current_batch) >= batch_size:
            batch_path = save_batch(current_batch, len(batch_paths), temp_dir)
            batch_paths.append(batch_path)
            current_batch = []
        
        # Stop at sample limit
        if sample_size is not None and total_count >= sample_size:
            break
    
    # Save final partial batch
    if current_batch:
        batch_path = save_batch(current_batch, len(batch_paths), temp_dir)
        batch_paths.append(batch_path)
    
    pbar.close()
    return batch_paths


def concatenate_batches(batch_paths: List[str], output_path: str) -> Dataset:
    """Load all batches and concatenate into final dataset."""
    print(f"   Concatenating {len(batch_paths)} batches...")
    batches = [Dataset.load_from_disk(path) for path in batch_paths]
    final_ds = concatenate_datasets(batches)
    final_ds.save_to_disk(output_path)
    return final_ds


def download_and_cache_dataset(
    config: DatasetConfig,
    batch_size: int = BATCH_SIZE
) -> str:
    """
    Download dataset in streaming mode with batched saving to avoid OOM.
    
    Returns path to cached dataset.
    """
    cache_path = get_cache_path(config.name)
    
    # Clean existing cache
    if os.path.exists(cache_path):
        print(f"   Existing cache at {cache_path}...")
        # shutil.rmtree(cache_path)
        pass
    
    os.makedirs(CACHE_DIR, exist_ok=True)
    
    # Log configuration
    sample_info = str(config.sample_size) if config.sample_size else "ALL"
    print(
        f"📥 {config.name}\n"
        f"   Dataset: {config.hf_dataset_name} | Config: {config.hf_config} | Split: {config.hf_split}\n"
        f"   Samples: {sample_info} | Batch size: {batch_size}"
    )
    
    # Create temporary directory for batches
    temp_dir = tempfile.mkdtemp(prefix=f"ds_{config.name}_")
    
    try:
        # Stream and batch the dataset
        dataset_stream = prepare_streaming_dataset(config)
        batch_paths = stream_and_batch_dataset(
            dataset_stream,
            config.sample_size,
            batch_size,
            temp_dir,
            config.name
        )
        
        # Concatenate and save final dataset
        final_ds = concatenate_batches(batch_paths, cache_path)
        
        print(f"✓ 💾 Cached {len(final_ds)} examples to {cache_path}")
        return cache_path
        
    finally:
        # Always cleanup temp directory
        shutil.rmtree(temp_dir, ignore_errors=True)


def download_all(datasets: Optional[List[DatasetConfig]] = None) -> None:
    """Download all configured datasets."""
    if datasets is None:
        datasets = create_dataset_configs()
    
    total_start = time.time()
    successes = 0
    failures = 0
    
    for config in tqdm(datasets, desc="All datasets", unit="ds"):
        start = time.time()
        try:
            download_and_cache_dataset(config)
            elapsed = time.time() - start
            sample_info = config.sample_size if config.sample_size else "ALL"
            print(f"⏱️  Finished in {elapsed:.1f}s\n")
            successes += 1
            
        except Exception as e:
            print(f"❌ Failed: {e}\n")
            failures += 1
    
    total_time = time.time() - total_start
    print(f"\n🏁 Complete! {successes} succeeded, {failures} failed")
    print(f"   Total time: {total_time:.1f}s ({total_time/60:.1f}m)")


# ============================================================
# Main
# ============================================================
if __name__ == "__main__":
    download_all()