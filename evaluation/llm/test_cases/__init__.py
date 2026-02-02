"""Test cases manager for LLM evaluation.

Provides centralized management of test cases organized by tool category.
Test cases are loaded from JSON files in category-specific directories.

Usage:
    from evaluation.llm.test_cases import TestCasesManager, Category, TestCase

    manager = TestCasesManager()

    # Get all test cases
    cases = manager.get_all()

    # Get quick subset (1 per category)
    quick_cases = manager.get_quick()

    # Get specific categories
    weather_cases = manager.get_by_category([Category.WEATHER_FORECAST, Category.WEATHER_DAY])
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Iterator


class Category(Enum):
    """Test case categories organized by tool."""

    # Weather tools
    WEATHER_FORECAST = "weather/forecast"
    WEATHER_DAY = "weather/day"
    WEATHER_TODAY = "weather/today"

    # Calendar tools
    CALENDAR_LIST = "calendar/list"
    CALENDAR_GET = "calendar/get"
    CALENDAR_CREATE = "calendar/create"
    CALENDAR_UPDATE = "calendar/update"
    CALENDAR_DELETE = "calendar/delete"
    CALENDAR_DELETE_ALL = "calendar/delete_all"
    CALENDAR_GET_FOR_DATE = "calendar/get_for_date"
    CALENDAR_DELETE_FOR_DATE = "calendar/delete_for_date"

    # General (no tool)
    NO_TOOL = "general/no_tool"


TOOL_TO_CATEGORY: dict[str | None, Category] = {
    "get_weather_forecast": Category.WEATHER_FORECAST,
    "get_weather_for_day": Category.WEATHER_DAY,
    "get_weather_for_today": Category.WEATHER_TODAY,
    "list_calendar_events": Category.CALENDAR_LIST,
    "get_calendar_event": Category.CALENDAR_GET,
    "create_calendar_event": Category.CALENDAR_CREATE,
    "update_calendar_event": Category.CALENDAR_UPDATE,
    "delete_calendar_event": Category.CALENDAR_DELETE,
    "delete_all_calendar_events": Category.CALENDAR_DELETE_ALL,
    "get_calendar_events_for_date": Category.CALENDAR_GET_FOR_DATE,
    "delete_calendar_events_for_date": Category.CALENDAR_DELETE_FOR_DATE,
    None: Category.NO_TOOL,
}


@dataclass
class TestCase:
    """A single test case for LLM evaluation."""

    id: str
    input: str
    expected_tool: str | None = None
    expected_args: dict = field(default_factory=dict)
    expected_args_contains: dict = field(default_factory=dict)
    expected_tool_one_of: list[str] = field(default_factory=list)
    category: Category | None = None

    @classmethod
    def from_dict(cls, data: dict, category: Category | None = None) -> "TestCase":
        """Create a TestCase from a dictionary."""
        tool = data.get("expected_tool")
        return cls(
            id=data["id"],
            input=data["input"],
            expected_tool=tool,
            expected_args=data.get("expected_args", {}),
            expected_args_contains=data.get("expected_args_contains", {}),
            expected_tool_one_of=data.get("expected_tool_one_of", []),
            category=category or TOOL_TO_CATEGORY.get(tool),
        )


class TestCasesManager:
    """Manages test cases organized by category.

    Test cases are loaded from JSON files:
        test_cases/dialogue/
        ├── weather/
        │   ├── forecast.json
        │   ├── day.json
        │   └── today.json
        ├── calendar/
        │   ├── list.json
        │   ├── get.json
        │   ├── create.json
        │   └── ...
        └── general/
            └── no_tool.json
    """

    def __init__(self, base_path: Path | None = None):
        """Initialize the test cases manager."""
        self.base_path = base_path or Path(__file__).parent / "dialogue"
        self._cache: dict[Category, list[TestCase]] = {}

    def get_categories(self) -> list[Category]:
        """Get available categories."""
        categories = []
        for cat in Category:
            if (self.base_path / f"{cat.value}.json").exists():
                categories.append(cat)
        return categories

    def load_category(self, category: Category) -> list[TestCase]:
        """Load test cases for a specific category."""
        if category in self._cache:
            return self._cache[category]

        file_path = self.base_path / f"{category.value}.json"
        if not file_path.exists():
            return []

        data = json.loads(file_path.read_text())
        cases = [TestCase.from_dict(d, category=category) for d in data]
        self._cache[category] = cases
        return cases

    def get_all(self) -> list[TestCase]:
        """Get all test cases."""
        cases = []
        for category in self.get_categories():
            cases.extend(self.load_category(category))
        return cases

    def get_quick(self) -> list[TestCase]:
        """Get one test case per category (first from each file)."""
        cases = []
        for category in self.get_categories():
            category_cases = self.load_category(category)
            if category_cases:
                cases.append(category_cases[0])
        return cases

    def get_by_category(self, categories: list[Category]) -> list[TestCase]:
        """Get test cases for specific categories."""
        cases = []
        for category in categories:
            cases.extend(self.load_category(category))
        return cases

    def get_by_tool(self, tool: str | None) -> list[TestCase]:
        """Get test cases for a specific tool."""
        category = TOOL_TO_CATEGORY.get(tool)
        if category:
            return self.load_category(category)
        return []

    def iter_all(self) -> Iterator[TestCase]:
        """Iterate over all test cases."""
        for category in self.get_categories():
            yield from self.load_category(category)

    def count(self) -> int:
        """Count total test cases."""
        return sum(len(self.load_category(cat)) for cat in self.get_categories())

    def summary(self) -> dict[str, int]:
        """Get summary of test cases by category."""
        return {
            cat.value: len(self.load_category(cat)) for cat in self.get_categories()
        }

    def clear_cache(self) -> None:
        """Clear the internal cache."""
        self._cache.clear()


__all__ = ["Category", "TestCase", "TestCasesManager", "TOOL_TO_CATEGORY"]
