"""
Frontend infrastructure for Music Quiz application.
Creates S3 bucket, CloudFront distribution, and ACM certificate.
"""
from aws_cdk import (
    aws_s3 as s3,
    aws_cloudfront as cloudfront,
    aws_cloudfront_origins as origins,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    aws_route53_targets as targets,
    RemovalPolicy,
    Duration,
)
from constructs import Construct


class FrontendInfrastructure(Construct):
    """Construct for creating frontend hosting infrastructure."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        domain_name: str = "katrins-music-quiz.kornis.bayern",
        hosted_zone_name: str = "kornis.bayern",
        audio_bucket: s3.IBucket = None,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        # Look up the existing hosted zone
        hosted_zone = route53.HostedZone.from_lookup(
            self, "HostedZone", domain_name=hosted_zone_name
        )

        # Create S3 bucket for frontend hosting
        # Note: If bucket already exists, delete it first or let CDK generate a unique name
        self.frontend_bucket = s3.Bucket(
            self,
            "FrontendBucket",
            # Remove bucket_name to let CDK auto-generate a unique name
            # Or manually delete the existing bucket first
            website_index_document="index.html",
            website_error_document="index.html",  # For SPA routing
            public_read_access=False,  # CloudFront will access via OAI
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=RemovalPolicy.RETAIN,
            auto_delete_objects=False,
            versioned=False,
        )

        # Create ACM certificate in us-east-1 (required for CloudFront)
        # Note: Certificate must be in us-east-1 for CloudFront
        # Using DnsValidatedCertificate which handles cross-region automatically
        self.certificate = acm.DnsValidatedCertificate(
            self,
            "FrontendCertificate",
            domain_name=domain_name,
            hosted_zone=hosted_zone,
            region="us-east-1",  # CloudFront requires us-east-1
        )

        # Create Origin Access Identity (OAI) for CloudFront to access S3
        oai = cloudfront.OriginAccessIdentity(
            self, "FrontendOAI", comment=f"OAI for {domain_name}"
        )

        # Grant the OAI read access to the frontend bucket
        self.frontend_bucket.grant_read(oai)

        # Additional behaviors for audio bucket if provided
        additional_behaviors = {}
        if audio_bucket:
            # Create separate OAI for audio bucket
            audio_oai = cloudfront.OriginAccessIdentity(
                self, "AudioOAI", comment="OAI for audio bucket"
            )
            # Grant the OAI read access to the audio bucket
            audio_bucket.grant_read(audio_oai)

            # Add behavior for /sessions/* path (where audio files are stored)
            additional_behaviors["/sessions/*"] = cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    audio_bucket,
                    origin_access_identity=audio_oai,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress=False,  # Don't compress audio files
            )

        # Create CloudFront distribution
        self.distribution = cloudfront.Distribution(
            self,
            "FrontendDistribution",
            default_behavior=cloudfront.BehaviorOptions(
                origin=origins.S3Origin(
                    self.frontend_bucket,
                    origin_access_identity=oai,
                ),
                viewer_protocol_policy=cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
                allowed_methods=cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
                cached_methods=cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
                cache_policy=cloudfront.CachePolicy.CACHING_OPTIMIZED,
                compress=True,
            ),
            additional_behaviors=additional_behaviors,
            domain_names=[domain_name],
            certificate=self.certificate,
            minimum_protocol_version=cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
            default_root_object="index.html",
            error_responses=[
                cloudfront.ErrorResponse(
                    http_status=404,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                ),
                cloudfront.ErrorResponse(
                    http_status=403,
                    response_http_status=200,
                    response_page_path="/index.html",
                    ttl=Duration.minutes(5),
                ),
            ],
            price_class=cloudfront.PriceClass.PRICE_CLASS_100,
            comment=f"Music Quiz Frontend - {domain_name}",
        )

        # Create Route53 A record pointing to CloudFront
        route53.ARecord(
            self,
            "FrontendAliasRecord",
            zone=hosted_zone,
            record_name=domain_name,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(self.distribution)
            ),
        )

        # Create Route53 AAAA record (IPv6) pointing to CloudFront
        route53.AaaaRecord(
            self,
            "FrontendAliasRecordIPv6",
            zone=hosted_zone,
            record_name=domain_name,
            target=route53.RecordTarget.from_alias(
                targets.CloudFrontTarget(self.distribution)
            ),
        )
