"""
Integration tests for embedding models API endpoints.
"""
import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from main import app
from app.models.user import User
from app.models.bot import Bot
from app.services.embedding_model_validator import ModelValidationResult, ModelValidationStatus
from app.services.embedding_model_migration import DimensionCompatibilityCheck, ModelChangeImpact, ImpactLevel


class TestEmbeddingModelsAPI:
    """Integration tests for embedding models API."""
    
    @pytest.fixture
    def client(self):
        """Test client."""
        return TestClient(app)
    
    @pytest.fixture
    def mock_user(self):
        """Mock authenticated user."""
        user = Mock(spec=User)
        user.id = uuid.uuid4()
        user.email = "test@example.com"
        return user
    
    @pytest.fixture
    def mock_bot(self, mock_user):
        """Mock bot."""
        bot = Mock(spec=Bot)
        bot.id = uuid.uuid4()
        bot.name = "Test Bot"
        bot.owner_id = mock_user.id
        bot.embedding_provider = "openai"
        bot.embedding_model = "text-embedding-3-small"
        return bot
    
    @pytest.fixture
    def auth_headers(self):
        """Authentication headers."""
        return {"Authorization": "Bearer test-token"}
    
    def test_validate_model_success(self, client, auth_headers):
        """Test successful model validation."""
        with patch('app.api.embedding_models.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock()
            
            with patch('app.api.embedding_models.EmbeddingModelValidator') as mock_validator_class:
                mock_validator = Mock()
                mock_validator.validate_model_availability = AsyncMock(return_value=ModelValidationResult(
                    provider="openai",
                    model="text-embedding-3-small",
                    status=ModelValidationStatus.VALID,
                    is_available=True,
                    dimension=1536,
                    validation_error=None,
                    last_validated=None,
                    deprecation_info=None,
                    api_requirements={"requires_api_key": True}
                ))
                mock_validator_class.return_value = mock_validator
                
                # Execute
                response = client.post(
                    "/api/embedding-models/validate",
                    json={
                        "provider": "openai",
                        "model": "text-embedding-3-small",
                        "api_key": "test-key"
                    },
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["provider"] == "openai"
        assert data["model"] == "text-embedding-3-small"
        assert data["status"] == "valid"
        assert data["is_available"] is True
        assert data["dimension"] == 1536
    
    def test_validate_model_invalid_provider(self, client, auth_headers):
        """Test model validation with invalid provider."""
        with patch('app.api.embedding_models.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock()
            
            with patch('app.api.embedding_models.EmbeddingModelValidator') as mock_validator_class:
                mock_validator = Mock()
                mock_validator.validate_model_availability = AsyncMock(return_value=ModelValidationResult(
                    provider="invalid",
                    model="some-model",
                    status=ModelValidationStatus.INVALID,
                    is_available=False,
                    dimension=0,
                    validation_error="Provider 'invalid' is not supported"
                ))
                mock_validator_class.return_value = mock_validator
                
                # Execute
                response = client.post(
                    "/api/embedding-models/validate",
                    json={
                        "provider": "invalid",
                        "model": "some-model"
                    },
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "invalid"
        assert data["is_available"] is False
        assert "not supported" in data["validation_error"]
    
    def test_check_model_compatibility_success(self, client, auth_headers, mock_bot):
        """Test successful model compatibility check."""
        with patch('app.api.embedding_models.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock(id=uuid.uuid4())
            
            with patch('app.api.embedding_models.EmbeddingModelValidator') as mock_validator_class:
                from app.services.embedding_model_validator import ModelCompatibilityResult, MigrationImpact
                
                mock_validator = Mock()
                mock_validator.check_model_compatibility = AsyncMock(return_value=ModelCompatibilityResult(
                    is_compatible=True,
                    current_model=ModelValidationResult(
                        provider="openai",
                        model="text-embedding-3-small",
                        status=ModelValidationStatus.VALID,
                        is_available=True,
                        dimension=1536
                    ),
                    target_model=ModelValidationResult(
                        provider="openai",
                        model="text-embedding-3-large",
                        status=ModelValidationStatus.VALID,
                        is_available=True,
                        dimension=3072
                    ),
                    migration_required=True,
                    migration_impact=MigrationImpact.MEDIUM,
                    compatibility_issues=["Dimension mismatch: current=1536, target=3072"],
                    recommendations=["Plan for migration downtime"],
                    estimated_migration_time="30-60 minutes",
                    affected_documents=100
                ))
                mock_validator_class.return_value = mock_validator
                
                # Execute
                response = client.post(
                    "/api/embedding-models/compatibility",
                    json={
                        "bot_id": str(mock_bot.id),
                        "target_provider": "openai",
                        "target_model": "text-embedding-3-large"
                    },
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_compatible"] is True
        assert data["migration_required"] is True
        assert data["migration_impact"] == "medium"
        assert len(data["compatibility_issues"]) > 0
        assert data["affected_documents"] == 100
    
    def test_get_model_suggestions(self, client, auth_headers):
        """Test model suggestions endpoint."""
        with patch('app.api.embedding_models.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock()
            
            with patch('app.api.embedding_models.EmbeddingModelValidator') as mock_validator_class:
                from app.services.embedding_model_validator import ModelSuggestion
                
                mock_validator = Mock()
                mock_validator.suggest_compatible_models = AsyncMock(return_value=[
                    ModelSuggestion(
                        provider="openai",
                        model="text-embedding-3-small",
                        dimension=1536,
                        compatibility_score=0.9,
                        reason="Highly compatible, reliable provider",
                        migration_required=False,
                        estimated_cost="Low"
                    ),
                    ModelSuggestion(
                        provider="gemini",
                        model="embedding-001",
                        dimension=1536,
                        compatibility_score=0.8,
                        reason="Good compatibility",
                        migration_required=False,
                        estimated_cost="Low"
                    )
                ])
                mock_validator_class.return_value = mock_validator
                
                # Execute
                response = client.post(
                    "/api/embedding-models/suggestions",
                    json={
                        "target_dimension": 1536,
                        "max_suggestions": 5
                    },
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["provider"] == "openai"
        assert data[0]["compatibility_score"] == 0.9
        assert data[1]["provider"] == "gemini"
        assert data[1]["compatibility_score"] == 0.8
    
    def test_detect_deprecated_models(self, client, auth_headers):
        """Test deprecated models detection endpoint."""
        with patch('app.api.embedding_models.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock()
            
            with patch('app.api.embedding_models.EmbeddingModelValidator') as mock_validator_class:
                mock_validator = Mock()
                mock_validator.detect_deprecated_models = AsyncMock(return_value=[
                    {
                        "bot_id": str(uuid.uuid4()),
                        "bot_name": "Test Bot",
                        "current_provider": "openai",
                        "current_model": "text-embedding-ada-002",
                        "deprecation_info": {
                            "deprecated_date": "2024-01-01",
                            "replacement": "text-embedding-3-small",
                            "reason": "Replaced by more efficient model"
                        },
                        "suggested_replacements": [
                            {
                                "provider": "openai",
                                "model": "text-embedding-3-small",
                                "reason": "Recommended replacement",
                                "migration_required": False
                            }
                        ],
                        "detected_at": "2024-01-15T10:00:00"
                    }
                ])
                mock_validator_class.return_value = mock_validator
                
                # Execute
                response = client.get(
                    "/api/embedding-models/deprecated?check_all_bots=true",
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["current_model"] == "text-embedding-ada-002"
        assert len(data[0]["suggested_replacements"]) > 0
    
    def test_validate_all_models(self, client, auth_headers):
        """Test validate all models endpoint."""
        with patch('app.api.embedding_models.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock()
            
            with patch('app.api.embedding_models.EmbeddingModelValidator') as mock_validator_class:
                mock_validator = Mock()
                mock_validator.validate_all_models = AsyncMock(return_value={
                    "openai": [
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
                            dimension=3072
                        )
                    ]
                })
                mock_validator_class.return_value = mock_validator
                
                # Execute
                response = client.get(
                    "/api/embedding-models/validate-all",
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert "openai" in data
        assert len(data["openai"]) == 2
        assert data["openai"][0]["model"] == "text-embedding-3-small"
        assert data["openai"][1]["model"] == "text-embedding-3-large"
    
    def test_check_dimension_compatibility(self, client, auth_headers):
        """Test dimension compatibility check endpoint."""
        with patch('app.api.embedding_models.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock()
            
            with patch('app.api.embedding_models.EmbeddingModelMigration') as mock_migration_class:
                mock_migration = Mock()
                mock_migration.check_dimension_compatibility = AsyncMock(return_value=DimensionCompatibilityCheck(
                    is_compatible=False,
                    current_dimension=1536,
                    target_dimension=3072,
                    dimension_change=1536,
                    compatibility_percentage=50.0,
                    migration_required=True,
                    impact_assessment="Major dimension change - high impact migration"
                ))
                mock_migration_class.return_value = mock_migration
                
                # Execute
                response = client.post(
                    "/api/embedding-models/migration/compatibility"
                    "?current_provider=openai&current_model=text-embedding-3-small"
                    "&target_provider=openai&target_model=text-embedding-3-large",
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["is_compatible"] is False
        assert data["current_dimension"] == 1536
        assert data["target_dimension"] == 3072
        assert data["dimension_change"] == 1536
        assert data["migration_required"] is True
        assert "Major dimension change" in data["impact_assessment"]
    
    def test_analyze_migration_impact(self, client, auth_headers, mock_bot):
        """Test migration impact analysis endpoint."""
        with patch('app.api.embedding_models.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock()
            
            with patch('app.api.embedding_models.get_db') as mock_get_db:
                mock_db = Mock()
                mock_db.query.return_value.filter.return_value.first.return_value = mock_bot
                mock_get_db.return_value = mock_db
                
                with patch('app.api.embedding_models.EmbeddingModelMigration') as mock_migration_class:
                    mock_migration = Mock()
                    mock_migration.check_dimension_compatibility = AsyncMock(return_value=DimensionCompatibilityCheck(
                        is_compatible=False,
                        current_dimension=1536,
                        target_dimension=3072,
                        dimension_change=1536,
                        compatibility_percentage=50.0,
                        migration_required=True,
                        impact_assessment="Major change"
                    ))
                    mock_migration.analyze_migration_impact = AsyncMock(return_value=ModelChangeImpact(
                        impact_level=ImpactLevel.SIGNIFICANT,
                        affected_documents=100,
                        affected_chunks=1000,
                        estimated_migration_time="45 minutes - 2 hours",
                        estimated_cost="~$0.50",
                        data_loss_risk="Medium - dimension change requires reprocessing",
                        performance_impact="Increased accuracy expected",
                        compatibility_issues=["Dimension mismatch"],
                        recommendations=["Plan for maintenance window"],
                        rollback_complexity="High - complex rollback process"
                    ))
                    mock_migration_class.return_value = mock_migration
                    
                    # Execute
                    response = client.post(
                        f"/api/embedding-models/migration/impact"
                        f"?bot_id={mock_bot.id}&target_provider=openai&target_model=text-embedding-3-large",
                        headers=auth_headers
                    )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["impact_level"] == "significant"
        assert data["affected_documents"] == 100
        assert data["affected_chunks"] == 1000
        assert "45 minutes" in data["estimated_migration_time"]
        assert data["estimated_cost"] == "~$0.50"
        assert len(data["compatibility_issues"]) > 0
        assert len(data["recommendations"]) > 0
    
    def test_create_migration_plan(self, client, auth_headers, mock_bot):
        """Test migration plan creation endpoint."""
        with patch('app.api.embedding_models.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock()
            
            with patch('app.api.embedding_models.EmbeddingModelMigration') as mock_migration_class:
                from app.services.embedding_model_migration import MigrationPlan
                from datetime import datetime
                
                mock_migration = Mock()
                mock_migration.create_migration_plan = AsyncMock(return_value=MigrationPlan(
                    migration_id="migration_test_123",
                    bot_id=mock_bot.id,
                    current_config={
                        "provider": "openai",
                        "model": "text-embedding-3-small",
                        "dimension": 1536
                    },
                    target_config={
                        "provider": "openai",
                        "model": "text-embedding-3-large",
                        "dimension": 3072
                    },
                    compatibility_check=DimensionCompatibilityCheck(
                        is_compatible=False,
                        current_dimension=1536,
                        target_dimension=3072,
                        dimension_change=1536,
                        compatibility_percentage=50.0,
                        migration_required=True,
                        impact_assessment="Major change"
                    ),
                    impact_analysis=ModelChangeImpact(
                        impact_level=ImpactLevel.SIGNIFICANT,
                        affected_documents=100,
                        affected_chunks=1000,
                        estimated_migration_time="1-2 hours",
                        estimated_cost="~$0.50",
                        data_loss_risk="Medium",
                        performance_impact="Better accuracy",
                        compatibility_issues=[],
                        recommendations=["Plan maintenance window"],
                        rollback_complexity="High"
                    ),
                    migration_steps=[
                        {"name": "Pre-migration validation", "type": "validation"},
                        {"name": "Create backup", "type": "backup"},
                        {"name": "Migrate data", "type": "data_migration"}
                    ],
                    rollback_plan=[
                        {"name": "Restore backup", "type": "restore"}
                    ],
                    validation_checkpoints=["Pre-migration", "Post-migration"],
                    estimated_duration="2 hours",
                    created_at=datetime.utcnow()
                ))
                mock_migration_class.return_value = mock_migration
                
                # Execute
                response = client.post(
                    "/api/embedding-models/migration/plan",
                    json={
                        "bot_id": str(mock_bot.id),
                        "target_provider": "openai",
                        "target_model": "text-embedding-3-large",
                        "migration_reason": "Performance improvement"
                    },
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["migration_id"] == "migration_test_123"
        assert data["bot_id"] == str(mock_bot.id)
        assert data["current_config"]["provider"] == "openai"
        assert data["target_config"]["model"] == "text-embedding-3-large"
        assert len(data["migration_steps"]) == 3
        assert len(data["rollback_plan"]) == 1
        assert data["estimated_duration"] == "2 hours"
    
    def test_update_model_lists(self, client, auth_headers):
        """Test model lists update endpoint."""
        with patch('app.api.embedding_models.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock()
            
            with patch('app.api.embedding_models.EmbeddingModelMigration') as mock_migration_class:
                mock_migration = Mock()
                mock_migration.update_model_lists = AsyncMock(return_value={
                    "success": True,
                    "providers_updated": 1,
                    "results": {
                        "openai": {
                            "static_models": 3,
                            "dynamic_models": 3,
                            "new_models": [],
                            "updated_at": "2024-01-15T10:00:00"
                        }
                    },
                    "updated_at": "2024-01-15T10:00:00"
                })
                mock_migration_class.return_value = mock_migration
                
                # Execute
                response = client.post(
                    "/api/embedding-models/migration/update-lists?provider=openai&force_refresh=true",
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["providers_updated"] == 1
        assert "openai" in data["results"]
    
    def test_unauthorized_access(self, client):
        """Test unauthorized access to endpoints."""
        # Test without authentication headers
        response = client.post(
            "/api/embedding-models/validate",
            json={
                "provider": "openai",
                "model": "text-embedding-3-small"
            }
        )
        
        # Should return 401 or 403 (depending on auth implementation)
        assert response.status_code in [401, 403]
    
    def test_invalid_request_data(self, client, auth_headers):
        """Test endpoints with invalid request data."""
        with patch('app.api.embedding_models.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock()
            
            # Test missing required fields
            response = client.post(
                "/api/embedding-models/validate",
                json={
                    "provider": "openai"
                    # Missing model field
                },
                headers=auth_headers
            )
            
            assert response.status_code == 422  # Validation error
    
    def test_service_error_handling(self, client, auth_headers):
        """Test error handling when services raise exceptions."""
        with patch('app.api.embedding_models.get_current_user') as mock_get_user:
            mock_get_user.return_value = Mock()
            
            with patch('app.api.embedding_models.EmbeddingModelValidator') as mock_validator_class:
                mock_validator = Mock()
                mock_validator.validate_model_availability = AsyncMock(side_effect=Exception("Service error"))
                mock_validator_class.return_value = mock_validator
                
                # Execute
                response = client.post(
                    "/api/embedding-models/validate",
                    json={
                        "provider": "openai",
                        "model": "text-embedding-3-small"
                    },
                    headers=auth_headers
                )
        
        # Assert
        assert response.status_code == 500
        data = response.json()
        assert "Service error" in data["detail"]