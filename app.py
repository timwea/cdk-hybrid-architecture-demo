#pylint: disable-all
#!/usr/bin/env python3
import os

import aws_cdk as cdk

from aws_cdk import Environment

from cdk_hybrid_architecture_demo.cdk_hybrid_architecture_demo_stack import CdkHybridArchitectureDemoStack


app = cdk.App()
CdkHybridArchitectureDemoStack(
    scope=app, 
    construct_id="CdkHybridArchitectureDemoStack",
    stack_name="hybrid-architecture-demo",
    env=Environment(
        region="us-east-1"
    )
)

app.synth()
