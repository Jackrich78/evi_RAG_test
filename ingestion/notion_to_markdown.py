"""
Notion to Markdown Converter - FEAT-002

Fetches workplace safety guidelines from Notion database and converts them to markdown files
for ingestion into the EVI 360 RAG system.

Approach:
1. Fetch all pages from Notion database (with pagination)
2. Convert Notion blocks to simple markdown
3. Save to documents/notion_guidelines/*.md
4. Existing ingestion pipeline handles the rest (chunking, embedding, storage)

Usage:
    python3 -m ingestion.notion_to_markdown
"""

import asyncio
import logging
import os
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from notion_client import AsyncClient
from dotenv import load_dotenv

try:
    from config.notion_config import NotionConfig
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config.notion_config import NotionConfig

load_dotenv()

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NotionToMarkdown:
    """
    Fetches guidelines from Notion and converts them to markdown files.
    """

    def __init__(self, config: NotionConfig, output_dir: str = "documents/notion_guidelines"):
        """
        Initialize the Notion to Markdown converter.

        Args:
            config: NotionConfig instance with API credentials
            output_dir: Directory to save markdown files
        """
        self.config = config
        self.output_dir = Path(output_dir)
        self.client = AsyncClient(auth=config.api_token)

        # Create output directory if it doesn't exist
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Output directory: {self.output_dir.absolute()}")

    async def validate_connection(self) -> bool:
        """
        Validate Notion API connection and database access.

        Returns:
            bool: True if connection is valid

        Raises:
            Exception: If authentication fails or database is inaccessible
        """
        try:
            # Validate database ID format
            if not self.config.validate_database_id():
                raise ValueError(
                    f"Invalid database ID format: {self.config.guidelines_database_id}. "
                    "Expected 32 hex characters."
                )

            # Try to query the database
            response = await self.client.databases.query(
                database_id=self.config.guidelines_database_id,
                page_size=1
            )

            total_count = len(response.get("results", []))
            has_more = response.get("has_more", False)

            logger.info("✅ Notion client initialized successfully")
            logger.info(f"✅ Database access verified (found at least {total_count} page{'s' if total_count != 1 else ''})")
            if has_more:
                logger.info("✅ Database contains more pages (pagination will be used)")

            return True

        except Exception as e:
            logger.error(f"❌ Notion API connection failed: {e}")
            raise

    async def fetch_all_guidelines(self) -> List[Dict[str, Any]]:
        """
        Fetch guideline pages from Notion database with filters.

        Filters:
        - Status = "Latest"
        - Add to KB? = True

        Returns:
            List of page objects from Notion API
        """
        all_pages = []
        start_cursor = None
        page_count = 0

        logger.info(f"Fetching pages from database: {self.config.guidelines_database_id}")
        logger.info(f"Filters: Status='Latest' AND 'Add to KB?'=True")

        while True:
            try:
                # Query database with filters and pagination
                query_params = {
                    "database_id": self.config.guidelines_database_id,
                    "filter": {
                        "and": [
                            {"property": "Status", "status": {"equals": "Latest"}},
                            {"property": "Add to KB?", "checkbox": {"equals": True}}
                        ]
                    },
                    "page_size": self.config.page_size
                }

                if start_cursor:
                    query_params["start_cursor"] = start_cursor

                response = await self.client.databases.query(**query_params)

                results = response.get("results", [])
                all_pages.extend(results)
                page_count += len(results)

                logger.info(f"Fetched {len(results)} pages (total: {page_count})")

                # Check if there are more pages
                has_more = response.get("has_more", False)
                if not has_more:
                    break

                start_cursor = response.get("next_cursor")

                # Small delay to respect rate limits
                await asyncio.sleep(0.1)

            except Exception as e:
                logger.error(f"Error fetching pages: {e}")
                raise

        logger.info(f"✅ Fetched total of {page_count} pages from Notion (expected: 87)")
        return all_pages

    async def fetch_page_blocks(self, page_id: str) -> List[Dict[str, Any]]:
        """
        Fetch all blocks (content) for a specific page.

        Args:
            page_id: Notion page ID

        Returns:
            List of block objects
        """
        all_blocks = []
        start_cursor = None

        while True:
            try:
                query_params = {"block_id": page_id, "page_size": 100}
                if start_cursor:
                    query_params["start_cursor"] = start_cursor

                response = await self.client.blocks.children.list(**query_params)

                results = response.get("results", [])
                all_blocks.extend(results)

                if not response.get("has_more", False):
                    break

                start_cursor = response.get("next_cursor")
                await asyncio.sleep(0.05)  # Rate limit

            except Exception as e:
                logger.error(f"Error fetching blocks for page {page_id}: {e}")
                raise

        return all_blocks

    def blocks_to_markdown(self, blocks: List[Dict[str, Any]]) -> str:
        """
        Convert Notion blocks to markdown text.

        Simple conversion that handles common block types:
        - Headings (heading_1, heading_2, heading_3)
        - Paragraphs
        - Bulleted lists
        - Numbered lists
        - Code blocks

        Args:
            blocks: List of Notion block objects

        Returns:
            Markdown formatted text
        """
        markdown_lines = []

        for block in blocks:
            block_type = block.get("type")

            # Skip unsupported or empty blocks
            if not block_type or block_type not in block:
                continue

            block_content = block[block_type]

            # Extract text from rich text array
            text = self._extract_text(block_content.get("rich_text", []))

            if not text:
                continue

            # Convert based on block type
            if block_type == "heading_1":
                markdown_lines.append(f"# {text}\n")
            elif block_type == "heading_2":
                markdown_lines.append(f"## {text}\n")
            elif block_type == "heading_3":
                markdown_lines.append(f"### {text}\n")
            elif block_type == "paragraph":
                markdown_lines.append(f"{text}\n")
            elif block_type == "bulleted_list_item":
                markdown_lines.append(f"- {text}")
            elif block_type == "numbered_list_item":
                markdown_lines.append(f"1. {text}")
            elif block_type == "code":
                language = block_content.get("language", "")
                markdown_lines.append(f"```{language}\n{text}\n```\n")
            elif block_type == "quote":
                markdown_lines.append(f"> {text}\n")
            elif block_type == "divider":
                markdown_lines.append("---\n")

        return "\n".join(markdown_lines)

    def _extract_text(self, rich_text: List[Dict[str, Any]]) -> str:
        """
        Extract plain text from Notion rich text array.

        Args:
            rich_text: Notion rich text array

        Returns:
            Plain text string
        """
        return "".join([rt.get("plain_text", "") for rt in rich_text])

    def extract_category_from_url(self, url: str) -> str:
        """
        Extract guideline category from source URL.

        Args:
            url: Source URL

        Returns:
            Category string (NVAB, STECR, UWV, etc.)
        """
        if not url:
            return "Unknown"

        url_lower = url.lower()

        if 'nvab-online.nl' in url_lower:
            return 'NVAB'
        elif 'stecr.nl' in url_lower:
            return 'STECR'
        elif 'uwv.nl' in url_lower:
            return 'UWV'
        elif 'arboportaal.nl' in url_lower:
            return 'Arboportaal'
        elif 'wikipedia.org' in url_lower:
            return 'Wikipedia'
        elif url_lower.startswith('http'):
            return 'External'
        else:
            return 'Manual'

    def get_page_title(self, page: Dict[str, Any]) -> str:
        """
        Extract title from a Notion page object.

        Args:
            page: Notion page object

        Returns:
            Page title as string
        """
        properties = page.get("properties", {})

        # Look for title property (usually "Name" or "Title")
        for prop_name, prop_value in properties.items():
            if prop_value.get("type") == "title":
                title_array = prop_value.get("title", [])
                if title_array:
                    return self._extract_text(title_array)

        # Fallback to page ID if no title found
        return page.get("id", "untitled")

    def sanitize_filename(self, title: str) -> str:
        """
        Convert page title to safe filename.

        Args:
            title: Page title

        Returns:
            Sanitized filename (without .md extension)
        """
        # Remove or replace invalid filename characters
        safe_title = re.sub(r'[<>:"/\\|?*]', '_', title)
        # Limit length
        safe_title = safe_title[:100]
        # Remove leading/trailing spaces and dots
        safe_title = safe_title.strip(' .')

        return safe_title or "untitled"

    async def save_page_as_markdown(self, page: Dict[str, Any]) -> Optional[str]:
        """
        Fetch page content and save as markdown file with YAML frontmatter.

        Args:
            page: Notion page object

        Returns:
            Path to saved markdown file, or None if failed
        """
        try:
            # Extract properties
            props = page.get("properties", {})

            # Get title (Dutch)
            title = self.get_page_title(page)

            # Get other metadata
            page_summary_nl = self._extract_text(props.get("page_summary_nl", {}).get("rich_text", []))
            source_url = props.get("URL", {}).get("url", "")
            status = props.get("Status", {}).get("status", {}).get("name", "")

            # Extract tags
            tags = props.get("Tags", {}).get("multi_select", [])
            tag_names = [tag.get("name", "") for tag in tags]

            # Extract category from URL
            guideline_category = self.extract_category_from_url(source_url)

            # Page ID
            page_id = page["id"]

            # Create filename
            filename = self.sanitize_filename(title) + ".md"
            filepath = self.output_dir / filename

            # Fetch page blocks
            blocks = await self.fetch_page_blocks(page_id)

            # Convert to markdown
            markdown_content = self.blocks_to_markdown(blocks)

            # Create YAML frontmatter
            frontmatter = "---\n"
            frontmatter += f'title: "{title}"\n'
            if source_url:
                frontmatter += f'source_url: "{source_url}"\n'
            if page_summary_nl:
                # Escape quotes and newlines in summary
                summary_escaped = page_summary_nl.replace('"', '\\"').replace('\n', ' ')
                frontmatter += f'summary: "{summary_escaped}"\n'
            frontmatter += f'guideline_category: "{guideline_category}"\n'
            if tag_names:
                frontmatter += f'tags: {tag_names}\n'
            frontmatter += f'status: "{status}"\n'
            frontmatter += f'notion_page_id: "{page_id}"\n'
            frontmatter += f'fetched_at: "{datetime.now().strftime("%Y-%m-%d")}"\n'
            frontmatter += "---\n\n"

            # Combine frontmatter + title + content
            full_content = frontmatter + f"# {title}\n\n" + markdown_content

            # Save to file
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(full_content)

            logger.info(f"✅ Saved: {filename} ({len(markdown_content)} chars) [Category: {guideline_category}]")
            return str(filepath)

        except Exception as e:
            logger.error(f"❌ Failed to save page {page.get('id')}: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return None

    async def fetch_and_save_all(self) -> int:
        """
        Main workflow: fetch all pages and save as markdown files.

        Returns:
            Number of files successfully saved
        """
        logger.info("=" * 60)
        logger.info("NOTION TO MARKDOWN CONVERTER - FEAT-002")
        logger.info("=" * 60)

        # Step 1: Validate connection
        logger.info("\nStep 1: Validating Notion API connection...")
        await self.validate_connection()

        # Step 2: Fetch all pages
        logger.info("\nStep 2: Fetching all guideline pages...")
        pages = await self.fetch_all_guidelines()

        if not pages:
            logger.warning("⚠️  No pages found in database")
            return 0

        # Step 3: Save each page as markdown
        logger.info(f"\nStep 3: Converting {len(pages)} pages to markdown...")

        saved_count = 0
        for i, page in enumerate(pages, 1):
            logger.info(f"\nProcessing page {i}/{len(pages)}...")
            filepath = await self.save_page_as_markdown(page)
            if filepath:
                saved_count += 1

            # Small delay to respect rate limits
            await asyncio.sleep(0.1)

        logger.info("\n" + "=" * 60)
        logger.info(f"✅ COMPLETE: Saved {saved_count}/{len(pages)} pages to {self.output_dir}")
        logger.info("=" * 60)

        return saved_count


async def main():
    """
    Main entry point for Notion to Markdown conversion.
    """
    try:
        # Load configuration from environment
        config = NotionConfig.from_env()

        # Create converter
        converter = NotionToMarkdown(config)

        # Run conversion
        saved_count = await converter.fetch_and_save_all()

        if saved_count > 0:
            logger.info("\n✨ Next steps:")
            logger.info(f"   1. Inspect markdown files in: {converter.output_dir}")
            logger.info(f"   2. Run ingestion: python3 -m ingestion.ingest {converter.output_dir}")
        else:
            logger.error("❌ No files saved. Check your Notion configuration.")
            return 1

        return 0

    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
