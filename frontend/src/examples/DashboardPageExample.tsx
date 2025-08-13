/**
 * Dashboard Page Example
 * 
 * This is an example of how to use the DashboardLayout component for a dashboard page.
 */
import React, { useState } from 'react';
import { DashboardLayout } from '../layouts';
import { Card, Grid, Panel, Container, Button } from '../components/common';

export const DashboardPageExample: React.FC = () => {
  const [isLoading, setIsLoading] = useState(false);
  
  // Mock data for the dashboard
  const stats = {
    totalBots: 12,
    activeBots: 8,
    totalDocuments: 156,
    totalChats: 342
  };
  
  const recentBots = [
    { id: 1, name: 'Customer Support Bot', description: 'Handles customer inquiries', provider: 'openai' },
    { id: 2, name: 'Sales Assistant', description: 'Helps with product recommendations', provider: 'anthropic' },
    { id: 3, name: 'Documentation Helper', description: 'Answers questions about docs', provider: 'gemini' },
  ];
  
  const handleRefresh = () => {
    setIsLoading(true);
    // Simulate API call
    setTimeout(() => {
      setIsLoading(false);
    }, 1000);
  };
  
  // Dashboard actions
  const dashboardActions = (
    <Button
      variant="outline"
      size="sm"
      onClick={handleRefresh}
      isLoading={isLoading}
    >
      Refresh
    </Button>
  );
  
  // Provider icon mapping
  const getProviderIcon = (provider: string) => {
    const icons = {
      openai: '🤖',
      anthropic: '🧠',
      gemini: '💎',
      openrouter: '🔀',
    };
    return icons[provider as keyof typeof icons] || '🤖';
  };

  return (
    <DashboardLayout
      title="Dashboard"
      subtitle="Welcome to your Multi-Bot RAG Platform dashboard!"
      actions={dashboardActions}
    >
      <Container>
        {/* Stats Cards */}
        <Grid cols={1} mdCols={2} lgCols={4} gap="medium" className="mb-8">
          <Card
            title="Total Bots"
            variant="default"
            padding="medium"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-full bg-primary-100 dark:bg-primary-900/30">
                <svg className="h-6 w-6 text-primary-600 dark:text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
              <div className="ml-5">
                <div className="text-3xl font-semibold text-neutral-900 dark:text-neutral-100">
                  {stats.totalBots}
                </div>
              </div>
            </div>
          </Card>
          
          <Card
            title="Active Bots"
            variant="default"
            padding="medium"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-full bg-success-100 dark:bg-success-900/30">
                <svg className="h-6 w-6 text-success-600 dark:text-success-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <div className="ml-5">
                <div className="text-3xl font-semibold text-neutral-900 dark:text-neutral-100">
                  {stats.activeBots}
                </div>
              </div>
            </div>
          </Card>
          
          <Card
            title="Total Documents"
            variant="default"
            padding="medium"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-full bg-accent-100 dark:bg-accent-900/30">
                <svg className="h-6 w-6 text-accent-600 dark:text-accent-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <div className="ml-5">
                <div className="text-3xl font-semibold text-neutral-900 dark:text-neutral-100">
                  {stats.totalDocuments}
                </div>
              </div>
            </div>
          </Card>
          
          <Card
            title="Total Chats"
            variant="default"
            padding="medium"
          >
            <div className="flex items-center">
              <div className="flex-shrink-0 p-3 rounded-full bg-warning-100 dark:bg-warning-900/30">
                <svg className="h-6 w-6 text-warning-600 dark:text-warning-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
                </svg>
              </div>
              <div className="ml-5">
                <div className="text-3xl font-semibold text-neutral-900 dark:text-neutral-100">
                  {stats.totalChats}
                </div>
              </div>
            </div>
          </Card>
        </Grid>
        
        {/* Quick Actions */}
        <Panel
          title="Quick Actions"
          variant="default"
          padding="medium"
          className="mb-8"
        >
          <Grid cols={1} mdCols={2} lgCols={4} gap="medium">
            <Card
              variant="outline"
              padding="medium"
              hover={true}
              onClick={() => console.log('Create bot clicked')}
            >
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-8 w-8 text-primary-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                </div>
                <div className="ml-4">
                  <h4 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">Create New Bot</h4>
                  <p className="text-sm text-neutral-500 dark:text-neutral-400">Build a new AI assistant</p>
                </div>
              </div>
            </Card>
            
            <Card
              variant="outline"
              padding="medium"
              hover={true}
              onClick={() => console.log('Upload documents clicked')}
            >
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-8 w-8 text-accent-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                  </svg>
                </div>
                <div className="ml-4">
                  <h4 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">Upload Documents</h4>
                  <p className="text-sm text-neutral-500 dark:text-neutral-400">Add knowledge to your bots</p>
                </div>
              </div>
            </Card>
            
            <Card
              variant="outline"
              padding="medium"
              hover={true}
              onClick={() => console.log('Manage API keys clicked')}
            >
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-8 w-8 text-success-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <h4 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">Manage API Keys</h4>
                  <p className="text-sm text-neutral-500 dark:text-neutral-400">Configure provider keys</p>
                </div>
              </div>
            </Card>
            
            <Card
              variant="outline"
              padding="medium"
              hover={true}
              onClick={() => console.log('View analytics clicked')}
            >
              <div className="flex items-center">
                <div className="flex-shrink-0">
                  <svg className="h-8 w-8 text-warning-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                  </svg>
                </div>
                <div className="ml-4">
                  <h4 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">View Analytics</h4>
                  <p className="text-sm text-neutral-500 dark:text-neutral-400">Monitor bot performance</p>
                </div>
              </div>
            </Card>
          </Grid>
        </Panel>
        
        {/* Recent Bots */}
        <Panel
          title="Recent Bots"
          variant="default"
          padding="medium"
          headerActions={
            <Button
              variant="outline"
              size="sm"
              onClick={() => console.log('View all bots clicked')}
            >
              View all
            </Button>
          }
        >
          <div className="space-y-4">
            {recentBots.map((bot) => (
              <Card
                key={bot.id}
                variant="outline"
                padding="medium"
                hover={true}
                onClick={() => console.log(`Bot ${bot.id} clicked`)}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center">
                    <div className="flex-shrink-0">
                      <span className="text-2xl">{getProviderIcon(bot.provider)}</span>
                    </div>
                    <div className="ml-4">
                      <h4 className="text-sm font-medium text-neutral-900 dark:text-neutral-100">{bot.name}</h4>
                      <p className="text-sm text-neutral-500 dark:text-neutral-400">{bot.description}</p>
                    </div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-success-300 text-success-700 hover:bg-success-50 dark:bg-neutral-900 dark:border-success-800 dark:text-success-300"
                      onClick={(e) => {
                        e.stopPropagation();
                        console.log(`Chat with bot ${bot.id}`);
                      }}
                    >
                      Chat
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-accent-300 text-accent-700 hover:bg-accent-50 dark:bg-neutral-900 dark:border-accent-800 dark:text-accent-300"
                      onClick={(e) => {
                        e.stopPropagation();
                        console.log(`View documents for bot ${bot.id}`);
                      }}
                    >
                      Documents
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      className="border-neutral-300 text-neutral-700 hover:bg-neutral-50 dark:bg-neutral-900 dark:border-neutral-700 dark:text-neutral-200"
                      onClick={(e) => {
                        e.stopPropagation();
                        console.log(`Edit bot ${bot.id}`);
                      }}
                    >
                      Edit
                    </Button>
                  </div>
                </div>
              </Card>
            ))}
          </div>
        </Panel>
      </Container>
    </DashboardLayout>
  );
};

export default DashboardPageExample;