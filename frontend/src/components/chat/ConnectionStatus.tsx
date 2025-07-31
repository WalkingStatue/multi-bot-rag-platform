/**
 * Connection status indicator component
 */
import React from 'react';
import { ConnectionStatus as ConnectionStatusType } from '../../types/chat';

interface ConnectionStatusProps {
  status: ConnectionStatusType;
  className?: string;
}

export const ConnectionStatus: React.FC<ConnectionStatusProps> = ({ 
  status, 
  className = '' 
}) => {
  const getStatusColor = () => {
    switch (status.status) {
      case 'connected':
        return 'text-green-600 bg-green-100';
      case 'disconnected':
        return 'text-gray-600 bg-gray-100';
      case 'error':
      case 'failed':
        return 'text-red-600 bg-red-100';
      default:
        return 'text-gray-600 bg-gray-100';
    }
  };

  const getStatusIcon = () => {
    switch (status.status) {
      case 'connected':
        return (
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <circle cx="10" cy="10" r="10" />
          </svg>
        );
      case 'disconnected':
        return (
          <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
            <circle cx="10" cy="10" r="8" stroke="currentColor" strokeWidth="2" fill="none" />
          </svg>
        );
      case 'error':
      case 'failed':
        return (
          <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        );
      default:
        return (
          <svg className="w-3 h-3 animate-spin" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
        );
    }
  };

  const getStatusText = () => {
    switch (status.status) {
      case 'connected':
        return 'Connected';
      case 'disconnected':
        return 'Disconnected';
      case 'error':
        return 'Connection Error';
      case 'failed':
        return 'Connection Failed';
      default:
        return 'Connecting...';
    }
  };

  return (
    <div className={`flex items-center space-x-2 ${className}`}>
      <div className={`flex items-center space-x-1 px-2 py-1 rounded-full text-xs font-medium ${getStatusColor()}`}>
        {getStatusIcon()}
        <span>{getStatusText()}</span>
      </div>
      
      {(status.error || status.message) && (
        <div className="text-xs text-gray-500 truncate" title={status.error || status.message}>
          {status.error || status.message}
        </div>
      )}
    </div>
  );
};