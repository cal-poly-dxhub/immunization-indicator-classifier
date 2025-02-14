#!/usr/bin/env python3
import os
import aws_cdk as cdk
from stacks.serverless_bedrock_stack import ServerlessBedrockStack
from stacks.SNOMED_to_CDSi_stack import ServerlessSNOMEDTOCDSi

app = cdk.App()
ServerlessBedrockStack(app, "ServerlessBedrockStack")
ServerlessSNOMEDTOCDSi(app, "ServerlessSNOMEDTOCDSi")
app.synth()
