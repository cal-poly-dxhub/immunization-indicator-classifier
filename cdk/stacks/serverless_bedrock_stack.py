from aws_cdk import (
    App,
    Stack,
    Duration,
    CfnOutput,
    aws_apigateway as apigw, 
)
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm 
from constructs import Construct

BUCKET_NAME = "dxhub-immunization-classification"

class ServerlessBedrockStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Store Configurations in AWS SSM Parameter Store
        ssm_bucket_param = ssm.StringParameter(
            self, "SSMBucketName",
            parameter_name="/config/BUCKET_NAME",
            string_value=BUCKET_NAME
        )

        ssm_model_id_param = ssm.StringParameter(
            self, "SSMModelID",
            parameter_name="/config/MODEL_ID",
            string_value="anthropic.claude-3-5-sonnet-20241022-v2:0"
        )

        ssm_cdsi_param = ssm.StringParameter(
            self, "SSMStaticCDSiKey",
            parameter_name="/config/STATIC_CDSi_KEY",
            string_value="static_data/CDSi.csv"
        )

        #  IAM Role for Lambda with necessary permissions
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
            ]
        )

        lambda_role.add_to_policy(iam.PolicyStatement(
            actions=["ssm:GetParameter"],
            resources=[
                ssm_bucket_param.parameter_arn,
                ssm_model_id_param.parameter_arn,
                ssm_cdsi_param.parameter_arn
            ]
        ))

        #  Lambda Layer for dependencies
        dependencies_layer = _lambda.LayerVersion(
            self, "DependenciesLayer",
            code=_lambda.Code.from_asset("lambda/llm_l1_classification/dependencies/package.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_13],
            description="Layer containing boto3 for AWS API calls"
        )

        # Lambda Function
        lambda_function = _lambda.Function(
            self, "BedrockProcessingLambda",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/llm_l1_classification/src"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            layers=[dependencies_layer],
            environment={
                "SSM_BUCKET_NAME": ssm_bucket_param.parameter_name,
                "SSM_MODEL_ID": ssm_model_id_param.parameter_name,
                "SSM_STATIC_CDSi_KEY": ssm_cdsi_param.parameter_name
            }
        )

        # ✅ API Gateway to Trigger Lambda
        api = apigw.LambdaRestApi(
            self, "Level_1_Immunization_Classification_API",
            handler=lambda_function,
            proxy=False
        )

        # ✅ Define API Route: /process-file
        process_file = api.root.add_resource("level-1-iz-classification")
        process_file.add_method("POST")  # Supports POST requests

        # ✅ Output API Gateway URL
        CfnOutput(self, "APIGatewayURL", value=api.url)
        print(f"API Gateway URL: {api.url}")

        ssm.StringParameter(
            self, "SSMLevel1IZClassificationEndpoint",
            parameter_name="/config/Level1IZClassificationEndpoint",
            string_value=f"{api.url}level-1-iz-classification"
        )


# Deploy the stack
app = App()
ServerlessBedrockStack(app, "ServerlessBedrockStack")
app.synth()
