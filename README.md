# Medical Paper Downloader

A Python tool to search PubMed Central (PMC) and PubMed, automatically downloading research papers in PDF format. Supports both individual searches and batch processing of multiple search terms.

## Features

- 🔍 Search PubMed Central (PMC) directly
- 📚 Search PubMed and download free full-text papers from PMC
- 📥 Batch download papers for multiple search terms
- 🤖 Automated browser-based downloading using Playwright
- 📁 Organized file storage with automatic directory creation
- ⚡ Configurable download limits and output directories

## Installation

1. Clone this repository:
```bash
git clone https://github.com/gjunjie/medical_paper_downloader.git
cd medical_paper_downloader
```

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

4. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

### Method 1: Direct PMC Search

Search PMC directly and download papers:

```python
from paper_downloader import download_pmc_papers

# Download top 5 papers for "vitamin c"
downloaded_files = download_pmc_papers("vitamin c", k=5)

# Download top 10 papers to a custom directory
downloaded_files = download_pmc_papers("machine learning", k=10, download_dir="my_papers")
```

### Method 2: PubMed Search (Recommended)

Search PubMed and download free full-text papers from PMC:

```python
from paper_downloader import download_pubmed_free_fulltext_papers

# Download top 5 papers
downloaded_files = download_pubmed_free_fulltext_papers("probiotics oral health", k=5)

# Download top 20 papers to a custom directory
downloaded_files = download_pubmed_free_fulltext_papers(
    "vitamin d health", 
    k=20, 
    download_dir="vitamin_d_papers"
)
```

### Method 3: Batch Download

Download papers for multiple search terms at once:

```python
from batch_downloader import batch_download_papers

search_terms = [
    'Probiotics health',
    'Vitamin B health',
    'Vitamin C health',
    'Vitamin D health',
    'Collagen health'
]

# Download top 15 papers for each term using PubMed search
results = batch_download_papers(
    search_terms, 
    k=15, 
    use_pubmed=True,  # Set to False for direct PMC search
    base_download_dir="downloads"
)
```

### Command-Line Usage

You can also use the scripts directly from the command line:

```bash
# Download top 5 papers using PMC search (default)
python paper_downloader.py "vitamin c"

# Download top 10 papers
python paper_downloader.py "vitamin c" 10

# Download to custom directory
python paper_downloader.py "vitamin c" 10 my_papers
```

For batch downloads, edit `batch_downloader.py` to customize your search terms and run:

```bash
python batch_downloader.py
```

## Parameters

### `download_pmc_papers()` and `download_pubmed_free_fulltext_papers()`

- `search_term` (str): The search term to query (e.g., "vitamin c", "machine learning")
- `k` (int): Number of top papers to download (default: 5)
- `download_dir` (str): Directory to save downloaded PDFs (default: "downloads")
- `headless` (bool): Whether to run browser in headless mode (default: True)

### `batch_download_papers()`

- `search_terms` (list): List of search terms to process
- `k` (int): Number of papers to download per term (default: 20)
- `base_download_dir` (str): Base directory for downloads (default: "downloads")
- `use_pubmed` (bool): If True, use PubMed search method. If False, use direct PMC search (default: True)
- `headless` (bool): Whether to run browser in headless mode (default: True)

## How It Works

### PMC Direct Search (`download_pmc_papers`)
1. Constructs a PMC search URL with the provided search term
2. Navigates to the search results page
3. Extracts links to the top k papers
4. For each paper:
   - Navigates to the article page
   - Finds and clicks the PDF download button
   - Saves the PDF to the specified directory

### PubMed Search (`download_pubmed_free_fulltext_papers`)
1. Searches PubMed with the search term
2. Extracts PubMed IDs (PMID) for each paper
3. Navigates to each PubMed page to get the PMC ID (PMCID)
4. Navigates to the PMC article page using the PMCID
5. Downloads the PDF from PMC

### Batch Processing
- Creates a subdirectory for each search term
- Processes each term sequentially
- Provides progress updates and summary statistics
- Continues processing even if individual downloads fail

## Project Structure

```
medical_paper_downloader/
├── paper_downloader.py      # Main downloader with PMC and PubMed methods
├── batch_downloader.py       # Batch processing script
├── requirements.txt         # Python dependencies
├── README.md               # This file
└── downloads/              # Default download directory (created automatically)
```

## Notes

- The script uses Playwright for browser automation to handle dynamic content and button clicks
- Downloaded PDFs are saved in the `downloads/` directory by default (or specified directory)
- For batch downloads, each search term gets its own subdirectory
- The script includes error handling and will continue processing even if some downloads fail
- For debugging, you can set `headless=False` to see the browser in action
- PubMed search method is recommended as it provides better access to free full-text papers

## Requirements

- Python 3.7+
- Playwright
- Chromium browser (installed via Playwright)

## License

This project is open source and available for use.

## Repository

GitHub: https://github.com/gjunjie/medical_paper_downloader
