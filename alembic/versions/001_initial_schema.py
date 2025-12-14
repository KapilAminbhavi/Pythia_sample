"""Initial schema

Revision ID: 001
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create insights table"""
    op.create_table(
        'insights',
        sa.Column('insight_id', UUID(as_uuid=True), primary_key=True,
                  server_default=sa.text("gen_random_uuid()")),
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('tenant_id', sa.String(255), nullable=False),
        sa.Column('input_type', sa.String(50), nullable=False),
        sa.Column('input_data', JSONB, nullable=False),
        sa.Column('features', JSONB, nullable=False),
        sa.Column('llm_output', JSONB, nullable=False),
        sa.Column('metadata', JSONB, nullable=False),
        sa.Column('fallback_used', sa.Boolean, default=False),
        sa.Column('processing_time_ms', sa.Float),
        sa.Column('llm_provider', sa.String(50)),
        sa.Column('created_at', sa.DateTime, nullable=False,
                  server_default=sa.text("NOW()")),
    )

    # Create indexes
    op.create_index(
        'idx_user_tenant_created',
        'insights',
        ['user_id', 'tenant_id', 'created_at']
    )

    op.create_index(
        'idx_tenant_severity',
        'insights',
        ['tenant_id', sa.text("(llm_output->>'severity')"), 'created_at']
    )

    op.create_index(
        'idx_created_at',
        'insights',
        ['created_at']
    )


def downgrade() -> None:
    """Drop insights table"""
    op.drop_index('idx_created_at', table_name='insights')
    op.drop_index('idx_tenant_severity', table_name='insights')
    op.drop_index('idx_user_tenant_created', table_name='insights')
    op.drop_table('insights')
