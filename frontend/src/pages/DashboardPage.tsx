/**
 * Dashboard page component
 */
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../hooks/useAuth';
import { Navigation } from '../components/common/Navigation';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { BotManagement } from '../components/bots/BotManagement';
import { APIKeyManagement } from '../components/apikeys/APIKeyManagement';
import { botService } from '../services/botService';
import { BotWithRole } from '../types/bot';

export const DashboardPage: React.FC = () => {
  const { /* user */ } = useAuth();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [bots, setBots] = useState<BotWithRole[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [stats, setStats] = useState({
    totalBots: 0,
    ownedBots: 0,
    sharedBots: 0,
    recentActivity: 0
  });

  // Get current view from URL parameters
  const currentView = searchParams.get('view') || 'dashboard';

  useEffect(() => {
    if (currentView === 'dashboard') {
      loadDashboardData();
    }
  }, [currentView]);

  const loadDashboardData = async () => {
    try {
      setIsLoading(true);
      const userBots = await botService.getUserBots();
      setBots(userBots);
      
      // Calculate stats
      const ownedBots = userBots.filter(bot => bot.role === 'owner').length;
      const sharedBots = userBots.filter(bot => bot.role !== 'owner').length;
      
      setStats({
        totalBots: userBots.length,
        ownedBots,
        sharedBots,
        recentActivity: userBots.filter(bot => {
          const lastUpdated = new Date(bot.bot.updated_at);
          const weekAgo = new Date();
          weekAgo.setDate(weekAgo.getDate() - 7);
          return lastUpdated > weekAgo;
        }).length
      });
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCreateBot = () => {
    navigate('/dashboard?view=bots&action=create');
  };

  const handleManageBots = () => {
    navigate('/dashboard?view=bots');
  };

  const handleManageAPIKeys = () => {
    navigate('/dashboard?view=api-keys');
  };

  const handleManageProfile = () => {
    navigate('/profile');
  };

  const handleBackToDashboard = () => {
    navigate('/dashboard');
  };

  const getRoleBadgeColor = (role: string) => {
    switch (role) {
      case 'owner': return 'bg-green-100 text-green-800';
      case 'admin': return 'bg-blue-100 text-blue-800';
      case 'editor': return 'bg-yellow-100 text-yellow-800';
      case 'viewer': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getProviderIcon = (provider: string) => {
    const icons = {
      openai: '🤖',
      anthropic: '🧠',
      gemini: '💎',
      openrouter: '🔀',
    };
    return icons[provider as keyof typeof icons] || '🤖';
  };

  const renderContent = () => {
    switch (currentView) {
      case 'bots':
        return <BotManagement />;
      case 'api-keys':
        return <APIKeyManagement />;
      default:
        return renderDashboardContent();
    }
  };

  const renderDashboardContent = () => (
    <>
      {/* Dashboard Header */}
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-gray-900 mb-2">
          Dashboard
        </h2>
        <p className="text-gray-600">
          Welcome to your Multi-Bot RAG Platform dashboard!
        </p>
      </div>

      {/* Quick Stats */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Total Bots
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {isLoading ? '...' : stats.totalBots}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-green-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Owned Bots
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {isLoading ? '...' : stats.ownedBots}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Shared Bots
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {isLoading ? '...' : stats.sharedBots}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-white overflow-hidden shadow rounded-lg">
          <div className="p-5">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <svg className="h-6 w-6 text-yellow-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <div className="ml-5 w-0 flex-1">
                <dl>
                  <dt className="text-sm font-medium text-gray-500 truncate">
                    Recent Activity
                  </dt>
                  <dd className="text-lg font-medium text-gray-900">
                    {isLoading ? '...' : stats.recentActivity}
                  </dd>
                </dl>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-white shadow rounded-lg mb-8">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Quick Actions</h3>
        </div>
        <div className="p-6">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <button
              onClick={handleCreateBot}
              className="flex items-center p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex-shrink-0">
                <svg className="h-8 w-8 text-blue-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
              </div>
              <div className="ml-4">
                <h4 className="text-sm font-medium text-gray-900">Create New Bot</h4>
                <p className="text-sm text-gray-500">Build a new AI assistant</p>
              </div>
            </button>

            <button
              onClick={handleManageBots}
              className="flex items-center p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex-shrink-0">
                <svg className="h-8 w-8 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="ml-4">
                <h4 className="text-sm font-medium text-gray-900">Manage Bots</h4>
                <p className="text-sm text-gray-500">View and edit your bots</p>
              </div>
            </button>

            <button
              onClick={handleManageAPIKeys}
              className="flex items-center p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex-shrink-0">
                <svg className="h-8 w-8 text-purple-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                </svg>
              </div>
              <div className="ml-4">
                <h4 className="text-sm font-medium text-gray-900">API Keys</h4>
                <p className="text-sm text-gray-500">Manage provider keys</p>
              </div>
            </button>

            <button
              onClick={handleManageProfile}
              className="flex items-center p-4 border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
            >
              <div className="flex-shrink-0">
                <svg className="h-8 w-8 text-indigo-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z" />
                </svg>
              </div>
              <div className="ml-4">
                <h4 className="text-sm font-medium text-gray-900">Profile</h4>
                <p className="text-sm text-gray-500">Update your settings</p>
              </div>
            </button>
          </div>
        </div>
      </div>

      {/* Recent Bots */}
      <div className="bg-white shadow rounded-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <h3 className="text-lg font-medium text-gray-900">Recent Bots</h3>
            <button
              onClick={handleManageBots}
              className="text-sm text-blue-600 hover:text-blue-500"
            >
              View all
            </button>
          </div>
        </div>
        <div className="p-6">
          {isLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
              <p className="mt-2 text-gray-600">Loading bots...</p>
            </div>
          ) : bots.length === 0 ? (
            <div className="text-center py-8">
              <svg className="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
              <h3 className="mt-2 text-sm font-medium text-gray-900">No bots yet</h3>
              <p className="mt-1 text-sm text-gray-500">
                Get started by creating your first AI assistant.
              </p>
              <div className="mt-6">
                <button
                  onClick={handleCreateBot}
                  className="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
                >
                  Create Your First Bot
                </button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {bots.slice(0, 5).map((botWithRole) => (
                <div
                  key={botWithRole.bot.id}
                  className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <span className="text-2xl">{getProviderIcon(botWithRole.bot.llm_provider)}</span>
                    </div>
                    <div className="ml-4">
                      <h4 className="text-sm font-medium text-gray-900">{botWithRole.bot.name}</h4>
                      <p className="text-sm text-gray-500">{botWithRole.bot.description || 'No description'}</p>
                      <div className="flex items-center mt-1 space-x-2">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getRoleBadgeColor(botWithRole.role)}`}>
                          {botWithRole.role}
                        </span>
                        <span className="text-xs text-gray-400">
                          {new Date(botWithRole.bot.updated_at).toLocaleDateString()}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => navigate(`/bots/${botWithRole.bot.id}/chat`)}
                      className="text-sm text-green-600 hover:text-green-500 font-medium"
                    >
                      Chat
                    </button>
                    <button
                      onClick={() => navigate(`/bots/${botWithRole.bot.id}/documents`)}
                      className="text-sm text-purple-600 hover:text-purple-500 font-medium"
                    >
                      Documents
                    </button>
                    {botWithRole.bot.allow_collaboration && (
                      <button
                        onClick={() => navigate(`/bots/${botWithRole.bot.id}/collaboration`)}
                        className="text-sm text-blue-600 hover:text-blue-500"
                      >
                        Collaboration
                      </button>
                    )}
                    <button
                      onClick={() => navigate('/dashboard?view=bots&action=edit&id=' + botWithRole.bot.id)}
                      className="text-sm text-gray-600 hover:text-gray-900"
                    >
                      Edit
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </>
  );

  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <Navigation />

        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            {/* Back button for non-dashboard views */}
            {currentView !== 'dashboard' && (
              <div className="mb-6">
                <button
                  onClick={handleBackToDashboard}
                  className="inline-flex items-center px-3 py-2 border border-gray-300 shadow-sm text-sm leading-4 font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500"
                >
                  <svg className="mr-2 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
                  </svg>
                  Back to Dashboard
                </button>
              </div>
            )}

            {renderContent()}
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
};