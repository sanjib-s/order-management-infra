from aws_cdk import (
    Stack,
    Duration,
    aws_lambda as _lambda,
    aws_iam as iam,
    aws_ssm as ssm,
    aws_ec2 as ec2,
)
from aws_cdk.aws_apigatewayv2 import HttpApi, HttpMethod
from aws_cdk.aws_apigatewayv2_integrations import HttpLambdaIntegration
from aws_cdk.aws_apigatewayv2_authorizers import HttpJwtAuthorizer
from constructs import Construct

from .shared_imports import NetworkImports


class ApiStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        env_name: str,
        ssm_paths: dict,
        user_pool_id: str,
        app_client_id: str,
        ddb_table_arn: str,
        ddb_table_name_param: str,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        net = NetworkImports(self, ssm_paths=ssm_paths)

       
        alb_dns = ssm.StringParameter.value_for_string_parameter(self, ssm_paths["eksOrdersAlbDns"])

        orders_fn = _lambda.Function(
            self,
            "OrdersHandlerFn",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="app.handler",
            code=_lambda.Code.from_asset("lambda"),
            timeout=Duration.seconds(15),
            vpc=net.vpc,
            vpc_subnets=ec2.SubnetSelection(subnets=[net.vpc.private_subnets[0]]),
            security_groups=[net.lambda_sg],
            environment={
                "TABLE_NAME_PARAM": ddb_table_name_param,  # SSM param name
                "EKS_ORDERS_URL": f"http://{alb_dns}/orders",
            },
        )

        # Lambda access to read the SSM table name param
        orders_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[f"arn:aws:ssm:{self.region}:{self.account}:parameter/orders/{env_name}/ddb/table_name"],
            )
        )

        # DynamoDB access (scope to the actual table ARN)
        orders_fn.add_to_role_policy(
            iam.PolicyStatement(
                actions=["dynamodb:GetItem", "dynamodb:PutItem", "dynamodb:UpdateItem"],
                resources=[ddb_table_arn],
            )
        )

        api = HttpApi(self, "OrdersHttpApi", api_name=f"orders-http-api-{env_name}")

        issuer = f"https://cognito-idp.{self.region}.amazonaws.com/{user_pool_id}"
        authorizer = HttpJwtAuthorizer(
            "OrdersJwtAuthorizer",
            jwt_issuer=issuer,
            jwt_audience=[app_client_id],
        )

        integration = HttpLambdaIntegration("OrdersLambdaIntegration", orders_fn)

        api.add_routes(
            path="/orders",
            methods=[HttpMethod.POST],
            integration=integration,
            #authorizer=authorizer,
        )

        api.add_routes(
            path="/orders/{orderId}",
            methods=[HttpMethod.GET],
            integration=integration,
            #authorizer=authorizer,
        )