"""
Kneser–Ney smoothed n‑gram language model.

We use interpolated Kneser–Ney with a fixed discount D for all
orders, and support generic n (e.g. 3‑gram, 4‑gram).

This model is still fully "classical" (count‑based) but significantly
stronger than simple MLE + linear interpolation.
"""

from collections import defaultdict
from typing import Dict, List, Tuple, Iterable, Set
import json
import random


class KneserNeyNGramModel:
    """
    Interpolated Kneser–Ney n‑gram model.

    For n = 4, this builds 1‑gram, 2‑gram, 3‑gram, and 4‑gram counts
    and uses the standard recursive KN formulation:

        P_kn(w_n | h) = (max(c(h,w_n) - D, 0) / c(h))
                        + λ(h) * P_kn(w_n | h_tail)

    with λ(h) = D * N_1+(h ·) / c(h), and unigram probability based
    on continuation counts.
    """

    def __init__(self, n: int = 4, discount: float = 0.75) -> None:
        assert n >= 2, "n must be at least 2 for n‑gram model"
        self.n = n
        self.D = discount

        # counts[k][ngram_tuple] for k in 1..n
        self.counts: Dict[int, Dict[Tuple[int, ...], int]] = {
            k: defaultdict(int) for k in range(1, n + 1)
        }
        # context_counts[k][history_tuple] = count of history occurrences
        # for k >= 2 (history length = k-1)
        self.context_counts: Dict[int, Dict[Tuple[int, ...], int]] = {
            k: defaultdict(int) for k in range(2, n + 1)
        }
        # N_1+(h ·): number of distinct continuations after history h
        self.unique_cont_after: Dict[int, Dict[Tuple[int, ...], int]] = {
            k: defaultdict(int) for k in range(2, n + 1)
        }
        # For unigram continuation probability: N_1+(* w)
        self.unigram_continuation_counts: Dict[int, int] = defaultdict(int)
        self.total_unigram_continuations: int = 0

        self.vocab: Set[int] = set()

    # ------------------------------------------------------------------
    # Training
    # ------------------------------------------------------------------

    def train(self, tokenized_corpus: List[List[int]]) -> None:
        """
        Build n‑gram counts from tokenized corpus.

        Args:
            tokenized_corpus: list of token sequences (each story as list[int])
        """
        print("=" * 60)
        print(f"Training {self.n}-gram Kneser–Ney model")
        print("=" * 60)

        for seq in tokenized_corpus:
            if len(seq) == 0:
                continue
            # populate vocabulary
            for t in seq:
                self.vocab.add(t)

            L = len(seq)
            # 1‑grams
            for t in seq:
                self.counts[1][(t,)] += 1

            # higher‑order n‑grams
            for k in range(2, self.n + 1):
                if L < k:
                    break
                for i in range(L - k + 1):
                    ngram = tuple(seq[i : i + k])
                    history = ngram[:-1]
                    w = ngram[-1]
                    self.counts[k][ngram] += 1
                    self.context_counts[k][history] += 1

        # Build continuation statistics
        # For each k‑gram (k>=2), increment unique continuation count for history
        for k in range(2, self.n + 1):
            seen_pairs = set()
            for ngram, c in self.counts[k].items():
                if c <= 0:
                    continue
                history = ngram[:-1]
                w = ngram[-1]
                key = (history, w)
                if key not in seen_pairs:
                    seen_pairs.add(key)
                    self.unique_cont_after[k][history] += 1

        # Unigram continuation counts from bigrams
        seen_bigram_pairs = set()
        for (w1, w2), c in self.counts[2].items():
            if c <= 0:
                continue
            key = (w1, w2)
            if key not in seen_bigram_pairs:
                seen_bigram_pairs.add(key)
                self.unigram_continuation_counts[w2] += 1

        self.total_unigram_continuations = sum(
            self.unigram_continuation_counts.values()
        )

        print(f"Vocabulary size: {len(self.vocab)}")
        print(f"Total unigrams: {sum(self.counts[1].values())}")
        print(f"Unique bigrams: {len(self.counts[2])}")
        if self.n >= 3:
            print(f"Unique trigrams: {len(self.counts[3])}")
        if self.n >= 4:
            print(f"Unique 4-grams: {len(self.counts[4])}")
        print("=" * 60)

    # ------------------------------------------------------------------
    # Probability computation (Interpolated Kneser–Ney)
    # ------------------------------------------------------------------

    def _p_cont_unigram(self, w: int) -> float:
        """Continuation probability for unigram KN."""
        if self.total_unigram_continuations == 0:
            # uniform fallback
            return 1.0 / max(len(self.vocab), 1)
        return self.unigram_continuation_counts[w] / self.total_unigram_continuations

    def _prob_recursive(self, history: Tuple[int, ...], w: int, order: int) -> float:
        """
        Recursive interpolated Kneser–Ney probability.

        history: tuple of previous tokens (length <= order-1)
        order: current n‑gram order to use
        """
        # Base case: unigram KN P(w)
        if order == 1:
            return self._p_cont_unigram(w)

        # If history is longer than order-1, keep only last order-1 tokens
        if len(history) > order - 1:
            history = history[-(order - 1) :]

        # If history shorter than order-1, back off to lower order
        if len(history) < order - 1:
            return self._prob_recursive(history, w, order - 1)

        # Now len(history) == order-1
        counts_k = self.counts[order]
        ctx_counts_k = self.context_counts[order]
        N1plus_after = self.unique_cont_after[order]

        hist_count = ctx_counts_k.get(history, 0)
        if hist_count == 0:
            # No evidence for this history, back off
            return self._prob_recursive(history[1:], w, order - 1)

        ngram = history + (w,)
        c_hw = counts_k.get(ngram, 0)

        # First term: discounted MLE
        numer = max(c_hw - self.D, 0.0)
        p_ml = numer / hist_count

        # Backoff weight λ(h)
        cont_count = N1plus_after.get(history, 0)
        lambda_h = (self.D * cont_count) / hist_count if hist_count > 0 else 0.0

        # Recursive lower‑order probability
        p_lower = self._prob_recursive(history[1:], w, order - 1)

        return p_ml + lambda_h * p_lower

    def prob(self, history: List[int], w: int) -> float:
        """
        Public probability interface.

        history: list of previous tokens
        w: next token
        """
        if not self.vocab:
            return 0.0
        hist_tuple: Tuple[int, ...] = tuple(history[-(self.n - 1) :]) if history else ()
        return self._prob_recursive(hist_tuple, w, self.n)

    # ------------------------------------------------------------------
    # Generation
    # ------------------------------------------------------------------

    def generate_next_token(
        self, history: List[int], temperature: float = 1.0
    ) -> int:
        """
        Sample next token given history using KN probabilities.

        history: list of previous tokens (we use last n-1 tokens)
        """
        if not self.vocab:
            raise ValueError("Model vocabulary is empty; train the model first.")

        # Compute probabilities for all vocab tokens
        probs = {}
        for w in self.vocab:
            p = self.prob(history, w)
            if p > 0.0:
                probs[w] = p

        if not probs:
            # Fallback uniform over vocab
            return random.choice(list(self.vocab))

        # Apply temperature
        if temperature != 1.0:
            for w in probs:
                probs[w] = probs[w] ** (1.0 / max(temperature, 1e-8))

        total = sum(probs.values())
        if total <= 0.0:
            return random.choice(list(self.vocab))

        for w in probs:
            probs[w] /= total

        tokens = list(probs.keys())
        weights = [probs[w] for w in tokens]
        return random.choices(tokens, weights=weights)[0]

    def generate(
        self,
        prefix: List[int],
        max_length: int = 500,
        eot_token: int = 2,
        temperature: float = 1.0,
    ) -> List[int]:
        """
        Generate a sequence, starting from prefix, until <EOT> or max_length.
        """
        if not self.vocab:
            raise ValueError("Model vocabulary is empty; train the model first.")

        generated = prefix.copy()

        # If prefix shorter than n‑1, it's fine; prob() handles shorter history
        while len(generated) < max_length:
            history = generated[-(self.n - 1) :] if generated else []
            next_token = self.generate_next_token(history, temperature=temperature)
            generated.append(next_token)
            if next_token == eot_token:
                break

        return generated

    # ------------------------------------------------------------------
    # Save / Load
    # ------------------------------------------------------------------

    def save(self, filepath: str) -> None:
        data = {
            "n": self.n,
            "discount": self.D,
            "counts": {
                str(k): {" ".join(map(str, ngram)): c for ngram, c in d.items()}
                for k, d in self.counts.items()
            },
            "context_counts": {
                str(k): {" ".join(map(str, h)): c for h, c in d.items()}
                for k, d in self.context_counts.items()
            },
            "unique_cont_after": {
                str(k): {" ".join(map(str, h)): c for h, c in d.items()}
                for k, d in self.unique_cont_after.items()
            },
            "unigram_continuation_counts": {
                str(w): c for w, c in self.unigram_continuation_counts.items()
            },
            "total_unigram_continuations": self.total_unigram_continuations,
            "vocab": list(self.vocab),
        }
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Kneser–Ney {self.n}-gram model saved to {filepath}")

    def load(self, filepath: str) -> None:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.n = int(data.get("n", self.n))
        self.D = float(data.get("discount", self.D))

        # Restore counts
        self.counts = {k: defaultdict(int) for k in range(1, self.n + 1)}
        for k_str, d in data["counts"].items():
            k = int(k_str)
            for key_str, c in d.items():
                ngram = tuple(int(x) for x in key_str.split()) if key_str else tuple()
                self.counts[k][ngram] = int(c)

        self.context_counts = {k: defaultdict(int) for k in range(2, self.n + 1)}
        for k_str, d in data["context_counts"].items():
            k = int(k_str)
            for key_str, c in d.items():
                hist = tuple(int(x) for x in key_str.split()) if key_str else tuple()
                self.context_counts[k][hist] = int(c)

        self.unique_cont_after = {k: defaultdict(int) for k in range(2, self.n + 1)}
        for k_str, d in data["unique_cont_after"].items():
            k = int(k_str)
            for key_str, c in d.items():
                hist = tuple(int(x) for x in key_str.split()) if key_str else tuple()
                self.unique_cont_after[k][hist] = int(c)

        self.unigram_continuation_counts = defaultdict(
            int,
            {int(w_str): int(c) for w_str, c in data["unigram_continuation_counts"].items()},
        )
        self.total_unigram_continuations = int(data["total_unigram_continuations"])
        self.vocab = set(int(x) for x in data["vocab"])

        print(f"Kneser–Ney {self.n}-gram model loaded from {filepath}")

