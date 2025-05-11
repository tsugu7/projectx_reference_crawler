# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a web crawler with diff detection capability that crawls all pages within a specified domain, exports content to Markdown format, and detects changes from previous crawls. The crawler can be run either locally or in Google Colab.

## Running the Crawler

### Local Execution

```bash
# Basic usage
python website_crawler_local.py https://example.com

# With detailed options
python website_crawler_local.py https://example.com --max-pages 200 --delay 2.0 --output-dir ./site_content --discord-webhook https://discord.com/api/webhooks/your-webhook-url --skip-no-changes
```

### Google Colab Execution

1. Upload `website_crawler_colab.ipynb` to Google Colab
2. Install required libraries
3. Mount Google Drive (for cache and output persistence)
4. Run code definition cells
5. Enter settings in the form and click "Run Crawler" button

## Command Line Options

| Option | Description |
|----------|------|
| `url` | URL to start crawling from (required) |
| `--max-pages` | Maximum number of pages to crawl (default: 100) |
| `--delay` | Delay between requests in seconds (default: 1.0) |
| `--output-dir` | Output directory (default: output) |
| `--discord-webhook` | Discord Webhook URL for notifications (optional) |
| `--no-diff` | Disable diff detection |
| `--skip-no-changes` | Skip file generation and notification if no changes detected |
| `--cache-dir` | Cache directory (default: cache) |

## Dependencies

The crawler requires the following libraries:
```bash
pip install requests html2text lxml markdown pdfkit discord-webhook
```

For PDF generation, the `wkhtmltopdf` command-line tool is also required:
- Ubuntu: `sudo apt-get install wkhtmltopdf`
- macOS: `brew install wkhtmltopdf`
- Windows: Download installer from the official site

## Architecture

The crawler has a modular design with the following components:

1. `UrlFilter` - Filters URLs to only process those within the same domain
2. `Fetcher` - Retrieves HTML content from URLs with conditional requests
3. `Parser` - Parses HTML to extract content and links
4. `MarkdownConverter` - Converts HTML content to Markdown format
5. `CrawlCache` - Persistent storage for crawl results and diff detection
6. `ContentRepository` - Manages crawled content
7. `FileExporter` - Exports content to Markdown files
8. `PdfConverter` - Converts Markdown files to PDF
9. `DiscordNotifier` - Sends notifications to Discord
10. `RobotsTxtParser` - Parses robots.txt to respect website crawl policies
11. `WebCrawler` - Main controller that orchestrates the crawling process