import aws_cdk as cdk
from stacks.anomaly_stack import AnomalyStack

app = cdk.App()
AnomalyStack(app, "AnomalyStack", env=cdk.Environment(region="eu-west-1"))
app.synth()