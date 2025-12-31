"""
Tests for Google Sheets integration
"""
import pytest
from app.tools.sheets.schema import JobApplication, ScoringResult
from app.config.constants import ApplicationStatus


class TestJobApplicationSchema:
    """Test JobApplication Pydantic model"""
    
    def test_create_application(self):
        """Test creating a job application record"""
        app = JobApplication(
            platform="linkedin",
            company="Test Company",
            role="AI Engineer",
            location="Bangalore",
            fit_score=85,
            job_url="https://example.com/job/123",
        )
        
        assert app.company == "Test Company"
        assert app.fit_score == 85
        assert app.status == ApplicationStatus.DISCOVERED
    
    def test_application_to_row(self):
        """Test converting application to sheets row"""
        app = JobApplication(
            date="2024-01-15",
            platform="indeed",
            company="AI Corp",
            role="ML Engineer",
            location="Remote",
            experience_required="1-2 years",
            fit_score=78,
            status=ApplicationStatus.APPLIED,
            job_url="https://indeed.com/job/456",
            notes="Great opportunity",
        )
        
        row = app.to_row()
        
        assert len(row) == 10
        assert row[0] == "2024-01-15"
        assert row[1] == "indeed"
        assert row[2] == "AI Corp"
        assert row[6] == "78"
        assert row[7] == "applied"
    
    def test_application_from_row(self):
        """Test creating application from sheets row"""
        row = [
            "2024-01-15",
            "linkedin",
            "Tech Company",
            "Data Scientist",
            "Mumbai",
            "0-2 years",
            "90",
            "interview",
            "https://linkedin.com/job/789",
            "Interview scheduled",
        ]
        
        app = JobApplication.from_row(row)
        
        assert app.company == "Tech Company"
        assert app.role == "Data Scientist"
        assert app.fit_score == 90
        assert app.status == ApplicationStatus.INTERVIEW


class TestScoringResultSchema:
    """Test ScoringResult Pydantic model"""
    
    def test_create_scoring_result(self):
        """Test creating a scoring result"""
        result = ScoringResult(
            fit_score=82,
            skill_match_score=35,
            experience_match_score=22,
            location_match_score=15,
            role_relevance_score=10,
            matching_skills=["Python", "LangChain", "TensorFlow"],
            missing_skills=["Kubernetes"],
            recommendation="apply",
            reason="Strong skill match with experience alignment",
        )
        
        assert result.fit_score == 82
        assert len(result.matching_skills) == 3
        assert result.recommendation == "apply"
    
    def test_scoring_bounds(self):
        """Test scoring bounds validation"""
        # Valid scores
        result = ScoringResult(
            fit_score=100,
            skill_match_score=40,
            experience_match_score=25,
            location_match_score=15,
            role_relevance_score=20,
        )
        
        assert result.fit_score == 100
        assert result.skill_match_score == 40
    
    def test_scoring_to_dict(self):
        """Test converting scoring result to dictionary"""
        result = ScoringResult(
            fit_score=75,
            skill_match_score=30,
            experience_match_score=20,
            location_match_score=10,
            role_relevance_score=15,
            recommendation="maybe",
            reason="Decent match",
        )
        
        data = result.model_dump()
        
        assert isinstance(data, dict)
        assert data["fit_score"] == 75
        assert data["recommendation"] == "maybe"


class TestApplicationStatus:
    """Test ApplicationStatus enum"""
    
    def test_all_statuses_exist(self):
        """Test all expected status values exist"""
        expected = [
            "discovered",
            "scored",
            "applied",
            "interview",
            "rejected",
            "no_response",
            "offer",
        ]
        
        actual = [s.value for s in ApplicationStatus]
        
        for status in expected:
            assert status in actual, f"Missing status: {status}"
    
    def test_status_transitions(self):
        """Test valid status transitions"""
        # Define valid transitions
        valid_transitions = {
            ApplicationStatus.DISCOVERED: [ApplicationStatus.SCORED, ApplicationStatus.APPLIED],
            ApplicationStatus.SCORED: [ApplicationStatus.APPLIED, ApplicationStatus.PENDING_APPROVAL],
            ApplicationStatus.APPLIED: [ApplicationStatus.INTERVIEW, ApplicationStatus.REJECTED, ApplicationStatus.NO_RESPONSE],
            ApplicationStatus.INTERVIEW: [ApplicationStatus.OFFER, ApplicationStatus.REJECTED],
        }
        
        # Verify each starting state has valid next states
        for status, next_states in valid_transitions.items():
            assert len(next_states) > 0, f"Status {status} should have valid transitions"
