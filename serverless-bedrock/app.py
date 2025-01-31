#!/usr/bin/env python3
import os
import aws_cdk as cdk
from serverless_bedrock_stack import ServerlessBedrockStack

app = cdk.App()
ServerlessBedrockStack(app, "ServerlessBedrockStack")
app.synth()
