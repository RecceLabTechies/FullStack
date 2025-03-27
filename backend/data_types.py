from dataclasses import dataclass
from datetime import date, datetime
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    get_type_hints,
)


class DataTypeConverter:
    """Utility class for type conversion functions."""

    @staticmethod
    def to_date(value: str) -> date:
        """Convert string to date object."""
        try:
            year, month, day = map(int, value.split("-"))
            return date(year, month, day)
        except (ValueError, TypeError):
            return value

    @staticmethod
    def to_datetime(value: str) -> datetime:
        """Convert string to datetime object for MongoDB compatibility."""
        try:
            year, month, day = map(int, value.split("-"))
            return datetime(year, month, day)
        except (ValueError, TypeError):
            return value

    @staticmethod
    def to_float(value: Any) -> float:
        """Convert value to float."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return value

    @staticmethod
    def to_int(value: Any) -> int:
        """Convert value to int."""
        try:
            return int(value)
        except (ValueError, TypeError):
            return value

    @staticmethod
    def to_str(value: Any) -> str:
        """Convert value to string."""
        return str(value)

    @staticmethod
    def to_bool(value: Any) -> bool:
        """Convert value to boolean."""
        if isinstance(value, str):
            return value.lower() in ("true", "yes", "y", "1", "t")
        return bool(value)


@dataclass
class CsvDataModel:
    """Base class for data models generated from CSV files."""

    # Class variable mapping field names to conversion functions
    field_converters: ClassVar[Dict[str, Callable]] = {}

    def __post_init__(self):
        """Convert fields based on their types and field_converters."""
        # Get type hints for this class
        hints = get_type_hints(self.__class__)

        # Apply conversions based on type hints
        for field_name, field_type in hints.items():
            if field_name == "field_converters":
                continue

            # Get current value
            value = getattr(self, field_name)

            # Apply custom converter if defined
            if field_name in self.field_converters:
                converted = self.field_converters[field_name](value)
                setattr(self, field_name, converted)
            # Apply conversions based on type annotations
            elif field_type == date and isinstance(value, str):
                setattr(self, field_name, DataTypeConverter.to_date(value))
            elif field_type == datetime and isinstance(value, str):
                setattr(self, field_name, DataTypeConverter.to_datetime(value))
            elif field_type == float and not isinstance(value, float):
                setattr(self, field_name, DataTypeConverter.to_float(value))
            elif field_type == int and not isinstance(value, int):
                setattr(self, field_name, DataTypeConverter.to_int(value))
            elif field_type == bool and not isinstance(value, bool):
                setattr(self, field_name, DataTypeConverter.to_bool(value))


@dataclass
class CampaignData(CsvDataModel):
    """Data model for campaign analytics data matching the CSV structure."""

    date: datetime  # Format: YYYY-MM-DD, stored as datetime for MongoDB compatibility
    campaign_id: str
    channel: str
    age_group: str
    ad_spend: float
    views: float
    leads: float
    new_accounts: float
    country: str
    revenue: float

    field_converters: ClassVar[Dict[str, Callable]] = {
        "date": DataTypeConverter.to_datetime,  # Use datetime for MongoDB compatibility
        "ad_spend": DataTypeConverter.to_float,
        "views": DataTypeConverter.to_float,
        "leads": DataTypeConverter.to_float,
        "new_accounts": DataTypeConverter.to_float,
        "revenue": DataTypeConverter.to_float,
    }


@dataclass
class UserData(CsvDataModel):
    """Data model for user information matching the users.csv structure."""

    username: str
    email: str
    role: str
    company: str
    password: str
    chart_access: bool
    report_generation_access: bool
    user_management_access: bool

    field_converters: ClassVar[Dict[str, Callable]] = {
        "chart_access": DataTypeConverter.to_bool,
        "report_generation_access": DataTypeConverter.to_bool,
        "user_management_access": DataTypeConverter.to_bool,
    }
