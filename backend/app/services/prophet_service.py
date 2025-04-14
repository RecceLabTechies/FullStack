import logging
import threading

import numpy as np
import pandas as pd
from prophet import Prophet
from sklearn.preprocessing import TargetEncoder
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tsa.stattools import adfuller

from app.database.connection import Database
from app.models.prophet_prediction import ProphetPredictionModel

logger = logging.getLogger(__name__)

# Global lock to ensure only one prediction can run at a time
prediction_lock = threading.Lock()
# Global flag to track if a prediction is already running
is_prediction_running = False
# Global variable to track the details of the last prediction
last_prediction = {"forecast_months": None, "timestamp": None, "status": "not_run"}


def prediction_pipeline(df, numerical_cols, period, target_var, n_pred_periods=4):
    """Takes in a df, prediction period, output predictions using enhanced techniques"""

    def encode_categorical_resample(df, period, target_var):
        """
        - Removes ID columns, low-correlated columns to target var
        - Target encodes categorical variables
        - Resamples df to user required period

        Output: df with useful columns (categorical encoded & numerical)
        """
        # First handle string columns
        string_cols = df.select_dtypes(include=["object"]).columns
        for col in string_cols:
            if df[col].nunique() > 0.5 * len(
                df
            ):  # concept: if you got a shit ton of unique values, it's probably an ID
                df = df.drop(columns=[col])

        # Then handle numerical columns correlation
        numerical_cols = df.select_dtypes(include=["number"]).columns
        correlation_threshold = (
            0.4  # Higher as multicollinearity and feature relevance are major concerns.
        )
        corr_matrix = df[numerical_cols].corr()
        cols_to_drop = [
            col
            for col in corr_matrix.columns
            if (corr_matrix[col].abs() < correlation_threshold).sum()
        ]
        df = df.drop(columns=cols_to_drop)

        # Initialize target encoder
        target_encoder = TargetEncoder()

        # Apply target encoding to categorical columns
        categorical_cols = df.select_dtypes(include=["object"]).columns.tolist()
        if categorical_cols:
            df[categorical_cols] = target_encoder.fit_transform(
                df[categorical_cols], df[target_var]
            )

        # apply groupby to get the mean/ mode of the target by each group
        try:
            df = df.resample(
                period
            ).agg(
                {
                    col: "mean"
                    if col in categorical_cols
                    else "sum"  # mean vector for features originally categorical, sum for numerical
                    for col in df.columns
                }
            )

            # Check if too many rows became nil after resampling
            nil_ratio = df.isna().sum() / len(df)
            if (nil_ratio > 0.5).any():  # If more than 50% of any column is nil
                raise ValueError(
                    f"Resampling period '{period}' is too granular for the input data frequency. Many rows became nil after resampling, select another PERIOD"
                )

        except Exception as e:
            raise Exception(f"Error during resampling: {str(e)}")

        # Drop columns with a single unique value or constant
        df = df.loc[
            :, df.nunique() > 1
        ]  # logic -- if categorical vector is same for all periods, it doesn't matter

        return df

    def feature_engineering(df, numerical_cols, target_var):
        """
        Manually implement feature engineering on the input DataFrame,

        Perform feature engineering on the input DataFrame, implementing:
        - Log transform on money related fields -- (revenue, ad spend)
        - EWA (Exponential Weighted Average)
        - Moving average
        - Auto differencing (for stationarity)
        - Lagged variables (for time series)

        Args:
            df: DataFrame with additional engineered features as new columns
        """

        dropped_col = df[target_var].copy()
        df = df.drop(columns=[target_var])

        for col in numerical_cols:
            if col != target_var and col in df.columns:
                if (df[col] > 0).all():  # Ensure we don't log transform negative values
                    df[f"log_{col}"] = np.log(df[col])  # Log transform
                df[f"ewa_{col}"] = (
                    df[col].ewm(span=12, adjust=False).mean().shift(1)
                )  # Exponential Weighted Average
                df[f"ma_{col}"] = (
                    df[col].rolling(window=12).mean().shift(1)
                )  # Moving Average

        def check_stationarity(series):
            if series.isna().any() or len(series.dropna()) <= 5:
                return True  # Insufficient data or NaN values - skip test

            try:
                result = adfuller(series.dropna())
                return result[1] < 0.05  # Returns True if stationary
            except Exception:
                return True  # Error in test, assume stationary

        # Check and apply differencing for each feature (max 2 times)
        diffed_columns = []
        for col in df.columns:
            if col in df.select_dtypes(include=["number"]).columns:
                diff_count = 1
                while (
                    not check_stationarity(df[col]) and diff_count < 3
                ):  # avoid over-differencing -> white noise
                    df[col] = df[col].diff()
                    df[f"{col}_diff{diff_count}"] = df[col]
                    diff_count += 1
                if diff_count > 1:  # If differencing was applied
                    diffed_columns.append(col)

        # Remove original columns that had differencing applied -- good practice
        df.drop(columns=diffed_columns, inplace=True, errors="ignore")

        # Create lagged variables for each column, except for the target
        for col in df.columns:
            df[f"{col}_lag1"] = df[col].shift(1)
            df[f"{col}_lag2"] = df[col].shift(2)

        df[target_var] = dropped_col
        df = (
            df.dropna()
        )  ## Drop rows with NaN values, better to use for moving averages

        return df

    def feature_selection(
        df, target_var, vif_threshold=7, xgb_importance_threshold=0.05
    ):
        """
        Feature selection using VIF (Variance Inflation Factor).

        Args:
            df: DataFrame of features
            vif_threshold: Maximum allowed VIF value (default=7)

        Returns:
            DataFrame with selected features (columns)
        """
        # First pass: VIF-based selection
        dropped_col = df[target_var].copy()
        df = df.drop(columns=[target_var])
        features = df.select_dtypes(include=["number"]).columns.tolist()

        # Skip VIF if we don't have enough features
        if len(features) <= 2:
            df[target_var] = dropped_col
            return df

        try:
            while len(features) > 1:
                vif_data = pd.DataFrame()
                vif_data["Feature"] = features
                vif_data["VIF"] = [
                    variance_inflation_factor(df[features].values, i)
                    for i in range(len(features))
                ]

                if vif_data["VIF"].max() <= vif_threshold:
                    break

                highest_vif_feature = vif_data.loc[vif_data["VIF"].idxmax(), "Feature"]
                features.remove(highest_vif_feature)

                if len(features) == 1:
                    break

            df = df[features]
            df[target_var] = dropped_col

            return df
        except Exception as e:
            logger.warning(f"VIF calculation error: {e}. Skipping feature selection.")
            df[target_var] = dropped_col
            return df

    def prophet_forecast(df, target_var, period, n_pred_periods):
        """Use Prophet to forecast the target variable"""
        try:
            df = df.reset_index()
            # Prepare data for Prophet
            df_prophet = df.rename(columns={"Date": "ds", target_var: "y"})

            # Initialize Prophet model
            model = Prophet()
            model.fit(df_prophet)

            # Create future dataframe for prediction
            future = model.make_future_dataframe(periods=n_pred_periods, freq=period)

            # Make predictions
            forecast = model.predict(future)
            forecast_snippet = forecast[["ds", "yhat"]][-n_pred_periods:]

            return forecast_snippet, model
        except Exception as e:
            logger.error(f"Error in prophet forecasting: {e}")
            # Fallback to simple Prophet model if the advanced pipeline fails
            simple_df = pd.DataFrame()
            simple_df["ds"] = df["Date"]
            simple_df["y"] = df[target_var]

            model = Prophet()
            model.fit(simple_df)

            future = model.make_future_dataframe(periods=n_pred_periods, freq=period)
            forecast = model.predict(future)
            forecast_snippet = forecast[["ds", "yhat"]][-n_pred_periods:]

            return forecast_snippet, model

    try:
        # Safely apply the pipeline with error handling
        numerical_cols = df.select_dtypes(include=["number"]).columns.tolist()

        # Apply the enhanced processing pipeline
        df = encode_categorical_resample(df, period, target_var)
        df = feature_engineering(df, numerical_cols, target_var)
        df = feature_selection(df, target_var)
        forecast_df, model = prophet_forecast(df, target_var, period, n_pred_periods)

        return forecast_df, model
    except Exception as e:
        logger.error(f"Error in prediction pipeline: {e}")
        # Fallback to basic prophet forecasting
        logger.info("Falling back to basic Prophet forecasting")
        df = df.reset_index() if hasattr(df, "reset_index") else df
        if "Date" not in df.columns and df.index.name != "Date":
            raise ValueError("DataFrame must have a 'Date' column or index")

        simple_df = pd.DataFrame()
        simple_df["ds"] = df["Date"] if "Date" in df.columns else df.index
        simple_df["y"] = df[target_var]

        model = Prophet()
        model.fit(simple_df)

        future = model.make_future_dataframe(periods=n_pred_periods, freq=period)
        forecast = model.predict(future)
        forecast_snippet = forecast[["ds", "yhat"]][-n_pred_periods:]

        return forecast_snippet, model


