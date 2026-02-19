#!/usr/bin/env python3
import os
from aws_cdk import App, Environment

from config import EnvConfig
from stacks.data_stack import DataStack
from stacks.auth_stack import AuthStack
from stacks.api_stack import ApiStack


app = App()

env_file = app.node.try_get_context("envFile") or "environments/dev.json"
cfg = EnvConfig.load(env_file)

aws_env = Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"),
    region=os.getenv("CDK_DEFAULT_REGION", "ca-central-1"),
)

data = DataStack(app, f"OrdersDataStack-{cfg.env_name}", env_name=cfg.env_name, env=aws_env)

auth = AuthStack(
    app,
    f"OrdersAuthStack-{cfg.env_name}",
    env_name=cfg.env_name,
    domain_prefix=cfg.cognito.get("domainPrefix", f"orders-demo-auth-{cfg.env_name}"),
    env=aws_env,
)

api = ApiStack(
    app,
    f"OrdersApiStack-{cfg.env_name}",
    env_name=cfg.env_name,
    ssm_paths=cfg.ssm,
    user_pool_id=auth.user_pool.user_pool_id,
    app_client_id=auth.app_client.user_pool_client_id,
    ddb_table_arn=data.table.table_arn,
    ddb_table_name_param=data.table_name_param.parameter_name,
    env=aws_env,
)

api.add_dependency(data)
api.add_dependency(auth)

app.synth()