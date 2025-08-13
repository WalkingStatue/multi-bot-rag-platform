# Performance Monitoring and Optimization Guide

This guide covers the comprehensive performance monitoring and optimization system implemented in the multi-bot RAG platform frontend.

## Overview

The performance monitoring system provides:
- Real-time performance metrics collection
- Web Vitals tracking
- Component render performance monitoring
- API call performance tracking
- Memory usage monitoring
- Device performance detection
- Automatic optimizations for low-performance devices
- Performance warnings and alerts

## Architecture

### Core Components

1. **PerformanceMonitor** (`src/utils/performance.ts`)
   - Central performance metrics collection
   - Web Vitals integration
   - Memory monitoring
   - Performance alerts

2. **Performance Hooks** (`src/hooks/usePerformance.ts`)
   - React hooks for performance tracking
   - Component-specific monitoring
   - API performance tracking
   - User interaction tracking

3. **PerformanceOptimizer** (`src/components/common/PerformanceOptimizer.tsx`)
   - Automatic device performance detection
   - Performance optimizations
   - Visual performance metrics (development)

## Usage

### Basic Setup

The performance monitoring system is automatically initialized in the main App component:

```tsx
import { PerformanceOptimizer, PerformanceMetrics } from './components/common/PerformanceOptimizer';

function App() {
  return (
    <PerformanceOptimizer
      enableMemoryTracking={true}
      memoryTrackingInterval={30000}
      enablePerformanceWarnings={true}
    >
      {/* Your app content */}
      <PerformanceMetrics />
    </PerformanceOptimizer>
  );
}
```

### Component Performance Monitoring

Track component render performance:

```tsx
import { useRenderPerformance } from '../hooks/usePerformance';

const MyComponent: React.FC = () => {
  const { renderCount } = useRenderPerformance('MyComponent');
  
  return (
    <div>
      {/* Component content */}
    </div>
  );
};
```

### API Performance Tracking

Monitor API call performance:

```tsx
import { useApiPerformance } from '../hooks/usePerformance';

const useMyApiCall = () => {
  const { trackApiCall } = useApiPerformance();
  
  const fetchData = async () => {
    const startTime = performance.now();
    
    try {
      const response = await api.get('/data');
      const endTime = performance.now();
      
      trackApiCall('/data', 'GET', startTime, endTime, true, response.status);
      return response.data;
    } catch (error) {
      const endTime = performance.now();
      trackApiCall('/data', 'GET', startTime, endTime, false, error.response?.status);
      throw error;
    }
  };
  
  return { fetchData };
};
```

### Page Performance Monitoring

Track page-level performance:

```tsx
import { usePagePerformance } from '../hooks/usePerformance';

const HomePage: React.FC = () => {
  const { trackPageInteraction } = usePagePerformance('HomePage');
  
  const handleButtonClick = () => {
    trackPageInteraction('button_click');
    // Handle click
  };
  
  return (
    <div>
      <button onClick={handleButtonClick}>Click me</button>
    </div>
  );
};
```

### User Interaction Tracking

Monitor user interactions:

```tsx
import { useInteractionPerformance } from '../hooks/usePerformance';

const InteractiveComponent: React.FC = () => {
  const { trackClick, trackFormSubmit } = useInteractionPerformance();
  
  const handleClick = (elementId: string) => {
    trackClick(elementId);
    // Handle click
  };
  
  const handleSubmit = (formId: string) => {
    const startTime = performance.now();
    
    // Process form
    
    const endTime = performance.now();
    trackFormSubmit(formId, endTime - startTime);
  };
  
  return (
    <form onSubmit={() => handleSubmit('contact-form')}>
      <button onClick={() => handleClick('submit-btn')}>Submit</button>
    </form>
  );
};
```

### Higher-Order Component for Performance Monitoring

Wrap components for automatic performance tracking:

```tsx
import { withPerformanceMonitoring } from '../components/common/PerformanceOptimizer';

const MyComponent: React.FC = () => {
  return <div>Component content</div>;
};

export default withPerformanceMonitoring(MyComponent, 'MyComponent');
```

## Performance Metrics

### Collected Metrics

1. **Web Vitals**
   - First Contentful Paint (FCP)
   - Largest Contentful Paint (LCP)
   - First Input Delay (FID)
   - Cumulative Layout Shift (CLS)
   - Time to First Byte (TTFB)

2. **Component Performance**
   - Render time
   - Render count
   - Re-render frequency

3. **API Performance**
   - Request duration
   - Success/failure rates
   - Response times by endpoint

4. **Memory Usage**
   - JavaScript heap size
   - Memory usage over time
   - Memory warnings

5. **User Interactions**
   - Click response times
   - Form submission times
   - Time to interaction

6. **Page Performance**
   - Page load times
   - Bundle load times
   - Resource load times

### Metric Structure

```typescript
interface PerformanceMetric {
  name: string;
  value: number;
  unit: 'ms' | 'bytes' | 'count' | 'score';
  timestamp: number;
  tags?: Record<string, string>;
  context: string;
}
```

## Performance Optimizations

### Automatic Optimizations

The system automatically detects low-performance devices and applies optimizations:

