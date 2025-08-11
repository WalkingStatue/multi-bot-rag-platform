/**
 * Debug component to check authentication state
 */
import React from 'react';

export const AuthDebug: React.FC = () => {
  const accessToken = localStorage.getItem('access_token');
  const refreshToken = localStorage.getItem('refresh_token');

  return (
    <div className="fixed bottom-4 right-4 bg-gray-800 text-white p-4 rounded-lg text-xs max-w-md">
      <h3 className="font-bold mb-2">Auth Debug</h3>
      <div className="space-y-1">
        <div>
          <strong>Access Token:</strong> {accessToken ? 'Present' : 'Missing'}
        </div>
        <div>
          <strong>Refresh Token:</strong> {refreshToken ? 'Present' : 'Missing'}
        </div>
        {accessToken && (
          <div>
            <strong>Token Preview:</strong> {accessToken.substring(0, 20)}...
          </div>
        )}
      </div>
    </div>
  );
};