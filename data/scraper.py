"""
Web scraper for Urdu children's stories from UrduPoint Kids.
Scrapes stories from urdupoint.com/kids/section/stories.html
"""

import requests
from bs4 import BeautifulSoup
import time
import os
import json
from urllib.parse import urljoin, urlparse
from typing import List, Dict
import re


class UrduStoryScraper:
    def __init__(self, base_url: str = "https://www.urdupoint.com/kids/section/stories.html", 
                 delay: float = 2.0, output_dir: str = "data/raw"):
        """
        Initialize the scraper.
        
        Args:
            base_url: Base URL for story listings
            delay: Delay between requests in seconds
            output_dir: Directory to save scraped data
        """
        self.base_url = base_url
        self.delay = delay
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        self.scraped_urls = set()
        self.stories = []
        
    def get_page(self, url: str) -> BeautifulSoup:
        """Fetch and parse a webpage."""
        try:
            time.sleep(self.delay)  # Polite delay
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_story_urls(self, soup: BeautifulSoup) -> List[str]:
        """Extract story URLs from a listing page."""
        urls = []
        if not soup:
            return urls
            
        # Look for story links - common patterns in UrduPoint
        # Try multiple selectors and patterns
        selectors = [
            'a[href*="/kids/stories/"]',
            'a[href*="/story/"]',
            'a[href*="/kids/"]',
            '.story-link',
            '.story-title a',
            'h2 a',
            'h3 a',
            'article a',
            '.content a',
            'a[href*="kahani"]',  # "story" in Urdu
            'a[href*="story"]'
        ]
        
        # Also try finding all links and filter
        all_links = soup.find_all('a', href=True)
        
        for link in all_links:
            href = link.get('href', '')
            if not href:
                continue
                
            full_url = urljoin(self.base_url, href)
            
            # Check if it's a story URL
            if any(pattern in full_url.lower() for pattern in [
                '/kids/stories/', '/story/', '/kids/', 'kahani'
            ]) and full_url not in self.scraped_urls:
                # Avoid non-story pages
                if not any(exclude in full_url.lower() for exclude in [
                    '/category/', '/section/', '/tag/', '?page=', '#'
                ]):
                    urls.append(full_url)
                    self.scraped_urls.add(full_url)
        
        return urls
    
    def extract_story_content(self, soup: BeautifulSoup, url: str) -> Dict:
        """Extract story content from a story page."""
        if not soup:
            return None
            
        story_data = {
            'url': url,
            'title': '',
            'content': '',
            'category': ''
        }
        
        # Extract title - try multiple selectors
        title_selectors = ['h1', '.story-title', '.title', 'article h1', 'main h1']
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                story_data['title'] = title_elem.get_text(strip=True)
                break
        
        # Extract main content - try multiple selectors
        content_selectors = [
            '.story-content',
            '.content',
            'article',
            '.story-text',
            '.post-content',
            'main article',
            '[class*="story"]',
            '[class*="content"]',
            '.entry-content',
            '#content',
            '.main-content',
            'main',
            'article p'
        ]
        
        content_text = []
        for selector in content_selectors:
            content_elems = soup.select(selector)
            for content_elem in content_elems:
                # Remove script and style elements
                for script in content_elem(["script", "style", "nav", "header", "footer", "aside", "form"]):
                    script.decompose()
                
                # Get text
                text = content_elem.get_text(separator='\n', strip=True)
                # Filter out very short or non-Urdu content
                if len(text) > 100 and any('\u0600' <= char <= '\u06FF' for char in text):
                    content_text.append(text)
                    break
            
            if content_text:
                break
        
        # Fallback: get all paragraph text
        if not content_text:
            paragraphs = soup.find_all('p')
            para_texts = []
            for p in paragraphs:
                text = p.get_text(strip=True)
                if len(text) > 20 and any('\u0600' <= char <= '\u06FF' for char in text):
                    para_texts.append(text)
            if para_texts:
                content_text.append('\n'.join(para_texts))
        
        if content_text:
            story_data['content'] = '\n'.join(content_text)
        
        # Extract category if available
        category_elem = soup.select_one('.category, .cat, [class*="category"]')
        if category_elem:
            story_data['category'] = category_elem.get_text(strip=True)
        
        return story_data if story_data['content'] else None
    
    def scrape_listing_pages(self, max_pages: int = 20) -> List[str]:
        """Scrape story URLs from listing pages."""
        all_urls = []
        
        # Try multiple category pages
        category_urls = [
            "https://www.urdupoint.com/kids/section/stories.html",
            "https://www.urdupoint.com/kids/category/moral-stories.html",
            "https://www.urdupoint.com/kids/category/true-stories.html",
            "https://www.urdupoint.com/kids/category/funny-stories.html",
            "https://www.urdupoint.com/kids/"
        ]
        
        for cat_url in category_urls:
            print(f"Scraping category page: {cat_url}")
            soup = self.get_page(cat_url)
            
            if soup:
                urls = self.extract_story_urls(soup)
                all_urls.extend(urls)
                print(f"Found {len(urls)} story URLs from this page (total: {len(all_urls)})")
        
        # Try pagination on main stories page
        page = 2
        while page <= max_pages and len(all_urls) < 200:
            url = f"{self.base_url}?page={page}"
            print(f"Scraping listing page {page}: {url}")
            soup = self.get_page(url)
            
            if not soup:
                break
            
            urls = self.extract_story_urls(soup)
            if not urls:
                break
            
            all_urls.extend(urls)
            print(f"Found {len(urls)} story URLs (total: {len(all_urls)})")
            page += 1
        
        return all_urls
    
    def scrape_stories(self, story_urls: List[str], min_stories: int = 200) -> List[Dict]:
        """Scrape content from story URLs."""
        stories = []
        
        for i, url in enumerate(story_urls, 1):
            if len(stories) >= min_stories:
                print(f"Reached target of {min_stories} stories")
                break
                
            print(f"Scraping story {i}/{len(story_urls)}: {url}")
            soup = self.get_page(url)
            
            story_data = self.extract_story_content(soup, url)
            if story_data and story_data['content']:
                stories.append(story_data)
                print(f"  ✓ Extracted: {story_data['title'][:50]}...")
            else:
                print(f"  ✗ Failed to extract content")
        
        return stories
    
    def save_stories(self, stories: List[Dict], filename: str = "stories.json"):
        """Save scraped stories to JSON file."""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(stories, f, ensure_ascii=False, indent=2)
        print(f"Saved {len(stories)} stories to {filepath}")
    
    def run(self, min_stories: int = 200, max_pages: int = 20):
        """Run the complete scraping process."""
        print("=" * 60)
        print("Starting Urdu Story Scraper")
        print("=" * 60)
        
        # Step 1: Get story URLs from listing pages
        print("\nStep 1: Collecting story URLs...")
        story_urls = self.scrape_listing_pages(max_pages=max_pages)
        print(f"Found {len(story_urls)} unique story URLs")
        
        if not story_urls:
            print("No story URLs found. Trying alternative approach...")
            # Try scraping directly from category pages
            category_urls = [
                "https://www.urdupoint.com/kids/category/moral-stories.html",
                "https://www.urdupoint.com/kids/category/true-stories.html",
                "https://www.urdupoint.com/kids/category/funny-stories.html"
            ]
            for cat_url in category_urls:
                soup = self.get_page(cat_url)
                if soup:
                    urls = self.extract_story_urls(soup)
                    story_urls.extend(urls)
            
            # If still no URLs, suggest using sample dataset
            if not story_urls:
                print("\n" + "=" * 60)
                print("WARNING: Could not scrape stories from website.")
                print("This might be due to:")
                print("1. Website structure has changed")
                print("2. Website is blocking requests")
                print("3. Network connectivity issues")
                print("\nAlternative options:")
                print("1. Run: python3 data/create_sample_dataset.py (for testing)")
                print("2. Manually download Urdu stories and save to data/raw/stories.json")
                print("3. Use alternative Urdu text corpus sources")
                print("=" * 60)
        
        # Step 2: Scrape story content
        print(f"\nStep 2: Scraping {min(len(story_urls), min_stories)} stories...")
        stories = self.scrape_stories(story_urls, min_stories=min_stories)
        
        # Step 3: Save results
        print(f"\nStep 3: Saving results...")
        self.save_stories(stories)
        
        print("\n" + "=" * 60)
        print(f"Scraping complete! Collected {len(stories)} stories")
        print("=" * 60)
        
        return stories


if __name__ == "__main__":
    scraper = UrduStoryScraper()
    stories = scraper.run(min_stories=200, max_pages=20)
