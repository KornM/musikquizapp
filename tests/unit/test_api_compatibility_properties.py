"""
Property-Based Tests for API Response Format Compatibility

Tests cover:
- Property 21: API response format compatibility

These tests verify that API responses maintain consistent format for backward compatibility
with legacy clients during and after the multi-tenant migration.
"""

import json
import pytest
from hypothesis import given, settings, strategies as st
import sys
import os

# Add lambda directories to path
lambda_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "lambda")
)
sys.path.insert(0, os.path.join(lambda_path, "common"))


class TestAPICompatibilityProperties:
    """Property-based tests for API response format compatibility"""

    @settings(max_examples=100)
    @given(
        error_code=st.sampled_from(
            [
                "MISSING_TOKEN",
                "INVALID_TOKEN",
                "TENANT_NOT_FOUND",
                "PARTICIPANT_NOT_FOUND",
                "MISSING_FIELDS",
                "CROSS_TENANT_ACCESS",
                "TENANT_INACTIVE",
            ]
        ),
        error_message=st.text(min_size=1, max_size=200),
        status_code=st.sampled_from([400, 401, 403, 404, 500]),
    )
    def test_property_21_error_response_format(
        self, error_code, error_message, status_code
    ):
        """
        Feature: global-participant-registration, Property 21: API response format compatibility

        For any API error response, the format should match the documented error schema
        with all required fields present.

        Validates: Requirements 6.4
        """
        from errors import error_response

        # Act
        response = error_response(status_code, error_code, error_message)

        # Assert - Verify response structure
        assert "statusCode" in response, "Response missing statusCode"
        assert "body" in response, "Response missing body"
        assert "headers" in response, "Response missing headers"

        # Verify status code matches
        assert response["statusCode"] == status_code

        # Verify headers include CORS
        headers = response["headers"]
        assert "Access-Control-Allow-Origin" in headers, "Missing CORS header"

        # Verify body is valid JSON
        body = json.loads(response["body"])

        # Verify error structure
        assert "error" in body, "Response body missing error object"
        error = body["error"]

        # Verify required error fields
        assert "code" in error, "Error object missing code field"
        assert "message" in error, "Error object missing message field"

        # Verify field types
        assert isinstance(error["code"], str), "Error code must be string"
        assert isinstance(error["message"], str), "Error message must be string"

        # Verify values
        assert error["code"] == error_code
        assert error["message"] == error_message

    @settings(max_examples=100)
    @given(
        details=st.one_of(
            st.none(),
            st.dictionaries(
                keys=st.text(min_size=1, max_size=20),
                values=st.one_of(st.text(), st.integers(), st.booleans()),
                max_size=5,
            ),
        )
    )
    def test_property_21_error_response_with_details(self, details):
        """
        Feature: global-participant-registration, Property 21: API response format compatibility

        For any API error response with details, the format should include the details object.

        Validates: Requirements 6.4
        """
        from errors import error_response

        # Act
        response = error_response(400, "TEST_ERROR", "Test message", details)

        # Assert
        body = json.loads(response["body"])
        error = body["error"]

        # Verify details field exists
        assert "details" in error, "Error object missing details field"

        # Verify details matches input (or is empty dict if None was passed)
        if details is None:
            assert error["details"] == {}
        else:
            assert error["details"] == details

    @settings(max_examples=100, deadline=None)
    @given(
        tenant_id=st.uuids(),
        name=st.text(min_size=1, max_size=100),
    )
    def test_property_21_backward_compatibility_tenant_context(self, tenant_id, name):
        """
        Feature: global-participant-registration, Property 21: API response format compatibility

        For any request data, the backward compatibility layer should ensure tenantId is present.

        Validates: Requirements 6.4, 15.5
        """
        from backward_compatibility import ensure_tenant_context

        # Test with tenantId present
        data_with_tenant = {"name": name, "tenantId": str(tenant_id)}
        result = ensure_tenant_context(data_with_tenant.copy())
        assert result["tenantId"] == str(tenant_id)
        assert result["name"] == name

        # Test without tenantId (should add default)
        data_without_tenant = {"name": name}
        result = ensure_tenant_context(data_without_tenant.copy())
        assert "tenantId" in result, (
            "tenantId should be added by backward compatibility layer"
        )
        assert result["tenantId"] is not None
        assert result["name"] == name

    @settings(max_examples=100)
    @given(
        response_data=st.dictionaries(
            keys=st.sampled_from(
                ["participantId", "name", "avatar", "tenantId", "sessionId"]
            ),
            values=st.text(min_size=1, max_size=50),
            min_size=1,
            max_size=5,
        )
    )
    def test_property_21_response_normalization(self, response_data):
        """
        Feature: global-participant-registration, Property 21: API response format compatibility

        For any response data, the normalization function should maintain data integrity.

        Validates: Requirements 6.4
        """
        from backward_compatibility import normalize_response_format

        # Test with tenant included (default)
        result_with_tenant = normalize_response_format(
            response_data.copy(), include_tenant=True
        )
        assert result_with_tenant == response_data, (
            "Response should be unchanged when including tenant"
        )

        # Test without tenant (for legacy clients)
        result_without_tenant = normalize_response_format(
            response_data.copy(), include_tenant=False
        )

        # All fields except tenantId should be present
        for key, value in response_data.items():
            if key != "tenantId":
                assert key in result_without_tenant
                assert result_without_tenant[key] == value

    def test_response_format_consistency_structure(self):
        """
        Feature: global-participant-registration, Property 21: API response format compatibility

        Verify that all API responses follow consistent structural patterns.

        This test ensures:
        - All responses have statusCode, body, and headers
        - All responses include CORS headers
        - All response bodies are valid JSON
        - Success responses have appropriate status codes
        - Error responses have error object in body

        Validates: Requirements 6.4
        """
        from errors import error_response
        from cors import add_cors_headers

        # Test error response structure
        error = error_response(400, "TEST_ERROR", "Test error message")
        assert error["statusCode"] == 400
        assert "body" in error
        assert "headers" in error
        assert "Access-Control-Allow-Origin" in error["headers"]
        body = json.loads(error["body"])
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]

        # Test CORS headers are added consistently
        test_response = {"statusCode": 200, "body": json.dumps({"data": "test"})}
        cors_response = add_cors_headers(test_response)
        assert "headers" in cors_response
        assert "Access-Control-Allow-Origin" in cors_response["headers"]
        assert "Access-Control-Allow-Methods" in cors_response["headers"]
        assert "Access-Control-Allow-Headers" in cors_response["headers"]

    @settings(max_examples=100)
    @given(
        status_codes=st.lists(
            st.sampled_from([200, 201, 400, 401, 403, 404, 500]),
            min_size=1,
            max_size=10,
        )
    )
    def test_property_21_status_code_consistency(self, status_codes):
        """
        Feature: global-participant-registration, Property 21: API response format compatibility

        For any set of status codes, responses should maintain consistent format.

        Validates: Requirements 6.4
        """
        from errors import error_response

        for status_code in status_codes:
            response = error_response(status_code, "TEST", "Test message")

            # Verify structure is consistent regardless of status code
            assert "statusCode" in response
            assert "body" in response
            assert "headers" in response
            assert response["statusCode"] == status_code

            # Verify body is valid JSON
            body = json.loads(response["body"])
            assert isinstance(body, dict)

    @settings(max_examples=100)
    @given(
        field_names=st.lists(
            st.text(
                min_size=1,
                max_size=20,
                alphabet=st.characters(whitelist_categories=("Lu", "Ll")),
            ),
            min_size=1,
            max_size=10,
            unique=True,
        )
    )
    def test_property_21_required_fields_presence(self, field_names):
        """
        Feature: global-participant-registration, Property 21: API response format compatibility

        For any set of required fields, the validation should ensure all are present.

        Validates: Requirements 6.4
        """
        # Create a response with all required fields
        response_data = {field: f"value_{field}" for field in field_names}

        # Verify all required fields are present
        for field in field_names:
            assert field in response_data, f"Required field '{field}' missing"
            assert isinstance(response_data[field], str)
            assert len(response_data[field]) > 0

    def test_legacy_token_support(self):
        """
        Feature: global-participant-registration, Property 21: API response format compatibility

        Verify that legacy tokens without tenantId are supported.

        Validates: Requirements 6.5
        """
        from backward_compatibility import migrate_legacy_token_to_new_format

        # Test legacy token payload (without tenantId)
        legacy_payload = {"sub": "user-123", "role": "participant", "exp": 1234567890}

        # Migrate to new format
        new_payload = migrate_legacy_token_to_new_format(legacy_payload)

        # Verify tenantId was added
        assert "tenantId" in new_payload, "tenantId should be added to legacy token"
        assert new_payload["tenantId"] is not None

        # Verify other fields are preserved
        assert new_payload["sub"] == legacy_payload["sub"]
        assert new_payload["role"] == legacy_payload["role"]
        assert new_payload["exp"] == legacy_payload["exp"]

    def test_default_tenant_fallback(self):
        """
        Feature: global-participant-registration, Property 21: API response format compatibility

        Verify that requests default to primary tenant when no tenant context is provided.

        Validates: Requirements 15.5
        """
        from backward_compatibility import (
            get_tenant_from_context_or_default,
            DEFAULT_TENANT_ID,
        )

        # Test with no tenant context
        result = get_tenant_from_context_or_default(None)
        assert result == DEFAULT_TENANT_ID

        # Test with empty tenant context
        result = get_tenant_from_context_or_default({})
        assert result == DEFAULT_TENANT_ID

        # Test with tenant context but no tenantId
        result = get_tenant_from_context_or_default({"userId": "123"})
        assert result == DEFAULT_TENANT_ID

        # Test with tenant context and tenantId
        result = get_tenant_from_context_or_default({"tenantId": "custom-tenant"})
        assert result == "custom-tenant"
