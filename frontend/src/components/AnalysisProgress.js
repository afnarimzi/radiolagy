import { CheckCircle, Clock, AlertCircle, Activity } from 'lucide-react';

const AnalysisProgress = ({ progress, isAnalyzing }) => {
  const agents = [
    { key: 'radiology', name: 'Radiology Agent', icon: '🔬', description: 'Analyzing X-ray image' },
    { key: 'clinical', name: 'Clinical Agent', icon: '🩺', description: 'Generating differential diagnosis' },
    { key: 'evidence', name: 'Evidence Agent', icon: '📚', description: 'Searching medical literature' },
    { key: 'risk', name: 'Risk Agent', icon: '⚠️', description: 'Assessing risk factors' },
    { key: 'chairman', name: 'Chairman Agent', icon: '👔', description: 'Synthesizing final report' }
  ];

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-5 h-5 text-success-600" />;
      case 'processing':
        return <Activity className="w-5 h-5 text-medical-600 animate-spin" />;
      case 'error':
        return <AlertCircle className="w-5 h-5 text-danger-600" />;
      default:
        return <Clock className="w-5 h-5 text-gray-400" />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'completed':
        return 'bg-success-50 border-success-200';
      case 'processing':
        return 'bg-medical-50 border-medical-200';
      case 'error':
        return 'bg-danger-50 border-danger-200';
      default:
        return 'bg-gray-50 border-gray-200';
    }
  };

  return (
    <div className="card">
      <h2 className="text-xl font-semibold text-gray-900 mb-6">
        Analysis Progress
      </h2>

      <div className="space-y-4">
        {agents.map((agent) => {
          const agentProgress = progress[agent.key] || { status: 'pending', time: null };
          
          return (
            <div
              key={agent.key}
              className={`p-4 rounded-lg border-2 transition-all duration-300 ${getStatusColor(agentProgress.status)}`}
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="text-2xl">{agent.icon}</div>
                  <div>
                    <h3 className="font-medium text-gray-900">{agent.name}</h3>
                    <p className="text-sm text-gray-600">{agent.description}</p>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  {agentProgress.time && (
                    <span className="text-sm text-gray-500 font-mono">
                      {agentProgress.time}
                    </span>
                  )}
                  {getStatusIcon(agentProgress.status)}
                </div>
              </div>

              {/* Progress Bar */}
              <div className="mt-3">
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div
                    className={`h-2 rounded-full transition-all duration-500 ${
                      agentProgress.status === 'completed'
                        ? 'bg-success-500 w-full'
                        : agentProgress.status === 'processing'
                        ? 'bg-medical-500 w-3/4 animate-pulse'
                        : agentProgress.status === 'error'
                        ? 'bg-danger-500 w-1/4'
                        : 'bg-gray-300 w-0'
                    }`}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      {/* Overall Status */}
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            {isAnalyzing ? (
              <>
                <Activity className="w-5 h-5 text-medical-600 animate-spin" />
                <span className="font-medium text-gray-900">Analysis in Progress...</span>
              </>
            ) : (
              <>
                <CheckCircle className="w-5 h-5 text-success-600" />
                <span className="font-medium text-gray-900">Analysis Complete</span>
              </>
            )}
          </div>
          
          <div className="text-sm text-gray-500">
            AI Analysis System
          </div>
        </div>
      </div>
    </div>
  );
};

export default AnalysisProgress;