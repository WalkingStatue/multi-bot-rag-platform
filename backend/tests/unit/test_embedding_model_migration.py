"""
Unit tests for embedding model migration service.
"""
import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from app.services.embedding_model_migration import (
    EmbeddingModelMigration,
    MigrationStatus,
    ImpactLevel,
    DimensionCompatibilityCheck,
    ModelChangeImpact,
    MigrationPlan,
    MigrationResult
)
from app.services.embedding_model_validator import ModelValidationResult, ModelValidationStatus
from app.models.bot import Bot
from app.models.document import DocumentChunk


class TestEmbeddingModelMigration:
    """Test cases for EmbeddingModelMigration."""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session."""
        return Mock()
    
    @pytest.fixture
    def mock_embedding_service(self):
        """Mock embedding service."""
        service = Mock()
        service.get_supported_providers.return_value = ["openai", "gemini", "anthropic"]
        return service
    
    @pytest.fixture
    def mock_model_validator(self):
        """Mock model validator."""
        validator = Mock()
        validator.validate_model_availability = AsyncMock()
        return validator
    
    @pytest.fixture
    def migration_service(self, mock_db, mock_embedding_service, mock_model_validator):
        """Create migration service with mocked dependencies."""
        service = EmbeddingModelMigration(mock_db)
        service.embedding_service = mock_embedding_service
        service.model_validator = mock_model_validator
        service.vector_manager = Mock()
        service.user_service = Mock()
        return service
    
    @pytest.mark.asyncio
    async def test_check_dimension_compatibility_same_dimensions(self, migration_service, mock_model_validator):
        """Test dimension compatibility check with same dimensions."""
        # Setup validation results
        mock_model_validator.validate_model_availability.side_effect = [
            ModelValidationResult(
                provider="openai",
                model="text-embedding-3-small",
                status=ModelValidationStatus.VALID,
                is_available=True,
                dimension=1536
            ),
            ModelValidationResult(
                provider="openai",
                model="text-embedding-3-large",
                status=ModelValidationStatus.VALID,
                is_available=True,
                dimension=1536  # Same dimension
            )
        ]
        
        # Execute
        result = await migration_service.check_dimension_compatibility(
            current_provider="openai",
            current_model="text-embedding-3-small",
            target_provider="openai",
            target_model="text-embedding-3-large"
        )
        
        # Assert
        assert result.is_compatible is True
        assert result.current_dimension == 1536
        assert result.target_dimension == 1536
        assert result.dimension_change == 0
        assert result.migration_required is False
        assert result.compatibility_percentage == 100.0
        assert "No migration required" in result.impact_assessment
    
    @pytest.mark.asyncio
    async def test_check_dimension_compatibility_different_dimensions(self, migration_service, mock_model_validator):
        """Test dimension compatibility check with different dimensions."""
        # Setup validation results
        mock_model_validator.validate_model_availability.side_effect = [
            ModelValidationResult(
                provider="openai",
                model="text-embedding-3-small",
                status=ModelValidationStatus.VALID,
                is_available=True,
                dimension=1536
            ),
            ModelValidationResult(
                provider="openai",
                model="text-embedding-3-large",
                status=ModelValidationStatus.VALID,
                is_available=True,
                dimension=3072  # Different dimension
            )
        ]
        
        # Execute
        result = await migration_service.check_dimension_compatibility(
            current_provider="openai",
            current_model="text-embedding-3-small",
            target_provider="openai",
            target_model="text-embedding-3-large"
        )
        
        # Assert
        assert result.is_compatible is False  # Large dimension change
        assert result.current_dimension == 1536
        assert result.target_dimension == 3072
        assert result.dimension_change == 1536
        assert result.migration_required is True
        assert result.compatibility_percentage == 50.0  # 1536/3072 * 100
        assert "Major dimension change" in result.impact_assessment
    
    @pytest.mark.asyncio
    async def test_check_dimension_compatibility_unavailable_model(self, migration_service, mock_model_validator):
        """Test dimension compatibility check with unavailable target model."""
        # Setup validation results
        mock_model_validator.validate_model_availability.side_effect = [
            ModelValidationResult(
                provider="openai",
                model="text-embedding-3-small",
                status=ModelValidationStatus.VALID,
                is_available=True,
                dimension=1536
            ),
            ModelValidationResult(
                provider="openai",
                model="unavailable-model",
                status=ModelValidationStatus.UNAVAILABLE,
                is_available=False,
                dimension=0
            )
        ]
        
        # Execute & Assert
        with pytest.raises(Exception):  # Should raise HTTPException
            await migration_service.check_dimension_compatibility(
                current_provider="openai",
                current_model="text-embedding-3-small",
                target_provider="openai",
                target_model="unavailable-model"
            )
    
    @pytest.mark.asyncio
    async def test_analyze_migration_impact_minimal(self, migration_service, mock_db):
        """Test migration impact analysis with minimal impact."""
        # Setup bot
        bot = Mock()
        bot.id = uuid.uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = bot
        
        # Setup document counts (small collection)
        mock_db.query.return_value.filter.return_value.scalar.return_value = 5  # documents
        mock_db.query.return_value.filter.return_value.count.return_value = 50  # chunks
        
        # Setup compatibility check
        compatibility_check = DimensionCompatibilityCheck(
            is_compatible=True,
            current_dimension=1536,
            target_dimension=1536,
            dimension_change=0,
            compatibility_percentage=100.0,
            migration_required=False,
            impact_assessment="No migration required"
        )
        
        # Execute
        result = await migration_service.analyze_migration_impact(
            bot_id=bot.id,
            target_provider="openai",
            target_model="text-embedding-3-large",
            compatibility_check=compatibility_check
        )
        
        # Assert
        assert result.impact_level == ImpactLevel.MINIMAL
        assert result.affected_documents == 5
        assert result.affected_chunks == 50
        assert "None" in result.data_loss_risk
        assert len(result.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_analyze_migration_impact_critical(self, migration_service, mock_db):
        """Test migration impact analysis with critical impact."""
        # Setup bot
        bot = Mock()
        bot.id = uuid.uuid4()
        mock_db.query.return_value.filter.return_value.first.return_value = bot
        
        # Setup document counts (large collection)
        mock_db.query.return_value.filter.return_value.scalar.return_value = 5000  # documents
        mock_db.query.return_value.filter.return_value.count.return_value = 50000  # chunks
        
        # Setup compatibility check with migration required
        compatibility_check = DimensionCompatibilityCheck(
            is_compatible=False,
            current_dimension=1536,
            target_dimension=3072,
            dimension_change=1536,
            compatibility_percentage=50.0,
            migration_required=True,
            impact_assessment="Major dimension change"
        )
        
        # Execute
        result = await migration_service.analyze_migration_impact(
            bot_id=bot.id,
            target_provider="openai",
            target_model="text-embedding-3-large",
            compatibility_check=compatibility_check
        )
        
        # Assert
        assert result.impact_level == ImpactLevel.CRITICAL
        assert result.affected_documents == 5000
        assert result.affected_chunks == 50000
        assert "6+ hours" in result.estimated_migration_time
        assert "Medium" in result.data_loss_risk  # Dimension change
        assert len(result.compatibility_issues) > 0
        assert any("phased migration" in rec for rec in result.recommendations)
    
    @pytest.mark.asyncio
    async def test_create_migration_plan(self, migration_service, mock_db):
        """Test migration plan creation."""
        # Setup bot
        bot = Mock()
        bot.id = uuid.uuid4()
        bot.embedding_provider = "openai"
        bot.embedding_model = "text-embedding-3-small"
        mock_db.query.return_value.filter.return_value.first.return_value = bot
        
        # Mock compatibility check and impact analysis
        with patch.object(migration_service, 'check_dimension_compatibility') as mock_compat:
            mock_compat.return_value = DimensionCompatibilityCheck(
                is_compatible=False,
                current_dimension=1536,
                target_dimension=3072,
                dimension_change=1536,
                compatibility_percentage=50.0,
                migration_required=True,
                impact_assessment="Major dimension change"
            )
            
            with patch.object(migration_service, 'analyze_migration_impact') as mock_impact:
                mock_impact.return_value = ModelChangeImpact(
                    impact_level=ImpactLevel.SIGNIFICANT,
                    affected_documents=100,
                    affected_chunks=1000,
                    estimated_migration_time="45 minutes - 2 hours",
                    estimated_cost="~$0.50",
                    data_loss_risk="Medium",
                    performance_impact="Increased accuracy expected",
                    compatibility_issues=["Dimension mismatch"],
                    recommendations=["Plan for maintenance window"],
                    rollback_complexity="High"
                )
                
                # Execute
                plan = await migration_service.create_migration_plan(
                    bot_id=bot.id,
                    target_provider="openai",
                    target_model="text-embedding-3-large",
                    migration_reason="Performance improvement"
                )
        
        # Assert
        assert plan.bot_id == bot.id
        assert plan.current_config["provider"] == "openai"
        assert plan.current_config["model"] == "text-embedding-3-small"
        assert plan.target_config["provider"] == "openai"
        assert plan.target_config["model"] == "text-embedding-3-large"
        assert len(plan.migration_steps) > 0
        assert len(plan.rollback_plan) > 0
        assert len(plan.validation_checkpoints) > 0
        assert plan.migration_id.startswith("migration_")
    
    @pytest.mark.asyncio
    async def test_execute_migration_dry_run(self, migration_service):
        """Test migration execution in dry run mode."""
        # Create a simple migration plan
        plan = MigrationPlan(
            migration_id="test-migration",
            bot_id=uuid.uuid4(),
            current_config={"provider": "openai", "model": "text-embedding-3-small", "dimension": 1536},
            target_config={"provider": "openai", "model": "text-embedding-3-large", "dimension": 3072},
            compatibility_check=Mock(),
            impact_analysis=Mock(),
            migration_steps=[
                {"name": "Pre-migration validation", "type": "validation", "validation_required": True},
                {"name": "Update configuration", "type": "configuration_update", "validation_required": True}
            ],
            rollback_plan=[],
            validation_checkpoints=[],
            estimated_duration="10 minutes",
            created_at=datetime.utcnow()
        )
        
        # Mock validation
        with patch.object(migration_service, '_validate_migration_step') as mock_validate:
            mock_validate.return_value = {"success": True}
            
            # Execute dry run
            result = await migration_service.execute_migration(
                migration_plan=plan,
                user_id=uuid.uuid4(),
                dry_run=True
            )
        
        # Assert
        assert result.migration_id == "test-migration"
        assert result.status == MigrationStatus.PENDING  # Dry run doesn't complete
        assert result.success is True
        assert result.completed_steps == 2
        assert result.total_steps == 2
        assert result.completed_at is None  # Dry run doesn't set completion time
    
    @pytest.mark.asyncio
    async def test_execute_migration_failure_with_rollback(self, migration_service):
        """Test migration execution with failure and rollback."""
        # Create migration plan
        plan = MigrationPlan(
            migration_id="test-migration",
            bot_id=uuid.uuid4(),
            current_config={"provider": "openai", "model": "text-embedding-3-small", "dimension": 1536},
            target_config={"provider": "openai", "model": "text-embedding-3-large", "dimension": 3072},
            compatibility_check=Mock(),
            impact_analysis=Mock(),
            migration_steps=[
                {"name": "Pre-migration validation", "type": "validation"},
                {"name": "Failing step", "type": "data_migration"}
            ],
            rollback_plan=[{"name": "Rollback step", "type": "rollback"}],
            validation_checkpoints=[],
            estimated_duration="10 minutes",
            created_at=datetime.utcnow()
        )
        
        # Mock step execution to fail on second step
        with patch.object(migration_service, '_execute_migration_step') as mock_execute:
            mock_execute.side_effect = [None, Exception("Migration failed")]
            
            with patch.object(migration_service, '_execute_rollback') as mock_rollback:
                # Execute migration
                result = await migration_service.execute_migration(
                    migration_plan=plan,
                    user_id=uuid.uuid4(),
                    dry_run=False
                )
        
        # Assert
        assert result.status == MigrationStatus.FAILED
        assert result.success is False
        assert result.completed_steps == 1  # Only first step completed
        assert result.error_message == "Migration failed"
        assert result.rollback_available is True
        mock_rollback.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_update_model_lists(self, migration_service, mock_embedding_service):
        """Test model list updates."""
        # Setup mock responses
        mock_embedding_service.get_available_models.return_value = [
            "text-embedding-3-small",
            "text-embedding-3-large"
        ]
        
        # Mock validation for new models
        with patch.object(migration_service.model_validator, 'validate_model_availability') as mock_validate:
            mock_validate.return_value = ModelValidationResult(
                provider="openai",
                model="new-model",
                status=ModelValidationStatus.VALID,
                is_available=True,
                dimension=1536
            )
            
            # Execute
            result = await migration_service.update_model_lists(
                provider="openai",
                force_refresh=True
            )
        
        # Assert
        assert result["success"] is True
        assert "openai" in result["results"]
        assert result["providers_updated"] == 1
    
    def test_estimate_detailed_migration_time(self, migration_service):
        """Test detailed migration time estimation."""
        # Test different scenarios
        assert "Immediate" in migration_service._estimate_detailed_migration_time(0, False)
        assert "configuration only" in migration_service._estimate_detailed_migration_time(0, True)
        assert "2-5 minutes" in migration_service._estimate_detailed_migration_time(25, True)
        assert "6+ hours" in migration_service._estimate_detailed_migration_time(50000, True)
    
    def test_estimate_migration_cost(self, migration_service):
        """Test migration cost estimation."""
        # Test different chunk counts and providers
        cost = migration_service._estimate_migration_cost(100, "openai", "text-embedding-3-small")
        assert "$" in cost
        
        cost_large = migration_service._estimate_migration_cost(10000, "openai", "text-embedding-3-small")
        assert "$" in cost_large
    
    def test_assess_performance_impact(self, migration_service):
        """Test performance impact assessment."""
        # Test dimension increase
        compatibility_check = DimensionCompatibilityCheck(
            is_compatible=False,
            current_dimension=1536,
            target_dimension=3072,
            dimension_change=1536,
            compatibility_percentage=50.0,
            migration_required=True,
            impact_assessment="Major change"
        )
        
        impact = migration_service._assess_performance_impact(
            compatibility_check, "openai", "text-embedding-3-large"
        )
        
        assert "Increased embedding dimension" in impact
        assert "improve accuracy" in impact
        assert "higher memory usage" in impact
    
    def test_generate_migration_recommendations(self, migration_service):
        """Test migration recommendation generation."""
        # Test critical impact recommendations
        recommendations = migration_service._generate_migration_recommendations(
            ImpactLevel.CRITICAL,
            Mock(is_compatible=False),
            50000
        )
        
        assert any("maintenance window" in rec for rec in recommendations)
        assert any("phased migration" in rec for rec in recommendations)
        assert any("backup" in rec for rec in recommendations)
        assert any("Monitor system resources" in rec for rec in recommendations)
    
    def test_assess_rollback_complexity(self, migration_service):
        """Test rollback complexity assessment."""
        # Test different impact levels
        assert "Simple" in migration_service._assess_rollback_complexity(
            ImpactLevel.MINIMAL, 10, False
        )
        
        assert "Very High" in migration_service._assess_rollback_complexity(
            ImpactLevel.CRITICAL, 50000, True
        )
    
    def test_create_migration_steps(self, migration_service):
        """Test migration step creation."""
        compatibility_check = DimensionCompatibilityCheck(
            is_compatible=False,
            current_dimension=1536,
            target_dimension=3072,
            dimension_change=1536,
            compatibility_percentage=50.0,
            migration_required=True,
            impact_assessment="Major change"
        )
        
        impact_analysis = ModelChangeImpact(
            impact_level=ImpactLevel.SIGNIFICANT,
            affected_documents=100,
            affected_chunks=1000,
            estimated_migration_time="1-2 hours",
            estimated_cost="~$1.00",
            data_loss_risk="Medium",
            performance_impact="Better accuracy",
            compatibility_issues=[],
            recommendations=[],
            rollback_complexity="High"
        )
        
        steps = migration_service._create_migration_steps(
            uuid.uuid4(), compatibility_check, impact_analysis
        )
        
        # Should include all necessary steps for migration
        step_names = [step["name"] for step in steps]
        assert "Pre-migration validation" in step_names
        assert "Create backup" in step_names
        assert "Create new collection" in step_names
        assert "Migrate embeddings" in step_names
        assert "Update bot configuration" in step_names
        assert "Post-migration validation" in step_names
    
    def test_create_rollback_plan(self, migration_service):
        """Test rollback plan creation."""
        compatibility_check = DimensionCompatibilityCheck(
            is_compatible=False,
            current_dimension=1536,
            target_dimension=3072,
            dimension_change=1536,
            compatibility_percentage=50.0,
            migration_required=True,
            impact_assessment="Major change"
        )
        
        rollback_steps = migration_service._create_rollback_plan(
            uuid.uuid4(), "openai", "text-embedding-3-small", compatibility_check
        )
        
        # Should include rollback steps for migration
        step_names = [step["name"] for step in rollback_steps]
        assert "Stop current operations" in step_names
        assert "Restore original collection" in step_names
        assert "Revert configuration" in step_names
        assert "Validate rollback" in step_names
    
    def test_estimate_total_duration(self, migration_service):
        """Test total duration estimation."""
        # Test with different migration times
        duration = migration_service._estimate_total_duration("15-30 minutes", 5)
        assert "minutes" in duration or "hour" in duration
        
        duration_long = migration_service._estimate_total_duration("2-4 hours", 8)
        assert "hour" in duration_long
    
    @pytest.mark.asyncio
    async def test_record_migration_history(self, migration_service, mock_db):
        """Test migration history recording."""
        plan = MigrationPlan(
            migration_id="test-migration",
            bot_id=uuid.uuid4(),
            current_config={"provider": "openai", "model": "text-embedding-3-small", "dimension": 1536},
            target_config={"provider": "openai", "model": "text-embedding-3-large", "dimension": 3072},
            compatibility_check=Mock(migration_required=True),
            impact_analysis=Mock(
                impact_level=ImpactLevel.SIGNIFICANT,
                affected_chunks=1000,
                estimated_migration_time="1 hour"
            ),
            migration_steps=[],
            rollback_plan=[],
            validation_checkpoints=[],
            estimated_duration="1 hour",
            created_at=datetime.utcnow()
        )
        
        # Execute
        await migration_service._record_migration_history(
            plan, uuid.uuid4(), True
        )
        
        # Assert
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_bot_not_found_in_impact_analysis(self, migration_service, mock_db):
        """Test impact analysis with non-existent bot."""
        # Setup
        mock_db.query.return_value.filter.return_value.first.return_value = None
        
        compatibility_check = Mock()
        
        # Execute & Assert
        with pytest.raises(Exception):  # Should raise HTTPException
            await migration_service.analyze_migration_impact(
                bot_id=uuid.uuid4(),
                target_provider="openai",
                target_model="text-embedding-3-large",
                compatibility_check=compatibility_check
            )