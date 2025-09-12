"""Add security and compliance tables

Revision ID: 006_add_security_compliance_tables
Revises: 005_add_enterprise_admin_features
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '006_add_security_compliance_tables'
down_revision = '005_add_enterprise_admin_features'
branch_labels = None
depends_on = None


def upgrade():
    # Create data_retention_policies table
    op.create_table('data_retention_policies',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('data_type', sa.String(), nullable=False),
        sa.Column('retention_days', sa.Integer(), nullable=False),
        sa.Column('auto_delete', sa.Boolean(), nullable=True),
        sa.Column('encryption_required', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_retention_policies_company_id'), 'data_retention_policies', ['company_id'], unique=False)
    op.create_index(op.f('ix_data_retention_policies_data_type'), 'data_retention_policies', ['data_type'], unique=False)

    # Create security_alerts table
    op.create_table('security_alerts',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('alert_type', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('resolved', sa.Boolean(), nullable=True),
        sa.Column('resolved_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_security_alerts_company_id'), 'security_alerts', ['company_id'], unique=False)
    op.create_index(op.f('ix_security_alerts_severity'), 'security_alerts', ['severity'], unique=False)
    op.create_index(op.f('ix_security_alerts_resolved'), 'security_alerts', ['resolved'], unique=False)

    # Create compliance_logs table
    op.create_table('compliance_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('subject_id', sa.String(), nullable=False),
        sa.Column('action', sa.String(), nullable=False),
        sa.Column('legal_basis', sa.String(), nullable=True),
        sa.Column('details', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('requested_by', sa.String(), nullable=True),
        sa.Column('processed_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['processed_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_compliance_logs_company_id'), 'compliance_logs', ['company_id'], unique=False)
    op.create_index(op.f('ix_compliance_logs_subject_id'), 'compliance_logs', ['subject_id'], unique=False)
    op.create_index(op.f('ix_compliance_logs_action'), 'compliance_logs', ['action'], unique=False)

    # Add indexes to existing audit_logs table for better performance
    op.create_index(op.f('ix_audit_logs_user_id'), 'audit_logs', ['user_id'], unique=False)
    op.create_index(op.f('ix_audit_logs_action'), 'audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_audit_logs_resource_type'), 'audit_logs', ['resource_type'], unique=False)
    op.create_index(op.f('ix_audit_logs_created_at'), 'audit_logs', ['created_at'], unique=False)

    # Add indexes to existing proctoring_events table for better performance
    op.create_index(op.f('ix_proctoring_events_interview_id'), 'proctoring_events', ['interview_id'], unique=False)
    op.create_index(op.f('ix_proctoring_events_event_type'), 'proctoring_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_proctoring_events_severity'), 'proctoring_events', ['severity'], unique=False)
    op.create_index(op.f('ix_proctoring_events_timestamp'), 'proctoring_events', ['timestamp'], unique=False)


def downgrade():
    # Drop indexes
    op.drop_index(op.f('ix_proctoring_events_timestamp'), table_name='proctoring_events')
    op.drop_index(op.f('ix_proctoring_events_severity'), table_name='proctoring_events')
    op.drop_index(op.f('ix_proctoring_events_event_type'), table_name='proctoring_events')
    op.drop_index(op.f('ix_proctoring_events_interview_id'), table_name='proctoring_events')
    
    op.drop_index(op.f('ix_audit_logs_created_at'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_resource_type'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_action'), table_name='audit_logs')
    op.drop_index(op.f('ix_audit_logs_user_id'), table_name='audit_logs')
    
    # Drop tables
    op.drop_index(op.f('ix_compliance_logs_action'), table_name='compliance_logs')
    op.drop_index(op.f('ix_compliance_logs_subject_id'), table_name='compliance_logs')
    op.drop_index(op.f('ix_compliance_logs_company_id'), table_name='compliance_logs')
    op.drop_table('compliance_logs')
    
    op.drop_index(op.f('ix_security_alerts_resolved'), table_name='security_alerts')
    op.drop_index(op.f('ix_security_alerts_severity'), table_name='security_alerts')
    op.drop_index(op.f('ix_security_alerts_company_id'), table_name='security_alerts')
    op.drop_table('security_alerts')
    
    op.drop_index(op.f('ix_data_retention_policies_data_type'), table_name='data_retention_policies')
    op.drop_index(op.f('ix_data_retention_policies_company_id'), table_name='data_retention_policies')
    op.drop_table('data_retention_policies')