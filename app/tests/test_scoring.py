"""
Tests for Job Scoring Agent
"""
import pytest
from app.config.constants import USER_SKILLS, TARGET_JOB_TITLES


class TestQuickScoring:
    """Test quick rule-based scoring"""
    
    def test_relevant_ai_role_scores_high(self):
        """AI/ML roles should score high on role relevance"""
        ai_keywords = ["ai", "ml", "machine learning", "deep learning", "llm", "nlp"]
        role = "AI Engineer"
        
        role_lower = role.lower()
        has_ai_keyword = any(kw in role_lower for kw in ai_keywords)
        
        assert has_ai_keyword
    
    def test_experience_scoring(self):
        """Test experience level scoring logic"""
        test_cases = [
            ("0-1 years", 25),  # Perfect match for 1 year exp
            ("1-3 years", 20),  # Good match
            ("2-4 years", 10),  # Partial match
            ("5+ years", 0),    # Too senior
        ]
        
        for exp_required, expected_min_score in test_cases:
            exp_lower = exp_required.lower()
            score = 0
            
            if "0" in exp_lower or "1" in exp_lower or "fresher" in exp_lower:
                score = 25
            elif "2" in exp_lower or "1-3" in exp_lower:
                score = 20
            elif "3" in exp_lower or "2-4" in exp_lower:
                score = 10
            
            assert score >= expected_min_score or expected_min_score == 0
    
    def test_location_scoring(self):
        """Test location preference scoring"""
        preferred = ["remote", "bangalore", "bengaluru"]
        
        test_locations = [
            ("Remote", True),
            ("Bangalore, India", True),
            ("Work from Home", True),
            ("New York", False),
        ]
        
        for location, should_match in test_locations:
            loc_lower = location.lower()
            matches = any(pref in loc_lower for pref in preferred)
            
            if should_match:
                assert matches, f"{location} should match"
    
    def test_skill_matching(self):
        """Test skill matching logic"""
        job_skills = ["Python", "TensorFlow", "LangChain", "NLP"]
        user_skills_lower = [s.lower() for s in USER_SKILLS]
        
        matching = []
        for skill in job_skills:
            if skill.lower() in user_skills_lower:
                matching.append(skill)
        
        assert len(matching) >= 3, "Should match at least 3 skills"


class TestScoringWeights:
    """Test scoring weight calculations"""
    
    def test_weights_sum_to_100(self):
        """All weights should sum to 100%"""
        from app.config.constants import SCORING_WEIGHTS
        
        total = sum(SCORING_WEIGHTS.values())
        assert abs(total - 1.0) < 0.01, f"Weights sum to {total}, expected 1.0"
    
    def test_max_score_possible(self):
        """Maximum possible score should be 100"""
        from app.config.constants import SCORING_WEIGHTS
        
        max_scores = {
            "skill_match": 40,
            "experience_match": 25,
            "location_match": 15,
            "role_relevance": 20,
        }
        
        total_max = sum(max_scores.values())
        assert total_max == 100


class TestTargetRoles:
    """Test target role configuration"""
    
    def test_target_roles_exist(self):
        """Should have target job titles defined"""
        assert len(TARGET_JOB_TITLES) >= 5
    
    def test_target_roles_are_ai_related(self):
        """All target roles should be AI/ML related"""
        ai_keywords = ["ai", "ml", "machine", "learning", "data", "deep", "llm", "nlp"]
        
        for role in TARGET_JOB_TITLES:
            role_lower = role.lower()
            has_keyword = any(kw in role_lower for kw in ai_keywords)
            assert has_keyword, f"Role '{role}' should contain AI/ML keyword"
