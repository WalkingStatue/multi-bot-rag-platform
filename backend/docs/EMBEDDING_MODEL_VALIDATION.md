# Embedding Model Validation and Migration System

This document describes the comprehensive embedding model validation and migration system implemented for the multi-bot RAG platform.

## Overview

The system provides robust validation, compatibility checking, and migration capabilities for embedding models across multiple providers (OpenAI, Gemini, Anthropic, OpenRouter). It ensures safe transitions between embedding configurations while maintaining data integrity and system reliability.

## Key Components

### 1. EmbeddingModelValidator

**Purpose**: Validates embedding models for availability, compatibility, and deprecation status.

**Key Features**:
- Model availability validation across all providers
- API key validation with timeout handling
- Deprecation detection and migration suggestions
- Compatibility scoring and recommendations
- Comprehensive caching for performance

**Main Methods**:
```python
async def validate_model_availability(provider, model, api_key=None, use_cache=True)
async def check_model_compatibility(bot_id, target_provider, target_model, api_key=None)
async def suggest_compatible_models(target_dimension=None, exclude_provider=None, max_suggestions=5)
async def detect_deprecated_models(check_all_bots=False, bot_id=None)
async def validate_all_models(refresh_cache=False)
```

### 2. EmbeddingModelMigration

**Purpose**: Handles model migration planning, execution, and rollback with comprehensive impact analysis.

**Key Features**:
- Dimension compatibility checking
- Migration impact analysis with detailed explanations
- Safe migration workflows with validation checkpoints
- Automatic rollback on failure
- Model list updates from providers

**Main Methods**:
```python
async def check_dimension_compatibility(current_provider, current_model, target_provider, target_model)
async def analyze_migration_impact(bot_id, target_provider, target_model, compatibility_check)
async def create_migration_plan(bot_id, target_provider, target_model, migration_reason=None)
async def execute_migration(migration_plan, user_id, dry_run=False)
async def update_model_lists(provider=None, force_refresh=False)
```

## API Endpoints

### Model Validation Endpoints

#### POST `/api/embedding-models/validate`
Validate a specific embedding model for availability and compatibility.

**Request**:
```json
{
  "provider": "openai",
  "model": "text-embedding-3-small",
  "api_key": "optional-api-key"
}
```

**Response**:
```json
{
  "provider": "openai",
  "model": "text-embedding-3-small",
  "status": "valid",
  "is_available": true,
  "dimension": 1536,
  "validation_error": null,
  "last_validated": "2024-01-15T10:00:00Z",
  "deprecation_info": null,
  "api_requirements": {
    "requires_api_key": true,
    "base_url": "https://api.openai.com/v1"
  }
}
```

#### POST `/api/embedding-models/compatibility`
Check compatibility between current and target model configurations.

**Request**:
```json
{
  "bot_id": "uuid",
  "target_provider": "openai",
  "target_model": "text-embedding-3-large"
}
```

**Response**:
```json
{
  "is_compatible": true,
  "current_model": { /* ModelValidationResponse */ },
  "target_model": { /* ModelValidationResponse */ },
  "migration_required": true,
  "migration_impact": "medium",
  "compatibility_issues": ["Dimension mismatch: current=1536, target=3072"],
  "recommendations": ["Plan for migration downtime"],
  "estimated_migration_time": "30-60 minutes",
  "affected_documents": 100
}
```

#### POST `/api/embedding-models/suggestions`
Get compatible model suggestions based on criteria.

**Request**:
```json
{
  "target_dimension": 1536,
  "exclude_provider": "openai",
  "exclude_model": "text-embedding-ada-002",
  "max_suggestions": 5
}
```

**Response**:
```json
[
  {
    "provider": "gemini",
    "model": "embedding-001",
    "dimension": 1536,
    "compatibility_score": 0.85,
    "reason": "Good compatibility, reliable provider",
    "migration_required": false,
    "estimated_cost": "Low"
  }
]
```

#### GET `/api/embedding-models/deprecated`
Detect deprecated models in use and suggest migrations.

**Query Parameters**:
- `check_all_bots`: boolean (default: false)
- `bot_id`: UUID (optional)

**Response**:
```json
[
  {
    "bot_id": "uuid",
    "bot_name": "My Bot",
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
        "migration_required": false
      }
    ],
    "detected_at": "2024-01-15T10:00:00Z"
  }
]
```

#### GET `/api/embedding-models/validate-all`
Validate all available models across all providers.

**Query Parameters**:
- `refresh_cache`: boolean (default: false)

**Response**:
```json
{
  "openai": [
    { /* ModelValidationResponse */ },
    { /* ModelValidationResponse */ }
  ],
  "gemini": [
    { /* ModelValidationResponse */ }
  ]
}
```

### Migration Endpoints

#### POST `/api/embedding-models/migration/compatibility`
Check dimension compatibility between old and new models.

**Query Parameters**:
- `current_provider`: string
- `current_model`: string
- `target_provider`: string
- `target_model`: string

