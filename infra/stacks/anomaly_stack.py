import os
from aws_cdk import Stack, Duration, RemovalPolicy, aws_lambda as _lambda, aws_events as events, aws_events_targets as targets, aws_iam as iam, aws_s3 as s3, aws_s3_deployment as s3deploy
from constructs import Construct


class AnomalyStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # S3 bucket for transaction data — one prefix per client
        bucket = s3.Bucket(
            self, "TransactionData",
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        layer = _lambda.LayerVersion(
            self, "AgentDeps",
            code=_lambda.Code.from_asset("../layer"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
        )

        fn = _lambda.Function(
            self, "AnomalyDetector",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="handler.lambda_handler",
            code=_lambda.Code.from_asset("../src"),
            layers=[layer],
            timeout=Duration.minutes(5),
            environment={
                "ANTHROPIC_API_KEY": os.environ.get("ANTHROPIC_API_KEY", ""),
                "LANGSMITH_API_KEY": os.environ.get("LANGSMITH_API_KEY", ""),
                "LANGSMITH_TRACING": "true",
                "LANGSMITH_ENDPOINT": "https://eu.api.smith.langchain.com",
                "LANGSMITH_PROJECT": "anomaly-alerting-service",
                "TRANSACTION_BUCKET": bucket.bucket_name,
            }
        )

        # Grant Lambda read access to the S3 bucket
        bucket.grant_read(fn)

        # Grant Lambda permission to write CloudWatch metrics
        fn.add_to_role_policy(iam.PolicyStatement(
            actions=["cloudwatch:PutMetricData"],
            resources=["*"],
        ))

        # Trigger Lambda every hour via EventBridge
        rule = events.Rule(
            self, "AnomalySchedule",
            schedule=events.Schedule.rate(Duration.hours(1))
        )
        rule.add_target(targets.LambdaFunction(fn))