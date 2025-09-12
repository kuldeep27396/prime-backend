"""
Simple test for application functionality without database dependencies
"""

import pytest
from datetime import datetime
from uuid import uuid4

from app.schemas.application import (
    ApplicationCreate, ApplicationUpdate, PipelineStatusUpdate,
    ApplicationFilters, ApplicationSort, RankingWeights,
    ApplicationStatus, SortField, SortDirection
)


def test_application_create_schema():
    """Test ApplicationCreate schema validation"""
    job_id = uuid4()
    candidate_id = uuid4()
    
    # Valid application creation
    app_data = ApplicationCreate(
        job_id=job_id,
        candidate_id=candidate_id,
        cover_letter="Test cover letter",
        application_data={"source": "website"}
    )
    
    assert app_data.job_id == job_id
    assert app_data.candidate_id == candidate_id
    assert app_data.cover_letter == "Test cover letter"
    assert app_data.application_data == {"source": "website"}


def test_application_update_schema():
    """Test ApplicationUpdate schema validation"""
    update_data = ApplicationUpdate(
        status=ApplicationStatus.SCREENING,
        cover_letter="Updated cover letter",
        application_data={"notes": "Updated notes"}
    )
    
    assert update_data.status == ApplicationStatus.SCREENING
    assert update_data.cover_letter == "Updated cover letter"
    assert update_data.application_data == {"notes": "Updated notes"}


def test_pipeline_status_update_schema():
    """Test PipelineStatusUpdate schema validation"""
    status_update = PipelineStatusUpdate(
        status=ApplicationStatus.INTERVIEWING,
        notes="Moved to interview stage",
        changed_by="user123"
    )
    
    assert status_update.status == ApplicationStatus.INTERVIEWING
    assert status_update.notes == "Moved to interview stage"
    assert status_update.changed_by == "user123"


def test_application_filters_schema():
    """Test ApplicationFilters schema validation"""
    job_id = uuid4()
    candidate_id = uuid4()
    
    filters = ApplicationFilters(
        job_id=job_id,
        candidate_id=candidate_id,
        status=[ApplicationStatus.APPLIED, ApplicationStatus.SCREENING],
        candidate_name="John Doe",
        job_title="Software Engineer",
        has_cover_letter=True,
        min_score=75.0
    )
    
    assert filters.job_id == job_id
    assert filters.candidate_id == candidate_id
    assert filters.status == [ApplicationStatus.APPLIED, ApplicationStatus.SCREENING]
    assert filters.candidate_name == "John Doe"
    assert filters.job_title == "Software Engineer"
    assert filters.has_cover_letter is True
    assert filters.min_score == 75.0


def test_application_sort_schema():
    """Test ApplicationSort schema validation"""
    sort = ApplicationSort(
        field=SortField.CREATED_AT,
        direction=SortDirection.DESC
    )
    
    assert sort.field == SortField.CREATED_AT
    assert sort.direction == SortDirection.DESC
    
    # Test default values
    default_sort = ApplicationSort()
    assert default_sort.field == SortField.CREATED_AT
    assert default_sort.direction == SortDirection.DESC


def test_ranking_weights_schema():
    """Test RankingWeights schema validation"""
    weights = RankingWeights(
        technical_weight=0.4,
        communication_weight=0.25,
        cultural_fit_weight=0.15,
        cognitive_weight=0.1,
        behavioral_weight=0.1
    )
    
    assert weights.technical_weight == 0.4
    assert weights.communication_weight == 0.25
    assert weights.cultural_fit_weight == 0.15
    assert weights.cognitive_weight == 0.1
    assert weights.behavioral_weight == 0.1
    
    # Test that weights sum to 1.0
    total = (weights.technical_weight + weights.communication_weight + 
             weights.cultural_fit_weight + weights.cognitive_weight + 
             weights.behavioral_weight)
    assert abs(total - 1.0) < 0.01


def test_ranking_weights_default_values():
    """Test RankingWeights default values"""
    weights = RankingWeights()
    
    assert weights.technical_weight == 0.3
    assert weights.communication_weight == 0.2
    assert weights.cultural_fit_weight == 0.2
    assert weights.cognitive_weight == 0.15
    assert weights.behavioral_weight == 0.15
    
    # Test that default weights sum to 1.0
    total = (weights.technical_weight + weights.communication_weight + 
             weights.cultural_fit_weight + weights.cognitive_weight + 
             weights.behavioral_weight)
    assert abs(total - 1.0) < 0.01


def test_application_status_enum():
    """Test ApplicationStatus enum values"""
    assert ApplicationStatus.APPLIED == "applied"
    assert ApplicationStatus.SCREENING == "screening"
    assert ApplicationStatus.INTERVIEWING == "interviewing"
    assert ApplicationStatus.ASSESSED == "assessed"
    assert ApplicationStatus.HIRED == "hired"
    assert ApplicationStatus.REJECTED == "rejected"


def test_sort_field_enum():
    """Test SortField enum values"""
    assert SortField.CREATED_AT == "created_at"
    assert SortField.UPDATED_AT == "updated_at"
    assert SortField.STATUS == "status"
    assert SortField.CANDIDATE_NAME == "candidate_name"
    assert SortField.JOB_TITLE == "job_title"
    assert SortField.OVERALL_SCORE == "overall_score"


def test_sort_direction_enum():
    """Test SortDirection enum values"""
    assert SortDirection.ASC == "asc"
    assert SortDirection.DESC == "desc"


def test_application_filters_optional_fields():
    """Test ApplicationFilters with optional fields"""
    # Test with minimal data
    filters = ApplicationFilters()
    
    assert filters.job_id is None
    assert filters.candidate_id is None
    assert filters.status is None
    assert filters.created_from is None
    assert filters.created_to is None
    assert filters.updated_from is None
    assert filters.updated_to is None
    assert filters.candidate_name is None
    assert filters.job_title is None
    assert filters.has_cover_letter is None
    assert filters.min_score is None


def test_application_filters_with_single_status():
    """Test ApplicationFilters with single status"""
    filters = ApplicationFilters(status=ApplicationStatus.APPLIED)
    assert filters.status == ApplicationStatus.APPLIED


def test_application_filters_with_multiple_statuses():
    """Test ApplicationFilters with multiple statuses"""
    statuses = [ApplicationStatus.APPLIED, ApplicationStatus.SCREENING, ApplicationStatus.INTERVIEWING]
    filters = ApplicationFilters(status=statuses)
    assert filters.status == statuses


def test_application_filters_with_date_ranges():
    """Test ApplicationFilters with date ranges"""
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    filters = ApplicationFilters(
        created_from=start_date,
        created_to=end_date,
        updated_from=start_date,
        updated_to=end_date
    )
    
    assert filters.created_from == start_date
    assert filters.created_to == end_date
    assert filters.updated_from == start_date
    assert filters.updated_to == end_date


def test_min_score_validation():
    """Test min_score field validation"""
    # Valid score
    filters = ApplicationFilters(min_score=85.5)
    assert filters.min_score == 85.5
    
    # Edge cases
    filters_min = ApplicationFilters(min_score=0.0)
    assert filters_min.min_score == 0.0
    
    filters_max = ApplicationFilters(min_score=100.0)
    assert filters_max.min_score == 100.0


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])