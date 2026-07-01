import json
import os
import numpy as np
import boto3

MOCK_DATA = [
        {"date": "2026-01-01", "price": 450000, "volume": 12},
        {"date": "2026-01-02", "price": 455000, "volume": 11},
        {"date": "2026-01-03", "price": 448000, "volume": 13},
        {"date": "2026-01-04", "price": 452000, "volume": 10},
        {"date": "2026-01-05", "price": 460000, "volume": 12},
        {"date": "2026-01-06", "price": 453000, "volume": 11},
        {"date": "2026-01-07", "price": 449000, "volume": 14},
        {"date": "2026-01-08", "price": 455000, "volume": 12},
        {"date": "2026-01-09", "price": 451000, "volume": 11},
        {"date": "2026-01-10", "price": 457000, "volume": 13},
        {"date": "2026-01-11", "price": 454000, "volume": 12},
        {"date": "2026-01-12", "price": 450000, "volume": 11},
        {"date": "2026-01-13", "price": 456000, "volume": 10},
        {"date": "2026-01-14", "price": 452000, "volume": 12},
        {"date": "2026-01-15", "price": 620000, "volume": 3},   # anomaly — price spike
        {"date": "2026-01-16", "price": 453000, "volume": 11},
        {"date": "2026-01-17", "price": 448000, "volume": 13},
        {"date": "2026-01-18", "price": 230000, "volume": 2},   # anomaly — price drop
        {"date": "2026-01-19", "price": 455000, "volume": 12},
        {"date": "2026-01-20", "price": 451000, "volume": 11},
]


def load_transactions(client_id: str = "demo", date: str = "2026-01-20") -> list[dict]:
    """Load property transaction data for a specific client from S3.

    Each client's data is isolated under their own S3 prefix: {client_id}/transactions/{date}.json
    Falls back to mock data if TRANSACTION_BUCKET env var is not set (local development).
    """
    bucket = os.environ.get("TRANSACTION_BUCKET")
    if not bucket:
        print("TRANSACTION_BUCKET not set, using mock data.")
        return MOCK_DATA

    s3 = boto3.client("s3")
    key = f"{client_id}/transactions/{date}.json"
    print(f"Loading transactions from s3://{bucket}/{key}")
    try:
        obj = s3.get_object(Bucket=bucket, Key=key)
        data = json.loads(obj["Body"].read())
        print(f"Loaded {len(data)} transactions from S3 for client '{client_id}'.")
        return data
    except Exception as e:
        print(f"Failed to load from S3 ({e}), using mock data.")
        return MOCK_DATA


def detect_anomalies(transactions: list[dict], threshold: float = 2.0) -> list[dict]:
    """Detect price anomalies using z-score analysis. Returns a list of anomalous transactions.

    A transaction is flagged as an anomaly if its price z-score exceeds the threshold.
    Default threshold of 2.0 means prices more than 2 standard deviations from the mean are flagged.
    """
    prices = [t["price"] for t in transactions]
    mean = float(np.mean(prices))
    std = float(np.std(prices))

    if std == 0:
        return []

    anomalies = []
    for t in transactions:
        z = abs((t["price"] - mean) / std)
        if z > threshold:
            anomalies.append({
                **t,
                "z_score": round(z, 2),
                "mean": round(mean, 2),
                "std": round(std, 2),
            })

    return anomalies


def push_metric(anomaly_count: int) -> None:
    """Push a custom AnomalyCount metric to CloudWatch."""
    cw = boto3.client("cloudwatch", region_name="eu-west-1")
    cw.put_metric_data(
        Namespace="AnomalyAlertingService",
        MetricData=[{
            "MetricName": "AnomalyCount",
            "Value": anomaly_count,
            "Unit": "Count",
        }]
    )


def fire_alert(anomalies: list[dict]) -> str:
    """Log anomalies as structured alerts. Each anomaly is printed as JSON, which CloudWatch captures automatically.

    Returns a summary string of how many alerts were fired.
    """
    if not anomalies:
        return "No anomalies detected. No alerts fired."

    for anomaly in anomalies:
        print(json.dumps({
            "alert": "ANOMALY_DETECTED",
            "date": anomaly["date"],
            "price": anomaly["price"],
            "z_score": anomaly["z_score"],
            "mean": anomaly["mean"],
            "std": anomaly["std"],
        }))

    return f"Fired {len(anomalies)} alert(s)."
