import logging
import pandas as pd
from app.models.data_types import CampaignData
from app.database.connection import get_campaign_performance_collection

logger = logging.getLogger(__name__)


def get_revenue_by_date():
    """
    Get revenue data aggregated by date (last 7 entries)

    Returns:
        list: List of dictionaries with date and revenue
    """
    collection = get_campaign_performance_collection()
    data = list(collection.find({}, {"_id": 0}))

    if not data:
        return []

    # Convert raw data to CampaignData objects for proper typing
    validated_data = []
    for item in data:
        try:
            campaign_obj = CampaignData(**item)
            validated_data.append(
                {"date": campaign_obj.date, "revenue": campaign_obj.revenue}
            )
        except Exception as e:
            logger.warning(f"Error converting campaign data: {e}")

    if not validated_data:
        df = pd.DataFrame(data)
    else:
        df = pd.DataFrame(validated_data)

    df = df[["date", "revenue"]]
    df["revenue"] = df["revenue"].astype(float)  # Convert to float for decimal values
    df_grouped = df.groupby("date", as_index=False).sum()
    df_grouped = df_grouped.sort_values("date").tail(7)

    data_summary = df_grouped.to_dict(orient="records")
    return data_summary
