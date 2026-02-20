"""
Trigram language model with Maximum Likelihood Estimation and interpolation.
"""

import json
import random
from collections import defaultdict
from typing import List, Dict, Tuple, Optional
import math


class TrigramModel:
    """
    Trigram language model with MLE and linear interpolation smoothing.
    """
    
    def __init__(self, lambda1: float = 0.1, lambda2: float = 0.3, lambda3: float = 0.6):
        """
        Initialize trigram model.
        
        Args:
            lambda1: Weight for unigram probability
            lambda2: Weight for bigram probability
            lambda3: Weight for trigram probability
        """
        # Normalize lambdas
        total = lambda1 + lambda2 + lambda3
        self.lambda1 = lambda1 / total
        self.lambda2 = lambda2 / total
        self.lambda3 = lambda3 / total
        
        # Count tables
        self.unigram_counts = defaultdict(int)
        self.bigram_counts = defaultdict(int)
        self.trigram_counts = defaultdict(int)
        
        # Total counts for normalization
        self.total_unigrams = 0
        self.bigram_contexts = defaultdict(int)  # count(w1, w2) for bigram contexts
        self.trigram_contexts = defaultdict(int)  # count(w1, w2) for trigram contexts
        
        # Vocabulary
        self.vocab = set()
        
    def train(self, tokenized_corpus: List[List[int]]):
        """
        Train trigram model on tokenized corpus.
        
        Args:
            tokenized_corpus: List of token sequences (each story as list of token IDs)
        """
        print("=" * 60)
        print("Training Trigram Language Model")
        print("=" * 60)
        
        # Count n-grams
        print("Counting n-grams...")
        for sequence in tokenized_corpus:
            if len(sequence) < 2:
                continue
            
            # Unigrams
            for token in sequence:
                self.unigram_counts[token] += 1
                self.total_unigrams += 1
                self.vocab.add(token)
            
            # Bigrams
            for i in range(len(sequence) - 1):
                bigram = (sequence[i], sequence[i + 1])
                self.bigram_counts[bigram] += 1
                self.bigram_contexts[sequence[i]] += 1
            
            # Trigrams
            for i in range(len(sequence) - 2):
                trigram = (sequence[i], sequence[i + 1], sequence[i + 2])
                self.trigram_counts[trigram] += 1
                bigram_context = (sequence[i], sequence[i + 1])
                self.trigram_contexts[bigram_context] += 1
        
        print(f"Vocabulary size: {len(self.vocab)}")
        print(f"Total unigrams: {self.total_unigrams}")
        print(f"Unique bigrams: {len(self.bigram_counts)}")
        print(f"Unique trigrams: {len(self.trigram_counts)}")
        print("=" * 60)
    
    def _unigram_prob(self, token: int) -> float:
        """Calculate unigram probability P(w)."""
        if self.total_unigrams == 0:
            return 0.0
        return self.unigram_counts[token] / self.total_unigrams
    
    def _bigram_prob(self, w1: int, w2: int) -> float:
        """Calculate bigram probability P(w2|w1)."""
        context_count = self.bigram_contexts[w1]
        if context_count == 0:
            return 0.0
        bigram_count = self.bigram_counts.get((w1, w2), 0)
        return bigram_count / context_count
    
    def _trigram_prob(self, w1: int, w2: int, w3: int) -> float:
        """Calculate trigram probability P(w3|w1,w2)."""
        context_count = self.trigram_contexts.get((w1, w2), 0)
        if context_count == 0:
            return 0.0
        trigram_count = self.trigram_counts.get((w1, w2, w3), 0)
        return trigram_count / context_count
    
    def prob(self, w1: int, w2: int, w3: int) -> float:
        """
        Calculate interpolated probability P(w3|w1,w2).
        
        Uses linear interpolation:
        P(w3|w1,w2) = λ3 * P_MLE(w3|w1,w2) + λ2 * P_MLE(w3|w2) + λ1 * P_MLE(w3)
        """
        p3 = self._trigram_prob(w1, w2, w3)
        p2 = self._bigram_prob(w2, w3)
        p1 = self._unigram_prob(w3)
        
        # Linear interpolation
        prob = (self.lambda3 * p3 + 
                self.lambda2 * p2 + 
                self.lambda1 * p1)
        
        return prob
    
    def generate_next_token(self, w1: int, w2: int, temperature: float = 1.0) -> int:
        """
        Generate next token given context (w1, w2).
        
        Args:
            w1: First token in context
            w2: Second token in context
            temperature: Sampling temperature (higher = more random)
            
        Returns:
            Next token ID
        """
        # Get probabilities for all possible next tokens
        # We consider tokens that appear in any trigram with (w1, w2) context
        # or fallback to all vocabulary if no trigrams found
        candidates = set()
        
        # Find candidates from trigrams
        for (t1, t2, t3) in self.trigram_counts.keys():
            if t1 == w1 and t2 == w2:
                candidates.add(t3)
        
        # If no candidates found, use bigram context
        if not candidates:
            for (t1, t2) in self.bigram_counts.keys():
                if t1 == w2:
                    candidates.add(t2)
        
        # If still no candidates, use all vocabulary
        if not candidates:
            candidates = self.vocab
        
        # Calculate probabilities for candidates
        probs = {}
        for candidate in candidates:
            prob = self.prob(w1, w2, candidate)
            if prob > 0:
                probs[candidate] = prob
        
        if not probs:
            # Fallback: return random token from vocabulary
            return random.choice(list(self.vocab))
        
        # Apply temperature
        if temperature != 1.0:
            for token in probs:
                probs[token] = probs[token] ** (1.0 / temperature)
        
        # Normalize
        total = sum(probs.values())
        if total == 0:
            return random.choice(list(self.vocab))
        
        for token in probs:
            probs[token] /= total
        
        # Sample
        tokens = list(probs.keys())
        weights = [probs[t] for t in tokens]
        
        return random.choices(tokens, weights=weights)[0]
    
    def generate(self, prefix: List[int], max_length: int = 500, 
                 eot_token: int = 2, temperature: float = 1.0) -> List[int]:
        """
        Generate story continuation from prefix.
        
        Args:
            prefix: Starting token sequence
            max_length: Maximum generation length
            eot_token: End-of-story token ID (default 2 for <EOT>)
            temperature: Sampling temperature
            
        Returns:
            Generated token sequence (including prefix)
        """
        generated = prefix.copy()
        
        if len(prefix) < 2:
            # Pad with special tokens if needed
            while len(generated) < 2:
                generated.insert(0, 0)  # Use EOS as padding
        
        # Generate until EOT or max_length
        while len(generated) < max_length:
            # Get last two tokens as context
            w1 = generated[-2]
            w2 = generated[-1]
            
            # Generate next token
            next_token = self.generate_next_token(w1, w2, temperature=temperature)
            generated.append(next_token)
            
            # Stop if EOT token generated
            if next_token == eot_token:
                break
        
        return generated
    
    def save(self, filepath: str):
        """Save model to file."""
        # Convert defaultdicts to regular dicts for JSON serialization
        data = {
            'lambda1': self.lambda1,
            'lambda2': self.lambda2,
            'lambda3': self.lambda3,
            'unigram_counts': dict(self.unigram_counts),
            'bigram_counts': {f"{k[0]},{k[1]}": v for k, v in self.bigram_counts.items()},
            'trigram_counts': {f"{k[0]},{k[1]},{k[2]}": v for k, v in self.trigram_counts.items()},
            'total_unigrams': self.total_unigrams,
            'bigram_contexts': dict(self.bigram_contexts),
            'trigram_contexts': {f"{k[0]},{k[1]}": v for k, v in self.trigram_contexts.items()},
            'vocab': list(self.vocab)
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
        
        print(f"Model saved to {filepath}")
    
    def load(self, filepath: str):
        """Load model from file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.lambda1 = data['lambda1']
        self.lambda2 = data['lambda2']
        self.lambda3 = data['lambda3']
        self.unigram_counts = defaultdict(int, data['unigram_counts'])
        self.bigram_counts = defaultdict(int, {
            tuple(map(int, k.split(','))): v for k, v in data['bigram_counts'].items()
        })
        self.trigram_counts = defaultdict(int, {
            tuple(map(int, k.split(','))): v for k, v in data['trigram_counts'].items()
        })
        self.total_unigrams = data['total_unigrams']
        self.bigram_contexts = defaultdict(int, data['bigram_contexts'])
        self.trigram_contexts = defaultdict(int, {
            tuple(map(int, k.split(','))): v for k, v in data['trigram_contexts'].items()
        })
        self.vocab = set(data['vocab'])
        
        print(f"Model loaded from {filepath}")