**Response**:
```json
{
  "is_compatible": false,
  "current_dimension": 1536,
  "target_dimension": 3072,
  "dimension_change": 1536,
  "compatibility_percentage": 50.0,
  "migration_required": true,
  "impact_assessment": "Major dimension change - high impact migration"
}
```

#### POST `/api/embedding-models/migration/impact`
Analyze the impact of model changes with clear explanations.

**Query Parameters**:
- `bot_id`: UUID
- `target_provider`: string
- `target_model`: string

**Response**:
```json
{
  "impact_level": "significant",
  "affected_documents": 500,
  "affected_chunks": 2500,
  "estimated_migration_time": "1-2 hours",
  "estimated_cost": "~$1.25",
  "data_loss_risk": "Medium - dimension change requires reprocessing",
  "performance_impact": "Increased accuracy expected with larger embeddings",
  "compatibility_issues": ["Dimension mismatch"],
  "recommendations": ["Schedule during maintenance window"],
  "rollback_complexity": "High - complex rollback process required"
}
```

#### POST `/api/embedding-models/migration/plan`
Create a comprehensive migration plan with validation and rollback.

**Request**:
```json
{
  "bot_id": "uuid",
  "target_provider": "openai",
  "target_model": "text-embedding-3-large",
  "migration_reason": "Performance improvement"
}
```

**Response**:
```json
{
  "migration_id": "migration_uuid_timestamp",
  "bot_id": "uuid",
  "current_config": {
    "provider": "openai",
    "model": "text-embedding-3-small",
    "dimension": 1536
  },
  "target_config": {
    "provider": "openai",
    "model": "text-embedding-3-large",
    "dimension": 3072
  },
  "compatibility_check": { /* DimensionCompatibilityResponse */ },
  "impact_analysis": { /* MigrationImpactResponse */ },
  "migration_steps": [
    {
      "name": "Pre-migration validation",
      "description": "Validate current configuration and target model",
      "type": "validation",
      "validation_required": true,
      "estimated_duration": "1-2 minutes"
    }
  ],
  "rollback_plan": [
    {
      "name": "Restore original collection",
      "description": "Restore original vector collection from backup",
      "type": "data_restoration"
    }
  ],
  "validation_checkpoints": [
    "Pre-migration validation",
    "Backup verification",
    "New collection creation",
    "Data migration validation",
    "Performance validation",
    "Post-migration verification"
  ],
  "estimated_duration": "2 hours",
  "created_at": "2024-01-15T10:00:00Z"
}
```

#### POST `/api/embedding-models/migration/update-lists`
Update model lists when providers add new models.

**Query Parameters**:
- `provider`: string (optional)
- `force_refresh`: boolean (default: false)

**Response**:
```json
{
  "success": true,
  "providers_updated": 2,
  "results": {
    "openai": {
      "static_models": 3,
      "dynamic_models": 3,
      "new_models": [],
      "updated_at": "2024-01-15T10:00:00Z"
    },
    "gemini": {
      "static_models": 1,
      "dynamic_models": 1,
      "new_models": [],
      "updated_at": "2024-01-15T10:00:00Z"
    }
  },
  "updated_at": "2024-01-15T10:00:00Z"
}
```

## Database Models

### CollectionMetadata
Tracks embedding configuration and dimensions for each bot's vector collection.

