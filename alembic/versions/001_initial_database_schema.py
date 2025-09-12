"""Initial database schema with all core models

Revision ID: 001
Revises: 
Create Date: 2025-01-08 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create companies table
    op.create_table('companies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('domain', sa.String(), nullable=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('password_hash', sa.String(), nullable=False),
        sa.Column('role', sa.String(), nullable=False),
        sa.Column('profile', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=False)

    # Create jobs table
    op.create_table('jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('requirements', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create candidates table
    op.create_table('candidates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('phone', sa.String(), nullable=True),
        sa.Column('resume_url', sa.String(), nullable=True),
        sa.Column('parsed_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_candidates_email'), 'candidates', ['email'], unique=False)

    # Create applications table
    op.create_table('applications',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('job_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('candidate_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('cover_letter', sa.Text(), nullable=True),
        sa.Column('application_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['candidate_id'], ['candidates.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['job_id'], ['jobs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('job_id', 'candidate_id', name='unique_job_candidate_application')
    )

    # Create interview_templates table
    op.create_table('interview_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('questions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create interviews table
    op.create_table('interviews',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['interview_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create assessments table
    op.create_table('assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('questions', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('responses', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('auto_grade', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('manual_grade', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create audit_logs table
    op.create_table('audit_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ip_address', postgresql.INET(), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create scores table
    op.create_table('scores',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('application_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('score', sa.Numeric(precision=5, scale=2), nullable=False),
        sa.Column('confidence', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('reasoning', sa.Text(), nullable=True),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_by', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['application_id'], ['applications.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create interview_responses table
    op.create_table('interview_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interview_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', sa.String(), nullable=False),
        sa.Column('response_type', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('media_url', sa.String(), nullable=True),
        sa.Column('duration', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create proctoring_events table
    op.create_table('proctoring_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('interview_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create assessment_questions table
    op.create_table('assessment_questions',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('test_cases', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('expected_answer', sa.Text(), nullable=True),
        sa.Column('time_limit', sa.Integer(), nullable=True),
        sa.Column('difficulty', sa.String(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create assessment_responses table
    op.create_table('assessment_responses',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assessment_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('question_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('response_content', sa.Text(), nullable=True),
        sa.Column('media_url', sa.String(), nullable=True),
        sa.Column('execution_result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('time_taken', sa.Integer(), nullable=True),
        sa.Column('auto_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('manual_score', sa.Numeric(precision=5, scale=2), nullable=True),
        sa.Column('feedback', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['assessment_id'], ['assessments.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['assessment_questions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Add check constraints
    op.execute("ALTER TABLE users ADD CONSTRAINT check_user_role CHECK (role IN ('admin', 'recruiter', 'interviewer'))")
    op.execute("ALTER TABLE jobs ADD CONSTRAINT check_job_status CHECK (status IN ('draft', 'active', 'paused', 'closed'))")
    op.execute("ALTER TABLE applications ADD CONSTRAINT check_application_status CHECK (status IN ('applied', 'screening', 'interviewing', 'assessed', 'hired', 'rejected'))")
    op.execute("ALTER TABLE interview_templates ADD CONSTRAINT check_template_type CHECK (type IN ('one_way', 'live_ai', 'technical'))")
    op.execute("ALTER TABLE interviews ADD CONSTRAINT check_interview_type CHECK (type IN ('one_way', 'live_ai', 'technical'))")
    op.execute("ALTER TABLE interviews ADD CONSTRAINT check_interview_status CHECK (status IN ('scheduled', 'in_progress', 'completed', 'cancelled'))")
    op.execute("ALTER TABLE interview_responses ADD CONSTRAINT check_response_type CHECK (response_type IN ('video', 'audio', 'text', 'code'))")
    op.execute("ALTER TABLE assessments ADD CONSTRAINT check_assessment_type CHECK (type IN ('coding', 'behavioral', 'cognitive'))")
    op.execute("ALTER TABLE scores ADD CONSTRAINT check_score_category CHECK (category IN ('technical', 'communication', 'cultural_fit', 'cognitive', 'behavioral'))")
    op.execute("ALTER TABLE scores ADD CONSTRAINT check_score_range CHECK (score >= 0 AND score <= 100)")
    op.execute("ALTER TABLE scores ADD CONSTRAINT check_confidence_range CHECK (confidence >= 0 AND confidence <= 100)")
    op.execute("ALTER TABLE proctoring_events ADD CONSTRAINT check_event_type CHECK (event_type IN ('face_detection', 'voice_analysis', 'suspicious_activity', 'browser_focus_lost'))")
    op.execute("ALTER TABLE proctoring_events ADD CONSTRAINT check_severity CHECK (severity IN ('low', 'medium', 'high', 'critical'))")
    op.execute("ALTER TABLE assessment_questions ADD CONSTRAINT check_question_type CHECK (question_type IN ('coding', 'multiple_choice', 'whiteboard', 'essay'))")


def downgrade() -> None:
    op.drop_table('assessment_responses')
    op.drop_table('assessment_questions')
    op.drop_table('proctoring_events')
    op.drop_table('interview_responses')
    op.drop_table('scores')
    op.drop_table('audit_logs')
    op.drop_table('assessments')
    op.drop_table('interviews')
    op.drop_table('interview_templates')
    op.drop_table('applications')
    op.drop_index(op.f('ix_candidates_email'), table_name='candidates')
    op.drop_table('candidates')
    op.drop_table('jobs')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('companies')