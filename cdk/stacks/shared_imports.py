from aws_cdk import (
    Stack,
    Fn,
    aws_ec2 as ec2,
    aws_ssm as ssm,
)
from constructs import Construct


class NetworkImports:
    def __init__(self, scope: Construct, *, ssm_paths: dict):
        self.scope = scope
        self.ssm_paths = ssm_paths

        # Deploy-time tokens
        vpc_id = ssm.StringParameter.value_for_string_parameter(scope, ssm_paths["vpcId"])
        private_subnet_ids_csv = ssm.StringParameter.value_for_string_parameter(scope, ssm_paths["privateSubnetIds"])
        private_subnet_azs_csv = ssm.StringParameter.value_for_string_parameter(scope, ssm_paths["privateSubnetAzs"])
        lambda_sg_id = ssm.StringParameter.value_for_string_parameter(scope, ssm_paths["lambdaSecurityGroupId"])

        private_subnet_ids = Fn.split(",", private_subnet_ids_csv)
        private_subnet_azs = Fn.split(",", private_subnet_azs_csv)
        self.vpc = ec2.Vpc.from_vpc_attributes(
            scope,
            "ImportedVpc",
            vpc_id=vpc_id,
            private_subnet_ids=private_subnet_ids,
            availability_zones=private_subnet_azs,
        )

        self.lambda_sg = ec2.SecurityGroup.from_security_group_id(
            scope,
            "ImportedLambdaSg",
            security_group_id=lambda_sg_id,
            mutable=False,
        )