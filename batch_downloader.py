"""
Batch PMC Paper Downloader

This script searches PMC for multiple terms and downloads the top k papers for each term.
"""

from paper_downloader import download_pmc_papers
import os
from pathlib import Path


def batch_download_papers(search_terms, k=20, base_download_dir="downloads"):
    """
    Download top k papers for each search term.
    
    Args:
        search_terms: List of search terms
        k: Number of papers to download per term (default: 20)
        base_download_dir: Base directory for downloads (default: "downloads")
    
    Returns:
        Dictionary mapping search terms to lists of downloaded file paths
    """
    results = {}
    
    print(f"Starting batch download for {len(search_terms)} search terms")
    print(f"Will download top {k} papers for each term\n")
    print("=" * 60)
    
    for i, term in enumerate(search_terms, 1):
        print(f"\n[{i}/{len(search_terms)}] Processing: {term}")
        print("-" * 60)
        
        # Create a subdirectory for each search term
        # Replace spaces and special characters with underscores
        safe_term = term.replace(' ', '_').replace('/', '_')
        download_dir = os.path.join(base_download_dir, safe_term)
        
        try:
            downloaded_files = download_pmc_papers(
                search_term=term,
                k=k,
                download_dir=download_dir,
                headless=True
            )
            results[term] = downloaded_files
            print(f"✓ Completed: {term} - {len(downloaded_files)} papers downloaded")
        except Exception as e:
            print(f"✗ Error processing {term}: {e}")
            results[term] = []
    
    print("\n" + "=" * 60)
    print("\nBatch download summary:")
    print("-" * 60)
    total_downloaded = 0
    for term, files in results.items():
        count = len(files)
        total_downloaded += count
        print(f"  {term}: {count} papers")
    
    print(f"\nTotal papers downloaded: {total_downloaded}")
    print(f"Download location: {base_download_dir}/")
    
    return results


if __name__ == "__main__":
    # Search terms to process
    search_terms = [
        # 'Probiotics health',
        'Vitamin B health',
        # 'Vitamin C',
        # 'Vitamin D',
        # 'Collagen',
        # 'Coenzyme Q10',
        # 'Calcium',
        # 'Iron',
        # 'Magnesium',
        # 'Fish Oil'
    ]
    
    # Download top 20 papers for each term
    results = batch_download_papers(search_terms, k=20)
    
    print("\n✓ Batch download complete!")

