"""
Word-level tokenizer for Urdu text.
Better suited for Urdu than BPE: Urdu uses spaces between words, and word-level
tokens provide cleaner trigram context for the language model.
"""

import json
import re
from collections import Counter
from typing import List, Dict, Set


class WordTokenizer:
    """
    Word-level tokenizer for Urdu.
    Each word (space-separated unit) maps to a single token ID.
    Handles punctuation attached to words.
    """
    
    def __init__(self, min_freq: int = 2, max_vocab_size: int = 8000):
        """
        Initialize word tokenizer.
        
        Args:
            min_freq: Minimum frequency for a word to be in vocabulary
            max_vocab_size: Maximum vocabulary size (including special tokens)
        """
        self.min_freq = min_freq
        self.max_vocab_size = max_vocab_size
        self.vocab = {}  # token_id -> word
        self.vocab_inv = {}  # word -> token_id
        
        # Special tokens (reserved IDs 0-3)
        self.special_tokens = {
            '<EOS>': 0,   # End of Sentence
            '<EOP>': 1,   # End of Paragraph  
            '<EOT>': 2,   # End of Story
            '<UNK>': 3,   # Unknown word
        }
        
        self._initialize_special_tokens()
    
    def _initialize_special_tokens(self):
        """Initialize special tokens in vocabulary."""
        for token, token_id in self.special_tokens.items():
            self.vocab[token_id] = token
            self.vocab_inv[token] = token_id
    
    def _tokenize_text(self, text: str) -> List[str]:
        """
        Split text into words, preserving punctuation as part of words.
        Urdu words are typically separated by spaces.
        Handles special tokens (EOS, EOP, EOT) that may be attached to words.
        """
        text = text.strip()
        if not text:
            return []
        
        words = re.split(r'\s+', text)
        result = []
        
        for w in words:
            w = w.strip()
            if not w:
                continue
            # Split off trailing special tokens (Unicode PUA)
            while w.endswith('\uE003') or w.endswith('\uE002') or w.endswith('\uE001'):
                if w.endswith('\uE003'):
                    result.append('<EOT>')
                    w = w[:-1]
                elif w.endswith('\uE002'):
                    result.append('<EOP>')
                    w = w[:-1]
                elif w.endswith('\uE001'):
                    result.append('<EOS>')
                    w = w[:-1]
            if w == '\uE001':
                result.append('<EOS>')
            elif w == '\uE002':
                result.append('<EOP>')
            elif w == '\uE003':
                result.append('<EOT>')
            elif w:
                result.append(w)
        
        return result
    
    def train(self, corpus: List[str]):
        """
        Train word tokenizer on corpus.
        Build vocabulary from most frequent words.
        
        Args:
            corpus: List of text strings (stories)
        """
        print("=" * 60)
        print("Training Word-Level Tokenizer for Urdu")
        print("=" * 60)
        print(f"Corpus size: {len(corpus)} texts")
        print(f"Min frequency: {self.min_freq}, Max vocab: {self.max_vocab_size}")
        
        # Count word frequencies
        word_counts = Counter()
        for text in corpus:
            words = self._tokenize_text(text)
            word_counts.update(words)
        
        # Filter out special tokens from counting
        for st in self.special_tokens:
            word_counts.pop(st, None)
            word_counts.pop('\uE001', None)
            word_counts.pop('\uE002', None)
            word_counts.pop('\uE003', None)
        
        # Build vocabulary: special tokens + most frequent words meeting min_freq
        current_id = len(self.special_tokens)
        sorted_words = sorted(
            word_counts.items(),
            key=lambda x: (-x[1], x[0])
        )
        
        for word, count in sorted_words:
            if count >= self.min_freq and current_id < self.max_vocab_size:
                if word not in self.vocab_inv:
                    self.vocab[current_id] = word
                    self.vocab_inv[word] = current_id
                    current_id += 1
        
        print(f"Vocabulary size: {len(self.vocab)}")
        print(f"Words in vocab: {len(self.vocab) - len(self.special_tokens)}")
        print("=" * 60)
    
    def encode(self, text: str) -> List[int]:
        """
        Encode text to token IDs.
        
        Args:
            text: Input text string
            
        Returns:
            List of token IDs
        """
        words = self._tokenize_text(text)
        tokens = []
        unk_id = self.special_tokens['<UNK>']
        
        for word in words:
            if word in self.vocab_inv:
                tokens.append(self.vocab_inv[word])
            else:
                tokens.append(unk_id)
        
        return tokens
    
    def decode(self, token_ids: List[int]) -> str:
        """
        Decode token IDs to text.
        Joins words with spaces for proper Urdu formatting.
        
        Args:
            token_ids: List of token IDs
            
        Returns:
            Decoded text string
        """
        words = []
        for tid in token_ids:
            if tid in self.vocab:
                token_str = self.vocab[tid]
                if token_str == '<EOT>':
                    break
                if token_str in ('<EOS>', '<EOP>', '<UNK>'):
                    continue  # Omit from display
                words.append(token_str)
            # Skip unknown IDs
        return ' '.join(words)
    
    def save(self, filepath: str):
        """Save tokenizer to file."""
        data = {
            'type': 'word',
            'min_freq': self.min_freq,
            'max_vocab_size': self.max_vocab_size,
            'vocab': {str(k): v for k, v in self.vocab.items()},
            'vocab_inv': self.vocab_inv,
            'special_tokens': self.special_tokens
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"Tokenizer saved to {filepath}")
    
    def load(self, filepath: str):
        """Load tokenizer from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.min_freq = data.get('min_freq', 2)
        self.max_vocab_size = data.get('max_vocab_size', 8000)
        self.vocab = {int(k): v for k, v in data['vocab'].items()}
        self.vocab_inv = data['vocab_inv']
        self.special_tokens = data['special_tokens']
        print(f"Tokenizer loaded from {filepath}")