def run_prophet_prediction(forecast_months=4):
    """
    Run the Prophet prediction pipeline.
    This is a long-running task that:
    1. Acquires data from the campaign_performance table
    2. Processes it and runs the Prophet model
    3. Deletes existing data in prophet_predictions table
    4. Inserts new prediction data

    Args:
        forecast_months (int): Number of months to forecast (1-12), defaults to 4

    Returns:
        dict: Status of the prediction run
    """
    global is_prediction_running, last_prediction

    # Update last prediction details
    last_prediction["forecast_months"] = forecast_months
    last_prediction["timestamp"] = pd.Timestamp.now().timestamp()
    last_prediction["status"] = "starting"

    # Check if prediction is already running
    if is_prediction_running:
        logger.info("A prediction is already running, skipping this request")
        last_prediction["status"] = "skipped"
        return {"status": "in_progress", "message": "A prediction is already running"}

    # Try to acquire the lock, return immediately if unable
    if not prediction_lock.acquire(blocking=False):
        logger.info(
            "Unable to acquire prediction lock, another prediction may be starting"
        )
        last_prediction["status"] = "lock_failed"
        return {
            "status": "error",
            "message": "Unable to start prediction, another task may be starting",
        }

    try:
        # Set flag to indicate prediction is running
        is_prediction_running = True
        last_prediction["status"] = "running"
        logger.info(f"Starting Prophet prediction task for {forecast_months} months")

        # Get data from PostgreSQL
        campaign_data = Database.execute_query("SELECT * FROM campaign_performance")

        if not campaign_data:
            logger.error("No campaign data found in the database")
            return {"status": "error", "message": "No campaign data found"}

        # Convert to DataFrame and prepare data
        df = pd.DataFrame(campaign_data)

        # Convert timestamp to datetime
        df["date_dt"] = pd.to_datetime(df["date"], unit="s")
        df.set_index("date_dt", inplace=True)

        # Define numerical columns
        numerical_cols = ["ad_spend", "new_accounts", "revenue", "views", "leads"]

        # Run enhanced predictions for each metric
        try:
            logger.info("Running enhanced revenue prediction model")
            future_rev, _ = prediction_pipeline(
                df.copy(), numerical_cols, "M", "revenue", forecast_months
            )

            logger.info("Running enhanced ad spend prediction model")
            future_ad, _ = prediction_pipeline(
                df.copy(), numerical_cols, "M", "ad_spend", forecast_months
            )

            logger.info("Running enhanced new accounts prediction model")
            future_accounts, _ = prediction_pipeline(
                df.copy(), numerical_cols, "M", "new_accounts", forecast_months
            )
        except Exception as e:
            logger.error(f"Enhanced prediction pipeline failed: {e}")
            logger.info("Falling back to original Prophet implementation")

            # Group by month (fallback to original implementation)
            df_grouped = (
                df.groupby(pd.Grouper(freq="M"))
                .agg(
                    {
                        "ad_spend": "sum",
                        "new_accounts": "sum",
                        "revenue": "sum",
                    }
                )
                .reset_index()
            )

            # Rename for prophet
            df_grouped.rename(columns={"date_dt": "Date"}, inplace=True)

            # Define simple forecast function (from original implementation)
            def simple_prophet_forecast(df_grouped, predict_col, time_period):
                # Prepare data for Prophet
                df_prophet = df_grouped.rename(columns={"Date": "ds", predict_col: "y"})

                # Initialize Prophet model
                model = Prophet()
                model.fit(df_prophet)

                # Create future dataframe for prediction
                future = model.make_future_dataframe(periods=time_period, freq="M")

                # Make predictions
                forecast = model.predict(future)
                forecast_snippet = forecast[["ds", "yhat"]][-time_period:]

                return forecast_snippet

            # Get individual forecasts with user-specified forecast months
            future_rev = simple_prophet_forecast(df_grouped, "revenue", forecast_months)
            future_ad = simple_prophet_forecast(df_grouped, "ad_spend", forecast_months)
            future_accounts = simple_prophet_forecast(
                df_grouped, "new_accounts", forecast_months
            )

        # Combine the forecasts
        predictions = pd.DataFrame()
        predictions["ds"] = future_rev["ds"]
        predictions["revenue"] = future_rev["yhat"]
        predictions["ad_spend"] = future_ad["yhat"]
        predictions["new_accounts"] = future_accounts["yhat"]

        # Convert to unix timestamp and prepare for database
        predictions_list = []
        for _, row in predictions.iterrows():
            timestamp = int(row["ds"].timestamp())
            predictions_list.append(
                {
                    "date": timestamp,
                    "revenue": float(row["revenue"]),
                    "ad_spend": float(row["ad_spend"]),
                    "new_accounts": float(row["new_accounts"]),
                }
            )

        # Delete existing predictions
        deleted_count = ProphetPredictionModel.delete_all()
        logger.info(f"Deleted {deleted_count} existing prophet predictions")

        # Insert new predictions
        if predictions_list:
            inserted_count = ProphetPredictionModel.create_many(predictions_list)
            logger.info(f"Inserted {inserted_count} new prophet predictions")

            last_prediction["status"] = "completed"
            return {
                "status": "success",
                "message": f"Prediction completed successfully. Deleted {deleted_count} records and inserted {inserted_count} new predictions.",
            }
        else:
            logger.error("No predictions were generated")
            last_prediction["status"] = "failed"
            return {"status": "error", "message": "No predictions were generated"}

    except Exception as e:
        logger.exception(f"Error running prophet prediction: {e}")
        last_prediction["status"] = "error"
        return {"status": "error", "message": f"Error running prediction: {str(e)}"}
    finally:
        # Reset flag and release lock
        is_prediction_running = False
        prediction_lock.release()


def get_prediction_status():
    """
    Check if a prediction is currently running and return information about the last prediction

    Returns:
        dict: The current status of the prediction task and details about the last prediction
    """
    global last_prediction

    status = {
        "is_running": is_prediction_running,
        "last_prediction": {
            "forecast_months": last_prediction["forecast_months"],
            "timestamp": last_prediction["timestamp"],
            "status": last_prediction["status"],
        },
    }

    if is_prediction_running:
        status["status"] = "in_progress"
        status["message"] = "Prediction is currently running"
    else:
        status["status"] = "idle"
        status["message"] = "No prediction is currently running"

    return status
