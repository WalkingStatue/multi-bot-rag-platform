/**
 * Reset password page component
 */
import React from 'react';
import { ResetPasswordForm } from '../components/auth/ResetPasswordForm';
import { ProtectedRoute } from '../components/auth/ProtectedRoute';

export const ResetPasswordPage: React.FC = () => {
  return (
    <ProtectedRoute requireAuth={false}>
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <ResetPasswordForm />
      </div>
    </ProtectedRoute>
  );
};