```sql
CREATE TABLE collection_metadata (
    id UUID PRIMARY KEY,
    bot_id UUID REFERENCES bots(id) ON DELETE CASCADE,
    collection_name VARCHAR(255) NOT NULL,
    embedding_provider VARCHAR(50) NOT NULL,
    embedding_model VARCHAR(100) NOT NULL,
    embedding_dimension INTEGER NOT NULL,
    status VARCHAR(20) DEFAULT 'active',
    points_count INTEGER DEFAULT 0,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    configuration_history JSONB,
    migration_info JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### EmbeddingConfigurationHistory
Audit trail of embedding configuration changes for rollback and analysis.

```sql
CREATE TABLE embedding_configuration_history (
    id UUID PRIMARY KEY,
    bot_id UUID REFERENCES bots(id) ON DELETE CASCADE,
    previous_provider VARCHAR(50),
    previous_model VARCHAR(100),
    previous_dimension INTEGER,
    new_provider VARCHAR(50) NOT NULL,
    new_model VARCHAR(100) NOT NULL,
    new_dimension INTEGER NOT NULL,
    change_reason TEXT,
    migration_required BOOLEAN DEFAULT FALSE,
    migration_completed BOOLEAN DEFAULT FALSE,
    migration_id VARCHAR(100),
    changed_by UUID REFERENCES users(id) ON DELETE SET NULL,
    changed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    extra_metadata JSONB
);
```

### DimensionCompatibilityCache
Cache for dimension compatibility information to avoid repeated API calls.

```sql
CREATE TABLE dimension_compatibility_cache (
    id UUID PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    model VARCHAR(100) NOT NULL,
    dimension INTEGER NOT NULL,
    is_valid BOOLEAN DEFAULT TRUE,
    last_validated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    validation_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

## Usage Examples

### 1. Basic Model Validation

```python
from app.services.embedding_model_validator import EmbeddingModelValidator

validator = EmbeddingModelValidator(db)

# Validate a specific model
result = await validator.validate_model_availability(
    provider="openai",
    model="text-embedding-3-small",
    api_key="your-api-key"
)

if result.is_available:
    print(f"Model is available with dimension {result.dimension}")
else:
    print(f"Model validation failed: {result.validation_error}")
```

### 2. Compatibility Check

```python
# Check if a bot can migrate to a new model
compatibility = await validator.check_model_compatibility(
    bot_id=bot_id,
    target_provider="openai",
    target_model="text-embedding-3-large"
)

if compatibility.is_compatible:
    if compatibility.migration_required:
        print(f"Migration required: {compatibility.estimated_migration_time}")
    else:
        print("Direct configuration change possible")
else:
    print("Models are not compatible")
    for issue in compatibility.compatibility_issues:
        print(f"  - {issue}")
```

### 3. Migration Planning and Execution

```python
from app.services.embedding_model_migration import EmbeddingModelMigration

migration_service = EmbeddingModelMigration(db)

# Create migration plan
plan = await migration_service.create_migration_plan(
    bot_id=bot_id,
    target_provider="openai",
    target_model="text-embedding-3-large",
    migration_reason="Performance improvement"
)

# Execute dry run first
dry_run_result = await migration_service.execute_migration(
    migration_plan=plan,
    user_id=user_id,
    dry_run=True
)

if dry_run_result.success:
    # Execute actual migration
    result = await migration_service.execute_migration(
        migration_plan=plan,
        user_id=user_id,
        dry_run=False
    )
    
    if result.success:
        print("Migration completed successfully")
    else:
        print(f"Migration failed: {result.error_message}")
        if result.rollback_available:
            print("System was rolled back to original state")
```

## Error Handling

The system provides comprehensive error handling for various scenarios:

### 1. Network Issues
- API timeouts are handled gracefully with fallback to cached results
- Connection errors trigger retry logic with exponential backoff
- Network failures don't prevent basic model availability checks

### 2. Invalid Configurations
- Unsupported providers return clear error messages with suggestions
- Invalid models are detected and alternatives are recommended
- API key issues are identified with specific remediation steps

### 3. Migration Failures
- Failed migrations automatically trigger rollback procedures
- Partial failures are isolated to prevent data corruption
- Detailed error logs help with troubleshooting

### 4. Data Integrity
- All operations include validation checkpoints
- Backup creation is mandatory for destructive operations
- Referential integrity is maintained between database and vector store

## Performance Considerations

### 1. Caching Strategy
- Validation results are cached for 6 hours by default
- API key validation results are cached with TTL
- Model lists are cached and updated periodically

### 2. Batch Processing
- Large migrations are processed in batches to avoid memory issues
- Progress tracking allows for resumption of interrupted operations
- Resource monitoring prevents system overload

### 3. Async Operations
- All operations are fully asynchronous
- Concurrent processing within resource limits
- Non-blocking validation and migration workflows

## Security Considerations

### 1. API Key Handling
- API keys are never logged or stored in plain text
- Validation occurs over secure connections
- Keys are encrypted before database storage

### 2. Access Control
- All endpoints require authentication
- Bot ownership is verified before migration operations
- Audit trails track all configuration changes

### 3. Data Protection
- Backups are created before destructive operations
- Rollback capabilities ensure data recovery
- Migration operations are atomic where possible

## Monitoring and Observability

### 1. Metrics Collection
- Migration success/failure rates
- Validation performance metrics
- API usage and cost tracking
- Cache hit rates and performance

### 2. Logging
- Detailed operation logs for troubleshooting
- Error categorization and tracking
- Performance metrics and timing data

### 3. Alerting
- Failed migrations trigger immediate alerts
- Deprecated model usage notifications
- Performance degradation warnings

## Best Practices

### 1. Before Migration
- Always run dry-run first
- Verify API key availability
- Schedule during low-usage periods
- Notify users of potential disruption

### 2. During Migration
- Monitor system resources
- Track progress through checkpoints
- Be prepared for rollback if needed
- Maintain communication with users

### 3. After Migration
- Validate migration success
- Monitor performance metrics
- Update documentation
- Collect user feedback

## Troubleshooting

### Common Issues

1. **API Key Validation Failures**
   - Verify key format and permissions
   - Check network connectivity
   - Ensure provider service availability

2. **Dimension Mismatch Errors**
   - Confirm model specifications
   - Check for model updates
   - Verify provider documentation

3. **Migration Timeouts**
   - Increase timeout settings
   - Process in smaller batches
   - Check system resources

4. **Rollback Failures**
   - Verify backup integrity
   - Check database connectivity
   - Ensure sufficient storage space

### Support Resources

- API documentation: `/docs` endpoint
- Example implementations: `examples/` directory
- Test cases: `tests/` directory
- Configuration guides: `docs/` directory