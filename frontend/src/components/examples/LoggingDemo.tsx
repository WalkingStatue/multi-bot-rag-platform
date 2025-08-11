/**
 * Demo component showing how to use the logging service in React
 */
import React, { useState, useEffect } from 'react';
import { useLogger } from '../../hooks/useLogger';
import loggingService from '../../services/loggingService';
import ErrorBoundary from '../common/ErrorBoundary';

const LoggingDemo: React.FC = () => {
  const logger = useLogger({ 
    component: 'LoggingDemo', 
    logMount: true, 
    logUnmount: true 
  });
  
  const [count,