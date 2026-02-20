"""
Training script for Urdu tokenizer.
Uses word-level tokenizer (better suited for Urdu) by default.
"""

import os
from tokenizer.word_tokenizer import WordTokenizer


def main():
    # Load corpus
    corpus_file = "data/processed/corpus.txt"
    
    if not os.path.exists(corpus_file):
        print(f"Error: {corpus_file} not found.")
        print("Please run data/preprocess.py first to generate the corpus.")
        return
    
    print("Loading corpus...")
    with open(corpus_file, 'r', encoding='utf-8') as f:
        corpus = [line.strip() for line in f if line.strip()]
    
    print(f"Loaded {len(corpus)} stories")
    
    # Train word-level tokenizer (better for Urdu)
    tokenizer = WordTokenizer(min_freq=2, max_vocab_size=8000)
    tokenizer.train(corpus)
    
    # Save tokenizer
    os.makedirs("models", exist_ok=True)
    tokenizer.save("models/tokenizer.json")
    
    # Test encoding/decoding
    print("\n" + "=" * 60)
    print("Testing tokenizer...")
    print("=" * 60)
    
    test_text = corpus[0][:100] if corpus else "test"
    print(f"Original: {test_text}")
    
    encoded = tokenizer.encode(test_text)
    print(f"Encoded ({len(encoded)} tokens): {encoded[:20]}...")
    
    decoded = tokenizer.decode(encoded)
    print(f"Decoded: {decoded[:100]}")
    
    print("\nTokenizer training complete!")


if __name__ == "__main__":
    main()
