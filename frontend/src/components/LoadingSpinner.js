import React from 'react';
import { Activity, Brain, Clock } from 'lucide-react';

const LoadingSpinner = ({ 
  size = 'medium', 
  message = 'Loading...', 
  type = 'default',
  showIcon = true 
}) => {
  const getSizeClasses = () => {
    switch (size) {
      case 'small':
        return 'w-4 h-4';
      case 'large':
        return 'w-12 h-12';
      case 'xlarge':
        return 'w-16 h-16';
      default:
        return 'w-8 h-8';
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'analysis':
        return <Brain className={`${getSizeClasses()} text-medical-600 animate-pulse`} />;
      case 'processing':
        return <Activity className={`${getSizeClasses()} text-medical-600 animate-spin`} />;
      case 'waiting':
        return <Clock className={`${getSizeClasses()} text-gray-400 animate-pulse`} />;
      default:
        return (
          <div className={`${getSizeClasses()} border-2 border-gray-200 border-t-medical-600 rounded-full animate-spin`} />
        );
    }
  };

  const getContainerClasses = () => {
    switch (size) {
      case 'small':
        return 'flex items-center space-x-2';
      case 'large':
      case 'xlarge':
        return 'flex flex-col items-center justify-center space-y-4 py-12';
      default:
        return 'flex flex-col items-center justify-center space-y-3 py-8';
    }
  };

  const getTextClasses = () => {
    switch (size) {
      case 'small':
        return 'text-sm text-gray-600';
      case 'large':
      case 'xlarge':
        return 'text-lg text-gray-700';
      default:
        return 'text-base text-gray-600';
    }
  };

  return (
    <div className={getContainerClasses()}>
      {showIcon && getIcon()}
      {message && (
        <div className={getTextClasses()}>
          {message}
        </div>
      )}
    </div>
  );
};

// Specialized loading components
export const AnalysisLoader = ({ message = 'Analyzing medical image...' }) => (
  <LoadingSpinner type="analysis" size="large" message={message} />
);

export const ProcessingLoader = ({ message = 'Processing...' }) => (
  <LoadingSpinner type="processing" size="medium" message={message} />
);

export const InlineLoader = ({ message = 'Loading...' }) => (
  <LoadingSpinner type="default" size="small" message={message} />
);

export const FullPageLoader = ({ message = 'Loading application...' }) => (
  <div className="min-h-screen bg-gray-50 flex items-center justify-center">
    <div className="card max-w-md w-full mx-4">
      <LoadingSpinner type="default" size="xlarge" message={message} />
    </div>
  </div>
);

// Loading skeleton for cards
export const CardSkeleton = () => (
  <div className="card animate-pulse">
    <div className="h-6 bg-gray-200 rounded mb-4"></div>
    <div className="space-y-3">
      <div className="h-4 bg-gray-200 rounded"></div>
      <div className="h-4 bg-gray-200 rounded w-3/4"></div>
      <div className="h-4 bg-gray-200 rounded w-1/2"></div>
    </div>
  </div>
);

// Loading skeleton for table rows
export const TableRowSkeleton = ({ columns = 4 }) => (
  <tr className="animate-pulse">
    {Array.from({ length: columns }).map((_, index) => (
      <td key={index} className="px-6 py-4">
        <div className="h-4 bg-gray-200 rounded"></div>
      </td>
    ))}
  </tr>
);

export default LoadingSpinner;