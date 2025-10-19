"""
Notion API configuration for EVI 360 guideline ingestion.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


@dataclass
class NotionConfig:
    """
    Configuration for Notion API integration.

    To set up:
    1. Go to https://www.notion.so/my-integrations
    2. Click "+ New integration"
    3. Name it "EVI RAG System" (or your preferred name)
    4. Select the workspace containing your guidelines database
    5. Copy the "Internal Integration Token"
    6. Add to .env as NOTION_API_TOKEN
    7. Share your guidelines database with the integration:
       - Open the database in Notion
       - Click "..." (three dots) in top right
       - Click "Add connections"
       - Select your integration
    8. Copy the database ID from the URL:
       - Database URL format: https://notion.so/workspace/<database_id>?v=...
       - Copy the <database_id> part (32 hex characters)
       - Add to .env as NOTION_GUIDELINES_DATABASE_ID
    """

    api_token: str
    guidelines_database_id: str
    base_url: str = "https://api.notion.com/v1"
    notion_version: str = "2022-06-28"  # Notion API version

    # Rate limiting
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds

    # Pagination
    page_size: int = 100  # Max 100 per Notion API

    @classmethod
    def from_env(cls) -> "NotionConfig":
        """
        Load configuration from environment variables.

        Returns:
            NotionConfig: Configuration instance.

        Raises:
            ValueError: If required environment variables are missing.
        """
        api_token = os.getenv("NOTION_API_TOKEN")
        database_id = os.getenv("NOTION_GUIDELINES_DATABASE_ID")

        if not api_token:
            raise ValueError(
                "NOTION_API_TOKEN not found in environment. "
                "Please set it in your .env file. "
                "Get your token from https://www.notion.so/my-integrations"
            )

        if not database_id:
            raise ValueError(
                "NOTION_GUIDELINES_DATABASE_ID not found in environment. "
                "Please set it in your .env file. "
                "Find the database ID in your Notion database URL."
            )

        return cls(
            api_token=api_token,
            guidelines_database_id=database_id
        )

    def get_headers(self) -> dict:
        """
        Get HTTP headers for Notion API requests.

        Returns:
            dict: Headers dictionary with authorization and version.
        """
        return {
            "Authorization": f"Bearer {self.api_token}",
            "Notion-Version": self.notion_version,
            "Content-Type": "application/json"
        }

    def validate_database_id(self) -> bool:
        """
        Validate that the database ID format is correct.

        Returns:
            bool: True if format is valid.
        """
        # Notion database IDs are 32 hex characters with optional hyphens
        clean_id = self.guidelines_database_id.replace("-", "")
        return len(clean_id) == 32 and all(c in "0123456789abcdef" for c in clean_id.lower())


# Example usage in code:
# from config.notion_config import NotionConfig
#
# config = NotionConfig.from_env()
# headers = config.get_headers()
