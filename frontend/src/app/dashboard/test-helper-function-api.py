# to be added to apis once complete (data needs to be grouped a certain way)
from datetime import date, timedelta

# for heatmap
def calculate_cost_metrics(df, time, show):
    """
    Calculates cost per lead, cost per view, and cost per new account, grouped by age group or channel.

    :param df: Pandas DataFrame containing marketing data.
    :param time: String representing the time selection ("last_365", "2023", "2024").
    :param show: String representing the grouping ("age_group" or "channel").
    :return: List of dictionaries with cost metrics grouped by the selected type.
    """

    # Convert 'Date' to datetime format
    df["Date"] = pd.to_datetime(df["Date"])

    # Filter data based on the selected time period
    today = date.today()

    if time == "last_365":
        start_date = today - timedelta(days=365)
        start_date = pd.to_datetime(start_date)  # Convert to datetime to match pandas type
        filtered_df = df[df["Date"] >= start_date]
    elif time in ["2023", "2024"]:
        filtered_df = df[df["Date"].dt.year == int(time)]
    else:
        raise ValueError("Invalid time option. Choose 'last_365', '2023', or '2024'.")

    # Validate 'show' argument
    if show not in ["age_group", "channel"]:
        raise ValueError("Invalid show option. Choose 'age_group' or 'channel'.")

    # Group by the selected type
    grouped = filtered_df.groupby(show).agg(
        total_ad_spend=("ad_spend", "sum"),
        total_views=("views", "sum"),
        total_leads=("leads", "sum"),
        total_new_accounts=("new_accounts", "sum")
    ).reset_index()

    # Calculate cost metrics
    grouped["costPerLead"] = grouped["total_ad_spend"] / grouped["total_leads"]
    grouped["costPerView"] = grouped["total_ad_spend"] / grouped["total_views"]
    grouped["costPerAccount"] = grouped["total_ad_spend"] / grouped["total_new_accounts"]

    # Handle divide-by-zero cases (replace infinities with 0)
    grouped.replace([float("inf"), -float("inf")], 0, inplace=True)
    grouped.fillna(0, inplace=True)

    # Convert to desired format
    result = grouped.rename(columns={show: "age_group"}).to_dict(orient="records")

    return result

# for stacked bar chart
def transform_data(df, time="2023", show="age_group"):
    """
    Transforms the marketing data into a format suitable for frontend display.

    :param df: Pandas DataFrame containing marketing data.
    :param time: String representing the time selection ("last_365", "2023", "2024").
    :param show: String representing the grouping ("age_group" or "channel").
    :return: List of dictionaries containing the transformed data by category.
    """

    # Convert 'Date' to datetime format
    df["Date"] = pd.to_datetime(df["Date"])

    # Filter data based on the selected time period
    today = date.today()

    if time == "last_365":
        start_date = today - timedelta(days=365)
        start_date = pd.to_datetime(start_date)  # Convert to datetime to match pandas type
        filtered_df = df[df["Date"] >= start_date]
    elif time in ["2023", "2024"]:
        filtered_df = df[df["Date"].dt.year == int(time)]
    else:
        raise ValueError("Invalid time option. Choose 'last_365', '2023', or '2024'.")

    # Validate 'show' argument
    if show not in ["age_group", "channel"]:
        raise ValueError("Invalid show option. Choose 'age_group' or 'channel'.")

    # Group by the selected type and aggregate data
    grouped = filtered_df.groupby([show]).agg(
        total_ad_spend=("ad_spend", "sum"),
        total_views=("views", "sum"),
        total_leads=("leads", "sum"),
        total_new_accounts=("new_accounts", "sum"),
        total_revenue=("revenue", "sum")
    ).reset_index()

    # Create the structure for the frontend
    categories = ["Spending", "Views", "Leads", "New Accounts", "Revenue"]
    transformed_data = []

    for category in categories:
        category_data = {"category": category}
        for channel_or_age_group in grouped[show]:
            if category == "Spending":
                category_data[channel_or_age_group] = grouped.loc[grouped[show] == channel_or_age_group, "total_ad_spend"].values[0].item()
            elif category == "Views":
                category_data[channel_or_age_group] = grouped.loc[grouped[show] == channel_or_age_group, "total_views"].values[0].item()
            elif category == "Leads":
                category_data[channel_or_age_group] = grouped.loc[grouped[show] == channel_or_age_group, "total_leads"].values[0].item()
            elif category == "New Accounts":
                category_data[channel_or_age_group] = grouped.loc[grouped[show] == channel_or_age_group, "total_new_accounts"].values[0].item()
            elif category == "Revenue":
                category_data[channel_or_age_group] = grouped.loc[grouped[show] == channel_or_age_group, "total_revenue"].values[0].item()
        
        transformed_data.append(category_data)

    return transformed_data