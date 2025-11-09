"""
Lambda function constructs for Music Quiz application.
"""
from aws_cdk import aws_lambda as lambda_, Duration, BundlingOptions
from constructs import Construct
import os


class LambdaFunctions(Construct):
    """Construct for creating all Lambda functions."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        admins_table,
        quiz_sessions_table,
        quiz_rounds_table,
        participants_table,
        answers_table,
        audio_bucket,
        cloudfront_domain: str = None,
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        # Common Lambda configuration
        common_environment = {
            "ADMINS_TABLE": admins_table.table_name,
            "QUIZ_SESSIONS_TABLE": quiz_sessions_table.table_name,
            "QUIZ_ROUNDS_TABLE": quiz_rounds_table.table_name,
            "PARTICIPANTS_TABLE": participants_table.table_name,
            "ANSWERS_TABLE": answers_table.table_name,
            "AUDIO_BUCKET": audio_bucket.bucket_name,
            "JWT_SECRET": "CHANGE_THIS_IN_PRODUCTION",  # Should use Secrets Manager
            "FRONTEND_URL": "https://katrins-music-quiz.kornis.bayern",
            "CLOUDFRONT_DOMAIN": cloudfront_domain or "",
        }

        # Get the parent directory (project root)
        project_root = os.path.join(os.path.dirname(__file__), "..", "..")

        # Lambda layer for common utilities with dependencies
        common_layer = lambda_.LayerVersion(
            self,
            "CommonLayer",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda_layer"),
                bundling=BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_11.bundling_image,
                    command=[
                        "bash",
                        "-c",
                        "mkdir -p /asset-output/python && "
                        "pip install -r requirements.txt -t /asset-output/python && "
                        "cp -au *.py /asset-output/python/",
                    ],
                ),
            ),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            compatible_architectures=[lambda_.Architecture.X86_64],
            description="Common utilities and dependencies for Music Quiz Lambda functions",
        )

        # Admin Login Lambda
        self.admin_login = lambda_.Function(
            self,
            "AdminLoginFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "admin_login")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        admins_table.grant_read_data(self.admin_login)

        # Create Quiz Session Lambda
        self.create_quiz = lambda_.Function(
            self,
            "CreateQuizFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "create_quiz")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        quiz_sessions_table.grant_write_data(self.create_quiz)

        # Add Quiz Round Lambda
        self.add_round = lambda_.Function(
            self,
            "AddRoundFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "add_round")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        quiz_sessions_table.grant_read_write_data(self.add_round)
        quiz_rounds_table.grant_read_write_data(self.add_round)

        # Upload Audio Lambda
        self.upload_audio = lambda_.Function(
            self,
            "UploadAudioFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "upload_audio")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(60),
            memory_size=512,
        )
        audio_bucket.grant_write(self.upload_audio)
        audio_bucket.grant_put(self.upload_audio)

        # Upload Image Lambda
        self.upload_image = lambda_.Function(
            self,
            "UploadImageFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "upload_image")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(60),
            memory_size=512,
        )
        audio_bucket.grant_write(self.upload_image)
        audio_bucket.grant_put(self.upload_image)

        # Get Quiz Session Lambda
        self.get_quiz = lambda_.Function(
            self,
            "GetQuizFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "get_quiz")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        quiz_sessions_table.grant_read_data(self.get_quiz)
        quiz_rounds_table.grant_read_data(self.get_quiz)

        # List Sessions Lambda
        self.list_sessions = lambda_.Function(
            self,
            "ListSessionsFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "list_sessions")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        quiz_sessions_table.grant_read_data(self.list_sessions)

        # Register Participant Lambda
        self.register_participant = lambda_.Function(
            self,
            "RegisterParticipantFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "register_participant")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        quiz_sessions_table.grant_read_data(self.register_participant)
        participants_table.grant_write_data(self.register_participant)

        # Get Audio Lambda
        self.get_audio = lambda_.Function(
            self,
            "GetAudioFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "get_audio")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        audio_bucket.grant_read(self.get_audio)

        # Generate QR Code Data Lambda
        self.generate_qr = lambda_.Function(
            self,
            "GenerateQRFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "generate_qr")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        quiz_sessions_table.grant_read_data(self.generate_qr)

        # Delete Session Lambda
        self.delete_session = lambda_.Function(
            self,
            "DeleteSessionFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "delete_session")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(60),
            memory_size=512,
        )
        quiz_sessions_table.grant_read_write_data(self.delete_session)
        quiz_rounds_table.grant_read_write_data(self.delete_session)
        audio_bucket.grant_delete(self.delete_session)

        # Delete Round Lambda
        self.delete_round = lambda_.Function(
            self,
            "DeleteRoundFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "delete_round")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        quiz_sessions_table.grant_read_write_data(self.delete_round)
        quiz_rounds_table.grant_read_write_data(self.delete_round)
        audio_bucket.grant_delete(self.delete_round)

        # Start Round Lambda
        self.start_round = lambda_.Function(
            self,
            "StartRoundFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "start_round")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        quiz_sessions_table.grant_read_write_data(self.start_round)
        quiz_rounds_table.grant_read_data(self.start_round)

        # Submit Answer Lambda
        self.submit_answer = lambda_.Function(
            self,
            "SubmitAnswerFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "submit_answer")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        participants_table.grant_read_data(self.submit_answer)
        quiz_rounds_table.grant_read_data(self.submit_answer)
        answers_table.grant_write_data(self.submit_answer)

        # Get Scoreboard Lambda
        self.get_scoreboard = lambda_.Function(
            self,
            "GetScoreboardFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "get_scoreboard")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(30),
            memory_size=256,
        )
        quiz_sessions_table.grant_read_data(self.get_scoreboard)
        participants_table.grant_read_data(self.get_scoreboard)
        answers_table.grant_read_data(self.get_scoreboard)

        # Reset Points Lambda
        self.reset_points = lambda_.Function(
            self,
            "ResetPointsFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "reset_points")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(60),
            memory_size=256,
        )
        answers_table.grant_read_write_data(self.reset_points)

        # Clear Participants Lambda
        self.clear_participants = lambda_.Function(
            self,
            "ClearParticipantsFunction",
            runtime=lambda_.Runtime.PYTHON_3_11,
            handler="handler.lambda_handler",
            code=lambda_.Code.from_asset(
                os.path.join(project_root, "lambda", "clear_participants")
            ),
            environment=common_environment,
            layers=[common_layer],
            timeout=Duration.seconds(60),
            memory_size=256,
        )
        participants_table.grant_read_write_data(self.clear_participants)
        answers_table.grant_read_write_data(self.clear_participants)
