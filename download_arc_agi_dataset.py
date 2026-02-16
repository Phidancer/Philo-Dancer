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
import time
from urllib.parse import urlparse

def download_file(url, filename, chunk_size=8192):
    """Download a file with progress bar."""
    response = requests.get(url, stream=True)
    response.raise_for_status()
    
    total_size = int(response.headers.get('content-length', 0))
    
    with open(filename, 'wb') as file, tqdm(
        desc=str(filename),
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

def download_github_repo_data(owner, repo, output_dir, branch="main"):
    """Download repository contents recursively via GitHub API."""
    base_url = f"https://api.github.com/repos/{owner}/{repo}/contents"
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    def download_directory(path="", current_dir=None):
        if current_dir is None:
            current_dir = output_path
        
        url = f"{base_url}/{path}" if path else base_url
        params = {"ref": branch}
        
        print(f"Fetching directory listing: {path or 'root'}")
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            items = response.json()
            
            if not isinstance(items, list):
                print(f"Warning: Expected list but got {type(items)} for path {path}")
                return
            
            for item in items:
                item_path = current_dir / item["name"]
                
                if item["type"] == "file":
                    print(f"Downloading file: {item['path']}")
                    download_url = item["download_url"]
                    if download_url:
                        download_file(download_url, item_path)
                    else:
                        print(f"Warning: No download URL for {item['path']}")
                        
                elif item["type"] == "dir":
                    item_path.mkdir(exist_ok=True)
                    download_directory(item["path"], item_path)
                    
        except requests.exceptions.RequestException as e:
            print(f"Error downloading directory {path}: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error processing directory {path}: {e}")
            raise
    
    download_directory()
    return output_path

def validate_dataset(data_dir):
    """Validate the downloaded dataset structure and content."""
    data_path = Path(data_dir)
    
    if not data_path.exists():
        raise ValueError(f"Dataset directory does not exist: {data_path}")
    
    # Expected files and their minimum task counts
    expected_files = {
        "training.json": 1000,  # Should have 1,000 training tasks
        "evaluation.json": 120,  # Should have 120 evaluation tasks
    }
    
    validation_results = {
        "valid": True,
        "files": {},
        "total_training_tasks": 0,
        "total_evaluation_tasks": 0,
        "errors": []
    }
    
    for filename, min_tasks in expected_files.items():
        file_path = data_path / filename
        
        if not file_path.exists():
            validation_results["valid"] = False
            validation_results["errors"].append(f"Missing file: {filename}")
            validation_results["files"][filename] = {"exists": False}
            continue
        
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            if not isinstance(data, dict):
                validation_results["valid"] = False
                validation_results["errors"].append(f"Invalid JSON structure in {filename}: expected object, got {type(data)}")
                continue
            
            task_count = len(data)
            validation_results["files"][filename] = {
                "exists": True,
                "task_count": task_count,
                "valid_json": True,
                "meets_minimum": task_count >= min_tasks
            }
            
            if filename == "training.json":
                validation_results["total_training_tasks"] = task_count
            elif filename == "evaluation.json":
                validation_results["total_evaluation_tasks"] = task_count
            
            if task_count < min_tasks:
                validation_results["valid"] = False
                validation_results["errors"].append(
                    f"{filename} has {task_count} tasks, expected at least {min_tasks}"
                )
            
            # Validate a few task structures
            sample_tasks = list(data.items())[:3]  # Check first 3 tasks
            for task_id, task_data in sample_tasks:
                if not isinstance(task_data, dict):
                    validation_results["valid"] = False
                    validation_results["errors"].append(f"Invalid task structure in {filename}: task {task_id}")
                    break
                
                required_keys = ["train", "test"]
                for key in required_keys:
                    if key not in task_data:
                        validation_results["valid"] = False
                        validation_results["errors"].append(f"Missing '{key}' in task {task_id} of {filename}")
                        break
        
        except json.JSONDecodeError as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Invalid JSON in {filename}: {e}")
            validation_results["files"][filename] = {"exists": True, "valid_json": False}
        
        except Exception as e:
            validation_results["valid"] = False
            validation_results["errors"].append(f"Error reading {filename}: {e}")
    
    return validation_results

def create_dataset_info(data_dir, validation_results):
    """Create a dataset info file with metadata."""
    data_path = Path(data_dir)
    info_file = data_path / "dataset_info.json"
    
    info = {
        "dataset_name": "ARC-AGI-2",
        "source_repository": "https://github.com/arcprize/ARC-AGI-2",
        "download_timestamp": time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
        "validation": validation_results,
        "summary": {
            "training_tasks": validation_results.get("total_training_tasks", 0),
            "evaluation_tasks": validation_results.get("total_evaluation_tasks", 0),
            "valid_dataset": validation_results.get("valid", False)
        },
        "file_structure": {
            "training.json": "Training tasks for model development",
            "evaluation.json": "Evaluation tasks for model assessment",
            "dataset_info.json": "This metadata file"
        }
    }
    
    with open(info_file, 'w') as f:
        json.dump(info, f, indent=2)
    
    print(f"Created dataset info file: {info_file}")
    return info_file

def download_arc_agi_dataset(output_dir="arc_agi_data"):
    """Download the ARC-AGI-2 dataset from the official GitHub repository."""
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    print("Downloading ARC-AGI-2 Dataset...")
    print(f"Output directory: {output_path.absolute()}")
    print(f"Source: https://github.com/arcprize/ARC-AGI-2")
    
    try:
        # Try GitHub API first, fall back to zip download
        data_dir = output_path / "data"
        data_dir.mkdir(exist_ok=True)
        
        try:
            print(f"\n1. Trying GitHub API download...")
            repo_data_dir = download_github_repo_data("arcprize", "ARC-AGI-2", output_path / "repo_data")
            
            # Find and organize the data files
            print(f"\n2. Organizing dataset files...")
            
            # Look for JSON files in the downloaded repository
            json_files = list(repo_data_dir.rglob("*.json"))
            
        except Exception as api_error:
            print(f"GitHub API failed: {api_error}")
            print(f"\n1. Falling back to zip download...")
            
            # Download as zip file
            zip_url = "https://github.com/arcprize/ARC-AGI-2/archive/refs/heads/main.zip"
            zip_path = output_path / "arc-agi-2-main.zip"
            
            download_file(zip_url, zip_path)
            
            print(f"\n2. Extracting repository...")
            extract_zip(zip_path, output_path)
            
            # Find the extracted directory
            extracted_dirs = [d for d in output_path.iterdir() if d.is_dir() and "ARC-AGI-2" in d.name]
            if not extracted_dirs:
                raise ValueError("Could not find extracted ARC-AGI-2 directory")
            
            repo_data_dir = extracted_dirs[0]
            
            # Clean up zip file
            zip_path.unlink()
            
            print(f"\n3. Organizing dataset files...")
            
            # Look for JSON files in the downloaded repository
            json_files = list(repo_data_dir.rglob("*.json"))
        
        # Check if we have the ARC-AGI-2 structure with individual task files
        training_dir = None
        evaluation_dir = None
        
        for subdir in repo_data_dir.rglob("*"):
            if subdir.is_dir():
                if "training" in subdir.name.lower():
                    training_dir = subdir
                elif "evaluation" in subdir.name.lower():
                    evaluation_dir = subdir
        
        if training_dir and evaluation_dir:
            print(f"Found ARC-AGI-2 structure with individual task files")
            print(f"Training directory: {training_dir.relative_to(repo_data_dir)}")
            print(f"Evaluation directory: {evaluation_dir.relative_to(repo_data_dir)}")
            
            # Combine individual files into consolidated JSON files
            training_data = {}
            evaluation_data = {}
            
            # Process training files
            training_files = list(training_dir.glob("*.json"))
            print(f"Processing {len(training_files)} training task files...")
            for task_file in training_files:
                try:
                    with open(task_file, 'r') as f:
                        task_data = json.load(f)
                    task_id = task_file.stem
                    training_data[task_id] = task_data
                except Exception as e:
                    print(f"Warning: Could not read {task_file.name}: {e}")
            
            # Process evaluation files
            evaluation_files = list(evaluation_dir.glob("*.json"))
            print(f"Processing {len(evaluation_files)} evaluation task files...")
            for task_file in evaluation_files:
                try:
                    with open(task_file, 'r') as f:
                        task_data = json.load(f)
                    task_id = task_file.stem
                    evaluation_data[task_id] = task_data
                except Exception as e:
                    print(f"Warning: Could not read {task_file.name}: {e}")
            
            # Save consolidated files
            training_json = data_dir / "training.json"
            evaluation_json = data_dir / "evaluation.json"
            
            with open(training_json, 'w') as f:
                json.dump(training_data, f, indent=2)
            print(f"Created consolidated training.json with {len(training_data)} tasks")
            
            with open(evaluation_json, 'w') as f:
                json.dump(evaluation_data, f, indent=2)
            print(f"Created consolidated evaluation.json with {len(evaluation_data)} tasks")
            
            copied_files = [training_json, evaluation_json]
            
        else:
            # Fall back to looking for existing consolidated files
            important_files = []
            for json_file in json_files:
                filename = json_file.name.lower()
                if any(keyword in filename for keyword in ['train', 'eval', 'test']):
                    important_files.append(json_file)
            
            if not important_files:
                # If no specific files found, look for any JSON files that might contain tasks
                print("No specific training/evaluation files found, checking all JSON files...")
                for json_file in json_files:
                    try:
                        with open(json_file, 'r') as f:
                            data = json.load(f)
                        if isinstance(data, dict) and len(data) > 10:  # Likely contains tasks
                            important_files.append(json_file)
                            print(f"Found potential dataset file: {json_file.relative_to(repo_data_dir)} ({len(data)} items)")
                    except:
                        continue
            
            # Copy important files to data directory
            copied_files = []
            for file_path in important_files:
                relative_path = file_path.relative_to(repo_data_dir)
                dest_path = data_dir / relative_path.name
                
                import shutil
                shutil.copy2(file_path, dest_path)
                copied_files.append(dest_path)
                print(f"Copied: {relative_path} -> {dest_path.name}")
        
        if not copied_files:
            raise ValueError("No dataset files found in the repository")
        
        print(f"\n4. Validating dataset...")
        validation_results = validate_dataset(data_dir)
        
        if validation_results["valid"]:
            print("✅ Dataset validation passed")
        else:
            print("⚠️  Dataset validation warnings:")
            for error in validation_results["errors"]:
                print(f"  - {error}")
        
        print(f"\n5. Creating dataset info file...")
        create_dataset_info(data_dir, validation_results)
        
        # Clean up repo directory if it exists
        if repo_data_dir.exists() and repo_data_dir != data_dir:
            import shutil
            shutil.rmtree(repo_data_dir)
            print(f"Cleaned up temporary directory: {repo_data_dir}")
        
        print(f"\n✅ ARC-AGI-2 dataset downloaded successfully to {output_path.absolute()}")
        
        # Display dataset info
        display_dataset_info(data_dir)
        
        return data_dir
        
    except Exception as e:
        print(f"\n❌ Error downloading dataset: {e}")
        raise

def display_dataset_info(data_dir):
    """Display information about the downloaded dataset."""
    print("\n📊 Dataset Information:")
    
    data_path = Path(data_dir)
    info_file = data_path / "dataset_info.json"
    
    # Try to load the info file first
    if info_file.exists():
        try:
            with open(info_file, 'r') as f:
                info = json.load(f)
            
            summary = info.get("summary", {})
            print(f"  Dataset: {info.get('dataset_name', 'Unknown')}")
            print(f"  Source: {info.get('source_repository', 'Unknown')}")
            print(f"  Downloaded: {info.get('download_timestamp', 'Unknown')}")
            print(f"  Training tasks: {summary.get('training_tasks', 0)}")
            print(f"  Evaluation tasks: {summary.get('evaluation_tasks', 0)}")
            print(f"  Valid dataset: {'✅' if summary.get('valid_dataset') else '❌'}")
            
            return
        except Exception as e:
            print(f"  Error reading dataset info: {e}")
    
    # Fallback to manual file inspection
    training_file = data_path / "training.json"
    evaluation_file = data_path / "evaluation.json"
    test_file = data_path / "test.json"
    
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
    
    # List all JSON files found
    all_json_files = list(data_path.glob("*.json"))
    if all_json_files:
        print(f"\n📁 Files in dataset directory:")
        for json_file in all_json_files:
            try:
                with open(json_file, 'r') as f:
                    data = json.load(f)
                if isinstance(data, dict):
                    print(f"  {json_file.name}: {len(data)} items")
                else:
                    print(f"  {json_file.name}: {type(data).__name__}")
            except:
                print(f"  {json_file.name}: Unable to read")

def main():
    parser = argparse.ArgumentParser(
        description="Download ARC-AGI-2 dataset from the official GitHub repository",
        epilog="This script downloads the complete ARC-AGI-2 dataset including 1,000 training tasks and 120 evaluation tasks."
    )
    parser.add_argument(
        "--output-dir", 
        default="arc_agi_data",
        help="Output directory for the dataset (default: arc_agi_data)"
    )
    
    args = parser.parse_args()
    
    print("ARC-AGI-2 Dataset Downloader")
    print("=" * 50)
    
    try:
        result_dir = download_arc_agi_dataset(args.output_dir)
        print(f"\n🎉 Success! Dataset saved to: {result_dir.absolute()}")
        return 0
        
    except KeyboardInterrupt:
        print("\n❌ Download interrupted by user")
        return 1
        
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network error: {e}")
        print("Please check your internet connection and try again.")
        return 1
        
    except ValueError as e:
        print(f"\n❌ Dataset error: {e}")
        print("The repository structure may have changed. Please report this issue.")
        return 1
        
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please report this issue with the full error message.")
        return 1

if __name__ == "__main__":
    main()