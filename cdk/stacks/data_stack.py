from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_dynamodb as ddb,
    aws_ssm as ssm,
)
from constructs import Construct


class DataStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, env_name: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        table = ddb.Table(
            self,
            "OrdersTable",
            table_name=f"orders-{env_name}",
            partition_key=ddb.Attribute(name="orderId", type=ddb.AttributeType.STRING),
            billing_mode=ddb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY if env_name == "dev" else RemovalPolicy.RETAIN,
        )

        # Store table name in SSM (Lambda will read SSM -> table name)
        table_name_param = ssm.StringParameter(
            self,
            "OrdersTableNameParam",
            parameter_name=f"/orders/{env_name}/ddb/table_name",
            string_value=table.table_name,
        )

        self.table = table
        self.table_name_param = table_name_param