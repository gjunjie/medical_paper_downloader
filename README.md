# PMC Paper Downloader

A Python tool to search PubMed Central (PMC) and automatically download the top k papers in PDF format.

## Installation

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

### As a Python function:

```python
from paper_downloader import download_pmc_papers

# Download top 5 papers for "vitamin c"
downloaded_files = download_pmc_papers("vitamin c", k=5)

# Download top 10 papers to a custom directory
downloaded_files = download_pmc_papers("machine learning", k=10, download_dir="my_papers")
```

### As a command-line script:

```bash
# Download top 5 papers (default)
python paper_downloader.py "vitamin c"

# Download top 10 papers
python paper_downloader.py "vitamin c" 10

# Download to custom directory
python paper_downloader.py "vitamin c" 10 my_papers
```

## Parameters

- `search_term`: The search term to query PMC (e.g., "vitamin c", "machine learning")
- `k`: Number of top papers to download (default: 5)
- `download_dir`: Directory to save downloaded PDFs (default: "downloads")
- `headless`: Whether to run browser in headless mode (default: True)

## How it works

1. Constructs a PMC search URL with the provided search term
2. Navigates to the search results page
3. Extracts links to the top k papers
4. For each paper:
   - Navigates to the article page
   - Finds and clicks the PDF download button
   - Saves the PDF to the specified directory

## Notes

- The script uses Playwright for browser automation to handle dynamic content and button clicks
- Downloaded PDFs are saved in the `downloads/` directory by default (or specified directory)
- The script includes error handling and will continue processing even if some downloads fail
- For debugging, you can set `headless=False` to see the browser in action

