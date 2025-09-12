"""Add integration tables

Revision ID: 004_add_integration_tables
Revises: 003_add_chatbot_pre_screening_tables
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    # Create integrations table
    op.create_table('integrations',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True),
        sa.Column('credentials', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('settings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('field_mappings', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('last_sync', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_integrations_company_id'), 'integrations', ['company_id'], unique=False)
    op.create_index(op.f('ix_integrations_type'), 'integrations', ['type'], unique=False)
    op.create_index(op.f('ix_integrations_status'), 'integrations', ['status'], unique=False)

    # Create sync_logs table
    op.create_table('sync_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('integration_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('operation_type', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('records_processed', sa.Integer(), nullable=True),
        sa.Column('records_success', sa.Integer(), nullable=True),
        sa.Column('records_failed', sa.Integer(), nullable=True),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['integration_id'], ['integrations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_sync_logs_integration_id'), 'sync_logs', ['integration_id'], unique=False)
    op.create_index(op.f('ix_sync_logs_status'), 'sync_logs', ['status'], unique=False)
    op.create_index(op.f('ix_sync_logs_started_at'), 'sync_logs', ['started_at'], unique=False)

    # Create email_templates table
    op.create_table('email_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('html_content', sa.Text(), nullable=False),
        sa.Column('text_content', sa.Text(), nullable=False),
        sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_email_templates_company_id'), 'email_templates', ['company_id'], unique=False)
    op.create_index(op.f('ix_email_templates_category'), 'email_templates', ['category'], unique=False)

    # Create campaigns table
    op.create_table('campaigns',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('type', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('total_recipients', sa.Integer(), nullable=True),
        sa.Column('sent_count', sa.Integer(), nullable=True),
        sa.Column('failed_count', sa.Integer(), nullable=True),
        sa.Column('recipients', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('variables', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('scheduled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['template_id'], ['email_templates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_campaigns_company_id'), 'campaigns', ['company_id'], unique=False)
    op.create_index(op.f('ix_campaigns_status'), 'campaigns', ['status'], unique=False)
    op.create_index(op.f('ix_campaigns_scheduled_at'), 'campaigns', ['scheduled_at'], unique=False)

    # Create calendar_events table
    op.create_table('calendar_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('external_id', sa.String(), nullable=True),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('timezone', sa.String(), nullable=True),
        sa.Column('attendees', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('location', sa.String(), nullable=True),
        sa.Column('meeting_url', sa.String(), nullable=True),
        sa.Column('interview_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['interview_id'], ['interviews.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_calendar_events_company_id'), 'calendar_events', ['company_id'], unique=False)
    op.create_index(op.f('ix_calendar_events_start_time'), 'calendar_events', ['start_time'], unique=False)
    op.create_index(op.f('ix_calendar_events_interview_id'), 'calendar_events', ['interview_id'], unique=False)

    # Set default values
    op.execute("ALTER TABLE integrations ALTER COLUMN enabled SET DEFAULT true")
    op.execute("ALTER TABLE integrations ALTER COLUMN credentials SET DEFAULT '{}'")
    op.execute("ALTER TABLE integrations ALTER COLUMN settings SET DEFAULT '{}'")
    op.execute("ALTER TABLE integrations ALTER COLUMN field_mappings SET DEFAULT '[]'")
    op.execute("ALTER TABLE integrations ALTER COLUMN status SET DEFAULT 'pending'")
    
    op.execute("ALTER TABLE sync_logs ALTER COLUMN records_processed SET DEFAULT 0")
    op.execute("ALTER TABLE sync_logs ALTER COLUMN records_success SET DEFAULT 0")
    op.execute("ALTER TABLE sync_logs ALTER COLUMN records_failed SET DEFAULT 0")
    op.execute("ALTER TABLE sync_logs ALTER COLUMN error_details SET DEFAULT '[]'")
    op.execute("ALTER TABLE sync_logs ALTER COLUMN metadata SET DEFAULT '{}'")
    
    op.execute("ALTER TABLE email_templates ALTER COLUMN variables SET DEFAULT '[]'")
    op.execute("ALTER TABLE email_templates ALTER COLUMN is_active SET DEFAULT true")
    
    op.execute("ALTER TABLE campaigns ALTER COLUMN type SET DEFAULT 'email'")
    op.execute("ALTER TABLE campaigns ALTER COLUMN status SET DEFAULT 'draft'")
    op.execute("ALTER TABLE campaigns ALTER COLUMN total_recipients SET DEFAULT 0")
    op.execute("ALTER TABLE campaigns ALTER COLUMN sent_count SET DEFAULT 0")
    op.execute("ALTER TABLE campaigns ALTER COLUMN failed_count SET DEFAULT 0")
    op.execute("ALTER TABLE campaigns ALTER COLUMN recipients SET DEFAULT '[]'")
    op.execute("ALTER TABLE campaigns ALTER COLUMN variables SET DEFAULT '{}'")
    op.execute("ALTER TABLE campaigns ALTER COLUMN error_details SET DEFAULT '[]'")
    
    op.execute("ALTER TABLE calendar_events ALTER COLUMN timezone SET DEFAULT 'UTC'")
    op.execute("ALTER TABLE calendar_events ALTER COLUMN attendees SET DEFAULT '[]'")
    op.execute("ALTER TABLE calendar_events ALTER COLUMN status SET DEFAULT 'scheduled'")


def downgrade():
    # Drop tables in reverse order
    op.drop_table('calendar_events')
    op.drop_table('campaigns')
    op.drop_table('email_templates')
    op.drop_table('sync_logs')
    op.drop_table('integrations')