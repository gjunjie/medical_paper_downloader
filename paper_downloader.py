"""
PMC Paper Downloader

This script searches PubMed Central (PMC) and downloads the top k papers in PDF format.
"""

import os
import re
import time
import urllib.parse
from pathlib import Path
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError


def download_pmc_papers(search_term: str, k: int = 5, download_dir: str = "downloads", headless: bool = True):
    """
    Search PMC and download the top k papers in PDF format.
    
    Args:
        search_term: The search term (e.g., "vitamin c")
        k: Number of top papers to download (default: 5)
        download_dir: Directory to save downloaded PDFs (default: "downloads")
        headless: Whether to run browser in headless mode (default: True)
    
    Returns:
        List of downloaded file paths
    """
    # Create download directory if it doesn't exist
    download_path = Path(download_dir)
    download_path.mkdir(exist_ok=True)
    
    # Construct search URL
    encoded_term = urllib.parse.quote(search_term)
    search_url = f"https://pmc.ncbi.nlm.nih.gov/search/?term={encoded_term}"
    
    downloaded_files = []
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            accept_downloads=True,
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            }
        )
        page = context.new_page()
        
        try:
            print(f"Searching PMC for: {search_term}")
            print(f"Search URL: {search_url}")
            
            # Navigate to search results
            page.goto(search_url, wait_until="networkidle", timeout=5000)
            time.sleep(1)  # Wait for page to fully load
            
            # Find all result links
            # PMC search results typically have links with class or data attributes
            # We'll look for links that contain PMC IDs
            result_links = []
            
            # Try multiple selectors to find result links
            selectors = [
                'a[href*="/articles/PMC"]',
                'a[href*="pmc/articles"]',
                '.result-item a',
                '.rprt a',
                'a[data-article-id]'
            ]
            
            for selector in selectors:
                links = page.query_selector_all(selector)
                if links:
                    for link in links:
                        href = link.get_attribute('href')
                        if href and ('PMC' in href or '/articles/' in href):
                            # Make absolute URL if needed
                            if href.startswith('/'):
                                href = f"https://pmc.ncbi.nlm.nih.gov{href}"
                            elif not href.startswith('http'):
                                href = f"https://pmc.ncbi.nlm.nih.gov/{href}"
                            
                            if href not in result_links:
                                result_links.append(href)
                    if result_links:
                        break
            
            # If no links found with selectors, try to find by text pattern
            if not result_links:
                print("Trying alternative method to find results...")
                # Look for any links that might be article links
                all_links = page.query_selector_all('a')
                for link in all_links:
                    href = link.get_attribute('href')
                    if href and ('/articles/PMC' in href or 'pmc/articles' in href):
                        if href.startswith('/'):
                            href = f"https://pmc.ncbi.nlm.nih.gov{href}"
                        elif not href.startswith('http'):
                            href = f"https://pmc.ncbi.nlm.nih.gov/{href}"
                        if href not in result_links:
                            result_links.append(href)
            
            if not result_links:
                print("No results found. The page structure might have changed.")
                print("Page title:", page.title())
                # Save page for debugging
                page.screenshot(path="debug_search_page.png")
                return downloaded_files
            
            # Limit to top k results
            result_links = result_links[:k]
            print(f"Found {len(result_links)} result(s) to process")
            
            # Process each result
            for i, article_url in enumerate(result_links, 1):
                try:
                    print(f"\n[{i}/{len(result_links)}] Processing: {article_url}")
                    
                    # Extract PMC ID from article URL
                    # URL format: https://pmc.ncbi.nlm.nih.gov/articles/PMC7681026
                    pmc_id = article_url.split('/')[-1] if '/' in article_url else None
                    
                    # Navigate to article page
                    page.goto(article_url, wait_until="networkidle", timeout=5000)
                    time.sleep(1)
                    
                    # Look for PDF link that follows the pattern: /articles/{PMC_ID}/pdf/{filename}.pdf
                    # Example: https://pmc.ncbi.nlm.nih.gov/articles/PMC7681026/pdf/zbc15870.pdf
                    pdf_link = None
                    
                    # Priority 1: Look for PDF link with the exact pattern /articles/{PMC_ID}/pdf/{filename}.pdf
                    if pmc_id:
                        # Try exact pattern first: /articles/PMC7681026/pdf/
                        pdf_links = page.query_selector_all(f'a[href*="/articles/{pmc_id}/pdf/"]')
                        if not pdf_links:
                            # Also try without "PMC" prefix in case URL format differs
                            pmc_num = pmc_id.replace('PMC', '') if pmc_id.startswith('PMC') else pmc_id
                            pdf_links = page.query_selector_all(f'a[href*="/articles/{pmc_num}/pdf/"]')
                        
                        if pdf_links:
                            for link in pdf_links:
                                href = link.get_attribute('href')
                                if href:
                                    # Normalize the href to full URL
                                    if href.startswith('/'):
                                        full_href = f"https://pmc.ncbi.nlm.nih.gov{href}"
                                    elif not href.startswith('http'):
                                        full_href = f"https://pmc.ncbi.nlm.nih.gov/{href}"
                                    else:
                                        full_href = href
                                    
                                    # Check if it matches the pattern /articles/{PMC_ID}/pdf/{filename}.pdf
                                    if f'/articles/{pmc_id}/pdf/' in full_href and full_href.endswith('.pdf'):
                                        pdf_link = full_href
                                        break
                                    # Also check pattern with just the number
                                    elif pmc_id.startswith('PMC'):
                                        pmc_num = pmc_id.replace('PMC', '')
                                        if f'/articles/{pmc_num}/pdf/' in full_href and full_href.endswith('.pdf'):
                                            pdf_link = full_href
                                            break
                                    # If it contains the pattern but might be missing .pdf extension
                                    elif f'/articles/{pmc_id}/pdf/' in full_href:
                                        pdf_link = full_href
                                        break
                        
                        # Also look for links with text "PDF" that might have the pattern
                        if not pdf_link:
                            pdf_text_links = page.query_selector_all('a:has-text("PDF"), a:has-text("pdf")')
                            for link in pdf_text_links:
                                href = link.get_attribute('href')
                                if href and f'/articles/{pmc_id}/pdf/' in href:
                                    if href.startswith('/'):
                                        pdf_link = f"https://pmc.ncbi.nlm.nih.gov{href}"
                                    elif not href.startswith('http'):
                                        pdf_link = f"https://pmc.ncbi.nlm.nih.gov/{href}"
                                    else:
                                        pdf_link = href
                                    break
                    
                    # Priority 2: If we found a PDF link but it's not in the full pattern, try to construct it
                    # Some pages use links like /pdf/filename.pdf or https://pmc.ncbi.nlm.nih.gov/pdf/filename.pdf
                    # We want to use the pattern: /articles/{PMC_ID}/pdf/{filename}.pdf
                    if not pdf_link and pmc_id:
                        # Look for any PDF link and try to construct the full path
                        all_pdf_links = page.query_selector_all('a[href*=".pdf"], a[href*="/pdf/"]')
                        for link in all_pdf_links:
                            href = link.get_attribute('href')
                            if href and href.endswith('.pdf'):
                                # Extract filename from any format
                                filename = href.split('/')[-1]
                                
                                # If the link doesn't already follow the /articles/{PMC_ID}/pdf/ pattern,
                                # construct it using the full pattern
                                if f'/articles/{pmc_id}/pdf/' not in href:
                                    # Construct the full pattern: /articles/{PMC_ID}/pdf/{filename}
                                    constructed_url = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc_id}/pdf/{filename}"
                                    pdf_link = constructed_url
                                    break
                                # If it already contains the PMC ID in the correct pattern, use it
                                elif f'/articles/{pmc_id}/pdf/' in href:
                                    if href.startswith('/'):
                                        pdf_link = f"https://pmc.ncbi.nlm.nih.gov{href}"
                                    elif not href.startswith('http'):
                                        pdf_link = f"https://pmc.ncbi.nlm.nih.gov/{href}"
                                    else:
                                        pdf_link = href
                                    break
                    
                    # Priority 3: Fallback - look for any PDF link on the page and construct full path if needed
                    if not pdf_link and pmc_id:
                        pdf_button_selectors = [
                            'a[href*="/pdf/"]',
                            'a[href$=".pdf"]',
                            'a[href*=".pdf"]',
                            'a:has-text("PDF")',
                            'a[title*="PDF"]',
                            'a[title*="pdf"]'
                        ]
                        
                        for selector in pdf_button_selectors:
                            try:
                                element = page.query_selector(selector)
                                if element:
                                    href = element.get_attribute('href')
                                    if href and href.endswith('.pdf'):
                                        # Extract filename
                                        filename = href.split('/')[-1]
                                        # Always construct using the full pattern: /articles/{PMC_ID}/pdf/{filename}
                                        pdf_link = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc_id}/pdf/{filename}"
                                        break
                            except:
                                continue
                    
                    # Download the PDF
                    if pdf_link:
                        try:
                            print(f"  Found PDF link: {pdf_link}")
                            
                            # Extract filename from URL
                            filename = pdf_link.split('/')[-1]
                            if not filename.endswith('.pdf'):
                                filename = f"{pmc_id or f'paper_{i}'}.pdf"
                            
                            # PMC PDFs require clicking the link to trigger download
                            # Try multiple methods to download the PDF
                            pdf_downloaded = False
                            
                            # Method 1: Try to find and click the PDF link on the article page
                            pdf_link_selectors = [
                                f'a[href*="/articles/{pmc_id}/pdf/"]',
                                f'a[href*="/pdf/"]',
                                'a:has-text("PDF")',
                                'a[href$=".pdf"]'
                            ]
                            
                            for selector in pdf_link_selectors:
                                try:
                                    pdf_element = page.query_selector(selector)
                                    if pdf_element:
                                        # Scroll element into view
                                        pdf_element.scroll_into_view_if_needed()
                                        time.sleep(0.3)
                                        # Click the link and wait for download
                                        with page.expect_download(timeout=5000) as download_info:
                                            pdf_element.click()
                                        download = download_info.value
                                        
                                        # Get suggested filename or use extracted one
                                        suggested_filename = download.suggested_filename
                                        if suggested_filename and suggested_filename.endswith('.pdf'):
                                            filename = suggested_filename
                                        
                                        file_path = download_path / filename
                                        download.save_as(file_path)
                                        downloaded_files.append(str(file_path))
                                        print(f"  ✓ Downloaded: {file_path}")
                                        pdf_downloaded = True
                                        break
                                except (PlaywrightTimeoutError, Exception):
                                    continue
                            
                            # Method 2: Use request API with proper headers to follow redirects
                            if not pdf_downloaded:
                                try:
                                    # Set headers to mimic a browser request
                                    response = context.request.get(
                                        pdf_link,
                                        headers={
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                                            'Accept': 'application/pdf,application/octet-stream,*/*'
                                        },
                                        timeout=5000
                                    )
                                    
                                    if response.ok:
                                        body = response.body()
                                        # Check if it's actually a PDF
                                        if body.startswith(b'%PDF'):
                                            file_path = download_path / filename
                                            with open(file_path, 'wb') as f:
                                                f.write(body)
                                            downloaded_files.append(str(file_path))
                                            print(f"  ✓ Downloaded: {file_path}")
                                            pdf_downloaded = True
                                except Exception as req_error:
                                    pass
                            
                            # Method 3: Try direct navigation with download event
                            if not pdf_downloaded:
                                try:
                                    with page.expect_download(timeout=5000) as download_info:
                                        page.goto(pdf_link, wait_until="networkidle", timeout=5000)
                                    download = download_info.value
                                    file_path = download_path / filename
                                    download.save_as(file_path)
                                    downloaded_files.append(str(file_path))
                                    print(f"  ✓ Downloaded: {file_path}")
                                    pdf_downloaded = True
                                except (PlaywrightTimeoutError, Exception):
                                    pass
                            
                            if not pdf_downloaded:
                                raise Exception("All download methods failed")
                                    
                        except Exception as e:
                            print(f"  ✗ Error downloading PDF: {e}")
                    else:
                        print(f"  ✗ Could not find PDF link for article {i}")
                    
                    # Small delay between downloads
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"  ✗ Error processing article {i}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error during search/download process: {e}")
        finally:
            browser.close()
    
    print(f"\n✓ Download complete! {len(downloaded_files)} file(s) downloaded to {download_dir}/")
    return downloaded_files


