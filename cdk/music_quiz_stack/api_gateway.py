"""
API Gateway configuration for Music Quiz application.
"""
from aws_cdk import (
    aws_apigateway as apigateway,
    Duration,
)
from constructs import Construct


class MusicQuizApi(Construct):
    """Construct for creating API Gateway REST API."""

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        lambda_functions,
        frontend_domain: str = "katrins-music-quiz.kornis.bayern",
        **kwargs,
    ):
        super().__init__(scope, construct_id, **kwargs)

        # CORS allowed origins - production domain and localhost for development
        allowed_origins = [
            f"https://{frontend_domain}",
            "http://localhost:3000",  # For local development
            "http://localhost:5173",  # Vite default port
        ]

        # Create REST API
        self.api = apigateway.RestApi(
            self,
            "MusicQuizApi",
            rest_api_name="Music Quiz API",
            description="API for Music Quiz application",
            deploy_options=apigateway.StageOptions(
                stage_name="prod", throttling_rate_limit=100, throttling_burst_limit=200
            ),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=allowed_origins,
                allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
                allow_headers=[
                    "Content-Type",
                    "Authorization",
                    "X-Amz-Date",
                    "X-Api-Key",
                    "X-Amz-Security-Token",
                ],
                allow_credentials=False,
                max_age=Duration.seconds(3600),
            ),
        )

        # Admin endpoints
        admin = self.api.root.add_resource("admin")

        # POST /admin/login
        admin_login = admin.add_resource("login")
        admin_login.add_method(
            "POST", apigateway.LambdaIntegration(lambda_functions.admin_login)
        )

        # POST /admin/quiz-sessions
        quiz_sessions_admin = admin.add_resource("quiz-sessions")
        quiz_sessions_admin.add_method(
            "POST", apigateway.LambdaIntegration(lambda_functions.create_quiz)
        )

        # /admin/quiz-sessions/{sessionId}
        session_admin = quiz_sessions_admin.add_resource("{sessionId}")

        # DELETE /admin/quiz-sessions/{sessionId}
        session_admin.add_method(
            "DELETE", apigateway.LambdaIntegration(lambda_functions.delete_session)
        )

        # POST /admin/quiz-sessions/{sessionId}/rounds
        rounds_admin = session_admin.add_resource("rounds")
        rounds_admin.add_method(
            "POST", apigateway.LambdaIntegration(lambda_functions.add_round)
        )

        # DELETE /admin/quiz-sessions/{sessionId}/rounds/{roundNumber}
        round_admin = rounds_admin.add_resource("{roundNumber}")
        round_admin.add_method(
            "DELETE", apigateway.LambdaIntegration(lambda_functions.delete_round)
        )

        # POST /admin/quiz-sessions/{sessionId}/rounds/{roundNumber}/start
        start_round = round_admin.add_resource("start")
        start_round.add_method(
            "POST", apigateway.LambdaIntegration(lambda_functions.start_round)
        )

        # DELETE /admin/quiz-sessions/{sessionId}/points
        points = session_admin.add_resource("points")
        points.add_method(
            "DELETE", apigateway.LambdaIntegration(lambda_functions.reset_points)
        )

        # DELETE /admin/quiz-sessions/{sessionId}/participants
        participants_admin = session_admin.add_resource("participants")
        participants_admin.add_method(
            "DELETE", apigateway.LambdaIntegration(lambda_functions.clear_participants)
        )

        # POST /admin/audio
        audio_admin = admin.add_resource("audio")
        audio_admin.add_method(
            "POST", apigateway.LambdaIntegration(lambda_functions.upload_audio)
        )

        # POST /admin/image
        image_admin = admin.add_resource("image")
        image_admin.add_method(
            "POST", apigateway.LambdaIntegration(lambda_functions.upload_image)
        )

        # Public quiz session endpoints
        quiz_sessions = self.api.root.add_resource("quiz-sessions")

        # GET /quiz-sessions
        quiz_sessions.add_method(
            "GET", apigateway.LambdaIntegration(lambda_functions.list_sessions)
        )

        # GET /quiz-sessions/{sessionId}
        session = quiz_sessions.add_resource("{sessionId}")
        session.add_method(
            "GET", apigateway.LambdaIntegration(lambda_functions.get_quiz)
        )

        # GET /quiz-sessions/{sessionId}/qr
        qr = session.add_resource("qr")
        qr.add_method("GET", apigateway.LambdaIntegration(lambda_functions.generate_qr))

        # GET /quiz-sessions/{sessionId}/scoreboard
        scoreboard = session.add_resource("scoreboard")
        scoreboard.add_method(
            "GET", apigateway.LambdaIntegration(lambda_functions.get_scoreboard)
        )

        # Participant endpoints
        participants = self.api.root.add_resource("participants")

        # POST /participants/register
        register = participants.add_resource("register")
        register.add_method(
            "POST", apigateway.LambdaIntegration(lambda_functions.register_participant)
        )

        # POST /participants/answers
        answers = participants.add_resource("answers")
        answers.add_method(
            "POST", apigateway.LambdaIntegration(lambda_functions.submit_answer)
        )

        # Audio endpoint - use query parameter for audio key
        audio = self.api.root.add_resource("audio")
        audio.add_method(
            "GET", apigateway.LambdaIntegration(lambda_functions.get_audio)
        )
