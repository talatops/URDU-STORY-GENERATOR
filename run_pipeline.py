"""
Complete pipeline script to run all phases:
1. Scrape stories
2. Preprocess corpus
3. Train tokenizer
4. Train model
"""

import os
import sys
import subprocess


def run_command(cmd, description):
    """Run a command and handle errors."""
    print("\n" + "=" * 60)
    print(description)
    print("=" * 60)
    print(f"Running: {cmd}")
    
    result = subprocess.run(cmd, shell=True, capture_output=False)
    
    if result.returncode != 0:
        print(f"\nError: {description} failed!")
        return False
    
    return True


def main():
    print("=" * 60)
    print("Urdu Story Generation System - Complete Pipeline")
    print("=" * 60)
    
    # Phase 1: Data Collection
    if not os.path.exists("data/raw/stories.json"):
        if not run_command(
            "python3 data/scraper.py",
            "Phase I: Scraping Urdu stories"
        ):
            print("\nScraping failed. You may need to:")
            print("1. Check internet connection")
            print("2. Verify UrduPoint website is accessible")
            print("3. Adjust scraper selectors if website structure changed")
            return
    else:
        print("\nSkipping scraping - stories.json already exists")
    
    # Phase 1: Preprocessing
    if not os.path.exists("data/processed/corpus.txt"):
        if not run_command(
            "python3 data/preprocess.py",
            "Phase I: Preprocessing corpus"
        ):
            print("\nPreprocessing failed!")
            return
    else:
        print("\nSkipping preprocessing - corpus.txt already exists")
    
    # Phase 2: Train Tokenizer
    if not os.path.exists("models/tokenizer.json"):
        if not run_command(
            "python3 train_tokenizer.py",
            "Phase II: Training BPE tokenizer"
        ):
            print("\nTokenizer training failed!")
            return
    else:
        print("\nSkipping tokenizer training - tokenizer.json already exists")
    
    # Phase 3: Train Model
    if not os.path.exists("models/trigram.json"):
        if not run_command(
            "python3 train_model.py",
            "Phase III: Training trigram model"
        ):
            print("\nModel training failed!")
            return
    else:
        print("\nSkipping model training - trigram.json already exists")
    
    print("\n" + "=" * 60)
    print("Pipeline Complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Start backend: cd backend && uvicorn main:app --reload")
    print("2. Start frontend: cd frontend && npm run dev")
    print("3. Open http://localhost:3000 in your browser")


if __name__ == "__main__":
    main()
