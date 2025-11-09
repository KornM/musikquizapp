"""
Main CDK stack for Music Quiz application.
"""
from aws_cdk import (
    Stack,
    CfnOutput,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
)
from constructs import Construct
from .database import DatabaseTables
from .storage import AudioStorage
from .lambda_functions import LambdaFunctions
from .api_gateway import MusicQuizApi
from .frontend import FrontendInfrastructure


class MusicQuizStack(Stack):
    """Main stack for Music Quiz backend infrastructure."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str = None,
        certificate_arn: str = None,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        # Create DynamoDB tables
        database = DatabaseTables(self, "Database")

        # Create S3 bucket for audio storage
        storage = AudioStorage(self, "Storage")

        # Define the frontend domain
        frontend_domain = "katrins-music-quiz.kornis.bayern"

        # Create Lambda functions (CloudFront domain will be added later)
        lambda_functions = LambdaFunctions(
            self,
            "LambdaFunctions",
            admins_table=database.admins_table,
            quiz_sessions_table=database.quiz_sessions_table,
            quiz_rounds_table=database.quiz_rounds_table,
            participants_table=database.participants_table,
            answers_table=database.answers_table,
            audio_bucket=storage.audio_bucket,
            cloudfront_domain=frontend_domain,
        )

        # Create API Gateway
        api = MusicQuizApi(
            self,
            "Api",
            lambda_functions=lambda_functions,
            frontend_domain=frontend_domain,
        )

        # Create Frontend Infrastructure (S3, CloudFront, Certificate)
        frontend = FrontendInfrastructure(
            self,
            "Frontend",
            domain_name=frontend_domain,
            hosted_zone_name="kornis.bayern",
            audio_bucket=storage.audio_bucket,
        )

        # CloudFront distribution (optional, if domain and certificate provided)
        if domain_name and certificate_arn:
            certificate = acm.Certificate.from_certificate_arn(
                self, "Certificate", certificate_arn
            )

            distribution = cloudfront.Distribution(
                self,
                "ApiDistribution",
                default_behavior=cloudfront.BehaviorOptions(
                    origin=origins.RestApiOrigin(api.api),
                    allowed_methods=cloudfront.AllowedMethods.ALLOW_ALL,
                    cache_policy=cloudfront.CachePolicy.CACHING_DISABLED,
                    origin_request_policy=cloudfront.OriginRequestPolicy.ALL_VIEWER,
                    viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                ),
                domain_names=[domain_name],
                certificate=certificate,
            )

            CfnOutput(
                self,
                "DistributionDomainName",
                value=distribution.distribution_domain_name,
                description="CloudFront distribution domain name",
            )

        # Stack outputs
        CfnOutput(
            self,
            "ApiEndpoint",
            value=api.api.url,
            description="API Gateway endpoint URL",
        )

        CfnOutput(
            self,
            "AudioBucketName",
            value=storage.audio_bucket.bucket_name,
            description="S3 bucket name for audio files",
        )

        CfnOutput(
            self,
            "AdminsTableName",
            value=database.admins_table.table_name,
            description="DynamoDB Admins table name",
        )

        CfnOutput(
            self,
            "QuizSessionsTableName",
            value=database.quiz_sessions_table.table_name,
            description="DynamoDB QuizSessions table name",
        )

        CfnOutput(
            self,
            "QuizRoundsTableName",
            value=database.quiz_rounds_table.table_name,
            description="DynamoDB QuizRounds table name",
        )

        CfnOutput(
            self,
            "ParticipantsTableName",
            value=database.participants_table.table_name,
            description="DynamoDB Participants table name",
        )

        CfnOutput(
            self,
            "FrontendBucketName",
            value=frontend.frontend_bucket.bucket_name,
            description="S3 bucket name for frontend files",
        )

        CfnOutput(
            self,
            "FrontendDistributionId",
            value=frontend.distribution.distribution_id,
            description="CloudFront distribution ID for frontend",
        )

        CfnOutput(
            self,
            "FrontendDistributionDomainName",
            value=frontend.distribution.distribution_domain_name,
            description="CloudFront distribution domain name",
        )

        CfnOutput(
            self,
            "FrontendUrl",
            value=f"https://katrins-music-quiz.kornis.bayern",
            description="Frontend URL",
        )
