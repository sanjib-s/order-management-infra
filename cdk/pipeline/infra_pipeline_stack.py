from aws_cdk import (
    Stack,
    aws_codepipeline as codepipeline,
    aws_codepipeline_actions as actions,
    aws_codebuild as codebuild,
    aws_iam as iam,
)
from constructs import Construct

class InfraPipelineStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        *,
        connection_arn: str,
        repo_owner: str,
        repo_name: str,
        repo_branch: str = "main",
        **kwargs
    ):
        super().__init__(scope, construct_id, **kwargs)

        source_output = codepipeline.Artifact()

        pipeline = codepipeline.Pipeline(self, "InfraPipeline", pipeline_name="order-management-infra-pipeline")

        pipeline.add_stage(
            stage_name="Source",
            actions=[
                actions.CodeStarConnectionsSourceAction(
                    action_name="GitHub_Source",
                    connection_arn=connection_arn,
                    owner=repo_owner,
                    repo=repo_name,
                    branch=repo_branch,
                    output=source_output,
                )
            ],
        )

        deploy_project = codebuild.PipelineProject(
            self,
            "CdkDeployProject",
            build_spec=codebuild.BuildSpec.from_source_filename("pipeline/buildspec_cdk_deploy.yml"),
            environment=codebuild.BuildEnvironment(
                build_image=codebuild.LinuxBuildImage.STANDARD_7_0,
                privileged=False,
            ),
        )

       #####
        deploy_project.add_to_role_policy(
            iam.PolicyStatement(
                actions=[
                    "cloudformation:*",
                    "iam:*",
                    "lambda:*",
                    "apigateway:*",
                    "apigatewayv2:*",
                    "cognito-idp:*",
                    "ssm:*",
                    "dynamodb:*",
                    "logs:*",
                    "ec2:Describe*",
                    "sts:GetCallerIdentity",
                ],
                resources=["*"],
            )
        )

        pipeline.add_stage(
            stage_name="Deploy",
            actions=[
                actions.CodeBuildAction(
                    action_name="CDK_Deploy",
                    project=deploy_project,
                    input=source_output,
                )
            ],
        )