1. **Device Detection**
   - CPU cores (≤2 cores = low performance)
   - Available memory (≤2GB = low performance)
   - Network connection (2G/slow-2G = low performance)

2. **Applied Optimizations**
   - Reduced animation durations
   - Disabled non-essential visual effects
   - Simplified UI components
   - Reduced polling frequencies

### Manual Optimizations

```tsx
// Check if device is low-performance
const isLowPerformance = performanceMonitor.isLowPerformanceDevice();

// Conditionally render expensive components
{!isLowPerformance && <ExpensiveComponent />}

// Adjust animation durations
const animationDuration = isLowPerformance ? 100 : 300;
```

## Performance Warnings

### Automatic Warnings

The system automatically warns about:

1. **Slow Renders** (>16ms)
2. **Long Tasks** (>50ms)
3. **High Memory Usage** (>80% of heap limit)
4. **Slow API Calls** (>3 seconds)
5. **Layout Shifts** (CLS >0.1)

### Custom Warnings

```typescript
import { performanceMonitor } from '../utils/performance';

// Record custom performance warning
performanceMonitor.recordMetric({
  name: 'custom_warning',
  value: duration,
  unit: 'ms',
  timestamp: Date.now(),
  tags: { component: 'MyComponent' },
  context: 'performance_warning',
});
```

## Development Tools

### Performance Metrics Display

In development mode, a performance metrics overlay is available:

- Shows real-time performance metrics
- Displays recent performance warnings
- Provides insights into component performance

### Browser DevTools Integration

The performance monitoring system integrates with browser DevTools:

1. **Performance Tab**: View detailed performance traces
2. **Memory Tab**: Monitor memory usage patterns
3. **Network Tab**: Analyze API call performance
4. **Console**: Performance warnings and metrics

## Configuration

### Environment Variables

```env
# Enable/disable performance monitoring
VITE_ENABLE_PERFORMANCE_MONITORING=true

# Performance monitoring endpoint (optional)
VITE_PERFORMANCE_ENDPOINT=https://api.example.com/performance

# Memory tracking interval (ms)
VITE_MEMORY_TRACKING_INTERVAL=30000

# Enable performance warnings
VITE_ENABLE_PERFORMANCE_WARNINGS=true
```

### Runtime Configuration

```typescript
import { performanceMonitor } from '../utils/performance';

// Configure performance monitoring
performanceMonitor.configure({
  enableWebVitals: true,
  enableMemoryTracking: true,
  memoryTrackingInterval: 30000,
  enableWarnings: true,
  warningThresholds: {
    renderTime: 16,
    apiCallTime: 3000,
    memoryUsage: 0.8,
  },
});
```

## Best Practices

### Component Performance

1. **Use React.memo** for expensive components
2. **Implement proper dependency arrays** in useEffect
3. **Avoid inline object/function creation** in render
4. **Use useCallback and useMemo** appropriately
5. **Monitor render counts** with useRenderPerformance

### API Performance

1. **Implement proper caching** with React Query
2. **Use request deduplication**
3. **Implement retry logic** with exponential backoff
4. **Monitor API response times**
5. **Use pagination** for large datasets

### Memory Management

1. **Clean up event listeners** in useEffect cleanup
2. **Avoid memory leaks** in closures
3. **Use WeakMap/WeakSet** for temporary references
4. **Monitor memory usage** regularly
5. **Implement proper component unmounting**

### Bundle Optimization

1. **Use code splitting** with React.lazy
2. **Implement tree shaking**
3. **Optimize bundle size** with webpack-bundle-analyzer
4. **Use dynamic imports** for large dependencies
5. **Monitor bundle load times**

## Troubleshooting

### Common Performance Issues

1. **Slow Renders**
   - Check for unnecessary re-renders
   - Optimize component dependencies
   - Use React DevTools Profiler

2. **High Memory Usage**
   - Check for memory leaks
   - Monitor component lifecycle
   - Use browser Memory tab

3. **Slow API Calls**
   - Check network conditions
   - Optimize API endpoints
   - Implement proper caching

4. **Layout Shifts**
   - Reserve space for dynamic content
   - Use proper image dimensions
   - Avoid DOM manipulation after load

### Debugging Tools

1. **Performance Metrics Overlay** (development)
2. **Browser DevTools Performance Tab**
3. **React DevTools Profiler**
4. **Network Tab for API analysis**
5. **Console warnings and metrics**

## Integration with Monitoring Services

### External Monitoring

The performance monitoring system can be integrated with external services:

```typescript
// Example integration with monitoring service
performanceMonitor.addMetricListener((metric) => {
  // Send to external monitoring service
  fetch('/api/metrics', {
    method: 'POST',
    body: JSON.stringify(metric),
  });
});
```

### Popular Monitoring Services

1. **Google Analytics 4** - Web Vitals tracking
2. **New Relic** - Application performance monitoring
3. **DataDog** - Real-time performance monitoring
4. **Sentry** - Error and performance monitoring
5. **LogRocket** - Session replay and performance

## Conclusion

The performance monitoring and optimization system provides comprehensive insights into application performance, enabling proactive optimization and improved user experience. Regular monitoring and optimization based on collected metrics will ensure optimal application performance across all devices and network conditions.