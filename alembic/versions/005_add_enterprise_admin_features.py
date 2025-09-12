"""Add enterprise admin features

Revision ID: 005_add_enterprise_admin_features
Revises: 004_add_integration_tables
Create Date: 2024-01-15 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    # Create roles table
    op.create_table('roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('permissions', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('is_system_role', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_roles_company_id'), 'roles', ['company_id'], unique=False)
    op.create_index(op.f('ix_roles_name'), 'roles', ['name'], unique=False)

    # Create user_roles table
    op.create_table('user_roles',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=True),
        sa.Column('resource_id', sa.String(), nullable=True),
        sa.Column('granted_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('granted_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['granted_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_user_roles_user_id'), 'user_roles', ['user_id'], unique=False)
    op.create_index(op.f('ix_user_roles_role_id'), 'user_roles', ['role_id'], unique=False)

    # Create company_branding table
    op.create_table('company_branding',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('logo_url', sa.String(), nullable=True),
        sa.Column('favicon_url', sa.String(), nullable=True),
        sa.Column('primary_color', sa.String(), nullable=True),
        sa.Column('secondary_color', sa.String(), nullable=True),
        sa.Column('accent_color', sa.String(), nullable=True),
        sa.Column('custom_domain', sa.String(), nullable=True),
        sa.Column('domain_verified', sa.Boolean(), nullable=True),
        sa.Column('email_header_logo', sa.String(), nullable=True),
        sa.Column('email_footer_text', sa.Text(), nullable=True),
        sa.Column('custom_css', sa.Text(), nullable=True),
        sa.Column('features', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('company_id'),
        sa.UniqueConstraint('custom_domain')
    )

    # Create templates table
    op.create_table('templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('content', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('template_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True),
        sa.Column('usage_count', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('version', sa.String(), nullable=True),
        sa.Column('parent_template_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.ForeignKeyConstraint(['parent_template_id'], ['templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_templates_type'), 'templates', ['type'], unique=False)
    op.create_index(op.f('ix_templates_category'), 'templates', ['category'], unique=False)
    op.create_index(op.f('ix_templates_is_public'), 'templates', ['is_public'], unique=False)

    # Create review_comments table
    op.create_table('review_comments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('resource_type', sa.String(), nullable=False),
        sa.Column('resource_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('rating', sa.Integer(), nullable=True),
        sa.Column('tags', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('parent_comment_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('thread_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('is_private', sa.Boolean(), nullable=True),
        sa.Column('is_resolved', sa.Boolean(), nullable=True),
        sa.Column('author_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['parent_comment_id'], ['review_comments.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_review_comments_resource_type'), 'review_comments', ['resource_type'], unique=False)
    op.create_index(op.f('ix_review_comments_resource_id'), 'review_comments', ['resource_id'], unique=False)
    op.create_index(op.f('ix_review_comments_author_id'), 'review_comments', ['author_id'], unique=False)

    # Create data_export_requests table
    op.create_table('data_export_requests',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('export_type', sa.String(), nullable=False),
        sa.Column('format', sa.String(), nullable=False),
        sa.Column('filters', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(), nullable=True),
        sa.Column('progress', sa.Integer(), nullable=True),
        sa.Column('file_url', sa.String(), nullable=True),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('retry_count', sa.Integer(), nullable=True),
        sa.Column('requested_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['requested_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_data_export_requests_company_id'), 'data_export_requests', ['company_id'], unique=False)
    op.create_index(op.f('ix_data_export_requests_status'), 'data_export_requests', ['status'], unique=False)

    # Set default values for new columns
    op.execute("UPDATE roles SET permissions = '{}' WHERE permissions IS NULL")
    op.execute("UPDATE roles SET is_system_role = false WHERE is_system_role IS NULL")
    op.execute("UPDATE company_branding SET domain_verified = false WHERE domain_verified IS NULL")
    op.execute("UPDATE company_branding SET features = '{}' WHERE features IS NULL")
    op.execute("UPDATE templates SET template_metadata = '{}' WHERE template_metadata IS NULL")
    op.execute("UPDATE templates SET is_public = false WHERE is_public IS NULL")
    op.execute("UPDATE templates SET is_featured = false WHERE is_featured IS NULL")
    op.execute("UPDATE templates SET usage_count = 0 WHERE usage_count IS NULL")
    op.execute("UPDATE templates SET version = '1.0' WHERE version IS NULL")
    op.execute("UPDATE review_comments SET tags = '{}' WHERE tags IS NULL")
    op.execute("UPDATE review_comments SET is_private = false WHERE is_private IS NULL")
    op.execute("UPDATE review_comments SET is_resolved = false WHERE is_resolved IS NULL")
    op.execute("UPDATE data_export_requests SET filters = '{}' WHERE filters IS NULL")
    op.execute("UPDATE data_export_requests SET status = 'pending' WHERE status IS NULL")
    op.execute("UPDATE data_export_requests SET progress = 0 WHERE progress IS NULL")
    op.execute("UPDATE data_export_requests SET retry_count = 0 WHERE retry_count IS NULL")


def downgrade():
    # Drop tables in reverse order
    op.drop_table('data_export_requests')
    op.drop_table('review_comments')
    op.drop_table('templates')
    op.drop_table('company_branding')
    op.drop_table('user_roles')
    op.drop_table('roles')