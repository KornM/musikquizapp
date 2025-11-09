"""
S3 bucket configuration for audio file storage.
"""
from aws_cdk import aws_s3 as s3, RemovalPolicy, Duration
from constructs import Construct


class AudioStorage(Construct):
    """Construct for creating S3 bucket for audio storage."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Create S3 bucket for audio files
        self.audio_bucket = s3.Bucket(
            self,
            "AudioBucket",
            bucket_name=None,  # Auto-generate unique name
            versioned=False,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            # CORS configuration for browser uploads
            cors=[
                s3.CorsRule(
                    allowed_methods=[
                        s3.HttpMethods.GET,
                        s3.HttpMethods.POST,
                        s3.HttpMethods.PUT,
                        s3.HttpMethods.HEAD,
                    ],
                    allowed_origins=["*"],
                    allowed_headers=["*"],
                    exposed_headers=[
                        "ETag",
                        "x-amz-server-side-encryption",
                        "x-amz-request-id",
                        "x-amz-id-2",
                    ],
                    max_age=3000,
                )
            ],
            # Lifecycle rules for cost optimization
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteOldAudioFiles",
                    enabled=True,
                    expiration=Duration.days(90),  # Delete files after 90 days
                    abort_incomplete_multipart_upload_after=Duration.days(7),
                )
            ],
            # Block public access (use presigned URLs instead)
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            # Enable encryption at rest
            encryption=s3.BucketEncryption.S3_MANAGED,
        )
