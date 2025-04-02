from dataclasses import dataclass
from datetime import date, datetime
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    get_type_hints,
    Union,
)


class DataTypeConverter:
    """Utility class for type conversion functions."""

    @staticmethod
    def to_date(value: Union[str, float, int]) -> float:
        """Convert value to Unix timestamp."""
        if not value:
            raise ValueError("Date value cannot be empty")
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid date format: {value}")

    @staticmethod
    def to_datetime(value: Union[str, float, int]) -> float:
        """Convert value to Unix timestamp."""
        if not value:
            raise ValueError("Datetime value cannot be empty")
        try:
            return float(value)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid datetime format: {value}")

    @staticmethod
    def to_float(value: Any) -> float:
        """Convert value to float."""
        if value == "":
            return 0.0
        try:
            return float(value)
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def to_int(value: Any) -> int:
        """Convert value to int."""
        if value == "":
            return 0
        try:
            return int(value)
        except (ValueError, TypeError):
            return 0

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

    @staticmethod
    def to_timestamp_int(value: Union[str, float, int]) -> int:
        """Convert value to Unix timestamp as integer."""
        if not value:
            raise ValueError("Date value cannot be empty")
        try:
            return int(float(value))
        except (ValueError, TypeError):
            raise ValueError(f"Invalid date format: {value}")


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
            elif field_type == date or field_type == datetime:
                setattr(self, field_name, DataTypeConverter.to_float(value))
            elif field_type == float and not isinstance(value, float):
                setattr(self, field_name, DataTypeConverter.to_float(value))
            elif field_type == int and not isinstance(value, int):
                setattr(self, field_name, DataTypeConverter.to_int(value))
            elif field_type == bool and not isinstance(value, bool):
                setattr(self, field_name, DataTypeConverter.to_bool(value))


@dataclass
class CampaignData(CsvDataModel):
    """Data model for campaign analytics data matching the CSV structure."""

    date: int
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
        "date": DataTypeConverter.to_timestamp_int,
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


@dataclass
class ProphetPredictionData(CsvDataModel):
    """Data model for prophet prediction data matching the prophet_prediction_data.csv structure."""

    date: int
    revenue: float
    ad_spend: float
    new_accounts: float

    field_converters: ClassVar[Dict[str, Callable]] = {
        "date": DataTypeConverter.to_timestamp_int,
        "revenue": DataTypeConverter.to_float,
        "ad_spend": DataTypeConverter.to_float,
        "new_accounts": DataTypeConverter.to_float,
    }
