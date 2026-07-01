import json
from agent import run_anomaly_agent
from tools.anomaly_tools import detect_anomalies, load_transactions, push_metric


def lambda_handler(event, context):
    client_id = event.get("client_id", "demo")
    date = event.get("date", "2026-01-20")

    # Run the agent
    result = run_anomaly_agent()

    # Push anomaly count as a CloudWatch custom metric
    transactions = load_transactions(client_id=client_id, date=date)
    anomalies = detect_anomalies(transactions)
    push_metric(len(anomalies))

    return {"statusCode": 200, "body": json.dumps({"result": result})}
