"""
Custom Byte Pair Encoding (BPE) tokenizer implementation from scratch.
No external tokenizer libraries used.
"""

import json
import re
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Set


class BPETokenizer:
    """
    Custom BPE tokenizer implementation.
    Based on the original BPE algorithm by Sennrich et al.
    """
    
    def __init__(self, vocab_size: int = 250):
        """
        Initialize BPE tokenizer.
        
        Args:
            vocab_size: Target vocabulary size (including special tokens)
        """
        self.vocab_size = vocab_size
        self.vocab = {}  # token_id -> token_string
        self.vocab_inv = {}  # token_string -> token_id
        self.merges = []  # List of (token1, token2) pairs that were merged
        self.word_freqs = defaultdict(int)
        
        # Special tokens (reserved IDs 0, 1, 2)
        self.special_tokens = {
            '<EOS>': 0,  # End of Sentence
            '<EOP>': 1,  # End of Paragraph
            '<EOT>': 2,  # End of Story
        }
        
        self._initialize_special_tokens()
    
    def _initialize_special_tokens(self):
        """Initialize special tokens in vocabulary."""
        for token, token_id in self.special_tokens.items():
            self.vocab[token_id] = token
            self.vocab_inv[token] = token_id
    
    def _get_word_freqs(self, corpus: List[str]) -> Dict[str, int]:
        """Count word frequencies in corpus."""
        word_freqs = defaultdict(int)
        for text in corpus:
            # Split by whitespace to get words
            words = text.split()
            for word in words:
                word_freqs[word] += 1
        return word_freqs
    
    def _get_stats(self, splits: Dict[str, List[str]]) -> Dict[Tuple[str, str], int]:
        """Get statistics of pairs in the splits."""
        pairs = defaultdict(int)
        for word, word_splits in splits.items():
            for i in range(len(word_splits) - 1):
                pair = (word_splits[i], word_splits[i + 1])
                pairs[pair] += self.word_freqs[word]
        return pairs
    
    def _get_splits(self, word_freqs: Dict[str, int]) -> Dict[str, List[str]]:
        """Split words into characters (or subwords)."""
        splits = {}
        for word in word_freqs:
            # Split word into characters
            # For Urdu, we split by Unicode code points
            splits[word] = list(word)
        return splits
    
    def _merge_pair(self, pair: Tuple[str, str], splits: Dict[str, List[str]]) -> Dict[str, List[str]]:
        """Merge a pair of tokens in all splits."""
        new_splits = {}
        bigram = ''.join(pair)
        
        for word in splits:
            new_word = []
            i = 0
            word_splits = splits[word]
            
            while i < len(word_splits):
                # Try to find the pair
                if (i < len(word_splits) - 1 and 
                    word_splits[i] == pair[0] and 
                    word_splits[i + 1] == pair[1]):
                    new_word.append(bigram)
                    i += 2
                else:
                    new_word.append(word_splits[i])
                    i += 1
            
            new_splits[word] = new_word
        
        return new_splits
    
    def train(self, corpus: List[str]):
        """
        Train BPE tokenizer on corpus.
        
        Args:
            corpus: List of text strings (stories)
        """
        print("=" * 60)
        print("Training BPE Tokenizer")
        print("=" * 60)
        print(f"Corpus size: {len(corpus)} texts")
        print(f"Target vocabulary size: {self.vocab_size}")
        
        # Step 1: Get word frequencies
        print("\nStep 1: Counting word frequencies...")
        self.word_freqs = self._get_word_freqs(corpus)
        print(f"Unique words: {len(self.word_freqs)}")
        
        # Step 2: Initialize splits (character-level)
        print("\nStep 2: Initializing character-level splits...")
        splits = self._get_splits(self.word_freqs)
        
        # Step 3: Build initial vocabulary from characters
        print("\nStep 3: Building initial vocabulary...")
        char_vocab = set()
        for word_splits in splits.values():
            char_vocab.update(word_splits)
        
        # Add all characters to vocabulary
        current_vocab_size = len(self.special_tokens)
        for char in sorted(char_vocab):
            if char not in self.vocab_inv:
                self.vocab[current_vocab_size] = char
                self.vocab_inv[char] = current_vocab_size
                current_vocab_size += 1
        
        print(f"Initial vocabulary size: {current_vocab_size} (chars + special tokens)")
        
        # Step 4: Iteratively merge most frequent pairs
        print("\nStep 4: Merging pairs...")
        num_merges = self.vocab_size - current_vocab_size
        
        for i in range(num_merges):
            if i % 10 == 0:
                print(f"  Merge {i}/{num_merges}...")
            
            # Get pair statistics
            pairs = self._get_stats(splits)
            
            if not pairs:
                print(f"  No more pairs to merge at iteration {i}")
                break
            
            # Find most frequent pair
            best_pair = max(pairs, key=pairs.get)
            
            # Merge the pair
            splits = self._merge_pair(best_pair, splits)
            
            # Add merged token to vocabulary
            merged_token = ''.join(best_pair)
            if merged_token not in self.vocab_inv:
                self.vocab[current_vocab_size] = merged_token
                self.vocab_inv[merged_token] = current_vocab_size
                self.merges.append(best_pair)
                current_vocab_size += 1
            
            if current_vocab_size >= self.vocab_size:
                break
        
        print(f"\nTraining complete!")
        print(f"Final vocabulary size: {len(self.vocab)}")
        print(f"Number of merges: {len(self.merges)}")
        print("=" * 60)
    
    def _apply_bpe(self, word: str) -> List[str]:
        """Apply BPE encoding to a single word."""
        if word in self.special_tokens:
            return [word]
        
        # Start with character-level split
        splits = list(word)
        
        # Apply merges in order
        for pair in self.merges:
            new_splits = []
            i = 0
            while i < len(splits):
                if (i < len(splits) - 1 and 
                    splits[i] == pair[0] and 
                    splits[i + 1] == pair[1]):
                    new_splits.append(''.join(pair))
                    i += 2
                else:
                    new_splits.append(splits[i])
                    i += 1
            splits = new_splits
        
        return splits
    
    def encode(self, text: str) -> List[int]:
        """
        Encode text to token IDs.
        
        Args:
            text: Input text string
            
        Returns:
            List of token IDs
        """
        tokens = []
        words = text.split()
        
        for word in words:
            # Check if word is a special token
            if word in self.special_tokens:
                tokens.append(self.special_tokens[word])
            else:
                # Apply BPE to word
                subwords = self._apply_bpe(word)
                for subword in subwords:
                    if subword in self.vocab_inv:
                        tokens.append(self.vocab_inv[subword])
                    else:
                        # Fallback: use character-level encoding
                        for char in subword:
                            if char in self.vocab_inv:
                                tokens.append(self.vocab_inv[char])
        
        return tokens
    
    def decode(self, token_ids: List[int]) -> str:
        """
        Decode token IDs to text.
        
        Args:
            token_ids: List of token IDs
            
        Returns:
            Decoded text string
        """
        tokens = []
        for token_id in token_ids:
            if token_id in self.vocab:
                tokens.append(self.vocab[token_id])
            else:
                # Unknown token - skip or use placeholder
                tokens.append('<UNK>')
        
        # Join tokens (special tokens are already strings)
        text = ''.join(tokens)
        
        # Replace special tokens with spaces for readability (optional)
        # Or keep them as-is for model training
        
        return text
    
    def save(self, filepath: str):
        """Save tokenizer to file."""
        data = {
            'vocab_size': self.vocab_size,
            'vocab': {str(k): v for k, v in self.vocab.items()},
            'vocab_inv': self.vocab_inv,
            'merges': [list(pair) for pair in self.merges],
            'special_tokens': self.special_tokens
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"Tokenizer saved to {filepath}")
    
    def load(self, filepath: str):
        """Load tokenizer from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.vocab_size = data['vocab_size']
        self.vocab = {int(k): v for k, v in data['vocab'].items()}
        self.vocab_inv = data['vocab_inv']
        self.merges = [tuple(pair) for pair in data['merges']]
        self.special_tokens = data['special_tokens']
        
        print(f"Tokenizer loaded from {filepath}")
