#!/usr/bin/env python3
"""
Collection Lifecycle Management Integration Example

This example demonstrates how the new collection lifecycle management
and monitoring features (Task 4.2) integrate with the existing RAG system.
"""

import asyncio
import uuid
from typing import Dict, Any

from app.services.vector_collection_manager import VectorCollectionManager
from app.services.rag_pipeline_manager import RAGPipelineManager


class CollectionLifecycleIntegration:
    """
    Integration example showing how collection lifecycle management
    works with the RAG pipeline.
    """
    
    def __init__(self, db_session):
        self.db = db_session
        self.collection_manager = VectorCollectionManager(db_session)
        self.rag_manager = RAGPipelineManager(db_session)
    
    async def handle_bot_configuration_change(
        self, 
        bot_id: uuid.UUID, 
        new_embedding_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle bot configuration changes with automatic migration detection.
        
        This method demonstrates how the new configuration change detection
        integrates with the existing RAG pipeline.
        """
        try:
            # Step 1: Detect configuration changes
            config_change = await self.collection_manager.detect_configuration_changes(bot_id)
            
            if config_change and config_change.migration_required:
                print(f"Configuration change detected for bot {bot_id}:")
                print(f"  Change type: {config_change.change_type}")
                print(f"  Priority: {config_change.priority}")
                print(f"  Migration required: {config_change.migration_required}")
                
                # Step 2: Validate new configuration
                validation_result = await self.collection_manager.validate_collection_configuration(
                    bot_id, new_embedding_config
                )
                
                if not validation_result.success:
                    return {
                        "success": False,
                        "error": f"Configuration validation failed: {validation_result.error}",
                        "requires_migration": validation_result.metadata.get("requires_migration", False)
                    }
                
                # Step 3: If migration is required, it will be automatically scheduled
                # The maintenance system will handle the actual migration
                return {
                    "success": True,
                    "configuration_change": config_change,
                    "migration_scheduled": True,
                    "message": "Configuration change detected and migration scheduled"
                }
            
            else:
                # No significant changes detected
                return {
                    "success": True,
                    "configuration_change": None,
                    "migration_scheduled": False,
                    "message": "No configuration changes requiring migration"
                }
                
        except Exception as e:
            # Log diagnostic information
            await self.collection_manager._log_diagnostic_info(
                bot_id=str(bot_id),
                error_type="configuration_change_handling_error",
                error_message=str(e),
                context={
                    "operation": "handle_bot_configuration_change",
                    "new_config": new_embedding_config
                }
            )
            
            return {
                "success": False,
                "error": f"Error handling configuration change: {str(e)}"
            }
    
    async def process_document_with_collection_management(
        self, 
        bot_id: uuid.UUID, 
        document_content: str
    ) -> Dict[str, Any]:
        """
        Process a document with automatic collection health checking.
        
        This method demonstrates how collection health monitoring
        integrates with document processing.
        """
        try:
            # Step 1: Check collection health before processing
            health_info = await self.collection_manager.check_collection_health(bot_id)
            
            if health_info.status == "failed":
                print(f"Collection health check failed for bot {bot_id}, attempting repair...")
                
                # Attempt automatic repair
                repair_result = await self.collection_manager.repair_collection(bot_id)
                
                if not repair_result.success:
                    return {
                        "success": False,
                        "error": f"Collection repair failed: {repair_result.error}",
                        "health_status": health_info.status
                    }
                
                print(f"Collection repair successful for bot {bot_id}")
            
            # Step 2: Process document using RAG pipeline
            # (This would integrate with the actual document processing logic)
            processing_result = {
                "success": True,
                "chunks_processed": 10,  # Example
                "embeddings_generated": 10,
                "collection_health": health_info.status
            }
            
            # Step 3: Schedule maintenance if needed
            if health_info.points_count and health_info.points_count > 1000:
                maintenance_scheduled = await self.collection_manager.schedule_maintenance(bot_id)
                processing_result["maintenance_scheduled"] = maintenance_scheduled
            
            return processing_result
            
        except Exception as e:
            # Use retry logic for critical operations
            try:
                # Retry the operation with exponential backoff
                async def retry_operation():
                    # Simplified retry logic - in practice this would be more complex
                    return {"success": True, "retried": True}
                
                result = await self.collection_manager.perform_collection_operation_with_retry(
                    "document_processing",
                    retry_operation,
                    bot_id
                )
                
                return result
                
            except Exception as retry_error:
                return {
                    "success": False,
                    "error": f"Document processing failed after retries: {str(retry_error)}"
                }
    
    async def run_maintenance_cycle(self) -> Dict[str, Any]:
        """
        Run a complete maintenance cycle.
        
        This method demonstrates how the maintenance scheduling and execution
        works in practice.
        """
        try:
            print("Starting maintenance cycle...")
            
            # Step 1: Schedule maintenance tasks
            scheduling_result = await self.collection_manager.schedule_maintenance_tasks()
            print(f"Scheduled {scheduling_result.get('tasks_scheduled', 0)} maintenance tasks")
            
            # Step 2: Execute maintenance tasks
            executed_tasks = []
            max_tasks_per_cycle = 5  # Limit tasks per cycle
            
            for _ in range(max_tasks_per_cycle):
                task_result = await self.collection_manager.execute_next_maintenance_task()
                
                if task_result is None:
                    break  # No more tasks
                
                executed_tasks.append(task_result)
                print(f"Executed {task_result['task_type']} for bot {task_result['bot_id']}: "
                      f"{'✓' if task_result['success'] else '✗'}")
            
            # Step 3: Get maintenance queue status
            queue_status = self.collection_manager.get_maintenance_queue_status()
            
            # Step 4: Get diagnostic summary
            diagnostic_summary = self.collection_manager.get_diagnostic_summary(hours=1)
            
            return {
                "success": True,
                "scheduling_result": scheduling_result,
                "executed_tasks": executed_tasks,
                "queue_status": queue_status,
                "diagnostic_summary": diagnostic_summary
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Maintenance cycle failed: {str(e)}"
            }
    
    async def get_system_health_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive system health report.
        
        This method demonstrates how to use the diagnostic and monitoring
        features to get insights into system health.
        """
        try:
            # Get collection health summary
            health_summary = self.collection_manager.get_collection_health_summary()
            
            # Get maintenance queue status
            queue_status = self.collection_manager.get_maintenance_queue_status()
            
            # Get diagnostic summary for last 24 hours
            diagnostic_summary = self.collection_manager.get_diagnostic_summary(hours=24)
            
            # Calculate health score
            total_collections = health_summary.get("total_collections", 0)
            healthy_collections = health_summary.get("status_distribution", {}).get("healthy", 0)
            health_score = (healthy_collections / max(total_collections, 1)) * 100
            
            return {
                "health_score": health_score,
                "collection_health": health_summary,
                "maintenance_queue": queue_status,
                "diagnostics": diagnostic_summary,
                "recommendations": self._generate_recommendations(
                    health_summary, queue_status, diagnostic_summary
                )
            }
            
        except Exception as e:
            return {
                "error": f"Failed to generate health report: {str(e)}"
            }
    
    def _generate_recommendations(
        self, 
        health_summary: Dict[str, Any], 
        queue_status: Dict[str, Any], 
        diagnostic_summary: Dict[str, Any]
    ) -> list:
        """Generate recommendations based on system health."""
        recommendations = []
        
        # Check for collections needing attention
        collections_needing_attention = health_summary.get("collections_needing_attention", [])
        if collections_needing_attention:
            recommendations.append(
                f"Attention needed for {len(collections_needing_attention)} collections: "
                f"{', '.join(collections_needing_attention[:3])}{'...' if len(collections_needing_attention) > 3 else ''}"
            )
        
        # Check maintenance queue
        total_tasks = queue_status.get("total_tasks", 0)
        if total_tasks > 10:
            recommendations.append(
                f"High maintenance queue ({total_tasks} tasks) - consider increasing maintenance frequency"
            )
        
        # Check error patterns
        error_types = diagnostic_summary.get("error_types", {})
        if error_types:
            most_common_error = max(error_types.items(), key=lambda x: x[1])
            if most_common_error[1] > 5:
                recommendations.append(
                    f"Frequent {most_common_error[0]} errors ({most_common_error[1]} occurrences) - investigate root cause"
                )
        
        if not recommendations:
            recommendations.append("System health is good - no immediate action required")
        
        return recommendations


async def main():
    """Example usage of the collection lifecycle integration."""
    print("Collection Lifecycle Management Integration Example")
    print("=" * 55)
    
    # This would normally use a real database session
    from unittest.mock import Mock
    mock_db = Mock()
    
    integration = CollectionLifecycleIntegration(mock_db)
    
    # Example 1: Handle configuration change
    print("\n1. Handling bot configuration change:")
    bot_id = uuid.uuid4()
    new_config = {
        "provider": "openai",
        "model": "text-embedding-3-small",
        "dimension": 1536
    }
    
    # This would normally work with real data
    print(f"   Bot ID: {bot_id}")
    print(f"   New config: {new_config}")
    print("   → Configuration change detection and migration scheduling would occur here")
    
    # Example 2: System health report
    print("\n2. System health monitoring:")
    print("   → Health reports would include:")
    print("     - Collection health scores")
    print("     - Maintenance queue status")
    print("     - Error pattern analysis")
    print("     - Automated recommendations")
    
    # Example 3: Maintenance cycle
    print("\n3. Automated maintenance:")
    print("   → Maintenance cycle would:")
    print("     - Schedule optimization tasks")
    print("     - Execute health checks")
    print("     - Perform collection repairs")
    print("     - Generate diagnostic reports")
    
    print("\n" + "=" * 55)
    print("✅ Integration example complete!")
    print("\nKey benefits of Task 4.2 implementation:")
    print("- Automatic detection of configuration changes")
    print("- Robust retry logic with exponential backoff")
    print("- Comprehensive diagnostic logging")
    print("- Proactive maintenance scheduling")
    print("- System health monitoring and reporting")


if __name__ == "__main__":
    asyncio.run(main())