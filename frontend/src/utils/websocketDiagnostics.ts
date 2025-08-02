/**
 * WebSocket diagnostics utilities
 */

export interface DiagnosticResult {
  test: string;
  success: boolean;
  message: string;
  details?: any;
}

export class WebSocketDiagnostics {
  /**
   * Run comprehensive WebSocket diagnostics
   */
  static async runDiagnostics(botId: string, token: string): Promise<DiagnosticResult[]> {
    const results: DiagnosticResult[] = [];
    
    // Test 1: Check if WebSocket is supported
    results.push(this.testWebSocketSupport());
    
    // Test 2: Check backend API availability
    results.push(await this.testBackendAvailability());
    
    // Test 3: Test WebSocket connection
    results.push(await this.testWebSocketConnection(botId, token));
    
    // Test 4: Check network connectivity
    results.push(await this.testNetworkConnectivity());
    
    return results;
  }

  private static testWebSocketSupport(): DiagnosticResult {
    const supported = 'WebSocket' in window;
    return {
      test: 'WebSocket Support',
      success: supported,
      message: supported ? 'WebSocket is supported' : 'WebSocket is not supported in this browser'
    };
  }

  private static async testBackendAvailability(): Promise<DiagnosticResult> {
    try {
      const apiUrl = (import.meta as any).env?.VITE_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/health`, {
        method: 'GET',
        signal: AbortSignal.timeout(5000)
      });

      return {
        test: 'Backend Availability',
        success: response.ok,
        message: response.ok ? 'Backend is available' : `Backend returned ${response.status}`,
        details: { status: response.status, statusText: response.statusText }
      };
    } catch (error: any) {
      return {
        test: 'Backend Availability',
        success: false,
        message: `Backend is not available: ${error.message}`,
        details: error
      };
    }
  }

  private static async testWebSocketConnection(botId: string, token: string): Promise<DiagnosticResult> {
    return new Promise((resolve) => {
      const wsUrl = (import.meta as any).env?.VITE_WS_URL || 'ws://localhost:8000';
      const chatUrl = `${wsUrl}/api/ws/chat/${botId}?token=${encodeURIComponent(token)}`;
      
      let socket: WebSocket;
      let resolved = false;
      
      const timeout = setTimeout(() => {
        if (!resolved) {
          resolved = true;
          if (socket) {
            socket.close();
          }
          resolve({
            test: 'WebSocket Connection',
            success: false,
            message: 'WebSocket connection timed out',
            details: { url: chatUrl.replace(token, '[TOKEN]') }
          });
        }
      }, 10000);

      try {
        socket = new WebSocket(chatUrl);
        
        socket.onopen = () => {
          if (!resolved) {
            resolved = true;
            clearTimeout(timeout);
            socket.close();
            resolve({
              test: 'WebSocket Connection',
              success: true,
              message: 'WebSocket connection successful',
              details: { url: chatUrl.replace(token, '[TOKEN]') }
            });
          }
        };

        socket.onerror = (error) => {
          if (!resolved) {
            resolved = true;
            clearTimeout(timeout);
            resolve({
              test: 'WebSocket Connection',
              success: false,
              message: 'WebSocket connection failed',
              details: { error, url: chatUrl.replace(token, '[TOKEN]') }
            });
          }
        };

        socket.onclose = (event) => {
          if (!resolved) {
            resolved = true;
            clearTimeout(timeout);
            resolve({
              test: 'WebSocket Connection',
              success: false,
              message: `WebSocket closed: ${event.code} - ${event.reason || 'No reason'}`,
              details: { code: event.code, reason: event.reason, url: chatUrl.replace(token, '[TOKEN]') }
            });
          }
        };

      } catch (error: any) {
        if (!resolved) {
          resolved = true;
          clearTimeout(timeout);
          resolve({
            test: 'WebSocket Connection',
            success: false,
            message: `Failed to create WebSocket: ${error.message}`,
            details: error
          });
        }
      }
    });
  }

  private static async testNetworkConnectivity(): Promise<DiagnosticResult> {
    const isOnline = navigator.onLine;
    
    if (!isOnline) {
      return {
        test: 'Network Connectivity',
        success: false,
        message: 'Browser reports offline status'
      };
    }

    try {
      // Test with a reliable external service
      const response = await fetch('https://httpbin.org/status/200', {
        method: 'HEAD',
        signal: AbortSignal.timeout(5000)
      });

      return {
        test: 'Network Connectivity',
        success: response.ok,
        message: response.ok ? 'Network connectivity is good' : 'Network connectivity issues detected'
      };
    } catch (error: any) {
      return {
        test: 'Network Connectivity',
        success: false,
        message: `Network connectivity test failed: ${error.message}`,
        details: error
      };
    }
  }

  /**
   * Format diagnostic results for display
   */
  static formatResults(results: DiagnosticResult[]): string {
    let output = 'WebSocket Diagnostics Results:\n\n';
    
    results.forEach((result, index) => {
      const status = result.success ? '✅' : '❌';
      output += `${index + 1}. ${status} ${result.test}: ${result.message}\n`;
      
      if (result.details) {
        output += `   Details: ${JSON.stringify(result.details, null, 2)}\n`;
      }
      output += '\n';
    });
    
    return output;
  }
}

// Helper function to run diagnostics and log results
export async function runWebSocketDiagnostics(botId: string, token: string): Promise<void> {
  console.log('Running WebSocket diagnostics...');
  
  const results = await WebSocketDiagnostics.runDiagnostics(botId, token);
  const formattedResults = WebSocketDiagnostics.formatResults(results);
  
  console.log(formattedResults);
  
  // Also log individual results for easier debugging
  results.forEach(result => {
    if (result.success) {
      console.log(`✅ ${result.test}: ${result.message}`);
    } else {
      console.error(`❌ ${result.test}: ${result.message}`, result.details);
    }
  });
}