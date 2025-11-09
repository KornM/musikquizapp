"""
DynamoDB table definitions for Music Quiz application.
"""
from aws_cdk import aws_dynamodb as dynamodb, RemovalPolicy
from constructs import Construct


class DatabaseTables(Construct):
    """Construct for creating all DynamoDB tables."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs):
        super().__init__(scope, construct_id, **kwargs)

        # Admins table
        self.admins_table = dynamodb.Table(
            self,
            "AdminsTable",
            table_name="Admins",
            partition_key=dynamodb.Attribute(
                name="adminId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # Add GSI for username lookup
        self.admins_table.add_global_secondary_index(
            index_name="UsernameIndex",
            partition_key=dynamodb.Attribute(
                name="username", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # QuizSessions table
        self.quiz_sessions_table = dynamodb.Table(
            self,
            "QuizSessionsTable",
            table_name="QuizSessions",
            partition_key=dynamodb.Attribute(
                name="sessionId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # Add GSI for querying sessions by creation date
        self.quiz_sessions_table.add_global_secondary_index(
            index_name="CreatedAtIndex",
            partition_key=dynamodb.Attribute(
                name="status", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="createdAt", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # QuizRounds table
        self.quiz_rounds_table = dynamodb.Table(
            self,
            "QuizRoundsTable",
            table_name="QuizRounds",
            partition_key=dynamodb.Attribute(
                name="sessionId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="roundNumber", type=dynamodb.AttributeType.NUMBER
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # Participants table
        self.participants_table = dynamodb.Table(
            self,
            "ParticipantsTable",
            table_name="Participants",
            partition_key=dynamodb.Attribute(
                name="participantId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # Add GSI for querying participants by session
        self.participants_table.add_global_secondary_index(
            index_name="SessionIndex",
            partition_key=dynamodb.Attribute(
                name="sessionId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="registeredAt", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Answers table
        self.answers_table = dynamodb.Table(
            self,
            "AnswersTable",
            table_name="Answers",
            partition_key=dynamodb.Attribute(
                name="answerId", type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.RETAIN,
            point_in_time_recovery=True,
        )

        # Add GSI for querying answers by participant
        self.answers_table.add_global_secondary_index(
            index_name="ParticipantIndex",
            partition_key=dynamodb.Attribute(
                name="participantId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="submittedAt", type=dynamodb.AttributeType.STRING
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )

        # Add GSI for querying answers by session and round
        self.answers_table.add_global_secondary_index(
            index_name="SessionRoundIndex",
            partition_key=dynamodb.Attribute(
                name="sessionId", type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name="roundNumber", type=dynamodb.AttributeType.NUMBER
            ),
            projection_type=dynamodb.ProjectionType.ALL,
        )
