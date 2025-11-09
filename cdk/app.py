#!/usr/bin/env python3
"""
CDK application entry point for Music Quiz Backend.
"""
import aws_cdk as cdk
from music_quiz_stack.stack import MusicQuizStack


app = cdk.App()

# Get configuration from context
account = app.node.try_get_context("account")
region = app.node.try_get_context("region")
domain_name = app.node.try_get_context("domain_name")
certificate_arn = app.node.try_get_context("certificate_arn")

# Create the main stack
MusicQuizStack(
    app,
    "MusicQuizStack",
    env=cdk.Environment(account=account, region=region),
    domain_name=domain_name,
    certificate_arn=certificate_arn,
)

app.synth()