def download_pubmed_free_fulltext_papers(search_term: str, k: int = 5, download_dir: str = "downloads", headless: bool = True):
    """
    Search PubMed and download PDFs from PMC.
    
    Workflow:
    1. Search PubMed with the search term
    2. Extract PubMed links (PMID) for each paper
    3. Navigate to each PubMed page to get the PMCID
    4. Navigate to PMC article page using the PMCID
    5. Download the PDF from PMC
    
    Args:
        search_term: The search term (e.g., "probiotics oral health")
        k: Number of top papers to download (default: 5)
        download_dir: Directory to save downloaded PDFs (default: "downloads")
        headless: Whether to run browser in headless mode (default: True)
    
    Returns:
        List of downloaded file paths
    """
    # Create download directory if it doesn't exist
    download_path = Path(download_dir)
    download_path.mkdir(exist_ok=True)
    
    # Construct PubMed search URL
    encoded_term = urllib.parse.quote(search_term)
    search_url = f"https://pubmed.ncbi.nlm.nih.gov/?term={encoded_term}"
    
    downloaded_files = []
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=headless)
        context = browser.new_context(
            accept_downloads=True,
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            extra_http_headers={
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
                "Sec-Fetch-Dest": "document",
                "Sec-Fetch-Mode": "navigate",
                "Sec-Fetch-Site": "none",
                "Sec-Fetch-User": "?1",
            }
        )
        page = context.new_page()
        
        try:
            print(f"Searching PubMed for: {search_term}")
            print(f"Search URL: {search_url}")
            print("Navigating to PubMed...")
            
            # Navigate to PubMed search results
            try:
                page.goto(search_url, wait_until="networkidle", timeout=15000)
            except Exception as nav_error:
                print(f"Navigation timeout, trying with load state...")
                page.goto(search_url, wait_until="load", timeout=15000)
            time.sleep(3)  # Wait for page to fully load
            print(f"Page loaded. Title: {page.title()}")
            print(f"Current URL: {page.url}")
            
            # Wait for results to load - look for result items
            try:
                page.wait_for_selector('.docsum-content, .rprt, article, [class*="result"]', timeout=10000)
            except:
                print("Warning: Results may not have loaded completely")
            
            # Find all PubMed result links (PMID links)
            # PubMed result links typically look like: /28390121/ or https://pubmed.ncbi.nlm.nih.gov/28390121/
            pubmed_links = []
            
            # Try multiple selectors to find result links - updated for current PubMed structure
            selectors = [
                '.docsum-title a',  # Most common selector for PubMed results
                'a.docsum-title',   # Alternative class format
                '.rprt a',          # Alternative result format
                'article a',        # Article tag links
                'a[href*="/pubmed/"]',  # Links containing /pubmed/
                'a[href^="/"]',     # Any link starting with /
            ]
            
            for selector in selectors:
                try:
                    links = page.query_selector_all(selector)
                    if links:
                        print(f"Found {len(links)} links with selector: {selector}")
                        for link in links:
                            href = link.get_attribute('href')
                            if href:
                                # Extract PMID from various URL patterns
                                # Patterns: /28390121/, /pubmed/28390121/, https://pubmed.ncbi.nlm.nih.gov/28390121/
                                pmid_match = re.search(r'/(\d{6,})/?$', href) or re.search(r'pubmed[^/]*/(\d{6,})', href)
                                if pmid_match:
                                    pmid = pmid_match.group(1)
                                    pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                                    if pubmed_url not in pubmed_links:
                                        pubmed_links.append(pubmed_url)
                        if pubmed_links:
                            print(f"Successfully extracted {len(pubmed_links)} PubMed links")
                            break
                except Exception as e:
                    continue
            
            # Alternative method: look for any links with numeric IDs that match PMID pattern
            if not pubmed_links:
                print("Trying alternative method to find PubMed links...")
                all_links = page.query_selector_all('a[href]')
                print(f"Found {len(all_links)} total links on page")
                for link in all_links:
                    href = link.get_attribute('href')
                    if href:
                        # Look for patterns like /12345678/ or /pubmed/12345678/ or pubmed.ncbi.nlm.nih.gov/12345678/
                        # PMIDs are typically 6-8 digits
                        pmid_match = re.search(r'/(\d{6,})/?$', href) or re.search(r'pubmed[^/]*/(\d{6,})', href)
                        if pmid_match:
                            pmid = pmid_match.group(1)
                            # Validate it's a reasonable PMID (not a year or other number)
                            if len(pmid) >= 6 and len(pmid) <= 8:
                                pubmed_url = f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/"
                                if pubmed_url not in pubmed_links:
                                    pubmed_links.append(pubmed_url)
                                    if len(pubmed_links) >= k * 2:  # Get extra to filter
                                        break
            
            if not pubmed_links:
                print("No PubMed results found. The page structure might have changed.")
                print("Page title:", page.title())
                print("Page URL:", page.url)
                # Save page for debugging
                page.screenshot(path="debug_pubmed_search_page.png")
                # Also save HTML for inspection
                with open("debug_pubmed_search_page.html", "w", encoding="utf-8") as f:
                    f.write(page.content())
                print("Debug files saved: debug_pubmed_search_page.png and debug_pubmed_search_page.html")
                return downloaded_files
            
            # Limit to top k results
            pubmed_links = pubmed_links[:k]
            print(f"Found {len(pubmed_links)} PubMed result(s) to process")
            
            # Process each PubMed result
            for i, pubmed_url in enumerate(pubmed_links, 1):
                try:
                    print(f"\n[{i}/{len(pubmed_links)}] Processing PubMed: {pubmed_url}")
                    
                    # Extract PMID from URL
                    pmid_match = re.search(r'/(\d+)/?$', pubmed_url)
                    pmid = pmid_match.group(1) if pmid_match else None
                    
                    # Navigate to PubMed page
                    page.goto(pubmed_url, wait_until="networkidle", timeout=10000)
                    time.sleep(2)
                    
                    # Extract PMCID from the PubMed page
                    # PMCID is usually shown in the "Full text links" section or as a link to PMC
                    pmc_id = None
                    pmc_link = None
                    
                    # First, try to find in the "Full text links" section
                    try:
                        # Look for the full text links section
                        fulltext_section = page.query_selector('#full-view-heading, .full-text-links, [id*="full"], [class*="full-text"]')
                        if fulltext_section:
                            pmc_links_in_section = fulltext_section.query_selector_all('a[href*="PMC"], a[href*="pmc"]')
                            for pmc_link_elem in pmc_links_in_section:
                                href = pmc_link_elem.get_attribute('href')
                                if href:
                                    pmc_match = re.search(r'PMC(\d+)', href, re.IGNORECASE)
                                    if pmc_match:
                                        pmc_id = f"PMC{pmc_match.group(1)}"
                                        if href.startswith('/'):
                                            pmc_link = f"https://pmc.ncbi.nlm.nih.gov{href}"
                                        elif not href.startswith('http'):
                                            pmc_link = f"https://pmc.ncbi.nlm.nih.gov/{href}"
                                        else:
                                            pmc_link = href
                                        break
                    except:
                        pass
                    
                    # Look for PMC links anywhere on the page
                    if not pmc_id:
                        pmc_link_selectors = [
                            'a[href*="/articles/PMC"]',
                            'a[href*="pmc.ncbi.nlm.nih.gov"]',
                            'a[href*="PMC"]',
                            'a:has-text("PMC")',
                            'a:has-text("Free PMC")',
                            'a:has-text("PubMed Central")'
                        ]
                        
                        for selector in pmc_link_selectors:
                            try:
                                pmc_links = page.query_selector_all(selector)
                                if pmc_links:
                                    for pmc_link_elem in pmc_links:
                                        href = pmc_link_elem.get_attribute('href')
                                        if href and ('PMC' in href.upper() or '/articles/' in href):
                                            # Extract PMC ID from URL
                                            pmc_match = re.search(r'PMC(\d+)', href, re.IGNORECASE)
                                            if pmc_match:
                                                pmc_id = f"PMC{pmc_match.group(1)}"
                                                # Construct full PMC URL
                                                if href.startswith('/'):
                                                    pmc_link = f"https://pmc.ncbi.nlm.nih.gov{href}"
                                                elif not href.startswith('http'):
                                                    pmc_link = f"https://pmc.ncbi.nlm.nih.gov/{href}"
                                                else:
                                                    pmc_link = href
                                                break
                                    if pmc_id:
                                        break
                            except:
                                continue
                    
                    # Alternative: Look for PMCID in the page text/content
                    if not pmc_id:
                        try:
                            page_content = page.content()
                            # Look for PMC ID in various formats
                            pmc_match = re.search(r'PMC(\d{6,})', page_content, re.IGNORECASE)
                            if pmc_match:
                                pmc_id = f"PMC{pmc_match.group(1)}"
                                pmc_link = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc_id}/"
                        except:
                            pass
                    
                    if not pmc_id:
                        print(f"  ✗ Could not find PMCID for PMID {pmid} - skipping (may not be available in PMC)")
                        continue
                    
                    print(f"  Found PMCID: {pmc_id}")
                    print(f"  PMC Link: {pmc_link}")
                    
                    # Navigate to PMC article page
                    page.goto(pmc_link, wait_until="networkidle", timeout=10000)
                    time.sleep(2)
                    
                    # Find PDF link on PMC page
                    pdf_link = None
                    
                    # Look for PDF link with pattern: /articles/{PMC_ID}/pdf/{filename}.pdf
                    pdf_link_selectors = [
                        f'a[href*="/articles/{pmc_id}/pdf/"]',
                        'a[href*="/pdf/"]',
                        'a:has-text("PDF")',
                        'a[href$=".pdf"]',
                        'a[title*="PDF"]'
                    ]
                    
                    for selector in pdf_link_selectors:
                        pdf_links = page.query_selector_all(selector)
                        if pdf_links:
                            for pdf_link_elem in pdf_links:
                                href = pdf_link_elem.get_attribute('href')
                                if href and '.pdf' in href:
                                    # Normalize the href to full URL
                                    if href.startswith('/'):
                                        full_href = f"https://pmc.ncbi.nlm.nih.gov{href}"
                                    elif not href.startswith('http'):
                                        full_href = f"https://pmc.ncbi.nlm.nih.gov/{href}"
                                    else:
                                        full_href = href
                                    
                                    # Check if it matches the pattern /articles/{PMC_ID}/pdf/{filename}.pdf
                                    if f'/articles/{pmc_id}/pdf/' in full_href and full_href.endswith('.pdf'):
                                        pdf_link = full_href
                                        break
                            if pdf_link:
                                break
                    
                    # If PDF link not found, try to construct it
                    if not pdf_link and pmc_id:
                        # Look for any PDF link and extract filename
                        all_pdf_links = page.query_selector_all('a[href*=".pdf"]')
                        for pdf_link_elem in all_pdf_links:
                            href = pdf_link_elem.get_attribute('href')
                            if href and href.endswith('.pdf'):
                                filename = href.split('/')[-1]
                                pdf_link = f"https://pmc.ncbi.nlm.nih.gov/articles/{pmc_id}/pdf/{filename}"
                                break
                    
                    # Download the PDF
                    if pdf_link:
                        try:
                            print(f"  Found PDF link: {pdf_link}")
                            
                            # Extract filename from URL
                            filename = pdf_link.split('/')[-1]
                            if not filename.endswith('.pdf'):
                                filename = f"{pmc_id}.pdf"
                            
                            pdf_downloaded = False
                            
                            # Method 1: Try to click PDF link
                            for selector in pdf_link_selectors:
                                try:
                                    pdf_element = page.query_selector(selector)
                                    if pdf_element:
                                        pdf_element.scroll_into_view_if_needed()
                                        time.sleep(0.3)
                                        with page.expect_download(timeout=10000) as download_info:
                                            pdf_element.click()
                                        download = download_info.value
                                        
                                        suggested_filename = download.suggested_filename
                                        if suggested_filename and suggested_filename.endswith('.pdf'):
                                            filename = suggested_filename
                                        
                                        file_path = download_path / filename
                                        download.save_as(file_path)
                                        downloaded_files.append(str(file_path))
                                        print(f"  ✓ Downloaded: {file_path}")
                                        pdf_downloaded = True
                                        break
                                except (PlaywrightTimeoutError, Exception):
                                    continue
                            
                            # Method 2: Use request API
                            if not pdf_downloaded:
                                try:
                                    response = context.request.get(
                                        pdf_link,
                                        headers={
                                            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
                                            'Accept': 'application/pdf,application/octet-stream,*/*'
                                        },
                                        timeout=10000
                                    )
                                    
                                    if response.ok:
                                        body = response.body()
                                        if body.startswith(b'%PDF'):
                                            file_path = download_path / filename
                                            with open(file_path, 'wb') as f:
                                                f.write(body)
                                            downloaded_files.append(str(file_path))
                                            print(f"  ✓ Downloaded: {file_path}")
                                            pdf_downloaded = True
                                except Exception as req_error:
                                    pass
                            
                            # Method 3: Direct navigation
                            if not pdf_downloaded:
                                try:
                                    with page.expect_download(timeout=10000) as download_info:
                                        page.goto(pdf_link, wait_until="networkidle", timeout=10000)
                                    download = download_info.value
                                    file_path = download_path / filename
                                    download.save_as(file_path)
                                    downloaded_files.append(str(file_path))
                                    print(f"  ✓ Downloaded: {file_path}")
                                    pdf_downloaded = True
                                except (PlaywrightTimeoutError, Exception):
                                    pass
                            
                            if not pdf_downloaded:
                                print(f"  ✗ Could not download PDF for {pmc_id}")
                        except Exception as e:
                            print(f"  ✗ Error downloading PDF: {e}")
                    else:
                        print(f"  ✗ Could not find PDF link for {pmc_id}")
                    
                    # Small delay between downloads
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"  ✗ Error processing PubMed result {i}: {e}")
                    continue
            
        except Exception as e:
            print(f"Error during search/download process: {e}")
        finally:
            browser.close()
    
    print(f"\n✓ Download complete! {len(downloaded_files)} file(s) downloaded to {download_dir}/")
    return downloaded_files


if __name__ == "__main__":
    # Example usage
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python paper_downloader.py <search_term> [k] [download_dir]")
        print("Example: python paper_downloader.py 'vitamin c' 5")
        sys.exit(1)
    
    search_term = sys.argv[1]
    k = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    download_dir = sys.argv[3] if len(sys.argv) > 3 else "downloads"
    
    download_pmc_papers(search_term, k, download_dir, headless=False)

