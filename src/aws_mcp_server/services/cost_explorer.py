"""Cost Explorer service integration (read-only)."""

from typing import Any, Callable, Dict
from datetime import datetime, timedelta

from .base import BaseService


class CostExplorerService(BaseService):
    """AWS Cost Explorer operations (read-only)."""

    service_name = "ce"
    display_name = "Cost Explorer"
    description = "AWS Cost and Usage reporting (read-only access)"

    def _build_tools(self) -> Dict[str, Callable]:
        return {
            "get_cost_and_usage": self.get_cost_and_usage,
            "get_cost_forecast": self.get_cost_forecast,
        }

    async def get_cost_and_usage(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get cost and usage data for a specified time period."""
        client = self.get_client(params.get("region"))

        # Default to last 7 days
        days = params.get("days", 7)
        end_date = datetime.utcnow().date()
        start_date = end_date - timedelta(days=days)

        kwargs = {
            "TimePeriod": {
                "Start": start_date.isoformat(),
                "End": end_date.isoformat(),
            },
            "Granularity": params.get("granularity", "DAILY"),  # DAILY, MONTHLY
            "Metrics": params.get("metrics", ["UnblendedCost"]),
            "GroupBy": [
                {"Type": "DIMENSION", "Key": params.get("group_by", "SERVICE")}
            ],
        }

        if filter_dict := params.get("filter"):
            kwargs["Filter"] = filter_dict

        response = client.get_cost_and_usage(**kwargs)

        results = []
        for result in response.get("ResultsByTime", []):
            time_period = result.get("TimePeriod", {})
            groups = result.get("Groups", [])

            for group in groups:
                results.append({
                    "start_date": time_period.get("Start"),
                    "end_date": time_period.get("End"),
                    "dimension": group.get("Keys", [""])[0],
                    "metrics": group.get("Metrics", {}),
                    "estimated": result.get("Estimated", False),
                })

        # Calculate totals
        total_cost = 0.0
        for result in results:
            if "UnblendedCost" in result["metrics"]:
                total_cost += float(result["metrics"]["UnblendedCost"].get("Amount", 0))

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "granularity": params.get("granularity", "DAILY"),
            "group_by": params.get("group_by", "SERVICE"),
            "total_cost": round(total_cost, 2),
            "results": results,
            "next_page_token": response.get("NextPageToken"),
        }

    async def get_cost_forecast(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Forecast AWS costs for future periods."""
        client = self.get_client(params.get("region"))

        # Default to next 7 days
        days = params.get("days", 7)
        end_date = datetime.utcnow().date() + timedelta(days=days)
        start_date = datetime.utcnow().date()

        kwargs = {
            "TimePeriod": {
                "Start": start_date.isoformat(),
                "End": end_date.isoformat(),
            },
            "Metric": params.get("metric", "UNBLENDED_COST"),
            "Granularity": params.get("granularity", "DAILY"),
        }

        if filter_dict := params.get("filter"):
            kwargs["Filter"] = filter_dict

        response = client.get_cost_forecast(**kwargs)

        forecasts = []
        for item in response.get("ForecastResultsByTime", []):
            time_period = item.get("TimePeriod", {})
            mean_value = item.get("MeanValue")
            preds = item.get("PredictionIntervalContents", {})

            forecasts.append({
                "start_date": time_period.get("Start"),
                "end_date": time_period.get("End"),
                "mean_value": float(mean_value) if mean_value else 0.0,
                "prediction_lower_bound": float(preds.get("LowerBound", 0)) if preds.get("LowerBound") else None,
                "prediction_upper_bound": float(preds.get("UpperBound", 0)) if preds.get("UpperBound") else None,
                "total": item.get("Total", {}),
            })

        return {
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "metric": params.get("metric", "UNBLENDED_COST"),
            "granularity": params.get("granularity", "DAILY"),
            "forecasts": forecasts,
        }
