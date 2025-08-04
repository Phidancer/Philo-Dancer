#!/usr/bin/env python3
"""
ARC-AGI 2 Training Dataset Download Script

This script downloads the ARC-AGI 2 training dataset from the official sources.
The ARC (Abstraction and Reasoning Corpus) dataset is used for testing artificial
general intelligence capabilities.
"""

import os
import json
import requests
import zipfile
from pathlib import Path
from tqdm import tqdm
import argparse

def download_file(url, filename, chunk_size=8192):
    """Download a file with progress bar."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as file, tqdm(
        desc=filename,
        total=total_size,
        unit='B',
        unit_scale=True,
        unit_divisor=1024,
    ) as pbar:
        for chunk in response.iter_content(chunk_size=chunk_size):
            if chunk:
                file.write(chunk)
                pbar.update(len(chunk))

def extract_zip(zip_path, extract_to):
    """Extract a zip file to the specified directory."""
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"Extracted {zip_path} to {extract_to}")

def download_arc_agi_dataset(output_dir="arc_agi_data"):
    """Download the ARC-AGI 2 training dataset."""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # ARC-AGI dataset URLs
    urls = {
        "training": "https://github.com/fchollet/ARC-AGI/archive/refs/heads/master.zip",
        "evaluation": "https://github.com/fchollet/ARC-AGI/raw/master/data/evaluation.json",
        "test": "https://github.com/fchollet/ARC-AGI/raw/master/data/test.json"
    }
    
    print("Downloading ARC-AGI 2 Training Dataset...")
    print(f"Output directory: {output_path.absolute()}")
    
    # Download main repository
    zip_path = output_path / "arc-agi-master.zip"
    print(f"\n1. Downloading main repository...")
    download_file(urls["training"], zip_path)
    
    # Extract the repository
    print(f"\n2. Extracting repository...")
    extract_zip(zip_path, output_path)
    
    # Move data files to a more accessible location
    extracted_dir = output_path / "ARC-AGI-master"
    data_dir = output_path / "data"
    
    if extracted_dir.exists():
        import shutil
        if (extracted_dir / "data").exists():
            if data_dir.exists():
                shutil.rmtree(data_dir)
            shutil.move(str(extracted_dir / "data"), str(data_dir))
            print(f"Moved data files to {data_dir}")
    
    # Download additional files if needed
    for name, url in [("evaluation", urls["evaluation"]), ("test", urls["test"])]:
        file_path = data_dir / f"{name}.json"
        if not file_path.exists():
            print(f"\n3. Downloading {name}.json...")
            download_file(url, file_path)
    
    # Clean up
    if zip_path.exists():
        zip_path.unlink()
        print(f"Cleaned up {zip_path}")
    
    if extracted_dir.exists():
        import shutil
        shutil.rmtree(extracted_dir)
        print(f"Cleaned up {extracted_dir}")
    
    print(f"\n✅ ARC-AGI dataset downloaded successfully to {output_path.absolute()}")
    
    # Display dataset info
    display_dataset_info(data_dir)

def display_dataset_info(data_dir):
    """Display information about the downloaded dataset."""
    print("\n📊 Dataset Information:")
    
    training_file = data_dir / "training.json"
    evaluation_file = data_dir / "evaluation.json"
    test_file = data_dir / "test.json"
    
    for file_path, name in [(training_file, "Training"), (evaluation_file, "Evaluation"), (test_file, "Test")]:
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                print(f"  {name}: {len(data)} tasks")
            except Exception as e:
                print(f"  {name}: Error reading file - {e}")
        else:
            print(f"  {name}: File not found")

def main():
    parser = argparse.ArgumentParser(description="Download ARC-AGI 2 training dataset")
    parser.add_argument(
        "--output-dir", 
        default="arc_agi_data",
        help="Output directory for the dataset (default: arc_agi_data)"
    )
    
    args = parser.parse_args()
    
    try:
        download_arc_agi_dataset(args.output_dir)
    except KeyboardInterrupt:
        print("\n❌ Download interrupted by user")
    except Exception as e:
        print(f"\n❌ Error downloading dataset: {e}")
        raise

if __name__ == "__main__":
    main()