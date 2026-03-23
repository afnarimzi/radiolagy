import React, { useState } from 'react';
import { 
  FileText, 
  Brain, 
  BookOpen, 
  AlertTriangle, 
  Crown,
  ChevronDown,
  ChevronRight,
  ExternalLink,
  Clock,
  TrendingUp
} from 'lucide-react';

const AnalysisResults = ({ results }) => {
  const [expandedSections, setExpandedSections] = useState({
    radiology: true,
    clinical: true,
    evidence: true,
    risk: true,
    chairman: true
  });

  const toggleSection = (section) => {
    setExpandedSections(prev => ({
      ...prev,
      [section]: !prev[section]
    }));
  };

  const ResultSection = ({ title, icon: Icon, color, isExpanded, onToggle, children }) => (
    <div className="card">
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between p-0 text-left"
      >
        <div className="flex items-center space-x-3">
          <div className={`w-10 h-10 ${color} rounded-lg flex items-center justify-center text-white`}>
            <Icon className="w-5 h-5" />
          </div>
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
        </div>
        {isExpanded ? (
          <ChevronDown className="w-5 h-5 text-gray-400" />
        ) : (
          <ChevronRight className="w-5 h-5 text-gray-400" />
        )}
      </button>
      
      {isExpanded && (
        <div className="mt-4 pt-4 border-t border-gray-200">
          {children}
        </div>
      )}
    </div>
  );

  return (
    <div className="space-y-6">
      {/* Case Information */}
      <div className="card bg-medical-50 border-medical-200">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-bold text-gray-900">Case Analysis Complete</h2>
            <p className="text-gray-600">Case ID: {results.case_id}</p>
            <p className="text-gray-600">Patient: {results.patient_code}</p>
          </div>
          <div className="text-right">
            <div className="flex items-center space-x-2 text-success-600">
              <Clock className="w-4 h-4" />
              <span className="font-medium">
                {results.processing_summary?.stage_timings?.total_pipeline || 'N/A'}s
              </span>
            </div>
            <p className="text-sm text-gray-500">Total Processing Time</p>
          </div>
        </div>
      </div>

      {/* Chairman Report (Executive Summary) */}
      <ResultSection
        title="Chairman Report - Executive Summary"
        icon={Crown}
        color="bg-indigo-500"
        isExpanded={expandedSections.chairman}
        onToggle={() => toggleSection('chairman')}
      >
        <div className="space-y-4">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Executive Summary</h4>
            <p className="text-gray-700 leading-relaxed">
              {results.chairman_report?.executive_summary || 'No executive summary available'}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Primary Diagnosis</h4>
              <p className="text-gray-700">
                {results.chairman_report?.primary_diagnosis || 'Not specified'}
              </p>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Confidence Level</h4>
              <div className="flex items-center space-x-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-medical-500 h-2 rounded-full"
                    style={{ width: `${(results.chairman_report?.confidence_level || 0) * 100}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-700">
                  {Math.round((results.chairman_report?.confidence_level || 0) * 100)}%
                </span>
              </div>
            </div>
          </div>

          {results.chairman_report?.immediate_actions && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Immediate Actions</h4>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {results.chairman_report.immediate_actions.map((action, index) => (
                  <li key={index}>{action}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </ResultSection>

      {/* Radiology Analysis */}
      <ResultSection
        title="Radiology Analysis"
        icon={FileText}
        color="bg-blue-500"
        isExpanded={expandedSections.radiology}
        onToggle={() => toggleSection('radiology')}
      >
        <div className="space-y-4">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Findings</h4>
            <p className="text-gray-700 leading-relaxed">
              {results.radiology_analysis?.findings || 'No findings available'}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Abnormalities</h4>
              {results.radiology_analysis?.abnormalities?.length > 0 ? (
                <ul className="list-disc list-inside space-y-1 text-gray-700">
                  {results.radiology_analysis.abnormalities.map((abnormality, index) => (
                    <li key={index}>{abnormality}</li>
                  ))}
                </ul>
              ) : (
                <p className="text-gray-500">No abnormalities detected</p>
              )}
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Image Quality</h4>
              <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-success-100 text-success-800">
                {results.radiology_analysis?.image_quality || 'Unknown'}
              </span>
              
              <div className="mt-2">
                <h5 className="text-sm font-medium text-gray-700">Confidence</h5>
                <div className="flex items-center space-x-2 mt-1">
                  <div className="flex-1 bg-gray-200 rounded-full h-2">
                    <div 
                      className="bg-blue-500 h-2 rounded-full"
                      style={{ width: `${(results.radiology_analysis?.confidence || 0) * 100}%` }}
                    />
                  </div>
                  <span className="text-sm text-gray-600">
                    {Math.round((results.radiology_analysis?.confidence || 0) * 100)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </ResultSection>

      {/* Clinical Analysis */}
      <ResultSection
        title="Clinical Analysis"
        icon={Brain}
        color="bg-green-500"
        isExpanded={expandedSections.clinical}
        onToggle={() => toggleSection('clinical')}
      >
        <div className="space-y-4">
          <div>
            <h4 className="font-medium text-gray-900 mb-2">Differential Diagnosis</h4>
            {results.clinical_analysis?.differential_diagnosis?.length > 0 ? (
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {results.clinical_analysis.differential_diagnosis.map((diagnosis, index) => (
                  <li key={index}>{diagnosis}</li>
                ))}
              </ul>
            ) : (
              <p className="text-gray-500">No differential diagnosis available</p>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Urgency Level</h4>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                results.clinical_analysis?.urgency === 'high' ? 'bg-danger-100 text-danger-800' :
                results.clinical_analysis?.urgency === 'medium' ? 'bg-warning-100 text-warning-800' :
                'bg-success-100 text-success-800'
              }`}>
                {results.clinical_analysis?.urgency || 'Unknown'}
              </span>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Recommended Follow-up</h4>
              <p className="text-sm text-gray-700">
                {results.clinical_analysis?.recommended_followup || 'No specific follow-up recommended'}
              </p>
            </div>
          </div>

          {results.clinical_analysis?.reasoning && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Clinical Reasoning</h4>
              <p className="text-gray-700 leading-relaxed">
                {results.clinical_analysis.reasoning}
              </p>
            </div>
          )}
        </div>
      </ResultSection>

      {/* Evidence Research */}
      <ResultSection
        title="Evidence Research"
        icon={BookOpen}
        color="bg-purple-500"
        isExpanded={expandedSections.evidence}
        onToggle={() => toggleSection('evidence')}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Search Keywords</h4>
              <p className="text-gray-700">
                {results.evidence_research?.search_keywords || 'No keywords available'}
              </p>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Papers Found</h4>
              <div className="flex items-center space-x-2">
                <TrendingUp className="w-4 h-4 text-purple-500" />
                <span className="font-medium text-gray-900">
                  {results.evidence_research?.total_papers_found || 0} papers
                </span>
              </div>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-900 mb-2">Evidence Summary</h4>
            <p className="text-gray-700 leading-relaxed">
              {results.evidence_research?.evidence_summary || 'No evidence summary available'}
            </p>
          </div>

          {results.evidence_research?.citations?.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Key Citations</h4>
              <div className="space-y-2">
                {results.evidence_research.citations.slice(0, 3).map((citation, index) => (
                  <div key={index} className="p-3 bg-gray-50 rounded-lg">
                    <h5 className="font-medium text-gray-900 text-sm">
                      {citation.title}
                    </h5>
                    <p className="text-xs text-gray-600 mt-1">
                      {Array.isArray(citation.authors) 
                        ? citation.authors.join(', ') 
                        : citation.authors}
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {citation.journal} — {citation.year}
                    </p>
                    {(citation.pmid || citation.url) && (
                      <button
                        onClick={() => {
                          const url = citation.pmid 
                            ? `https://pubmed.ncbi.nlm.nih.gov/${citation.pmid}/`
                            : citation.url;
                          window.open(url, '_blank', 'noopener,noreferrer');
                        }}
                        className="inline-flex items-center space-x-1 text-xs text-purple-600 hover:text-purple-700 mt-1 cursor-pointer"
                      >
                        <span>View Paper</span>
                        <ExternalLink className="w-3 h-3" />
                      </button>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </ResultSection>

      {/* Risk Assessment */}
      <ResultSection
        title="Risk Assessment"
        icon={AlertTriangle}
        color="bg-orange-500"
        isExpanded={expandedSections.risk}
        onToggle={() => toggleSection('risk')}
      >
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Risk Level</h4>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                results.risk_assessment?.risk_level === 'high' ? 'bg-danger-100 text-danger-800' :
                results.risk_assessment?.risk_level === 'medium' ? 'bg-warning-100 text-warning-800' :
                'bg-success-100 text-success-800'
              }`}>
                {results.risk_assessment?.risk_level || 'Unknown'}
              </span>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Risk Score</h4>
              <div className="flex items-center space-x-2">
                <div className="flex-1 bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-orange-500 h-2 rounded-full"
                    style={{ width: `${(results.risk_assessment?.risk_score || 0) * 10}%` }}
                  />
                </div>
                <span className="text-sm font-medium text-gray-700">
                  {results.risk_assessment?.risk_score || 0}/10
                </span>
              </div>
            </div>

            <div>
              <h4 className="font-medium text-gray-900 mb-2">Recommended Action</h4>
              <p className="text-sm text-gray-700">
                {results.risk_assessment?.recommended_action || 'No action specified'}
              </p>
            </div>
          </div>

          {results.risk_assessment?.critical_findings?.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Critical Findings</h4>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {results.risk_assessment.critical_findings.map((finding, index) => (
                  <li key={index}>{finding}</li>
                ))}
              </ul>
            </div>
          )}

          {results.risk_assessment?.next_steps?.length > 0 && (
            <div>
              <h4 className="font-medium text-gray-900 mb-2">Next Steps</h4>
              <ul className="list-disc list-inside space-y-1 text-gray-700">
                {results.risk_assessment.next_steps.map((step, index) => (
                  <li key={index}>{step}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      </ResultSection>
    </div>
  );
};

export default AnalysisResults;