"""Baseline migration - create all tables from current schema

Revision ID: 001_baseline
Revises: 
Create Date: 2026-04-15 14:00:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_baseline'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create datasets table
    op.create_table(
        'datasets',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('time_column', sa.String(100), nullable=True),
        sa.Column('entity_column', sa.String(100), nullable=True),
        sa.Column('target_column', sa.String(100), nullable=True),
        sa.Column('total_row_count', sa.Integer, server_default='0'),
        sa.Column('total_column_count', sa.Integer, server_default='0'),
        sa.Column('total_file_size', sa.BigInteger, server_default='0'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create dataset_files table
    op.create_table(
        'dataset_files',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column('dataset_id', sa.UUID(as_uuid=True), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('file_name', sa.String(255), nullable=False),
        sa.Column('file_size', sa.BigInteger, server_default='0'),
        sa.Column('role', sa.String(50), server_default='primary'),
        sa.Column('row_count', sa.Integer, server_default='0'),
        sa.Column('column_count', sa.Integer, server_default='0'),
        sa.Column('columns_info', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create dataset_subsets table
    op.create_table(
        'dataset_subsets',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column('parent_dataset_id', sa.UUID(as_uuid=True), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('purpose', sa.String(50), nullable=False),
        sa.Column('file_path', sa.String(500), nullable=False),
        sa.Column('row_count', sa.Integer, nullable=True),
        sa.Column('split_config', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create experiments table
    op.create_table(
        'experiments',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('dataset_id', sa.UUID(as_uuid=True), sa.ForeignKey('datasets.id'), nullable=False),
        sa.Column('subset_id', sa.UUID(as_uuid=True), sa.ForeignKey('dataset_subsets.id'), nullable=True),
        sa.Column('config', sa.JSON, nullable=False),
        sa.Column('tags', sa.JSON, nullable=True),
        sa.Column('status', sa.String(50), server_default='pending'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('finished_at', sa.DateTime, nullable=True),
    )

    # Create training_metrics table
    op.create_table(
        'training_metrics',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column('experiment_id', sa.UUID(as_uuid=True), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('iteration', sa.Integer, nullable=False),
        sa.Column('train_loss', sa.Float, nullable=True),
        sa.Column('val_loss', sa.Float, nullable=True),
        sa.Column('train_metric', sa.Float, nullable=True),
        sa.Column('val_metric', sa.Float, nullable=True),
        sa.Column('recorded_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create training_logs table
    op.create_table(
        'training_logs',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column('experiment_id', sa.UUID(as_uuid=True), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('level', sa.String(20), server_default='INFO'),
        sa.Column('message', sa.Text, nullable=False),
        sa.Column('timestamp', sa.DateTime, server_default=sa.func.now()),
    )

    # Create models table
    op.create_table(
        'models',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column('experiment_id', sa.UUID(as_uuid=True), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False, unique=True),
        sa.Column('storage_type', sa.String(20), server_default='local'),
        sa.Column('object_key', sa.String(500), nullable=True),
        sa.Column('format', sa.String(20), nullable=False),
        sa.Column('file_size', sa.BigInteger, nullable=True),
        sa.Column('file_path', sa.String(500), nullable=True),
        sa.Column('metrics', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
    )

    # Create feature_importance table
    op.create_table(
        'feature_importance',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column('experiment_id', sa.UUID(as_uuid=True), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('feature_name', sa.String(255), nullable=False),
        sa.Column('importance', sa.Float, nullable=False),
        sa.Column('rank', sa.Integer, nullable=True),
    )

    # Create model_versions table
    op.create_table(
        'model_versions',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column('experiment_id', sa.UUID(as_uuid=True), sa.ForeignKey('experiments.id', ondelete='CASCADE'), nullable=False),
        sa.Column('version_number', sa.String(20), nullable=False),
        sa.Column('config_snapshot', sa.JSON, nullable=False),
        sa.Column('metrics_snapshot', sa.JSON, nullable=False),
        sa.Column('tags', sa.JSON, nullable=True),
        sa.Column('is_active', sa.Integer, server_default='1'),
        sa.Column('source_model_id', sa.UUID(as_uuid=True), sa.ForeignKey('models.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.UniqueConstraint('experiment_id', 'version_number', name='uq_experiment_version'),
    )

    # Create async_tasks table
    op.create_table(
        'async_tasks',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column('task_type', sa.String(50), nullable=False),
        sa.Column('dataset_id', sa.UUID(as_uuid=True), sa.ForeignKey('datasets.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', sa.String(20), server_default='queued'),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('config', sa.JSON, nullable=True),
        sa.Column('result', sa.JSON, nullable=True),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('started_at', sa.DateTime, nullable=True),
        sa.Column('finished_at', sa.DateTime, nullable=True),
    )

    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=sa.text("gen_random_uuid()")),
        sa.Column('username', sa.String(50), nullable=False, index=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(20), server_default='user'),
        sa.Column('status', sa.String(20), server_default='active'),
        sa.Column('must_change_password', sa.Boolean, server_default='false'),
        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('last_login_at', sa.DateTime, nullable=True),
        sa.UniqueConstraint('username', name='uq_user_username'),
    )


def downgrade() -> None:
    op.drop_table('users')
    op.drop_table('async_tasks')
    op.drop_table('model_versions')
    op.drop_table('feature_importance')
    op.drop_table('models')
    op.drop_table('training_logs')
    op.drop_table('training_metrics')
    op.drop_table('experiments')
    op.drop_table('dataset_subsets')
    op.drop_table('dataset_files')
    op.drop_table('datasets')