import os
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


class ConfigManager:
    """Configuration manager for the application."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize the configuration manager.

        Args:
            config_path: Optional path to the configuration file.
                        If not provided, uses default path.
        """
        self.config = None
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "config",
            "config.yaml"
        )

    def load_config(self) -> None:
        """Load the configuration from the YAML file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Configuration file not found: {self.config_path}")

        with open(self.config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

    def get_scraper_config(self) -> Dict[str, Any]:
        """Get the scraper configuration.

        Returns:
            Dict containing scraper configuration.

        Raises:
            Exception: If configuration is not loaded.
        """
        if not self.config:
            raise Exception("Configuration not loaded")
        return self.config.get("scraper", {})

    def get_dynamodb_config(self) -> Dict[str, Any]:
        """Get the DynamoDB configuration.

        Returns:
            Dict containing DynamoDB configuration.

        Raises:
            Exception: If configuration is not loaded.
        """
        if not self.config:
            raise Exception("Configuration not loaded")
        return self.config.get("dynamodb", {})

    def get_urls_config(self) -> Dict[str, Any]:
        """Get the URLs configuration.

        Returns:
            Dict containing URLs configuration.

        Raises:
            Exception: If configuration is not loaded.
        """
        if not self.config:
            raise Exception("Configuration not loaded")
        return self.config.get("urls", {}) 