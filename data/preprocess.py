"""
Preprocessing pipeline for Urdu story corpus.
Handles cleaning, normalization, and special token insertion.
Produces cleaner Urdu text for better model training.
"""

import json
import re
import unicodedata
from typing import List, Dict, Set
import os


# Special tokens using Unicode Private Use Area
EOS_TOKEN = '\uE001'  # End of Sentence
EOP_TOKEN = '\uE002'  # End of Paragraph
EOT_TOKEN = '\uE003'  # End of Story

# Minimum Urdu character ratio to keep a story (EOS/special tokens dilute ratio)
MIN_URDU_RATIO = 0.45
# Minimum story length (chars) after cleaning
MIN_STORY_LENGTH = 80
# Minimum word count per story
MIN_WORD_COUNT = 15


class UrduPreprocessor:
    def __init__(self):
        """Initialize the preprocessor."""
        # Urdu Unicode ranges
        self.urdu_range = (
            (0x0600, 0x06FF),  # Arabic block (includes Urdu)
            (0x0750, 0x077F),  # Arabic Supplement
            (0x08A0, 0x08FF),  # Arabic Extended-A
            (0xFB50, 0xFDFF),  # Arabic Presentation Forms-A
            (0xFE70, 0xFEFF),  # Arabic Presentation Forms-B
        )
        
        # Allowed punctuation (basic punctuation marks)
        self.allowed_punctuation = set([
            '.', '!', '?', ',', ';', ':', '-', '–', '—', 
            '(', ')', '[', ']', '{', '}', '"', "'", '،', '۔', '؟', '؛'
        ])
        
        # Whitespace characters
        self.whitespace = set([' ', '\t', '\n', '\r', '\u2000', '\u2001', '\u2002', '\u2003', '\u2004', '\u2005', '\u2006', '\u2007', '\u2008', '\u2009', '\u200A', '\u200B', '\u200C', '\u200D'])
    
    def is_urdu_char(self, char: str) -> bool:
        """Check if character is in Urdu Unicode range."""
        code = ord(char)
        for start, end in self.urdu_range:
            if start <= code <= end:
                return True
        return False
    
    def is_allowed_char(self, char: str) -> bool:
        """Check if character should be kept (Urdu, punctuation, or whitespace)."""
        if char in self.whitespace:
            return True
        if char in self.allowed_punctuation:
            return True
        if self.is_urdu_char(char):
            return True
        return False
    
    def remove_html_tags(self, text: str) -> str:
        """Remove HTML tags and entities."""
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        # Decode HTML entities
        text = text.replace('&nbsp;', ' ')
        text = text.replace('&amp;', '&')
        text = text.replace('&lt;', '<')
        text = text.replace('&gt;', '>')
        text = text.replace('&quot;', '"')
        text = text.replace('&#39;', "'")
        return text
    
    def remove_non_urdu(self, text: str) -> str:
        """Remove non-Urdu characters while preserving Urdu script and basic punctuation."""
        result = []
        for char in text:
            if self.is_allowed_char(char):
                result.append(char)
        return ''.join(result)
    
    def remove_zero_width_chars(self, text: str) -> str:
        """Remove zero-width and control characters that cause display issues."""
        # Zero-width: U+200B, U+200C, U+200D, U+FEFF, U+00A0 (NBSP) as space
        text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
        text = text.replace('\u00A0', ' ')  # NBSP -> space
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)  # Control chars
        return text
    
    def remove_english_blocks(self, text: str) -> str:
        """Remove large blocks of English/Latin text."""
        # Split on whitespace, filter out tokens that are mostly ASCII
        words = text.split()
        cleaned = []
        for w in words:
            ascii_count = sum(1 for c in w if ord(c) < 128)
            if len(w) > 0 and ascii_count / len(w) < 0.5:  # Keep if mostly non-ASCII
                cleaned.append(w)
            elif len(w) <= 2:  # Keep short tokens (could be punctuation)
                cleaned.append(w)
        return ' '.join(cleaned)
    
    def get_urdu_ratio(self, text: str) -> float:
        """Calculate ratio of Urdu/Arabic script characters."""
        if not text:
            return 0.0
        urdu_count = sum(1 for c in text if self.is_urdu_char(c) or c in '۔،؟')
        return urdu_count / len(text)
    
    def normalize_unicode(self, text: str) -> str:
        """Normalize Unicode to NFC form."""
        return unicodedata.normalize('NFC', text)
    
    def standardize_punctuation(self, text: str) -> str:
        """Standardize punctuation marks."""
        # Map various dash types to standard dash
        text = text.replace('–', '-')  # En dash
        text = text.replace('—', '-')  # Em dash
        text = text.replace('…', '...')  # Ellipsis
        
        # Standardize quotes
        text = text.replace('"', '"').replace('"', '"')
        text = text.replace(''', "'").replace(''', "'")
        
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """Normalize whitespace."""
        # Replace all whitespace characters with regular space
        for ws in self.whitespace:
            if ws != ' ':
                text = text.replace(ws, ' ')
        
        # Collapse multiple spaces
        text = re.sub(r' +', ' ', text)
        
        # Trim
        text = text.strip()
        
        return text
    
    def insert_special_tokens(self, text: str) -> str:
        """Insert special tokens for sentence, paragraph, and story boundaries."""
        # Replace multiple newlines (paragraph breaks) with EOP
        text = re.sub(r'\n\s*\n+', EOP_TOKEN, text)
        
        # Replace single newlines with space (they're usually just line breaks)
        text = text.replace('\n', ' ')
        
        # Insert EOS after sentence-ending punctuation only
        # Use Urdu full stop ۔ as primary; avoid ASCII ? which can corrupt output
        sentence_endings = ['۔', '.', '!', '؟']  # Exclude ASCII ? to prevent corruption
        for ending in sentence_endings:
            text = re.sub(rf'{re.escape(ending)}(\s+|$)', f'{ending}{EOS_TOKEN} ', text)
        
        return text
    
    def preprocess_story(self, story_text: str) -> str:
        """Preprocess a single story - cleaner Urdu output."""
        # Step 1: Remove HTML
        text = self.remove_html_tags(story_text)
        
        # Step 2: Remove zero-width and control chars early
        text = self.remove_zero_width_chars(text)
        
        # Step 3: Remove large English blocks
        text = self.remove_english_blocks(text)
        
        # Step 4: Remove non-Urdu characters
        text = self.remove_non_urdu(text)
        
        # Step 5: Normalize Unicode
        text = self.normalize_unicode(text)
        
        # Step 6: Standardize punctuation
        text = self.standardize_punctuation(text)
        
        # Step 7: Normalize whitespace
        text = self.normalize_whitespace(text)
        
        # Step 8: Insert special tokens
        text = self.insert_special_tokens(text)
        
        # Step 9: Final cleanup - allowed chars only
        text = re.sub(r'[^\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF\uE000-\uE003\s\.\,\!\?\-\(\)\[\]\{\}\"\'\u060C\u06D4\u061F\u061B]', '', text)
        
        return text.strip()
    
    def process_stories(self, stories: List[Dict], output_file: str = "data/processed/corpus.txt"):
        """Process all stories and create corpus file. Deduplicates and filters for quality."""
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        processed_stories = []
        seen_hashes: Set[int] = set()
        
        print("=" * 60)
        print("Preprocessing Urdu Stories (Clean)")
        print("=" * 60)
        
        for i, story in enumerate(stories, 1):
            title = story.get('title', 'Untitled')[:50]
            print(f"Processing story {i}/{len(stories)}: {title}...")
            
            content = story.get('content', '')
            if not content:
                print(f"  ✗ Skipping: No content")
                continue
            
            processed = self.preprocess_story(content)
            
            # Deduplicate by content hash
            content_hash = hash(processed[:500])
            if content_hash in seen_hashes:
                print(f"  ✗ Skipping: Duplicate")
                continue
            seen_hashes.add(content_hash)
            
            # Quality filters
            if len(processed) < MIN_STORY_LENGTH:
                print(f"  ✗ Skipping: Too short ({len(processed)} chars)")
                continue
            
            urdu_ratio = self.get_urdu_ratio(processed)
            if urdu_ratio < MIN_URDU_RATIO:
                print(f"  ✗ Skipping: Low Urdu ratio ({urdu_ratio:.1%})")
                continue
            
            word_count = len([w for w in processed.split() if w and w not in (EOS_TOKEN, EOP_TOKEN, EOT_TOKEN)])
            if word_count < MIN_WORD_COUNT:
                print(f"  ✗ Skipping: Too few words ({word_count})")
                continue
            
            processed = processed.rstrip() + ' ' + EOT_TOKEN
            processed_stories.append(processed)
            print(f"  ✓ Processed: {len(processed)} chars, {word_count} words")
        
        print(f"\nWriting corpus to {output_file}...")
        with open(output_file, 'w', encoding='utf-8') as f:
            for story in processed_stories:
                f.write(story + '\n')
        
        print(f"\nPreprocessing complete!")
        print(f"Processed {len(processed_stories)} unique stories (from {len(stories)} input)")
        print(f"Corpus saved to {output_file}")
        print("=" * 60)
        
        return processed_stories


if __name__ == "__main__":
    # Load scraped stories
    input_file = "data/raw/stories.json"
    
    if not os.path.exists(input_file):
        print(f"Error: {input_file} not found. Please run scraper.py first.")
        exit(1)
    
    with open(input_file, 'r', encoding='utf-8') as f:
        stories = json.load(f)
    
    # Merge curated classic stories (fox, etc.) for better generation
    curated_file = "data/curated_classic_stories.json"
    if os.path.exists(curated_file):
        with open(curated_file, 'r', encoding='utf-8') as f:
            curated = json.load(f)
        stories = curated + stories
        print(f"Merged {len(curated)} curated stories for better animal story generation\n")
    
    # Preprocess
    preprocessor = UrduPreprocessor()
    preprocessor.process_stories(stories)
