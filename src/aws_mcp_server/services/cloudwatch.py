"""CloudWatch service integration (read-only)."""

from typing import Any, Callable, Dict, List
from datetime import datetime, timedelta

from .base import BaseService


class CloudWatchService(BaseService):
    """CloudWatch monitoring and observability operations (read-only)."""

    service_name = "cloudwatch"
    display_name = "CloudWatch"
    description = "Monitoring and observability service (read-only access)"

    def _build_tools(self) -> Dict[str, Callable]:
        return {
            "list_metrics": self.list_metrics,
            "list_alarms": self.list_alarms,
            "get_metric_statistics": self.get_metric_statistics,
        }

    async def list_metrics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List CloudWatch metrics."""
        client = self.get_client(params.get("region"))

        kwargs: Dict[str, Any] = {}
        if namespace := params.get("namespace"):
            kwargs["Namespace"] = namespace
        if metric_name := params.get("metric_name"):
            kwargs["MetricName"] = metric_name

        all_metrics: List[Dict[str, Any]] = []
        next_token = None

        while True:
            if next_token:
                kwargs["NextToken"] = next_token

            response = client.list_metrics(**kwargs)

            for metric in response.get("Metrics", []):
                all_metrics.append({
                    "namespace": metric.get("Namespace"),
                    "metric_name": metric.get("MetricName"),
                    "dimensions": metric.get("Dimensions", []),
                    "statistics": metric.get("Statistics", []),
                    "unit": metric.get("Unit"),
                })

            if "NextToken" not in response:
                break
            next_token = response["NextToken"]

        return {
            "count": len(all_metrics),
            "metrics": all_metrics[:100],  # Limit to 100 metrics
            "namespace": params.get("namespace", "All"),
        }

    async def list_alarms(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List CloudWatch alarms."""
        client = self.get_client(params.get("region"))

        kwargs: Dict[str, Any] = {"MaxRecords": 100}
        if state := params.get("state_value"):
            kwargs["StateValue"] = state  # "ALARM", "INSUFFICIENT_DATA", "OK"

        response = client.describe_alarms(**kwargs)

        alarms = []
        for alarm in response.get("MetricAlarms", []):
            alarms.append({
                "alarm_name": alarm.get("AlarmName"),
                "alarm_arn": alarm.get("AlarmArn"),
                "state_value": alarm.get("StateValue"),
                "state_reason": alarm.get("StateReason"),
                "metric_name": alarm.get("MetricName"),
                "namespace": alarm.get("Namespace"),
                "statistic": alarm.get("Statistic"),
                "dimensions": alarm.get("Dimensions", []),
                "threshold": alarm.get("Threshold"),
                "comparison_operator": alarm.get("ComparisonOperator"),
                "period": alarm.get("Period"),
                "evaluation_periods": alarm.get("EvaluationPeriods"),
                "enabled": alarm.get("ActionsEnabled"),
                "alarm_description": alarm.get("AlarmDescription"),
            })

        return {
            "count": len(alarms),
            "alarms": alarms,
            "state_filter": params.get("state_value", "All"),
        }

    async def get_metric_statistics(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get metric statistics for a specified time period."""
        client = self.get_client(params.get("region"))

        # Parse dates
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=params.get("hours", 1))

        kwargs = {
            "Namespace": params["namespace"],
            "MetricName": params["metric_name"],
            "StartTime": start_time,
            "EndTime": end_time,
            "Period": params.get("period", 300),  # 5 minutes default
            "Statistics": params.get("statistics", ["Average", "Sum"]),
        }

        if dimensions := params.get("dimensions"):
            kwargs["Dimensions"] = dimensions

        response = client.get_metric_statistics(**kwargs)

        datapoints = []
        for dp in response.get("Datapoints", []):
            datapoints.append({
                "timestamp": str(dp.get("Timestamp", "")),
                "average": dp.get("Average"),
                "sum": dp.get("Sum"),
                "minimum": dp.get("Minimum"),
                "maximum": dp.get("Maximum"),
                "sample_count": dp.get("SampleCount"),
                "unit": dp.get("Unit"),
            })

        return {
            "metric_name": params["metric_name"],
            "namespace": params["namespace"],
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat(),
            "datapoints": sorted(datapoints, key=lambda x: x["timestamp"]),
            "label": response.get("Label"),
        }
