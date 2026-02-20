"""
Training script for trigram language model.
Works with both BPE and word tokenizers via tokenizer.loader.
"""

import os
from tokenizer.loader import load_tokenizer
from model.trigram import TrigramModel


def main():
    # Load tokenizer
    tokenizer_file = "models/tokenizer.json"
    if not os.path.exists(tokenizer_file):
        print(f"Error: {tokenizer_file} not found.")
        print("Please run train_tokenizer.py first to train the tokenizer.")
        return

    print("Loading tokenizer...")
    tokenizer = load_tokenizer(tokenizer_file)

    # Load corpus
    corpus_file = "data/processed/corpus.txt"
    if not os.path.exists(corpus_file):
        print(f"Error: {corpus_file} not found.")
        print("Please run data/preprocess.py first to generate the corpus.")
        return

    print("Loading corpus...")
    with open(corpus_file, "r", encoding="utf-8") as f:
        corpus = [line.strip() for line in f if line.strip()]

    print(f"Loaded {len(corpus)} stories")

    # Tokenize corpus
    print("Tokenizing corpus...")
    tokenized_corpus = []
    for i, story in enumerate(corpus):
        if (i + 1) % 50 == 0:
            print(f"  Tokenized {i + 1}/{len(corpus)} stories...")
        tokens = tokenizer.encode(story)
        if len(tokens) > 0:
            tokenized_corpus.append(tokens)

    print(f"Tokenized {len(tokenized_corpus)} stories")

    # Train trigram model
    print("\nTraining trigram model...")
    model = TrigramModel(lambda1=0.1, lambda2=0.3, lambda3=0.6)
    model.train(tokenized_corpus)

    # Save model
    os.makedirs("models", exist_ok=True)
    model.save("models/trigram.json")

    # Test generation
    print("\n" + "=" * 60)
    print("Testing generation...")
    print("=" * 60)

    # Test with a simple prefix
    test_prefix = "ایک"  # "One" in Urdu
    print(f"Test prefix: {test_prefix}")

    prefix_tokens = tokenizer.encode(test_prefix)
    print(f"Prefix tokens: {prefix_tokens}")

    generated_tokens = model.generate(prefix_tokens, max_length=100, temperature=1.0)
    generated_text = tokenizer.decode(generated_tokens)

    print(f"\nGenerated text ({len(generated_tokens)} tokens):")
    print(generated_text[:200])

    print("\nModel training complete!")


if __name__ == "__main__":
    main()
