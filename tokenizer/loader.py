"""
Tokenizer loader - loads the appropriate tokenizer from saved JSON.
Supports both BPE and Word tokenizers for backward compatibility.
"""

import json
from typing import Union

from tokenizer.bpe import BPETokenizer
from tokenizer.word_tokenizer import WordTokenizer


def load_tokenizer(filepath: str) -> Union[BPETokenizer, WordTokenizer]:
    """
    Load tokenizer from JSON file.
    Detects tokenizer type from the saved file.
    
    Args:
        filepath: Path to tokenizer JSON file
        
    Returns:
        Loaded tokenizer (BPETokenizer or WordTokenizer)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    tokenizer_type = data.get('type', 'bpe')
    
    if tokenizer_type == 'word':
        tokenizer = WordTokenizer()
        tokenizer.load(filepath)
        return tokenizer
    else:
        tokenizer = BPETokenizer()
        tokenizer.load(filepath)
        return tokenizer
