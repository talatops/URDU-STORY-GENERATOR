"""
Multi-platform scraper for Urdu children's stories.
Scrapes from multiple sources to collect diverse stories.
"""

import requests
from bs4 import BeautifulSoup
import time
import os
import json
from urllib.parse import urljoin, urlparse
from typing import List, Dict, Optional
import re


class MultiPlatformUrduScraper:
    """Scraper for multiple Urdu story platforms."""
    
    def __init__(self, delay: float = 1.5, output_dir: str = "data/raw"):
        """Initialize multi-platform scraper."""
        self.delay = delay
        self.output_dir = output_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        })
        
        os.makedirs(output_dir, exist_ok=True)
        self.scraped_urls = set()
        self.stories = []
        
    def get_page(self, url: str) -> Optional[BeautifulSoup]:
        """Fetch and parse a webpage."""
        try:
            time.sleep(self.delay)
            response = self.session.get(url, timeout=15, allow_redirects=True)
            response.raise_for_status()
            # Try different encodings
            try:
                response.encoding = 'utf-8'
            except:
                pass
            return BeautifulSoup(response.content, 'html.parser')
        except Exception as e:
            print(f"  Error fetching {url}: {e}")
            return None
    
    def scrape_urdupoint(self, min_stories: int = 100) -> List[Dict]:
        """Scrape from UrduPoint Kids with pagination and deep crawling."""
        print("\n" + "="*60)
        print("Scraping from UrduPoint Kids")
        print("="*60)
        
        stories = []
        base_url = "https://www.urdupoint.com/kids"
        
        # Try category pages with pagination
        category_urls = [
            f"{base_url}/category/moral-stories.html",
            f"{base_url}/category/true-stories.html",
            f"{base_url}/category/funny-stories.html",
            f"{base_url}/section/stories.html",
        ]
        
        all_urls = set()
        
        # Collect URLs from multiple pages
        for cat_url in category_urls:
            print(f"\nChecking: {cat_url}")
            
            # Try pagination (up to 50 pages per category)
            for page in range(1, 51):
                if page == 1:
                    url = cat_url
                else:
                    # Try different pagination patterns
                    url = cat_url.replace('.html', f'-{page}.html')
                    if url == cat_url:
                        url = f"{cat_url}?page={page}"
                
                soup = self.get_page(url)
                if not soup:
                    if page > 1:
                        break  # No more pages
                    continue
                
                links = soup.find_all('a', href=True)
                page_urls = 0
                
                for link in links:
                    href = link.get('href', '')
                    full_url = urljoin(url, href)
                    
                    # Look for story detail pages
                    is_detail = '/detail/' in full_url.lower()
                    is_story = any(x in full_url.lower() for x in [
                        '/kids/detail/', '/story/', '/kids/stories/'
                    ])
                    is_excluded = any(x in full_url.lower() for x in [
                        '/category/', '/section/', '/tag/', '/video', '/poem',
                        '/joke', '/puzzel', '/recipe', '/urdu-videos'
                    ])
                    
                    if is_detail and is_story and not is_excluded:
                        if full_url not in self.scraped_urls:
                            all_urls.add(full_url)
                            page_urls += 1
                
                print(f"  Page {page}: Found {page_urls} new story URLs (total: {len(all_urls)})")
                
                # If no new URLs found on this page, try next category
                if page_urls == 0 and page > 1:
                    break
        
        print(f"\nFound {len(all_urls)} total story URLs from UrduPoint")
        
        # Scrape stories (prioritize detail pages)
        detail_urls = [u for u in all_urls if '/detail/' in u.lower()]
        other_urls = [u for u in all_urls if '/detail/' not in u.lower()]
        sorted_urls = detail_urls + other_urls
        
        print(f"Scraping {min(len(sorted_urls), min_stories * 3)} URLs...")
        
        for i, url in enumerate(sorted_urls[:min_stories * 3], 1):
            if len(stories) >= min_stories:
                break
                
            if url in self.scraped_urls:
                continue
                
            if i % 10 == 0:
                print(f"  Progress: {i}/{min(len(sorted_urls), min_stories * 3)} URLs, {len(stories)} stories collected")
            
            soup = self.get_page(url)
            
            if soup:
                story = self.extract_urdupoint_story(soup, url)
                if story and story.get('content'):
                    stories.append(story)
                    self.scraped_urls.add(url)
                    if i % 5 == 0:  # Print every 5th story
                        print(f"    ✓ [{len(stories)}] {story.get('title', 'Untitled')[:50]}")
        
        print(f"\n✓ Collected {len(stories)} stories from UrduPoint")
        return stories
    
    def extract_urdupoint_story(self, soup: BeautifulSoup, url: str) -> Optional[Dict]:
        """Extract story from UrduPoint page."""
        story = {'url': url, 'title': '', 'content': '', 'source': 'urdupoint'}
        
        # Title
        title_selectors = ['h1', '.story-title', '.title', 'article h1', 'main h1', 'h2']
        for sel in title_selectors:
            elem = soup.select_one(sel)
            if elem:
                title = elem.get_text(strip=True)
                if title and len(title) > 5:
                    story['title'] = title
                    break
        
        # Content
        content_selectors = [
            '.story-content', '.content', 'article', '.story-text',
            '.post-content', 'main article', '[class*="story"]',
            '[class*="content"]', '.entry-content', '#content'
        ]
        
        for sel in content_selectors:
            elems = soup.select(sel)
            for elem in elems:
                # Clean
                for tag in elem(["script", "style", "nav", "header", "footer", "aside", "form", "iframe"]):
                    tag.decompose()
                
                text = elem.get_text(separator='\n', strip=True)
                # Check if it's Urdu content
                urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
                if len(text) > 150 and urdu_chars > len(text) * 0.3:
                    story['content'] = text
                    return story
        
        # Fallback: paragraphs
        paragraphs = soup.find_all('p')
        para_texts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
            if len(text) > 30 and urdu_chars > len(text) * 0.2:
                para_texts.append(text)
        
        if para_texts:
            story['content'] = '\n'.join(para_texts)
            return story
        
        return None
    
    def scrape_urdu_com(self, min_stories: int = 50) -> List[Dict]:
        """Scrape from Urdu.com directory (if accessible)."""
        print("\n" + "="*60)
        print("Scraping from Urdu.com")
        print("="*60)
        
        stories = []
        base_url = "https://urdu.com/bachon_ki_kahaniyan.html"
        
        print(f"Checking: {base_url}")
        soup = self.get_page(base_url)
        
        if soup:
            # Find links to story pages
            links = soup.find_all('a', href=True)
            story_urls = set()
            
            for link in links:
                href = link.get('href', '')
                text = link.get_text(strip=True)
                
                # Look for story-related links
                if any(x in text.lower() for x in ['کہانی', 'story', 'kahani']) or \
                   any(x in href.lower() for x in ['story', 'kahani', 'bachon']):
                    full_url = urljoin(base_url, href)
                    if full_url not in self.scraped_urls:
                        story_urls.add(full_url)
            
            print(f"Found {len(story_urls)} potential story links")
            
            # Scrape stories
            for i, url in enumerate(list(story_urls)[:min_stories*2], 1):
                if len(stories) >= min_stories:
                    break
                    
                print(f"  [{i}/{min(len(story_urls), min_stories*2)}] {url[:60]}...")
                soup = self.get_page(url)
                
                if soup:
                    story = self.extract_generic_story(soup, url, 'urdu.com')
                    if story and story.get('content'):
                        stories.append(story)
                        self.scraped_urls.add(url)
                        print(f"    ✓ {story.get('title', 'Untitled')[:40]}")
        
        print(f"\n✓ Collected {len(stories)} stories from Urdu.com")
        return stories
    
    def extract_generic_story(self, soup: BeautifulSoup, url: str, source: str) -> Optional[Dict]:
        """Generic story extraction for unknown sites."""
        story = {'url': url, 'title': '', 'content': '', 'source': source}
        
        # Title
        for sel in ['h1', 'h2', '.title', '.story-title', 'title']:
            elem = soup.select_one(sel)
            if elem:
                title = elem.get_text(strip=True)
                if title and len(title) > 5:
                    story['title'] = title
                    break
        
        # Content - try multiple strategies
        content_selectors = [
            'article', '.content', '.story-content', '.post-content',
            'main', '.entry-content', '#content', '[class*="story"]'
        ]
        
        for sel in content_selectors:
            elems = soup.select(sel)
            for elem in elems:
                for tag in elem(["script", "style", "nav", "header", "footer", "aside", "form"]):
                    tag.decompose()
                
                text = elem.get_text(separator='\n', strip=True)
                urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
                
                if len(text) > 150 and urdu_chars > len(text) * 0.25:
                    story['content'] = text
                    return story
        
        # Fallback: all paragraphs
        paragraphs = soup.find_all('p')
        para_texts = []
        for p in paragraphs:
            text = p.get_text(strip=True)
            urdu_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
            if len(text) > 30 and urdu_chars > len(text) * 0.2:
                para_texts.append(text)
        
        if para_texts and len('\n'.join(para_texts)) > 100:
            story['content'] = '\n'.join(para_texts)
            return story
        
        return None
    
    def scrape_virtual_urdu(self, min_stories: int = 30) -> List[Dict]:
        """Scrape from Virtual Urdu (NYU)."""
        print("\n" + "="*60)
        print("Scraping from Virtual Urdu (NYU)")
        print("="*60)
        
        stories = []
        base_url = "https://wp.nyu.edu/virtualurdu/children-stories/"
        
        print(f"Checking: {base_url}")
        soup = self.get_page(base_url)
        
        if soup:
            # Find story links
            links = soup.find_all('a', href=True)
            story_urls = set()
            
            for link in links:
                href = link.get('href', '')
                if 'virtualurdu' in href and ('story' in href.lower() or 'children' in href.lower()):
                    full_url = urljoin(base_url, href)
                    if full_url not in self.scraped_urls:
                        story_urls.add(full_url)
            
            print(f"Found {len(story_urls)} potential story links")
            
            for i, url in enumerate(list(story_urls)[:min_stories*2], 1):
                if len(stories) >= min_stories:
                    break
                    
                print(f"  [{i}/{min(len(story_urls), min_stories*2)}] {url[:60]}...")
                soup = self.get_page(url)
                
                if soup:
                    story = self.extract_generic_story(soup, url, 'virtualurdu')
                    if story and story.get('content'):
                        stories.append(story)
                        self.scraped_urls.add(url)
                        print(f"    ✓ {story.get('title', 'Untitled')[:40]}")
        
        print(f"\n✓ Collected {len(stories)} stories from Virtual Urdu")
        return stories
    
    def run(self, target_stories: int = 300):
        """Run multi-platform scraping."""
        print("="*70)
        print("Multi-Platform Urdu Story Scraper")
        print("="*70)
        print(f"Target: {target_stories} stories")
        print("="*70)
        
        all_stories = []
        
        # Scrape from multiple platforms (UrduPoint + Virtual Urdu only; Urdu.com is unreliable)
        try:
            # UrduPoint: Try to get most stories (aim for 80% of target)
            urdupoint_target = int(target_stories * 0.8)
            print(f"\nTargeting {urdupoint_target} stories from UrduPoint...")
            stories = self.scrape_urdupoint(min_stories=urdupoint_target)
            all_stories.extend(stories)
            print(f"✓ Collected {len(stories)} stories from UrduPoint")
        except Exception as e:
            print(f"Error scraping UrduPoint: {e}")
            import traceback
            traceback.print_exc()

        if len(all_stories) < target_stories:
            remaining = target_stories - len(all_stories)
            try:
                print(f"\nTargeting {remaining} more stories from Virtual Urdu...")
                stories = self.scrape_virtual_urdu(min_stories=min(100, remaining))
                all_stories.extend(stories)
                print(f"✓ Collected {len(stories)} stories from Virtual Urdu")
            except Exception as e:
                print(f"Error scraping Virtual Urdu: {e}")
                import traceback
                traceback.print_exc()
        
        # If still not enough, try UrduPoint again with more aggressive settings
        if len(all_stories) < target_stories:
            remaining = target_stories - len(all_stories)
            print(f"\nNeed {remaining} more stories. Trying UrduPoint again with more pages...")
            try:
                stories = self.scrape_urdupoint(min_stories=remaining)
                all_stories.extend(stories)
            except Exception as e:
                print(f"Error in second UrduPoint pass: {e}")
        
        # Remove duplicates based on content similarity
        unique_stories = []
        seen_content = set()
        
        for story in all_stories:
            content_hash = hash(story.get('content', '')[:200])  # First 200 chars
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                unique_stories.append(story)
        
        # Save results
        output_file = os.path.join(self.output_dir, "stories.json")
        
        # Load existing stories if any
        existing_stories = []
        if os.path.exists(output_file):
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_stories = json.load(f)
            except:
                pass
        
        # Merge and deduplicate
        all_unique = existing_stories + unique_stories
        final_stories = []
        final_content_hashes = set()
        
        for story in all_unique:
            content_hash = hash(story.get('content', '')[:200])
            if content_hash not in final_content_hashes:
                final_content_hashes.add(content_hash)
                final_stories.append(story)
        
        # Save
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(final_stories, f, ensure_ascii=False, indent=2)
        
        print("\n" + "="*70)
        print(f"Scraping Complete!")
        print(f"Total unique stories collected: {len(final_stories)}")
        print(f"Saved to: {output_file}")
        print("="*70)
        
        return final_stories


if __name__ == "__main__":
    import sys
    
    # Parse command line arguments
    target_stories = 2000  # Default to 2000
    delay = 1.0  # Faster delay for large scraping
    
    if len(sys.argv) > 1:
        try:
            target_stories = int(sys.argv[1])
        except ValueError:
            print(f"Invalid number: {sys.argv[1]}. Using default: 2000")
    
    if len(sys.argv) > 2:
        try:
            delay = float(sys.argv[2])
        except ValueError:
            print(f"Invalid delay: {sys.argv[2]}. Using default: 1.0")
    
    print(f"Starting scraper with target: {target_stories} stories, delay: {delay}s")
    print("This may take a while...")
    
    scraper = MultiPlatformUrduScraper(delay=delay)
    stories = scraper.run(target_stories=target_stories)
