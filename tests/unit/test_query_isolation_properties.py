"""
Property-Based Tests for Query Tenant Isolation

Feature: global-participant-registration, Property 42: Query tenant isolation

For any database query for tenant-specific data, the results should only include
records matching the authenticated user's tenantId.

Validates: Requirements 14.2
"""

import json
import os
import sys
import uuid
from unittest.mock import MagicMock, patch
from hypothesis import given, settings, strategies as st
from decimal import Decimal

# Add lambda paths
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "lambda"))


# Strategy for generating tenant IDs
tenant_ids = st.uuids().map(str)


# Strategy for generating session data
def session_strategy(tenant_id):
    return st.fixed_dictionaries(
        {
            "sessionId": st.uuids().map(str),
            "tenantId": st.just(tenant_id),
            "title": st.text(min_size=1, max_size=50),
            "status": st.sampled_from(["draft", "active", "completed"]),
            "roundCount": st.integers(min_value=0, max_value=10),
            "createdAt": st.integers(min_value=1000000000, max_value=2000000000).map(
                str
            ),
        }
    )


@settings(max_examples=100, deadline=None)
@given(
    tenant1_id=tenant_ids,
    tenant2_id=tenant_ids,
    num_tenant1_sessions=st.integers(min_value=1, max_value=5),
    num_tenant2_sessions=st.integers(min_value=1, max_value=5),
)
def test_property_42_list_sessions_tenant_filtering(
    tenant1_id, tenant2_id, num_tenant1_sessions, num_tenant2_sessions
):
    """
    Feature: global-participant-registration, Property 42: Query tenant isolation

    For any tenant admin querying sessions, the results should only include
    sessions where the session's tenantId matches the admin's tenantId.
    """
    # Ensure tenants are different
    if tenant1_id == tenant2_id:
        tenant2_id = str(uuid.uuid4())

    # Generate sessions for both tenants
    tenant1_sessions = [
        {
            "sessionId": str(uuid.uuid4()),
            "tenantId": tenant1_id,
            "title": f"Tenant1 Session {i}",
            "status": "active",
            "roundCount": i,
            "createdAt": str(1000000000 + i),
        }
        for i in range(num_tenant1_sessions)
    ]

    tenant2_sessions = [
        {
            "sessionId": str(uuid.uuid4()),
            "tenantId": tenant2_id,
            "title": f"Tenant2 Session {i}",
            "status": "active",
            "roundCount": i,
            "createdAt": str(1000000000 + i),
        }
        for i in range(num_tenant2_sessions)
    ]

    all_sessions = tenant1_sessions + tenant2_sessions

    # Mock the database query to return all sessions
    with (
        patch("list_sessions.handler.query") as mock_query,
        patch("list_sessions.handler.scan") as mock_scan,
    ):
        # Import handler after patching
        from list_sessions import handler

        # Mock query to filter by tenantId (simulating GSI)
        def query_side_effect(table, key_condition, values, index_name=None):
            tenant_id = values.get(":tenantId")
            return [s for s in all_sessions if s["tenantId"] == tenant_id]

        mock_query.side_effect = query_side_effect

        # Mock scan to return all sessions (for super admin)
        mock_scan.return_value = all_sessions

        # Test 1: Tenant admin 1 should only see their sessions
        event = {
            "headers": {"Authorization": "Bearer mock_token"},
            "pathParameters": {},
        }

        with patch("list_sessions.handler.require_tenant_admin") as mock_auth:
            # Simulate tenant admin 1
            mock_auth.return_value = (
                {"tenantId": tenant1_id, "role": "tenant_admin"},
                None,
            )

            response = handler.lambda_handler(event, None)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            returned_sessions = body["sessions"]

            # Verify all returned sessions belong to tenant 1
            for session in returned_sessions:
                assert session["tenantId"] == tenant1_id, (
                    f"Session {session['sessionId']} has wrong tenant ID"
                )

            # Verify count matches expected
            assert len(returned_sessions) == num_tenant1_sessions

        # Test 2: Tenant admin 2 should only see their sessions
        with patch("list_sessions.handler.require_tenant_admin") as mock_auth:
            # Simulate tenant admin 2
            mock_auth.return_value = (
                {"tenantId": tenant2_id, "role": "tenant_admin"},
                None,
            )

            response = handler.lambda_handler(event, None)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            returned_sessions = body["sessions"]

            # Verify all returned sessions belong to tenant 2
            for session in returned_sessions:
                assert session["tenantId"] == tenant2_id, (
                    f"Session {session['sessionId']} has wrong tenant ID"
                )

            # Verify count matches expected
            assert len(returned_sessions) == num_tenant2_sessions

        # Test 3: Super admin should see all sessions
        with patch("list_sessions.handler.require_tenant_admin") as mock_auth:
            # Simulate super admin
            mock_auth.return_value = ({"tenantId": None, "role": "super_admin"}, None)

            response = handler.lambda_handler(event, None)

            assert response["statusCode"] == 200
            body = json.loads(response["body"])
            returned_sessions = body["sessions"]

            # Verify all sessions are returned
            assert len(returned_sessions) == num_tenant1_sessions + num_tenant2_sessions


