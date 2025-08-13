/**
 * Login Page Example
 * 
 * This is an example of how to use the AuthLayout component for a login page.
 */
import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { AuthLayout } from '../layouts';
import { Button, Input, Alert } from '../components/common';

interface LoginFormData {
  username: string;
  password: string;
}

export const LoginPageExample: React.FC = () => {
  const [formData, setFormData] = useState<LoginFormData>({
    username: '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    
    // Clear error when user starts typing
    if (error) {
      setError(null);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    // Simple validation
    if (!formData.username || !formData.password) {
      setError('Please enter both username and password');
      return;
    }
    
    setIsLoading(true);
    
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // Handle successful login
      console.log('Login successful', formData);
      
      // Redirect would happen here
    } catch (err) {
      setError('Invalid username or password');
    } finally {
      setIsLoading(false);
    }
  };

  // Footer content with registration link
  const footerContent = (
    <p className="text-sm text-neutral-600 dark:text-neutral-400">
      Don't have an account?{' '}
      <Link
        to="/register"
        className="font-medium text-primary-600 hover:text-primary-500"
      >
        Sign up
      </Link>
    </p>
  );

  return (
    <AuthLayout
      title="Sign in to your account"
      subtitle={
        <span>
          Welcome back! Please enter your credentials to access your account.
        </span>
      }
      footer={footerContent}
    >
      {error && (
        <Alert
          type="error"
          message={error}
          onClose={() => setError(null)}
          className="mb-6"
        />
      )}
      
      <form onSubmit={handleSubmit} className="space-y-6">
        <Input
          label="Username"
          name="username"
          type="text"
          autoComplete="username"
          required
          value={formData.username}
          onChange={handleInputChange}
          placeholder="Enter your username"
        />
        
        <Input
          label="Password"
          name="password"
          type="password"
          autoComplete="current-password"
          required
          value={formData.password}
          onChange={handleInputChange}
          placeholder="Enter your password"
        />
        
        <div className="flex items-center justify-between">
          <div className="text-sm">
            <Link
              to="/forgot-password"
              className="font-medium text-primary-600 hover:text-primary-500"
            >
              Forgot your password?
            </Link>
          </div>
        </div>
        
        <Button
          type="submit"
          className="w-full"
          isLoading={isLoading}
          disabled={isLoading}
        >
          {isLoading ? 'Signing in...' : 'Sign in'}
        </Button>
      </form>
    </AuthLayout>
  );
};

export default LoginPageExample;