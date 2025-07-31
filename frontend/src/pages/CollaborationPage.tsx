/**
 * Collaboration Management Page
 * Comprehensive page for managing bot collaborators and permissions
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { BotWithRole, BotPermission } from '../types/bot';
import { botService } from '../services/botService';
import { permissionService } from '../services/permissionService';
import { CollaborationManagement } from '../components/bots/CollaborationManagement';
import { BulkPermissionManager } from '../components/bots/BulkPermissionManager';
import { NotificationSystem } from '../components/common/NotificationSystem';
import { Alert } from '../components/common/Alert';
import { Button } from '../components/common/Button';

interface CollaborationPageProps {
  botId?: string;
}

export const CollaborationPage: React.FC<CollaborationPageProps> = ({ botId: propBotId }) => {
  const { botId: urlBotId } = useParams<{ botId: string }>();
  const navigate = useNavigate();
  
  const botId = propBotId || urlBotId;
  
  const [bot, setBot] = useState<BotWithRole | null>(null);
  const [collaborators, setCollaborators] = useState<BotPermission[]>([]);
  const [currentUserRole, setCurrentUserRole] = useState<'owner' | 'admin' | 'editor' | 'viewer'>('viewer');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'collaborators' | 'bulk-update' | 'activity'>('collaborators');

  useEffect(() => {
    if (botId) {
      loadBotData();
    }
  }, [botId]);

  const loadBotData = async () => {
    if (!botId) return;

    try {
      setLoading(true);
      setError(null);

      // Load bot details and user's role
      const [botData, userRole] = await Promise.all([
        botService.getBot(botId),
        permissionService.getUserBotRole(botId)
      ]);

      // Transform BotResponse to BotWithRole
      const botWithRole: BotWithRole = {
        bot: botData,
        role: (userRole as 'owner' | 'admin' | 'editor' | 'viewer') || 'viewer'
      };

      setBot(botWithRole);
      setCurrentUserRole((userRole as 'owner' | 'admin' | 'editor' | 'viewer') || 'viewer');

      // Load collaborators if user has permission
      if (['owner', 'admin'].includes(userRole || 'viewer')) {
        try {
          const collaboratorsData = await permissionService.getBotPermissions(botId);
          setCollaborators(collaboratorsData);
        } catch (err) {
          console.warn('Could not load collaborators:', err);
        }
      }
    } catch (err: any) {
      console.error('Failed to load bot data:', err);
      setError(err.response?.data?.detail || 'Failed to load bot data');
    } finally {
      setLoading(false);
    }
  };

  const handlePermissionUpdate = () => {
    // Reload collaborators after permission changes
    if (['owner', 'admin'].includes(currentUserRole)) {
      loadBotData();
    }
  };

  const handleNotificationClick = (notification: any) => {
    // Handle notification clicks - could navigate to specific sections
    console.log('Notification clicked:', notification);
  };

  const canManageCollaborators = ['owner', 'admin'].includes(currentUserRole);

  if (loading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading collaboration data...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Alert type="error" message={error} />
        <div className="mt-4">
          <Button
            onClick={() => navigate('/bots')}
            className="bg-gray-600 hover:bg-gray-700 text-white"
          >
            Back to Bots
          </Button>
        </div>
      </div>
    );
  }

  if (!bot) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Alert type="error" message="Bot not found" />
        <div className="mt-4">
          <Button
            onClick={() => navigate('/bots')}
            className="bg-gray-600 hover:bg-gray-700 text-white"
          >
            Back to Bots
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between">
          <div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => navigate('/bots')}
                className="text-gray-400 hover:text-gray-600"
              >
                <svg className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                </svg>
              </button>
              <h1 className="text-3xl font-bold text-gray-900">
                Collaboration Management
              </h1>
            </div>
            <p className="mt-2 text-gray-600">
              Manage collaborators and permissions for "{bot.bot.name}"
            </p>
          </div>
          
          {/* Notification System */}
          <NotificationSystem
            botId={botId}
            onNotificationClick={handleNotificationClick}
          />
        </div>

        {/* Bot Info Card */}
        <div className="mt-6 bg-white shadow rounded-lg p-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-xl font-semibold text-gray-900">{bot.bot.name}</h2>
              <p className="text-gray-600">{bot.bot.description || 'No description'}</p>
              <div className="mt-2 flex items-center space-x-4 text-sm text-gray-500">
                <span>Your role: <span className="font-medium text-gray-900">{currentUserRole}</span></span>
                <span>•</span>
                <span>Provider: {bot.bot.llm_provider}</span>
                <span>•</span>
                <span>Collaboration: {bot.bot.allow_collaboration ? 'Enabled' : 'Disabled'}</span>
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-gray-500">Created</div>
              <div className="text-sm font-medium text-gray-900">
                {new Date(bot.bot.created_at).toLocaleDateString()}
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="border-b border-gray-200 mb-8">
        <nav className="-mb-px flex space-x-8">
          <button
            onClick={() => setActiveTab('collaborators')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'collaborators'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Collaborators
          </button>
          {canManageCollaborators && (
            <button
              onClick={() => setActiveTab('bulk-update')}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === 'bulk-update'
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              Bulk Update
            </button>
          )}
          <button
            onClick={() => setActiveTab('activity')}
            className={`py-2 px-1 border-b-2 font-medium text-sm ${
              activeTab === 'activity'
                ? 'border-blue-500 text-blue-600'
                : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
            }`}
          >
            Activity Log
          </button>
        </nav>
      </div>

      {/* Content */}
      <div className="mt-6">
        {activeTab === 'collaborators' && (
          <CollaborationManagement
            botId={botId!}
            botName={bot.bot.name}
            currentUserRole={currentUserRole}
            onPermissionUpdate={handlePermissionUpdate}
          />
        )}

        {activeTab === 'bulk-update' && canManageCollaborators && (
          <BulkPermissionManager
            botId={botId!}
            collaborators={collaborators}
            currentUserRole={currentUserRole}
            onUpdateComplete={handlePermissionUpdate}
          />
        )}

        {activeTab === 'activity' && (
          <div className="space-y-6">
            <div className="border-b border-gray-200 pb-4">
              <h2 className="text-2xl font-bold text-gray-900">Activity Log</h2>
              <p className="mt-1 text-sm text-gray-600">
                View recent activity and permission changes for this bot
              </p>
            </div>
            
            <CollaborationManagement
              botId={botId!}
              botName={bot.bot.name}
              currentUserRole={currentUserRole}
              onPermissionUpdate={handlePermissionUpdate}
            />
          </div>
        )}
      </div>

      {/* Permission Warning */}
      {!canManageCollaborators && (
        <div className="mt-8 bg-yellow-50 border border-yellow-200 rounded-md p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Limited Permissions
              </h3>
              <div className="mt-2 text-sm text-yellow-700">
                <p>
                  You have {currentUserRole} permissions for this bot. 
                  Only owners and admins can manage collaborators and permissions.
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}; 