# Deployment Guide

This guide covers the deployment process for the multi-bot RAG platform frontend, including Docker containerization, environment configuration, and production best practices.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [Build Process](#build-process)
4. [Docker Deployment](#docker-deployment)
5. [Production Deployment](#production-deployment)
6. [CI/CD Pipeline](#cicd-pipeline)
7. [Monitoring and Logging](#monitoring-and-logging)
8. [Security Considerations](#security-considerations)
9. [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Node.js 18+ (for development)
- Docker 20+ (for containerization)
- Docker Compose 2+ (for multi-container setup)
- Nginx (for reverse proxy in production)

### Development Dependencies

```bash
npm install
```

## Environment Configuration

### Environment Variables

Copy the example environment file and configure for your environment:

```bash
cp .env.example .env.local
```

### Key Configuration Variables

#### API Configuration
```env
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com/ws
VITE_API_TIMEOUT=30000
```

#### Feature Flags
```env
VITE_ENABLE_OFFLINE_MODE=true
VITE_ENABLE_PERFORMANCE_MONITORING=true
VITE_ENABLE_ERROR_REPORTING=true
VITE_ENABLE_ANALYTICS=true
```

#### Security
```env
VITE_CSP_NONCE=your-csp-nonce
VITE_ENABLE_HTTPS=true
```

#### External Services
```env
VITE_SENTRY_DSN=https://your-sentry-dsn
VITE_GOOGLE_ANALYTICS_ID=GA-XXXXXXXXX
```

### Environment-Specific Configurations

#### Development (.env.development)
```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENABLE_DEBUG_MODE=true
VITE_SHOW_PERFORMANCE_METRICS=true
VITE_LOG_LEVEL=debug
```

#### Staging (.env.staging)
```env
VITE_API_URL=https://staging-api.yourdomain.com
VITE_WS_URL=wss://staging-api.yourdomain.com/ws
VITE_ENABLE_ERROR_REPORTING=true
VITE_LOG_LEVEL=info
```

#### Production (.env.production)
```env
VITE_API_URL=https://api.yourdomain.com
VITE_WS_URL=wss://api.yourdomain.com/ws
VITE_ENABLE_ERROR_REPORTING=true
VITE_ENABLE_ANALYTICS=true
VITE_LOG_LEVEL=warn
```

## Build Process

### Development Build

```bash
# Start development server
npm run dev

# Type checking
npm run type-check

# Linting
npm run lint
```

### Production Build

```bash
# Clean previous builds
npm run clean

# Type check and lint
npm run prepare

# Build for production
npm run build:production

# Preview production build
npm run preview:dist
```

### Build Analysis

```bash
# Analyze bundle size
npm run build:analyze
```

This generates a `dist/stats.html` file with detailed bundle analysis.

### Build Optimization

The build process includes:

- **Code Splitting**: Automatic vendor and feature-based chunks
- **Tree Shaking**: Removes unused code
- **Minification**: JavaScript and CSS minification
- **Asset Optimization**: Image and font optimization
- **Gzip Compression**: Static asset compression
- **Source Maps**: Hidden source maps for production debugging

## Docker Deployment

### Building Docker Image

#### Development Image
```bash
npm run docker:build
```

#### Production Image
```bash
npm run docker:build:prod
```

#### Custom Build Arguments
```bash
docker build \
  --build-arg VITE_API_URL=https://api.yourdomain.com \
  --build-arg VITE_WS_URL=wss://api.yourdomain.com/ws \
  --build-arg NODE_ENV=production \
  -t multi-bot-rag-frontend:latest .
```

### Running Docker Container

#### Basic Run
```bash
npm run docker:run
```

#### Production Run with Environment Variables
```bash
docker run -d \
  --name rag-frontend \
  -p 3000:3000 \
  -e VITE_API_URL=https://api.yourdomain.com \
  -e VITE_WS_URL=wss://api.yourdomain.com/ws \
  -e VITE_ENABLE_ANALYTICS=true \
  multi-bot-rag-frontend:latest
```

#### Docker Compose
```yaml
version: '3.8'
services:
  frontend:
    build:
      context: .
      args:
        - NODE_ENV=production
        - VITE_API_URL=https://api.yourdomain.com
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=https://api.yourdomain.com
      - VITE_WS_URL=wss://api.yourdomain.com/ws
      - VITE_ENABLE_ANALYTICS=true
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Docker Security

The Docker image includes:

- **Non-root user**: Runs as nginx user
- **Security headers**: Comprehensive security headers
- **Minimal base image**: Alpine Linux for smaller attack surface
- **Health checks**: Built-in health monitoring
- **Read-only filesystem**: Where possible

## Production Deployment

### Nginx Reverse Proxy

#### Basic Nginx Configuration
```nginx
server {
    listen 80;
    server_name yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;

    location / {
        proxy_pass http://localhost:3000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Load Balancing

#### Multiple Frontend Instances
```nginx
upstream frontend {
    server localhost:3000;
    server localhost:3001;
    server localhost:3002;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    location / {
        proxy_pass http://frontend;
        # ... other proxy settings
    }
}
```

### CDN Integration

#### CloudFlare Configuration
1. Set up CloudFlare for your domain
2. Configure caching rules for static assets
3. Enable Brotli compression
4. Set up security rules

#### AWS CloudFront
```json
{
  "Origins": [{
    "DomainName": "yourdomain.com",
    "Id": "frontend-origin",
    "CustomOriginConfig": {
      "HTTPPort": 443,
      "OriginProtocolPolicy": "https-only"
    }
  }],
  "DefaultCacheBehavior": {
    "TargetOriginId": "frontend-origin",
    "ViewerProtocolPolicy": "redirect-to-https",
    "CachePolicyId": "managed-caching-optimized"
  }
}
```

## CI/CD Pipeline

### GitHub Actions

#### Build and Test Workflow
```yaml
name: Build and Test

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
          cache: 'npm'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run CI checks
        run: npm run ci:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
```

#### Deployment Workflow
```yaml
name: Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: |
          docker build \
            --build-arg VITE_API_URL=${{ secrets.API_URL }} \
            --build-arg VITE_WS_URL=${{ secrets.WS_URL }} \
            -t ${{ secrets.REGISTRY }}/frontend:${{ github.sha }} .
      
      - name: Push to registry
        run: |
          echo ${{ secrets.REGISTRY_PASSWORD }} | docker login -u ${{ secrets.REGISTRY_USERNAME }} --password-stdin ${{ secrets.REGISTRY }}
          docker push ${{ secrets.REGISTRY }}/frontend:${{ github.sha }}
      
      - name: Deploy to production
        run: |
          # Your deployment script here
```

### GitLab CI/CD

```yaml
stages:
  - test
  - build
  - deploy

variables:
  DOCKER_DRIVER: overlay2

test:
  stage: test
  image: node:18-alpine
  script:
    - npm ci
    - npm run ci:coverage
  coverage: '/All files[^|]*\|[^|]*\s+([\d\.]+)/'

build:
  stage: build
  image: docker:latest
  services:
    - docker:dind
  script:
    - docker build -t $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA .
    - docker push $CI_REGISTRY_IMAGE:$CI_COMMIT_SHA
  only:
    - main

deploy:
  stage: deploy
  script:
    - # Your deployment script
  only:
    - main
```

## Monitoring and Logging

### Application Monitoring

#### Sentry Integration
```typescript
import * as Sentry from '@sentry/react';

Sentry.init({
  dsn: import.meta.env.VITE_SENTRY_DSN,
  environment: import.meta.env.MODE,
  tracesSampleRate: 1.0,
});
```

#### Performance Monitoring
The application includes built-in performance monitoring:
- Web Vitals tracking
- Component render performance
- API call monitoring
- Memory usage tracking

### Log Aggregation

#### ELK Stack Integration
```typescript
// Configure remote logging
const logger = new Logger({
  level: import.meta.env.VITE_LOG_LEVEL,
  remote: {
    enabled: import.meta.env.VITE_ENABLE_REMOTE_LOGGING === 'true',
    endpoint: import.meta.env.VITE_LOG_ENDPOINT,
  },
});
```

### Health Checks

#### Application Health
```bash
curl -f http://localhost:3000/health
```

#### Docker Health Check
```dockerfile
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:3000/health || exit 1
```

## Security Considerations

### Content Security Policy

The application includes comprehensive CSP headers:

```nginx
add_header Content-Security-Policy "
  default-src 'self';
  script-src 'self' 'unsafe-inline' https://www.google-analytics.com;
  style-src 'self' 'unsafe-inline';
  img-src 'self' data: https:;
  connect-src 'self' wss: https:;
  font-src 'self';
  frame-ancestors 'none';
" always;
```

### Security Headers

```nginx
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

### Environment Security

- Never commit `.env` files to version control
- Use secrets management for sensitive data
- Rotate API keys regularly
- Use HTTPS in production
- Implement proper CORS policies

## Troubleshooting

### Common Issues

#### Build Failures

**TypeScript Errors**
```bash
# Check TypeScript configuration
npm run type-check

# Fix common issues
npm run lint:fix
```

**Memory Issues**
```bash
# Increase Node.js memory limit
NODE_OPTIONS="--max-old-space-size=4096" npm run build
```

#### Runtime Issues

**API Connection Problems**
1. Check environment variables
2. Verify API endpoint accessibility
3. Check CORS configuration
4. Verify SSL certificates

**Performance Issues**
1. Enable performance monitoring
2. Check bundle size analysis
3. Verify CDN configuration
4. Monitor memory usage

#### Docker Issues

**Build Failures**
```bash
# Clear Docker cache
docker system prune -a

# Rebuild without cache
docker build --no-cache -t frontend .
```

**Container Startup Issues**
```bash
# Check container logs
docker logs container-name

# Debug container
docker run -it --entrypoint /bin/sh frontend
```

### Debugging Tools

#### Development
- React DevTools
- Redux DevTools (if using Redux)
- Performance monitoring overlay
- Network tab analysis

#### Production
- Sentry error tracking
- Performance monitoring
- Log aggregation
- Health check endpoints

### Support

For additional support:
1. Check application logs
2. Review performance metrics
3. Consult error tracking (Sentry)
4. Check health endpoints
5. Review deployment logs

## Best Practices

### Performance
- Use code splitting
- Implement lazy loading
- Optimize images and assets
- Enable compression
- Use CDN for static assets

### Security
- Keep dependencies updated
- Use security headers
- Implement CSP
- Use HTTPS everywhere
- Regular security audits

### Monitoring
- Set up comprehensive logging
- Monitor performance metrics
- Implement health checks
- Use error tracking
- Monitor user experience

### Deployment
- Use immutable deployments
- Implement blue-green deployments
- Use infrastructure as code
- Automate testing
- Monitor deployment metrics