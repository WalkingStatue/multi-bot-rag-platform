/**
 * Demo component showing how to use the logging service in React
 */
import React, { useState, useEffect } from 'react';
import { ErrorBoundary } from '../common/ErrorBoundary';

// Simple mock logger for demo purposes
const createLogger = (componentName: string) => {
  return {
    info: (message: string, data?: any) => console.log(`[INFO][${componentName}]`, message, data),
    warn: (message: string, data?: any) => console.warn(`[WARN][${componentName}]`, message, data),
    error: (message: string, data?: any) => console.error(`[ERROR][${componentName}]`, message, data),
    debug: (message: string, data?: any) => console.debug(`[DEBUG][${componentName}]`, message, data)
  };
};

const LoggingDemo: React.FC = () => {
  const logger = createLogger('LoggingDemo');
  const [count, setCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Log when count changes
    logger.info('Count changed', { count });
    
    // Example of logging different levels
    if (count > 5) {
      logger.warn('Count is getting high', { count });
    }
    
    if (count > 10) {
      logger.error('Count is too high!', { count });
    }
  }, [count]);

  const handleIncrement = () => {
    setCount(prev => prev + 1);
    logger.debug('Increment button clicked', { newCount: count + 1 });
  };

  const handleDecrement = () => {
    setCount(prev => prev - 1);
    logger.debug('Decrement button clicked', { newCount: count - 1 });
  };

  const handleReset = () => {
    setCount(0);
    logger.info('Counter reset');
  };

  const triggerError = () => {
    try {
      // Intentionally cause an error
      throw new Error('This is a test error');
    } catch (err) {
      if (err instanceof Error) {
        setError(err.message);
        logger.error('Error occurred', { message: err.message });
      }
    }
  };

  const sendCustomLog = () => {
    logger.info('Custom log from button', {
      component: 'LoggingDemo',
      count,
      timestamp: new Date().toISOString(),
      custom: true
    });
  };

  return (
    <ErrorBoundary>
      <div className="p-6 bg-white dark:bg-neutral-900 rounded-lg shadow">
        <h2 className="text-xl font-semibold mb-4 text-neutral-900 dark:text-neutral-100">Logging Demo</h2>
        
        <div className="mb-6">
          <p className="text-neutral-700 dark:text-neutral-300 mb-2">
            Current count: <span className="font-semibold">{count}</span>
          </p>
          
          <div className="flex space-x-2">
            <button
              onClick={handleDecrement}
              className="px-3 py-1 bg-neutral-200 dark:bg-neutral-700 rounded hover:bg-neutral-300 dark:hover:bg-neutral-600"
            >
              Decrement
            </button>
            
            <button
              onClick={handleIncrement}
              className="px-3 py-1 bg-neutral-200 dark:bg-neutral-700 rounded hover:bg-neutral-300 dark:hover:bg-neutral-600"
            >
              Increment
            </button>
            
            <button
              onClick={handleReset}
              className="px-3 py-1 bg-neutral-200 dark:bg-neutral-700 rounded hover:bg-neutral-300 dark:hover:bg-neutral-600"
            >
              Reset
            </button>
          </div>
        </div>
        
        <div className="mb-6">
          <button
            onClick={triggerError}
            className="px-3 py-1 bg-red-500 text-white rounded hover:bg-red-600 mr-2"
          >
            Trigger Error
          </button>
          
          <button
            onClick={sendCustomLog}
            className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Send Custom Log
          </button>
        </div>
        
        {error && (
          <div className="p-3 bg-red-100 border border-red-300 text-red-700 rounded">
            <p className="font-semibold">Error:</p>
            <p>{error}</p>
          </div>
        )}
        
        <div className="mt-4 text-sm text-neutral-500 dark:text-neutral-400">
          <p>Check the console to see logs being sent.</p>
          <p>Different actions trigger different log levels.</p>
        </div>
      </div>
    </ErrorBoundary>
  );
};

export default LoggingDemo;