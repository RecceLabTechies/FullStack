import logging
import threading

import pandas as pd
from prophet import Prophet

from app.database.connection import get_campaign_performance_collection
from app.models.prophet_prediction import ProphetPredictionModel

logger = logging.getLogger(__name__)

# Global lock to ensure only one prediction can run at a time
prediction_lock = threading.Lock()
# Global flag to track if a prediction is already running
is_prediction_running = False
# Global variable to track the details of the last prediction
last_prediction = {"forecast_months": None, "timestamp": None, "status": "not_run"}


def run_prophet_prediction(forecast_months=4):
    """
    Run the Prophet prediction pipeline.
    This is a long-running task that:
    1. Acquires data from the campaign_performance collection
    2. Processes it and runs the Prophet model
    3. Deletes existing data in prophet_predictions collection
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

        # Get data from MongoDB
        campaign_collection = get_campaign_performance_collection()
        # Convert MongoDB data to DataFrame
        campaign_data = list(campaign_collection.find({}, {"_id": 0}))

        if not campaign_data:
            logger.error("No campaign data found in MongoDB")
            return {"status": "error", "message": "No campaign data found"}

        # Convert to DataFrame and prepare data
        df = pd.DataFrame(campaign_data)

        # Convert timestamp to datetime
        df["date_dt"] = pd.to_datetime(df["date"], unit="s")

        # Group by month
        df_grouped = (
            df.groupby(pd.Grouper(key="date_dt", freq="M"))
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

        # Run predictions for each metric
        def prophet_forecast(df_grouped, predict_col, time_period):
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
        future_rev = prophet_forecast(df_grouped, "revenue", forecast_months)
        future_ad = prophet_forecast(df_grouped, "ad_spend", forecast_months)
        future_accounts = prophet_forecast(df_grouped, "new_accounts", forecast_months)

        # Combine the forecasts
        predictions = pd.DataFrame()
        predictions["ds"] = future_rev["ds"]
        predictions["revenue"] = future_rev["yhat"]
        predictions["ad_spend"] = future_ad["yhat"]
        predictions["new_accounts"] = future_accounts["yhat"]

        # Convert to unix timestamp and prepare for MongoDB
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
