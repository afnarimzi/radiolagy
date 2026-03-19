import React from 'react';
import { AlertTriangle, RefreshCw, Home, Bug } from 'lucide-react';

class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { 
      hasError: false, 
      error: null, 
      errorInfo: null,
      errorId: null
    };
  }

  static getDerivedStateFromError(error) {
    return { 
      hasError: true,
      errorId: Date.now().toString(36) + Math.random().toString(36).substr(2)
    };
  }

  componentDidCatch(error, errorInfo) {
    this.setState({
      error: error,
      errorInfo: errorInfo
    });

    // Log error to monitoring service
    this.logErrorToService(error, errorInfo);
  }

  logErrorToService = (error, errorInfo) => {
    try {
      fetch('/log-error', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          error: error.toString(),
          errorInfo: errorInfo.componentStack,
          errorId: this.state.errorId,
          timestamp: new Date().toISOString(),
          userAgent: navigator.userAgent,
          url: window.location.href
        }),
      });
    } catch (logError) {
      console.error('Failed to log error:', logError);
    }
  };

  handleReload = () => {
    window.location.reload();
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  handleReportBug = () => {
    const subject = encodeURIComponent(`Bug Report - Error ID: ${this.state.errorId}`);
    const body = encodeURIComponent(`
Error ID: ${this.state.errorId}
Error: ${this.state.error?.toString() || 'Unknown error'}
Timestamp: ${new Date().toISOString()}
URL: ${window.location.href}
User Agent: ${navigator.userAgent}

Component Stack:
${this.state.errorInfo?.componentStack || 'Not available'}

Please describe what you were doing when this error occurred:
[Your description here]
    `);
    
    window.open(`mailto:support@example.com?subject=${subject}&body=${body}`);
  };

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
          <div className="max-w-md w-full">
            <div className="card text-center">
              <div className="w-16 h-16 bg-danger-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <AlertTriangle className="w-8 h-8 text-danger-600" />
              </div>
              
              <h1 className="text-2xl font-bold text-gray-900 mb-4">
                Something went wrong
              </h1>
              
              <p className="text-gray-600 mb-6">
                We're sorry, but something unexpected happened. The error has been logged 
                and our team will investigate.
              </p>

              <div className="bg-gray-50 rounded-lg p-4 mb-6 text-left">
                <div className="text-sm text-gray-500 mb-2">Error ID:</div>
                <div className="font-mono text-sm text-gray-900 bg-white px-2 py-1 rounded border">
                  {this.state.errorId}
                </div>
              </div>

              <div className="space-y-3">
                <button
                  onClick={this.handleReload}
                  className="w-full btn-primary flex items-center justify-center space-x-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Reload Page</span>
                </button>

                <button
                  onClick={this.handleGoHome}
                  className="w-full btn-secondary flex items-center justify-center space-x-2"
                >
                  <Home className="w-4 h-4" />
                  <span>Go to Dashboard</span>
                </button>

                <button
                  onClick={this.handleReportBug}
                  className="w-full text-gray-600 hover:text-gray-800 flex items-center justify-center space-x-2 py-2"
                >
                  <Bug className="w-4 h-4" />
                  <span>Report Bug</span>
                </button>
              </div>

              {process.env.NODE_ENV === 'development' && this.state.error && (
                <details className="mt-6 text-left">
                  <summary className="cursor-pointer text-sm text-gray-500 hover:text-gray-700">
                    Show Error Details (Development)
                  </summary>
                  <div className="mt-3 p-3 bg-red-50 rounded border text-xs">
                    <div className="font-semibold text-red-800 mb-2">Error:</div>
                    <pre className="text-red-700 whitespace-pre-wrap mb-3">
                      {this.state.error.toString()}
                    </pre>
                    
                    {this.state.errorInfo && (
                      <>
                        <div className="font-semibold text-red-800 mb-2">Component Stack:</div>
                        <pre className="text-red-700 whitespace-pre-wrap text-xs">
                          {this.state.errorInfo.componentStack}
                        </pre>
                      </>
                    )}
                  </div>
                </details>
              )}
            </div>

            <div className="text-center mt-6">
              <p className="text-sm text-gray-500">
                If this problem persists, please contact our support team with the error ID above.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;