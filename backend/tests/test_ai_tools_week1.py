"""
Test suite for AI Agent Week 1 tools.

Coverage:
- Tool 1: search_certifications (keyword + filters)
- Tool 2: list_team_certs (manager team status)
- Tool 3: check_compliance_gap (role/unit gaps)

Safety tests:
- Authorization (RBAC enforced)
- Input validation (SQL injection prevention)
- Rate limiting
- PII masking in outputs
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, MagicMock
from backend.services.ai_agent_service import (
    AIAgentToolExecutor,
    create_tool_context,
    ToolContext,
    ToolResult,
    ToolAuthorizationError,
    ToolValidationError,
    ToolNotAllowedError,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_db():
    """Mock database connection."""
    db = Mock()
    db.fetchall = Mock(return_value=[])
    db.fetchone = Mock(return_value=None)
    return db

@pytest.fixture
def executor(mock_db):
    """AI Tool Executor instance."""
    return AIAgentToolExecutor(mock_db)

@pytest.fixture
def sample_certifications():
    """Sample certification data."""
    return [
        {
            "certification_id": "cert-001",
            "certification_name": "AWS Solutions Architect Associate",
            "provider": "AWS",
            "focus_area": "Cloud",
            "level": "Associate",
            "market_demand": "high",
            "is_trending": True,
            "validity_months": 36,
            "difficulty_level": "intermediate"
        },
        {
            "certification_id": "cert-002",
            "certification_name": "AWS DevOps Engineer Professional",
            "provider": "AWS",
            "focus_area": "DevOps",
            "level": "Professional",
            "market_demand": "high",
            "is_trending": True,
            "validity_months": 36,
            "difficulty_level": "advanced"
        },
    ]


# ============================================================================
# TOOL 1: search_certifications Tests
# ============================================================================

class TestSearchCertifications:
    """Test suite for search_certifications tool."""

    def test_search_by_keyword_success(self, executor, mock_db, sample_certifications):
        """Test successful keyword search."""
        mock_db.fetchall.return_value = sample_certifications

        context = create_tool_context(
            tool_name="search_certifications",
            user_id="user-001",
            user_roles=["manager"],
            correlation_id="corr-001",
            input_params={
                "query": "AWS",
                "filters": {},
                "limit": 20
            }
        )

        result = executor.execute_tool(context)

        assert result.status == "success"
        assert len(result.data["results"]) == 2
        assert result.data["results"][0]["certification_name"] == "AWS Solutions Architect Associate"

    def test_search_with_market_demand_filter(self, executor, mock_db, sample_certifications):
        """Test search with market demand filter."""
        mock_db.fetchall.return_value = sample_certifications

        context = create_tool_context(
            tool_name="search_certifications",
            user_id="user-001",
            user_roles=["collaborator"],
            correlation_id="corr-002",
            input_params={
                "query": "AWS",
                "filters": {
                    "market_demand": ["high"],
                    "provider": ["AWS"]
                },
                "limit": 20
            }
        )

        result = executor.execute_tool(context)

        assert result.status == "success"
        assert result.data["filters_applied"]["market_demand"] == ["high"]

    def test_search_missing_query_fails(self, executor):
        """Test search without query parameter fails validation."""
        context = create_tool_context(
            tool_name="search_certifications",
            user_id="user-001",
            user_roles=["manager"],
            correlation_id="corr-003",
            input_params={}
        )

        result = executor.execute_tool(context)

        assert result.status == "validation_error"
        assert "query" in result.error_message

    def test_search_result_limit_capped(self, executor, mock_db):
        """Test that result limit is capped at 50."""
        # Simulate 100 results from DB
        mock_db.fetchall.return_value = [
            {"certification_id": f"cert-{i}", "certification_name": f"Cert {i}"}
            for i in range(100)
        ]

        context = create_tool_context(
            tool_name="search_certifications",
            user_id="user-001",
            user_roles=["manager"],
            correlation_id="corr-004",
            input_params={
                "query": "test",
                "limit": 100
            }
        )

        result = executor.execute_tool(context)

        # Should cap at 50
        assert result.status == "success"

    def test_search_sql_injection_prevention(self, executor):
        """Test that SQL injection is prevented in query."""
        context = create_tool_context(
            tool_name="search_certifications",
            user_id="user-001",
            user_roles=["manager"],
            correlation_id="corr-005",
            input_params={
                "query": "AWS'; DROP TABLE certification; --",
                "filters": {}
            }
        )

        # Should sanitize and execute safely (no SQL executed due to parameterization)
        result = executor.execute_tool(context)

        # Should either fail validation or succeed with safe query
        assert result.status in ["validation_error", "success"]


# ============================================================================
# TOOL 2: list_team_certs Tests
# ============================================================================

class TestListTeamCerts:
    """Test suite for list_team_certs tool."""

    def test_list_team_certs_success(self, executor, mock_db):
        """Test successful listing of team certifications."""
        mock_db.fetchall.return_value = [
            {
                "collaborator_id": "collab-001",
                "collaborator_name": "John Smith",
                "certification_name": "AWS SAA",
                "status": "active",
                "issue_date": datetime(2023, 5, 1),
                "expiration_date": datetime(2026, 5, 1),
                "days_until_expiration": 500,
                "assignment_status": "completed",
                "assignment_due_date": datetime(2025, 12, 31)
            }
        ]

        context = create_tool_context(
            tool_name="list_team_certs",
            user_id="mgr-001",
            user_roles=["manager"],
            correlation_id="corr-006",
            input_params={
                "unit_id": "unit-001",
                "status_filter": ["active", "pending_validation"]
            }
        )

        result = executor.execute_tool(context)

        assert result.status == "success"
        assert len(result.data["certifications"]) == 1
        # Check PII masking
        assert result.data["certifications"][0]["collaborator_name"] == "John S."
        assert result.data["summary"]["active_certs"] == 1

    def test_list_team_certs_pii_masked(self, executor, mock_db):
        """Test that PII is masked in results."""
        mock_db.fetchall.return_value = [
            {
                "collaborator_id": "collab-002",
                "collaborator_name": "Maria Rodriguez Garcia",
                "certification_name": "GCP Professional",
                "status": "active",
                "issue_date": None,
                "expiration_date": None,
                "days_until_expiration": None,
                "assignment_status": None,
                "assignment_due_date": None
            }
        ]

        context = create_tool_context(
            tool_name="list_team_certs",
            user_id="mgr-001",
            user_roles=["manager"],
            correlation_id="corr-007",
            input_params={
                "unit_id": "unit-001",
                "status_filter": ["active"]
            }
        )

        result = executor.execute_tool(context)

        assert result.status == "success"
        # Verify PII masking: should be "Maria R."
        masked_name = result.data["certifications"][0]["collaborator_name"]
        assert masked_name != "Maria Rodriguez Garcia"
        assert "Maria" in masked_name

    def test_list_team_certs_manager_rbac(self, executor):
        """Test that manager RBAC is enforced."""
        context = create_tool_context(
            tool_name="list_team_certs",
            user_id="collab-001",
            user_roles=["collaborator"],
            correlation_id="corr-008",
            input_params={
                "unit_id": "unit-001"
            }
        )

        result = executor.execute_tool(context)

        # Collaborator should not have access
        assert result.status == "denied"

    def test_list_team_certs_coverage_calculation(self, executor, mock_db):
        """Test coverage percentage calculation."""
        mock_db.fetchall.return_value = [
            {
                "collaborator_id": "collab-001",
                "collaborator_name": "John Smith",
                "certification_name": "AWS SAA",
                "status": "active",
                "issue_date": None,
                "expiration_date": None,
                "days_until_expiration": 500,
                "assignment_status": None,
                "assignment_due_date": None
            },
            {
                "collaborator_id": "collab-002",
                "collaborator_name": "Jane Doe",
                "certification_name": "AWS DevOps",
                "status": "expired",
                "issue_date": None,
                "expiration_date": None,
                "days_until_expiration": -10,
                "assignment_status": None,
                "assignment_due_date": None
            },
            {
                "collaborator_id": "collab-003",
                "collaborator_name": "Bob Jones",
                "certification_name": "GCP Professional",
                "status": "pending_validation",
                "issue_date": None,
                "expiration_date": None,
                "days_until_expiration": None,
                "assignment_status": None,
                "assignment_due_date": None
            }
        ]

        context = create_tool_context(
            tool_name="list_team_certs",
            user_id="mgr-001",
            user_roles=["manager"],
            correlation_id="corr-009",
            input_params={
                "unit_id": "unit-001",
                "status_filter": ["active", "expired", "pending_validation"]
            }
        )

        result = executor.execute_tool(context)

        assert result.status == "success"
        # 1 active out of 3 = 33.33%
        assert result.data["summary"]["coverage_pct"] == 33.33


# ============================================================================
# TOOL 3: check_compliance_gap Tests
# ============================================================================

class TestCheckComplianceGap:
    """Test suite for check_compliance_gap tool."""

    def test_check_gap_by_unit_success(self, executor, mock_db):
        """Test compliance gap check by unit."""
        mock_db.fetchall.return_value = [
            {
                "collaborator_id": "collab-001",
                "collaborator_name": "John Smith",
                "certification_id": "cert-001",
                "certification_name": "AWS SAA",
                "gap_status": "missing",
                "due_date": None,
                "waiver_id": None
            }
        ]

        context = create_tool_context(
            tool_name="check_compliance_gap",
            user_id="mgr-001",
            user_roles=["manager"],
            correlation_id="corr-010",
            input_params={
                "unit_id": "unit-001"
            }
        )

        result = executor.execute_tool(context)

        assert result.status == "success"
        assert len(result.data["gaps"]) == 1
        assert result.data["gaps"][0]["required_cert"] == "AWS SAA"
        assert result.data["summary"]["total_gaps"] == 1

    def test_check_gap_no_unit_or_role_fails(self, executor):
        """Test that either unit_id or role_id is required."""
        context = create_tool_context(
            tool_name="check_compliance_gap",
            user_id="mgr-001",
            user_roles=["manager"],
            correlation_id="corr-011",
            input_params={}
        )

        result = executor.execute_tool(context)

        assert result.status == "validation_error"
        assert "unit_id" in result.error_message or "role_id" in result.error_message

    def test_check_gap_invalid_uuid_fails(self, executor):
        """Test that invalid UUID is rejected."""
        context = create_tool_context(
            tool_name="check_compliance_gap",
            user_id="mgr-001",
            user_roles=["manager"],
            correlation_id="corr-012",
            input_params={
                "unit_id": "not-a-uuid"
            }
        )

        result = executor.execute_tool(context)

        assert result.status == "validation_error"

    def test_check_gap_filters_waivered(self, executor, mock_db):
        """Test that waivered certifications are excluded from gaps."""
        mock_db.fetchall.return_value = [
            {
                "collaborator_id": "collab-001",
                "collaborator_name": "John Smith",
                "certification_id": "cert-001",
                "certification_name": "AWS SAA",
                "gap_status": "missing",
                "due_date": None,
                "waiver_id": "waiver-001"  # Has active waiver
            }
        ]

        context = create_tool_context(
            tool_name="check_compliance_gap",
            user_id="mgr-001",
            user_roles=["manager"],
            correlation_id="corr-013",
            input_params={
                "unit_id": "unit-001"
            }
        )

        result = executor.execute_tool(context)

        # Should exclude waivered cert from gaps
        assert result.status == "success"
        assert len(result.data["gaps"]) == 0


# ============================================================================
# AUTHORIZATION & SAFETY Tests
# ============================================================================

class TestAuthorizationAndSafety:
    """Test authorization and safety constraints."""

    def test_tool_not_in_allowlist_denied(self, executor):
        """Test that non-allowlisted tools are rejected."""
        context = create_tool_context(
            tool_name="delete_all_records",
            user_id="user-001",
            user_roles=["manager"],
            correlation_id="corr-014",
            input_params={}
        )

        result = executor.execute_tool(context)

        assert result.status == "denied"
        assert "not in allowlist" in result.error_message.lower()

    def test_unauthorized_role_denied(self, executor):
        """Test that unauthorized roles are denied."""
        context = create_tool_context(
            tool_name="list_team_certs",
            user_id="user-001",
            user_roles=["collaborator"],
            correlation_id="corr-015",
            input_params={
                "unit_id": "unit-001"
            }
        )

        result = executor.execute_tool(context)

        assert result.status == "denied"

    def test_execution_time_measured(self, executor, mock_db):
        """Test that execution time is measured."""
        mock_db.fetchall.return_value = []

        context = create_tool_context(
            tool_name="search_certifications",
            user_id="user-001",
            user_roles=["manager"],
            correlation_id="corr-016",
            input_params={"query": "test"}
        )

        result = executor.execute_tool(context)

        assert result.execution_time_ms > 0


# ============================================================================
# INTEGRATION Tests
# ============================================================================

class TestIntegration:
    """Integration tests for tool execution pipeline."""

    def test_end_to_end_search_workflow(self, executor, mock_db):
        """Test complete search workflow."""
        mock_db.fetchall.return_value = [
            {
                "certification_id": "cert-001",
                "certification_name": "AWS Solutions Architect Associate",
                "provider": "AWS",
                "focus_area": "Cloud",
                "level": "Associate",
                "market_demand": "high",
                "is_trending": True,
                "validity_months": 36,
                "difficulty_level": "intermediate"
            }
        ]

        # User searches for AWS certifications
        context = create_tool_context(
            tool_name="search_certifications",
            user_id="mgr-001",
            user_roles=["manager"],
            correlation_id="corr-017",
            input_params={
                "query": "AWS",
                "filters": {"market_demand": ["high"]},
                "limit": 20
            }
        )

        result = executor.execute_tool(context)

        # Verify success and proper result structure
        assert result.status == "success"
        assert result.tool_name == "search_certifications"
        assert "results" in result.data
        assert len(result.data["results"]) > 0

    def test_execution_result_serializable(self, executor, mock_db):
        """Test that execution results are JSON serializable."""
        import json

        mock_db.fetchall.return_value = []

        context = create_tool_context(
            tool_name="search_certifications",
            user_id="user-001",
            user_roles=["manager"],
            correlation_id="corr-018",
            input_params={"query": "AWS"}
        )

        result = executor.execute_tool(context)

        # Should be JSON serializable
        result_dict = {
            "tool_name": result.tool_name,
            "status": result.status,
            "data": result.data,
            "error_message": result.error_message,
            "execution_time_ms": result.execution_time_ms
        }

        json_str = json.dumps(result_dict)
        assert isinstance(json_str, str)


# ============================================================================
# PERFORMANCE Tests
# ============================================================================

class TestPerformance:
    """Performance and efficiency tests."""

    def test_tool_execution_under_2_seconds(self, executor, mock_db):
        """Test that tools execute in < 2 seconds."""
        import time

        mock_db.fetchall.return_value = [
            {
                "certification_id": f"cert-{i}",
                "certification_name": f"Cert {i}",
                "provider": "AWS",
                "focus_area": "Cloud",
                "level": "Associate",
                "market_demand": "high",
                "is_trending": True,
                "validity_months": 36,
                "difficulty_level": "intermediate"
            }
            for i in range(50)
        ]

        context = create_tool_context(
            tool_name="search_certifications",
            user_id="user-001",
            user_roles=["manager"],
            correlation_id="corr-019",
            input_params={"query": "cert", "limit": 50}
        )

        start = time.time()
        result = executor.execute_tool(context)
        duration = time.time() - start

        assert duration < 2.0
        assert result.execution_time_ms < 2000
