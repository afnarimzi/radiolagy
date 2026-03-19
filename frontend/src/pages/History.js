import React, { useState, useEffect } from 'react';
import { 
  FileText, 
  Search, 
  Filter, 
  Download, 
  Eye,
  Calendar,
  User,
  Clock,
  CheckCircle,
  AlertCircle,
  ChevronRight
} from 'lucide-react';

const History = () => {
  const [analyses, setAnalyses] = useState([]);
  const [filteredAnalyses, setFilteredAnalyses] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState('all');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchAnalysisHistory();
  }, []);

  useEffect(() => {
    filterAnalyses();
  }, [analyses, searchTerm, filterStatus]);

  const fetchAnalysisHistory = async () => {
    try {
      const response = await fetch('/cases?limit=50');
      if (response.ok) {
        const data = await response.json();
        setAnalyses(data || []);
      }
    } catch (error) {
      console.error('Failed to fetch analysis history:', error);
    } finally {
      setLoading(false);
    }
  };

  const filterAnalyses = () => {
    let filtered = analyses;

    // Filter by search term
    if (searchTerm) {
      filtered = filtered.filter(analysis => 
        analysis.patient_code?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        analysis.case_id?.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Filter by status
    if (filterStatus !== 'all') {
      filtered = filtered.filter(analysis => analysis.report_status === filterStatus);
    }

    setFilteredAnalyses(filtered);
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-success-600" />;
      case 'failed':
        return <AlertCircle className="w-4 h-4 text-danger-600" />;
      default:
        return <Clock className="w-4 h-4 text-warning-600" />;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'completed':
        return 'status-success';
      case 'failed':
        return 'status-danger';
      default:
        return 'status-warning';
    }
  };

  const downloadReport = async (caseId) => {
    try {
      const response = await fetch(`/reports/${caseId}`);
      if (response.ok) {
        const data = await response.json();
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `medical_report_${caseId}.json`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);
      }
    } catch (error) {
      console.error('Failed to download report:', error);
    }
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-medical-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Analysis History</h1>
          <p className="text-gray-600 mt-2">
            View and manage all previous medical analyses
          </p>
        </div>
        <div className="text-sm text-gray-500">
          {filteredAnalyses.length} of {analyses.length} analyses
        </div>
      </div>

      {/* Search and Filter */}
      <div className="card">
        <div className="flex flex-col md:flex-row gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
            <input
              type="text"
              placeholder="Search by patient code or case ID..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-medical-500 focus:border-medical-500"
            />
          </div>

          {/* Filter */}
          <div className="flex items-center space-x-2">
            <Filter className="w-4 h-4 text-gray-400" />
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              className="border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-medical-500 focus:border-medical-500"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="processing">Processing</option>
              <option value="failed">Failed</option>
            </select>
          </div>
        </div>
      </div>

      {/* Analysis List */}
      <div className="space-y-4">
        {filteredAnalyses.length > 0 ? (
          filteredAnalyses.map((analysis) => (
            <div key={analysis.case_id} className="card hover:shadow-lg transition-shadow duration-200">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-4">
                  <div className="w-12 h-12 bg-medical-100 rounded-lg flex items-center justify-center">
                    <FileText className="w-6 h-6 text-medical-600" />
                  </div>
                  
                  <div className="flex-1">
                    <div className="flex items-center space-x-3">
                      <h3 className="font-semibold text-gray-900">{analysis.patient_code}</h3>
                      <span className={getStatusBadge(analysis.report_status)}>
                        {analysis.report_status || 'Unknown'}
                      </span>
                    </div>
                    
                    <div className="flex items-center space-x-4 mt-1 text-sm text-gray-500">
                      <div className="flex items-center space-x-1">
                        <User className="w-3 h-3" />
                        <span>Case: {analysis.case_id}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Calendar className="w-3 h-3" />
                        <span>{new Date(analysis.created_at).toLocaleDateString()}</span>
                      </div>
                      <div className="flex items-center space-x-1">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(analysis.created_at).toLocaleTimeString()}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex items-center space-x-2">
                  {analysis.confidence && (
                    <div className="text-right mr-4">
                      <div className="text-sm font-medium text-gray-900">
                        {Math.round(analysis.confidence * 100)}%
                      </div>
                      <div className="text-xs text-gray-500">Confidence</div>
                    </div>
                  )}

                  <button
                    onClick={() => downloadReport(analysis.case_id)}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-200"
                    title="Download Report"
                  >
                    <Download className="w-4 h-4" />
                  </button>

                  <button className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-200">
                    <Eye className="w-4 h-4" />
                  </button>

                  <ChevronRight className="w-4 h-4 text-gray-400" />
                </div>
              </div>

              {/* Additional Details */}
              {analysis.findings_summary && (
                <div className="mt-4 pt-4 border-t border-gray-200">
                  <p className="text-sm text-gray-700 line-clamp-2">
                    {analysis.findings_summary}
                  </p>
                </div>
              )}
            </div>
          ))
        ) : (
          <div className="card text-center py-12">
            <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-medium text-gray-900 mb-2">No analyses found</h3>
            <p className="text-gray-500 mb-6">
              {searchTerm || filterStatus !== 'all' 
                ? 'Try adjusting your search or filter criteria'
                : 'Start your first medical analysis to see results here'
              }
            </p>
            {!searchTerm && filterStatus === 'all' && (
              <button className="btn-primary">
                Start New Analysis
              </button>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default History;