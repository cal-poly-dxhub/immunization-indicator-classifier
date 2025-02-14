from aws_cdk import (
    App,
    Stack,
    Duration,
    CfnOutput,
    aws_apigateway as apigw, 
    aws_dynamodb as dynamodb
)
# from aws_cdk import aws_s3 as s3
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_iam as iam
from aws_cdk import aws_ssm as ssm 
from constructs import Construct

BUCKET_NAME = "hl7-xml-to-snomed-code"
TABLE_NAME = "snomed-to-cdsi"

class ServerlessSNOMEDTOCDSi(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs):
        super().__init__(scope, id, **kwargs)

        # Store Configurations in AWS SSM Parameter Store
        ssm_bucket_param = ssm.StringParameter(
            self, "SSMSNOMEDToCDSiBucketName",
            parameter_name="/config/SSMSNOMEDToCDSiBucketName",
            string_value=BUCKET_NAME
        )
        
        ssm_dynamo_table_param = ssm.StringParameter(
            self, "DynamoSNOMEDToCDSiTableName",
            parameter_name="/config/DynamoSNOMEDToCDSiTableName",
            string_value=TABLE_NAME
        )
        dynamodb.Table(
            self, "SNOMEDToCDSiTable",
            table_name=TABLE_NAME,
            partition_key=dynamodb.Attribute(
                name="snomed_code",
                type=dynamodb.AttributeType.NUMBER
            ),
            sort_key=dynamodb.Attribute(  # ✅ Add sort key (cdsi_code)
            name="cdsi_code",
            type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST
        )

        #  IAM Role for Lambda with necessary permissions
        lambda_role = iam.Role(
            self, "LambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonDynamoDBFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
            ]
        )

        #  Lambda Layer for dependencies
        dependencies_layer = _lambda.LayerVersion(
            self, "DependenciesLayerSNOMEDTOCDSi",
            code=_lambda.Code.from_asset("lambda/SNOMED_to_CDSi/dependencies/package.zip"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_13],
            description="Layer containing boto3 for AWS API calls"
        )

        # Lambda Function
        lambda_function = _lambda.Function(
            self, "SNOMEDTOCDSiLambda",
            runtime=_lambda.Runtime.PYTHON_3_13,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda/SNOMED_to_CDSi/src"),
            role=lambda_role,
            timeout=Duration.seconds(30),
            memory_size=256,
            layers=[dependencies_layer],
            environment={
                "SSMSNOMEDToCDSiBucketName": ssm_bucket_param.parameter_name,
                "DynamoSNOMEDToCDSiTableName": ssm_dynamo_table_param.parameter_name
            }
        )

        # ✅ API Gateway to Trigger Lambda
        api = apigw.LambdaRestApi(
            self, "HL7SNOMEDToCDSiAPI",
            handler=lambda_function,
            proxy=False
        )

        # ✅ Define API Route: /process-file
        process_file = api.root.add_resource("snomed-to-cdsi")
        process_file.add_method("POST")  # Supports POST requests

        # ✅ Output API Gateway URL
        CfnOutput(self, "APIGatewayURL", value=api.url)
        print(f"API Gateway URL: {api.url}")

# Deploy the stack
app = App()
ServerlessSNOMEDTOCDSi(app, "ServerlessSNOMEDTOCDSi")
app.synth()