@settings(max_examples=100, deadline=None)
@given(
    tenant1_id=tenant_ids,
    tenant2_id=tenant_ids,
    num_tenant1_participants=st.integers(min_value=1, max_value=5),
    num_tenant2_participants=st.integers(min_value=1, max_value=5),
)
def test_property_42_get_participants_tenant_filtering(
    tenant1_id, tenant2_id, num_tenant1_participants, num_tenant2_participants
):
    """
    Feature: global-participant-registration, Property 42: Query tenant isolation

    For any session participant list query, the results should only include
    participants from the same tenant as the session.
    """
    # Ensure tenants are different
    if tenant1_id == tenant2_id:
        tenant2_id = str(uuid.uuid4())

    session_id = str(uuid.uuid4())

    # Create session for tenant 1
    session = {
        "sessionId": session_id,
        "tenantId": tenant1_id,
        "title": "Test Session",
        "status": "active",
    }

    # Generate participations for both tenants (simulating data corruption or cross-tenant attempt)
    tenant1_participations = [
        {
            "participationId": str(uuid.uuid4()),
            "participantId": str(uuid.uuid4()),
            "sessionId": session_id,
            "tenantId": tenant1_id,
            "totalPoints": i * 10,
            "correctAnswers": i,
            "joinedAt": str(1000000000 + i),
        }
        for i in range(num_tenant1_participants)
    ]

    tenant2_participations = [
        {
            "participationId": str(uuid.uuid4()),
            "participantId": str(uuid.uuid4()),
            "sessionId": session_id,
            "tenantId": tenant2_id,
            "totalPoints": i * 10,
            "correctAnswers": i,
            "joinedAt": str(1000000000 + i),
        }
        for i in range(num_tenant2_participants)
    ]

    all_participations = tenant1_participations + tenant2_participations

    # Create global participants for all participations
    global_participants = {}
    for participation in all_participations:
        participant_id = participation["participantId"]
        global_participants[participant_id] = {
            "participantId": participant_id,
            "tenantId": participation["tenantId"],
            "name": f"Participant {participant_id[:8]}",
            "avatar": "😀",
        }

    with (
        patch("get_participants.handler.get_item") as mock_get,
        patch("get_participants.handler.query") as mock_query,
        patch("get_participants.handler.validate_token") as mock_validate,
    ):
        from get_participants import handler

        # Mock get_item to return session or participant
        def get_item_side_effect(table, key):
            if "sessionId" in key:
                return session
            elif "participantId" in key:
                return global_participants.get(key["participantId"])
            return None

        mock_get.side_effect = get_item_side_effect

        # Mock query to return all participations
        mock_query.return_value = all_participations

        # Mock token validation
        mock_validate.return_value = {
            "role": "tenant_admin",
            "tenantId": tenant1_id,
            "adminId": str(uuid.uuid4()),
        }

        event = {
            "headers": {"Authorization": "Bearer mock_token"},
            "pathParameters": {"sessionId": session_id},
        }

        response = handler.lambda_handler(event, None)

        assert response["statusCode"] == 200
        body = json.loads(response["body"])
        returned_participants = body["participants"]

        # Verify all returned participants belong to tenant 1 (same as session)
        for participant in returned_participants:
            # The handler filters by checking global participant's tenantId
            participant_id = participant["participantId"]
            global_participant = global_participants[participant_id]
            assert global_participant["tenantId"] == tenant1_id, (
                f"Participant {participant_id} has wrong tenant ID"
            )

        # Verify only tenant 1 participants are returned
        assert len(returned_participants) == num_tenant1_participants


@settings(max_examples=100, deadline=None)
@given(
    tenant1_id=tenant_ids,
    tenant2_id=tenant_ids,
)
def test_property_42_cross_tenant_access_denial(tenant1_id, tenant2_id):
    """
    Feature: global-participant-registration, Property 42: Query tenant isolation

    For any tenant admin attempting to access a session from a different tenant,
    the system should deny access with a 403 error.
    """
    # Ensure tenants are different
    if tenant1_id == tenant2_id:
        tenant2_id = str(uuid.uuid4())

    session_id = str(uuid.uuid4())

    # Create session for tenant 2
    session = {
        "sessionId": session_id,
        "tenantId": tenant2_id,
        "title": "Tenant 2 Session",
        "status": "active",
    }

    with (
        patch("get_participants.handler.get_item") as mock_get,
        patch("get_participants.handler.validate_token") as mock_validate,
    ):
        from get_participants import handler

        # Mock get_item to return session
        mock_get.return_value = session

        # Mock token validation for tenant 1 admin
        mock_validate.return_value = {
            "role": "tenant_admin",
            "tenantId": tenant1_id,
            "adminId": str(uuid.uuid4()),
        }

        event = {
            "headers": {"Authorization": "Bearer mock_token"},
            "pathParameters": {"sessionId": session_id},
        }

        response = handler.lambda_handler(event, None)

        # Should return 403 Forbidden
        assert response["statusCode"] == 403
        body = json.loads(response["body"])
        assert body["error"]["code"] == "CROSS_TENANT_ACCESS"


if __name__ == "__main__":
    # Run tests
    test_property_42_list_sessions_tenant_filtering()
    test_property_42_get_participants_tenant_filtering()
    test_property_42_cross_tenant_access_denial()
    print("All property tests passed!")
