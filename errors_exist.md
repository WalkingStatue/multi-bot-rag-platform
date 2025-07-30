FAILED tests/e2e/workflows/test_chat_rag_integration.py::TestChatRAGIntegration::test_chat_with_bot_success - AssertionError: Expected 'get_user_api_key' to have been called once. Called 2 times.
FAILED tests/e2e/workflows/test_chat_rag_integration.py::TestChatRAGIntegration::test_chat_with_nonexistent_bot - assert 403 == 404
FAILED tests/e2e/workflows/test_chat_rag_integration.py::TestChatRAGIntegration::test_chat_without_api_key - assert 500 == 400
FAILED tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_analytics_endpoints_require_authentication - assert 403 == 401
FAILED tests/integration/api/test_chat_api.py::TestChatAPI::test_chat_with_bot_success - assert 403 == 200
FAILED tests/integration/api/test_chat_api.py::TestChatAPI::test_chat_with_bot_with_session_id - assert 401 == 200
FAILED tests/integration/api/test_chat_api.py::TestChatAPI::test_chat_with_bot_permission_denied - assert 401 == 403
FAILED tests/integration/api/test_chat_api.py::TestChatAPI::test_chat_with_bot_not_found - assert 401 == 404
FAILED tests/integration/api/test_chat_api.py::TestChatAPI::test_chat_with_invalid_message - assert 401 == 422
FAILED tests/integration/api/test_chat_api.py::TestChatAPI::test_chat_with_very_long_message - assert 401 == 422
FAILED tests/integration/api/test_chat_api.py::TestChatAPI::test_create_bot_session_success - assert 401 == 200
FAILED tests/integration/api/test_chat_api.py::TestChatAPI::test_create_bot_session_without_title - assert 401 == 200
FAILED tests/integration/api/test_chat_api.py::TestChatAPI::test_create_bot_session_permission_denied - assert 401 == 403
FAILED tests/integration/api/test_chat_api.py::TestChatAPI::test_chat_with_invalid_bot_id - assert 401 == 422
FAILED tests/integration/api/test_chat_api.py::TestChatAPI::test_chat_with_invalid_session_id - assert 401 == 422
FAILED tests/integration/api/test_chat_api.py::TestChatAPI::test_chat_service_internal_error - assert 401 == 500
FAILED tests/integration/api/test_collaboration_api.py::TestCollaborationAPI::test_invite_collaborator_by_username - assert 403 == 201
FAILED tests/integration/api/test_collaboration_api.py::TestCollaborationAPI::test_invite_collaborator_by_email - assert 403 == 201
FAILED tests/integration/api/test_collaboration_api.py::TestCollaborationAPI::test_invite_nonexistent_user - assert 403 == 201
FAILED tests/integration/api/test_collaboration_api.py::TestCollaborationAPI::test_bulk_update_permissions - assert 403 == 200
FAILED tests/integration/api/test_collaboration_api.py::TestCollaborationAPI::test_bulk_update_with_invalid_data - assert 403 == 200
FAILED tests/integration/api/test_collaboration_api.py::TestCollaborationAPI::test_get_permission_history - assert 403 == 200
FAILED tests/integration/api/test_collaboration_api.py::TestCollaborationAPI::test_get_permission_history_with_pagination - assert 403 == 200
FAILED tests/integration/api/test_collaboration_api.py::TestCollaborationAPI::test_get_bot_activity_logs - assert 403 == 200
FAILED tests/integration/api/test_collaboration_api.py::TestCollaborationAPI::test_get_bot_activity_logs_with_filter - assert 403 == 200
FAILED tests/integration/api/test_collaboration_api.py::TestCollaborationWorkflows::test_complete_collaboration_workflow - assert 403 == 201
FAILED tests/integration/api/test_conversation_api.py::TestConversationAPI::test_update_session_success - assert 403 == 200
FAILED tests/integration/api/test_documents_api.py::TestDocumentAPI::test_upload_document_success - TypeError: object bool can't be used in 'await' expression       
FAILED tests/integration/api/test_permissions_api.py::TestPermissionsAPI::test_list_bot_collaborators - assert 403 == 200
FAILED tests/integration/api/test_permissions_api.py::TestPermissionsAPI::test_grant_bot_permission - assert 403 == 201
FAILED tests/integration/api/test_permissions_api.py::TestPermissionsAPI::test_grant_owner_role_forbidden - assert 403 == 400
FAILED tests/integration/api/test_permissions_api.py::TestPermissionsAPI::test_update_bot_permission - assert 403 == 200
FAILED tests/integration/api/test_permissions_api.py::TestPermissionsAPI::test_revoke_bot_permission - assert 403 == 204
FAILED tests/integration/api/test_permissions_api.py::TestPermissionsAPI::test_revoke_nonexistent_permission - assert 403 == 404
FAILED tests/integration/api/test_permissions_api.py::TestPermissionsAPI::test_revoke_owner_permission_forbidden - assert 403 == 400
FAILED tests/integration/api/test_permissions_api.py::TestPermissionsAPI::test_get_my_bot_role - assert 403 == 200
FAILED tests/integration/api/test_users_api.py::TestUsersAPI::test_update_profile_success - sqlalchemy.exc.InvalidRequestError: Instance '<User at 0x7def6a451ed0>' is not persistent within this Session
FAILED tests/integration/api/test_users_api.py::TestUsersAPI::test_change_password_success - assert 400 == 200
FAILED tests/integration/api/test_users_api.py::TestUsersAPI::test_search_users_success - AssertionError: assert 1 == 2
FAILED tests/integration/api/test_users_api.py::TestUsersAPI::test_get_api_keys_success - assert 401 == 200
FAILED tests/integration/api/test_users_api.py::TestUsersAPI::test_add_api_key_success - assert 500 == 201
FAILED tests/integration/api/test_users_api.py::TestUsersAPI::test_update_api_key_success - assert 404 == 200
FAILED tests/integration/api/test_users_api.py::TestUsersAPI::test_delete_api_key_success - assert 404 == 204
FAILED tests/integration/api/test_users_api.py::TestUsersAPI::test_get_user_settings_success - sqlalchemy.exc.IntegrityError: (psycopg2.errors.ForeignKeyViolation) insert or update on table "user_settings" violates foreign key constraint "user_settings_us...
FAILED tests/integration/api/test_users_api.py::TestUsersAPI::test_update_user_settings_success - assert 500 == 200
FAILED tests/integration/api/test_users_api.py::TestUsersAPI::test_update_user_settings_invalid_provider - assert 401 == 422
FAILED tests/integration/api/test_users_api.py::TestUsersAPI::test_get_user_analytics_success - assert 0 == 3
FAILED tests/integration/api/test_users_api.py::TestUsersAPI::test_get_user_activity_success - assert 0 == 3
FAILED tests/integration/api/test_websocket_api.py::TestWebSocketEndpoints::test_websocket_stats_endpoint - assert 0 == 5
FAILED tests/integration/api/test_websocket_api.py::TestWebSocketEndpoints::test_websocket_connections_endpoint - AssertionError: assert [] == ['user1', 'user2']    
FAILED tests/integration/api/test_websocket_api.py::TestWebSocketNotificationsEndpoint::test_websocket_notifications_successful_connection - AssertionError: Expected 'connect' to be called once. Called 0 times.
ERROR tests/e2e/scenarios/test_analytics_service.py::TestAnalyticsService::test_get_bot_usage_analytics_success
ERROR tests/e2e/scenarios/test_analytics_service.py::TestAnalyticsService::test_get_bot_usage_analytics_no_permission
ERROR tests/e2e/scenarios/test_analytics_service.py::TestAnalyticsService::test_get_user_dashboard_analytics_success
ERROR tests/e2e/scenarios/test_analytics_service.py::TestAnalyticsService::test_get_user_dashboard_analytics_no_bots
ERROR tests/e2e/scenarios/test_analytics_service.py::TestAnalyticsService::test_get_bot_activity_logs_success
ERROR tests/e2e/scenarios/test_analytics_service.py::TestAnalyticsService::test_get_bot_activity_logs_with_filter
ERROR tests/e2e/scenarios/test_analytics_service.py::TestAnalyticsService::test_get_system_analytics_success
ERROR tests/e2e/scenarios/test_analytics_service.py::TestAnalyticsService::test_export_bot_data_success
ERROR tests/e2e/scenarios/test_analytics_service.py::TestAnalyticsService::test_export_bot_data_selective_inclusion
ERROR tests/e2e/scenarios/test_analytics_service.py::TestAnalyticsService::test_export_bot_data_no_permission
ERROR tests/e2e/scenarios/test_analytics_service.py::TestAnalyticsService::test_analytics_with_date_filtering
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_get_bot_analytics_success
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_get_bot_analytics_no_permission
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_get_dashboard_analytics_success
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_get_bot_activity_logs_success
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_get_bot_activity_logs_with_filter
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_get_system_analytics_success
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_export_bot_data_success
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_export_bot_data_selective_inclusion
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_get_user_analytics_success
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_get_analytics_summary_success
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_analytics_with_date_range_validation
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_activity_logs_limit_validation
ERROR tests/integration/api/test_analytics_api.py::TestAnalyticsAPI::test_export_format_validation