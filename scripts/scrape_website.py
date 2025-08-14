#!/usr/bin/env python3
"""
Script to scrape website content and upload it to Pinecone.
Usage: python scripts/scrape_website.py --url "https://example.com" --source-name "website-name"
"""

import os
import sys
import argparse
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import re
import unicodedata
from pathlib import Path
from typing import List, Dict, Any

# Add the parent directory to the path so we can import app modules
sys.path.append(str(Path(__file__).parent.parent))

from app.services.openai_service import OpenAIService
from app.services.pinecone_service import PineconeService
from app.config import settings

class WebsiteScraper:
    def __init__(self):
        self.openai_service = OpenAIService()
        self.pinecone_service = PineconeService()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def clean_text(self, text: str) -> str:
        """Clean and normalize text content"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Remove common HTML artifacts
        text = re.sub(r'&[a-zA-Z]+;', '', text)
        
        # Remove script and style content
        text = re.sub(r'<script.*?</script>', '', text, flags=re.DOTALL)
        text = re.sub(r'<style.*?</style>', '', text, flags=re.DOTALL)
        
        return text
    
    def create_clean_id(self, text: str, max_length: int = 50) -> str:
        """Create a clean ASCII ID from text"""
        # Normalize unicode characters
        text = unicodedata.normalize('NFKD', text)
        
        # Convert to ASCII, replacing non-ASCII with spaces
        text = ''.join(c if ord(c) < 128 else ' ' for c in text)
        
        # Remove special characters and extra spaces
        text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
        text = re.sub(r'\s+', '_', text.strip())
        
        # Limit length
        if len(text) > max_length:
            text = text[:max_length]
        
        # Remove trailing underscores
        text = text.rstrip('_')
        
        return text.lower()
    
    def extract_text_from_html(self, html: str) -> str:
        """Extract clean text from HTML content"""
        soup = BeautifulSoup(html, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Get text content
        text = soup.get_text()
        
        # Clean the text
        text = self.clean_text(text)
        
        return text
    
    def scrape_webpage(self, url: str) -> Dict[str, Any]:
        """Scrape a single webpage"""
        try:
            print(f"Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            # Extract text content
            text_content = self.extract_text_from_html(response.text)
            
            # Get page title
            soup = BeautifulSoup(response.text, 'html.parser')
            title = soup.find('title')
            page_title = title.get_text().strip() if title else "Untitled"
            
            # Skip pages that appear to be non-English
            if any(lang in page_title.lower() for lang in [
                'albanian', 'amharic', 'arabic', 'bengali', 'bosnian',
                'chinese', 'dutch', 'finnish', 'french', 'german',
                'hindi', 'indonesian', 'malay', 'persian', 'oromo',
                'russian', 'swedish', 'somali', 'tamil', 'telugu',
                'thai', 'turkish', 'urdu', 'bangla', 'bahasa',
                'suomi', 'svenska', 'shqip', 'amargna', 'soomaali',
                'farsi', 'bosanski'
            ]) and 'allah' not in page_title.lower():
                print(f"Skipping non-English page: {page_title}")
                return {
                    "url": url,
                    "title": page_title,
                    "content": "",
                    "status": "skipped"
                }
            
            return {
                "url": url,
                "title": page_title,
                "content": text_content,
                "status": "success"
            }
            
        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return {
                "url": url,
                "title": "Error",
                "content": "",
                "status": "error",
                "error": str(e)
            }
    
    def find_links(self, html: str, base_url: str) -> List[str]:
        """Find all links on a webpage"""
        soup = BeautifulSoup(html, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)
            
            # Only include links to the same domain
            if urlparse(full_url).netloc == urlparse(base_url).netloc:
                # Filter out non-English language pages
                if not any(lang in full_url.lower() for lang in [
                    '/albanian/', '/amharic/', '/arabic/', '/bengali/', '/bosnian/',
                    '/chinese/', '/dutch/', '/finnish/', '/french/', '/german/',
                    '/hindi/', '/indonesian/', '/malay/', '/persian/', '/oromo/',
                    '/russian/', '/swedish/', '/somali/', '/tamil/', '/telugu/',
                    '/thai/', '/turkish/', '/urdu/', '/bangla/', '/bahasa/',
                    '/suomi/', '/svenska/', '/shqip/', '/amargna/', '/soomaali/',
                    '/farsi/', '/telugu/', '/thai/', '/bosanski/', '/french/',
                    '/russian/', '/bangla/', '/bahasa/', '/chinese/'
                ]):
                    links.append(full_url)
        
        return list(set(links))  # Remove duplicates
    
    def scrape_website(self, base_url: str, max_pages: int = 10) -> List[Dict[str, Any]]:
        """Scrape multiple pages from a website"""
        scraped_pages = []
        visited_urls = set()
        urls_to_visit = [base_url]
        
        while urls_to_visit and len(scraped_pages) < max_pages:
            current_url = urls_to_visit.pop(0)
            
            if current_url in visited_urls:
                continue
            
            visited_urls.add(current_url)
            
            # Scrape the current page
            page_data = self.scrape_webpage(current_url)
            if page_data["status"] == "success" and page_data["content"]:
                scraped_pages.append(page_data)
                
                # Find more links if we haven't reached the limit
                if len(scraped_pages) < max_pages:
                    try:
                        response = self.session.get(current_url, timeout=10)
                        new_links = self.find_links(response.text, current_url)
                        urls_to_visit.extend([link for link in new_links if link not in visited_urls])
                    except:
                        pass
            
            print(f"Scraped {len(scraped_pages)}/{max_pages} pages")
        
        return scraped_pages
    
    async def process_website_content(self, pages: List[Dict[str, Any]], source_name: str) -> List[Dict[str, Any]]:
        """Process scraped website content and prepare for Pinecone"""
        all_documents = []
        
        for page in pages:
            if page["status"] != "success" or not page["content"]:
                continue
            
            # Split content into chunks
            chunks = self.openai_service.chunk_text(page["content"])
            
            # Generate embeddings for chunks
            embeddings = await self.openai_service.get_embeddings(chunks)
            
            # Prepare documents for Pinecone
            for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
                clean_title = self.create_clean_id(page['title'])
                doc_id = f"{source_name}_{clean_title}_{i}_{hash(page['url']) % 10000}"
                
                all_documents.append({
                    "id": doc_id,
                    "text": chunk,
                    "embedding": embedding,
                    "source": source_name,
                    "url": page["url"],
                    "title": page["title"],
                    "chunk_index": i
                })
        
        return all_documents
    
    async def upload_to_pinecone(self, documents: List[Dict[str, Any]]) -> bool:
        """Upload documents to Pinecone"""
        if not documents:
            print("No documents to upload")
            return False
        
        print(f"Uploading {len(documents)} document chunks to Pinecone...")
        
        try:
            # Upload in batches to avoid rate limits
            batch_size = 100
            for i in range(0, len(documents), batch_size):
                batch = documents[i:i + batch_size]
                await self.pinecone_service.upsert_documents(batch)
                print(f"  Uploaded batch {i//batch_size + 1}/{(len(documents) + batch_size - 1)//batch_size}")
            
            print("Upload completed successfully!")
            return True
        except Exception as e:
            print(f"Error uploading documents: {str(e)}")
            return False

async def main():
    parser = argparse.ArgumentParser(description="Scrape website content and upload to Pinecone")
    parser.add_argument("--url", required=True, help="Website URL to scrape")
    parser.add_argument("--source-name", required=True, help="Source name for the documents")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum number of pages to scrape")
    parser.add_argument("--dry-run", action="store_true", help="Process content but don't upload to Pinecone")
    
    args = parser.parse_args()
    
    # Validate environment variables
    if not settings.openai_api_key:
        print("Error: OPENAI_API_KEY not set in environment")
        sys.exit(1)
    
    if not settings.pinecone_api_key:
        print("Error: PINECONE_API_KEY not set in environment")
        sys.exit(1)
    
    if not settings.pinecone_environment:
        print("Error: PINECONE_ENVIRONMENT not set in environment")
        sys.exit(1)
    
    scraper = WebsiteScraper()
    
    # Scrape website
    print(f"Scraping website: {args.url}")
    pages = scraper.scrape_website(args.url, args.max_pages)
    
    if not pages:
        print("No content found to process")
        sys.exit(1)
    
    print(f"Scraped {len(pages)} pages")
    
    # Process content
    documents = await scraper.process_website_content(pages, args.source_name)
    
    if not documents:
        print("No documents to process")
        sys.exit(1)
    
    print(f"Processed {len(documents)} document chunks")
    
    if args.dry_run:
        print("Dry run mode - documents not uploaded to Pinecone")
        return
    
    # Upload to Pinecone
    success = await scraper.upload_to_pinecone(documents)
    
    if success:
        print("Website content successfully uploaded to Pinecone!")
    else:
        sys.exit(1)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 