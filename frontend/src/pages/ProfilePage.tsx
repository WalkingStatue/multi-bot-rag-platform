/**
 * Profile page component
 */
import React from 'react';
import { UserProfile } from '../components/auth/UserProfile';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';
import { Navigation } from '../components/common/Navigation';

export const ProfilePage: React.FC = () => {
  return (
    <ProtectedRoute>
      <div className="min-h-screen bg-gray-50">
        <Navigation />
        <main className="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
          <div className="px-4 py-6 sm:px-0">
            <UserProfile />
          </div>
        </main>
      </div>
    </ProtectedRoute>
  );
};