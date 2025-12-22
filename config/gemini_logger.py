"""Gemini Interaction Logger.

Logs all Gemini API requests and responses to daily log files.
Latest entries appear at the top for easy viewing.
Provides human-readable formatted output with metadata.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


class GeminiLogger:
    """Logger for Gemini API interactions with daily rotation.

    Features:
    - Daily log file rotation
    - Latest entries at top of file
    - Human-readable formatting
    - Metadata tracking (model, latency, tokens)
    """

    def __init__(self, log_dir: str | None = None):
        """Initialize Gemini logger.

        Args:
            log_dir: Directory for log files. Defaults to logs/gemini/
        """
        if log_dir is None:
            project_root = Path(__file__).parent.parent
            log_dir = project_root / "logs" / "gemini"

        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def _get_log_file_path(self) -> Path:
        """Get current log file path with date-based naming."""
        today = datetime.now().strftime("%Y-%m-%d")
        return self.log_dir / f"gemini_{today}.log"

    def _format_prompt(self, prompt: str, max_length: int = 2000) -> str:
        """Format prompt for readable display.

        Args:
            prompt: Raw prompt text.
            max_length: Max characters before truncation.

        Returns:
            Formatted prompt string.
        """
        # Clean up whitespace
        lines = prompt.strip().split("\n")
        formatted_lines = []

        for line in lines:
            # Indent each line for readability
            formatted_lines.append(f"    {line}")

        formatted = "\n".join(formatted_lines)

        if len(formatted) > max_length:
            return formatted[:max_length] + f"\n    ... [truncated, total: {len(prompt)} chars]"
        return formatted

    def _format_response(self, response: Any) -> str:
        """Format response for readable display.

        Args:
            response: Response from Gemini (string, dict, or other).

        Returns:
            Formatted response string.
        """
        if isinstance(response, dict):
            try:
                formatted = json.dumps(response, indent=4, ensure_ascii=False)
                # Indent each line
                lines = formatted.split("\n")
                return "\n".join(f"    {line}" for line in lines)
            except:
                return f"    {str(response)}"
        elif isinstance(response, str):
            try:
                # Try to parse as JSON for pretty printing
                parsed = json.loads(response)
                formatted = json.dumps(parsed, indent=4, ensure_ascii=False)
                lines = formatted.split("\n")
                return "\n".join(f"    {line}" for line in lines)
            except:
                # Plain text - indent each line
                lines = response.strip().split("\n")
                return "\n".join(f"    {line}" for line in lines)
        return f"    {str(response)}"

    def log_interaction(
        self,
        operation: str,
        prompt: str,
        response: Any,
        metadata: Optional[dict[str, Any]] = None,
    ) -> None:
        """Log a Gemini API interaction.

        Args:
            operation: Type of operation (e.g., 'allergy_verification', 'tone_check')
            prompt: The prompt/request sent to Gemini
            response: The response received from Gemini
            metadata: Optional metadata (model_name, latency, etc.)
        """
        log_file = self._get_log_file_path()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]

        # Build log entry with clear visual separators
        separator = "=" * 100
        section_sep = "-" * 100

        entry_parts = [
            separator,
            f"TIMESTAMP:  {timestamp}",
            f"OPERATION:  {operation}",
        ]

        # Add metadata if provided
        if metadata:
            entry_parts.append(f"\nMETADATA:")
            for key, value in metadata.items():
                entry_parts.append(f"    {key}: {value}")

        # Add formatted request
        entry_parts.extend([
            f"\n{section_sep}",
            "REQUEST (Prompt):",
            section_sep,
            self._format_prompt(prompt),
        ])

        # Add formatted response
        entry_parts.extend([
            f"\n{section_sep}",
            "RESPONSE:",
            section_sep,
            self._format_response(response),
        ])

        entry_parts.append(f"\n{separator}\n")

        log_entry = "\n".join(entry_parts)

        try:
            # Read existing content
            existing_content = ""
            if log_file.exists():
                with open(log_file, "r", encoding="utf-8") as f:
                    existing_content = f.read()

            # Write new entry at top (latest first)
            with open(log_file, "w", encoding="utf-8") as f:
                f.write(log_entry)
                if existing_content:
                    f.write("\n")
                    f.write(existing_content)

        except Exception as e:
            # Fail silently - don't break the main application
            print(f"Warning: Failed to write Gemini log: {e}")

    def get_recent_entries(self, count: int = 10) -> str:
        """Get recent log entries as formatted string.

        Args:
            count: Maximum number of entries to return.

        Returns:
            Formatted string with recent entries.
        """
        log_file = self._get_log_file_path()

        if not log_file.exists():
            return "No logs found for today."

        try:
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Split by separator and take first N entries
            entries = content.split("=" * 100)
            # Filter empty entries and reconstruct
            valid_entries = [e for e in entries if e.strip()][:count]

            return ("=" * 100).join(valid_entries)

        except Exception as e:
            return f"Error reading logs: {e}"

    def get_available_dates(self) -> list[str]:
        """Get list of dates that have log files.

        Returns:
            List of date strings (YYYY-MM-DD), most recent first.
        """
        dates = []
        for log_file in self.log_dir.glob("gemini_*.log"):
            # Extract date from filename
            date_str = log_file.stem.replace("gemini_", "")
            dates.append(date_str)
        return sorted(dates, reverse=True)

    def get_log_path(self) -> Path:
        """Get the current log file path.

        Returns:
            Path to today's log file.
        """
        return self._get_log_file_path()


# Global instance
_gemini_logger: GeminiLogger | None = None


def get_gemini_logger() -> GeminiLogger:
    """Get or create the global Gemini logger instance.

    Returns:
        GeminiLogger singleton instance.
    """
    global _gemini_logger
    if _gemini_logger is None:
        _gemini_logger = GeminiLogger()
    return _gemini_logger
