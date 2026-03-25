import React, { useState, useEffect } from 'react';
import jsPDF from 'jspdf';
import { useNavigate } from 'react-router-dom';
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
  const navigate = useNavigate();
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
      const response = await fetch('/api/cases?limit=50');
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

  const downloadPDFReport = async (caseId) => {
    try {
      const response = await fetch(`/reports/${caseId}`);
      if (response.ok) {
        const results = await response.json();
        const doc = new jsPDF();
        const pageWidth = doc.internal.pageSize.getWidth();
        const margin = 20;
        const contentWidth = pageWidth - 2 * margin;
        let yPos = 20;

        // Helper function to add text with word wrap
        const addText = (text, x, y, options = {}) => {
          const { fontSize = 10, fontStyle = 'normal', 
                  color = [0, 0, 0], align = 'left' } = options;
          doc.setFontSize(fontSize);
          doc.setFont('helvetica', fontStyle);
          doc.setTextColor(...color);
          const lines = doc.splitTextToSize(text || 'N/A', contentWidth - (x - margin));
          
          let currentY = y;
          lines.forEach(line => {
            currentY = checkNewPage(currentY, fontSize * 0.45);
            doc.text(line, x, currentY, { align });
            currentY += fontSize * 0.45;
          });
          
          return currentY;
        };

        const addSection = (title, y) => {
          y = checkNewPage(y, 50); // Ensure page break before section header
          doc.setFillColor(41, 128, 185);
          doc.rect(margin, y - 5, contentWidth, 10, 'F');
          doc.setTextColor(255, 255, 255);
          doc.setFontSize(13);
          doc.setFont('helvetica', 'bold');
          doc.text(title, margin + 4, y + 2);
          doc.setTextColor(0, 0, 0);
          return y + 12;
        };

        const addDivider = (y) => {
          doc.setDrawColor(200, 200, 200);
          doc.setLineWidth(0.3);
          doc.line(margin, y, pageWidth - margin, y);
          return y + 8;
        };

        const checkNewPage = (y, space = 50) => {
          if (y > 240 || (y + space > 280)) {
            doc.addPage();
            // Add header to new page
            doc.setFillColor(26, 54, 93);
            doc.rect(0, 0, pageWidth, 15, 'F');
            doc.setFillColor(52, 152, 219);
            doc.rect(0, 15, pageWidth, 2, 'F');
            return 30;
          }
          return y;
        };

        const drawConfidenceBar = (confidence, y) => {
          const barWidth = 60;
          doc.setFillColor(220, 220, 220);
          doc.roundedRect(margin + 100, y - 4, barWidth, 5, 2, 2, 'F');
          doc.setFillColor(52, 152, 219);
          doc.roundedRect(margin + 100, y - 4, barWidth * (confidence / 100), 5, 2, 2, 'F');
          doc.setFontSize(9);
          doc.setTextColor(100, 100, 100);
          doc.text(`${Math.round(confidence)}%`, margin + 100 + barWidth + 5, y);
          return y;
        };

        // ─── HEADER ───
        doc.setFillColor(26, 54, 93);
        doc.rect(0, 0, pageWidth, 40, 'F');
        doc.setFillColor(52, 152, 219);
        doc.rect(0, 40, pageWidth, 3, 'F');
        
        doc.setTextColor(255, 255, 255);
        doc.setFontSize(22);
        doc.setFont('helvetica', 'bold');
        doc.text('Medical AI Analysis Report', margin, 22);
        
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text(`Generated: ${new Date().toLocaleString()}`, margin, 32);
        yPos = 55;

        // ─── PATIENT INFO ───
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.setTextColor(0, 0, 0);
        doc.text('PATIENT INFORMATION', margin, yPos);
        yPos += 8;
        
        doc.setFontSize(10);
        doc.setFont('helvetica', 'normal');
        doc.text(`Patient Code:`, margin, yPos);
        doc.setFont('helvetica', 'bold');
        doc.text(`${results.patient_code || 'Unknown'}`, margin + 30, yPos);
        
        doc.setFont('helvetica', 'normal');
        doc.text(`Case ID:`, margin + 100, yPos);
        doc.setFont('helvetica', 'bold');
        doc.text(`${results.case_id || 'N/A'}`, margin + 120, yPos);
        yPos += 8;
        
        doc.setFont('helvetica', 'normal');
        doc.text(`Pipeline:`, margin, yPos);
        doc.text(`${results.orchestration || 'LangGraph StateGraph'}`, margin + 30, yPos);
        yPos += 15;

        // ─── CHAIRMAN SUMMARY ───
        yPos = addSection('EXECUTIVE SUMMARY', yPos);
        const chairman = results.chairman_report || {};
        
        doc.setFontSize(11);
        doc.setFont('helvetica', 'bold');
        doc.text('Primary Diagnosis:', margin, yPos);
        yPos = addText(chairman.primary_diagnosis || 'N/A', margin + 40, yPos, { fontSize: 11, fontStyle: 'bold', color: [41, 128, 185] });
        yPos += 8;
        
        yPos = addText('Executive Summary:', margin, yPos, { fontSize: 11, fontStyle: 'bold' });
        yPos += 2;
        yPos = addText(chairman.executive_summary || 'No summary available', margin, yPos, { fontSize: 10 });
        yPos += 8;

        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text('Confidence Score:', margin, yPos);
        drawConfidenceBar((chairman.confidence_level || 0) * 100, yPos);
        yPos += 10;
        
        doc.text(`Urgency: ${(chairman.urgency_level || 'N/A').toUpperCase()}`, margin, yPos);
        doc.text(`Consensus: ${((chairman.consensus_score || 0) * 100).toFixed(0)}%`, margin + 100, yPos);
        yPos += 15;

        // ─── RADIOLOGY ───
        yPos = checkNewPage(yPos, 80);
        yPos = addDivider(yPos);
        yPos = addSection('RADIOLOGY ANALYSIS', yPos);
        const radiology = results.radiology_analysis || {};
        
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text('Findings:', margin, yPos);
        yPos += 6;
        yPos = addText(radiology.findings || 'No findings', margin, yPos, { fontSize: 10 });
        yPos += 8;
        
        if (radiology.abnormalities?.length > 0) {
          doc.setFont('helvetica', 'bold');
          doc.text('Abnormalities Detected:', margin, yPos);
          yPos += 6;
          radiology.abnormalities.forEach(ab => {
            yPos = checkNewPage(yPos);
            doc.circle(margin + 3, yPos - 1.5, 1, 'F');
            yPos = addText(ab, margin + 7, yPos, { fontSize: 10 });
            yPos += 2;
          });
          yPos += 5;
        }
        
        doc.setFont('helvetica', 'bold');
        doc.text(`Image Quality:`, margin, yPos);
        doc.setFont('helvetica', 'normal');
        doc.text(`${radiology.image_quality || 'N/A'}`, margin + 30, yPos);
        
        doc.setFont('helvetica', 'bold');
        doc.text(`Confidence:`, margin + 100, yPos);
        drawConfidenceBar((radiology.confidence || 0) * 100, yPos);
        yPos += 20;

        // ─── CLINICAL ───
        yPos = checkNewPage(yPos, 80);
        yPos = addDivider(yPos);
        yPos = addSection('CLINICAL ANALYSIS', yPos);
        const clinical = results.clinical_analysis || {};
        
        doc.setFont('helvetica', 'bold');
        doc.text('Differential Diagnosis:', margin, yPos);
        yPos += 6;
        const diagnoses = Array.isArray(clinical.differential_diagnosis)
          ? clinical.differential_diagnosis
          : [clinical.differential_diagnosis];
        diagnoses.forEach(d => {
          yPos = checkNewPage(yPos);
          doc.circle(margin + 3, yPos - 1.5, 1, 'F');
          yPos = addText(d, margin + 7, yPos, { fontSize: 10 });
          yPos += 2;
        });
        yPos += 8;
        
        doc.setFont('helvetica', 'bold');
        doc.text('Clinical Reasoning:', margin, yPos);
        yPos += 6;
        yPos = addText(clinical.reasoning || 'No reasoning available', margin, yPos, { fontSize: 9 });
        yPos += 8;

        doc.setFont('helvetica', 'bold');
        doc.text(`Urgency:`, margin, yPos);
        doc.setFont('helvetica', 'normal');
        doc.text(`${clinical.urgency || 'N/A'}`, margin + 20, yPos);
        
        doc.setFont('helvetica', 'bold');
        doc.text(`Confidence:`, margin + 100, yPos);
        drawConfidenceBar((clinical.confidence || 0) * 100, yPos);
        yPos += 20;

        // ─── RISK ───
        yPos = checkNewPage(yPos, 80);
        yPos = addDivider(yPos);
        yPos = addSection('RISK ASSESSMENT', yPos);
        const risk = results.risk_assessment || {};
        
        const riskColors = {
          low: [39, 174, 96],
          medium: [243, 156, 18],
          high: [231, 76, 60],
          critical: [142, 68, 173]
        };
        const riskColor = riskColors[risk.risk_level?.toLowerCase()] || [128, 128, 128];
        
        const riskText = `${(risk.risk_level || 'UNKNOWN').toUpperCase()} RISK`;
        doc.setFontSize(14);
        const riskTextWidth = doc.getTextWidth(riskText);
        const badgeWidth = riskTextWidth + 16;
        
        doc.setFillColor(...riskColor);
        doc.roundedRect(margin, yPos - 3, badgeWidth, 10, 2, 2, 'F');
        doc.setTextColor(255, 255, 255);
        doc.setFont('helvetica', 'bold');
        doc.text(riskText, margin + 8, yPos + 4);
        
        doc.setTextColor(0, 0, 0);
        doc.setFontSize(11);
        doc.setFont('helvetica', 'normal');
        doc.text(`Risk Score: ${((risk.risk_score || 0) * 100).toFixed(0)}%`, margin + badgeWidth + 10, yPos + 4);
        yPos += 16;
        
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text('Recommended Action:', margin, yPos);
        doc.setFont('helvetica', 'normal');
        doc.text(risk.recommended_action || 'N/A', margin + 45, yPos);
        yPos += 8;
        
        doc.setFont('helvetica', 'bold');
        doc.text('Urgency Timeline:', margin, yPos);
        doc.setFont('helvetica', 'normal');
        doc.text(risk.urgency_timeline || 'N/A', margin + 45, yPos);
        yPos += 12;

        if (risk.critical_findings?.length > 0) {
          doc.setFont('helvetica', 'bold');
          doc.setFontSize(10);
          doc.setTextColor(231, 76, 60);
          doc.text('Critical Findings:', margin, yPos);
          doc.setTextColor(0, 0, 0);
          yPos += 6;
          risk.critical_findings.forEach(finding => {
            yPos = checkNewPage(yPos);
            doc.setFillColor(231, 76, 60);
            doc.circle(margin + 3, yPos - 1, 1.5, 'F');
            doc.setTextColor(231, 76, 60);
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(9);
            const lines = doc.splitTextToSize(`   ${finding}`, contentWidth - 10);
            doc.text(lines, margin + 7, yPos);
            yPos += lines.length * 4 + 3;
            doc.setTextColor(0, 0, 0);
          });
          yPos += 5;
        }

        if (risk.risk_factors?.length > 0) {
          doc.setFont('helvetica', 'bold');
          doc.setFontSize(10);
          doc.setTextColor(0, 0, 0);
          doc.text('Risk Factors:', margin, yPos);
          yPos += 6;
          risk.risk_factors.forEach(factor => {
            yPos = checkNewPage(yPos);
            doc.setFillColor(80, 80, 80);
            doc.circle(margin + 3, yPos - 1, 1.5, 'F');
            doc.setTextColor(60, 60, 60);
            doc.setFont('helvetica', 'normal');
            doc.setFontSize(9);
            const lines = doc.splitTextToSize(`   ${factor}`, contentWidth - 10);
            doc.text(lines, margin + 7, yPos);
            yPos += lines.length * 4 + 3;
            doc.setTextColor(0, 0, 0);
          });
          yPos += 10;
        }

        // ─── EVIDENCE ───
        yPos = checkNewPage(yPos, 80);
        yPos = addDivider(yPos);
        yPos = addSection('EVIDENCE RESEARCH', yPos);
        const evidence = results.evidence_research || {};
        
        doc.setFontSize(10);
        doc.setFont('helvetica', 'bold');
        doc.text(`Keywords:`, margin, yPos);
        doc.setFont('helvetica', 'normal');
        doc.text(`${evidence.search_keywords || 'N/A'}`, margin + 25, yPos);
        
        doc.setFont('helvetica', 'bold');
        doc.text(`Papers Found:`, margin + 100, yPos);
        doc.setFont('helvetica', 'normal');
        doc.text(`${evidence.total_papers_found || 0}`, margin + 130, yPos);
        yPos += 10;
        
        yPos = addText('Evidence Summary:', margin, yPos, { fontSize: 10, fontStyle: 'bold' });
        yPos += 2;
        yPos = addText(evidence.evidence_summary || 'No summary available', margin, yPos, { fontSize: 9 });
        yPos += 10;

        if (evidence.citations?.length > 0) {
          doc.setFont('helvetica', 'bold');
          doc.text('Key Citations:', margin, yPos);
          yPos += 6;
          evidence.citations.slice(0, 3).forEach((c, i) => {
            yPos = checkNewPage(yPos);
            yPos = addText(`${i + 1}. ${c.title} — ${c.journal} (${c.year})`, margin + 5, yPos, { fontSize: 8 });
            yPos += 2;
          });
        }
        yPos += 15;

        // ─── IMMEDIATE ACTIONS ───
        yPos = checkNewPage(yPos, 80);
        yPos = addDivider(yPos);
        yPos = addSection('IMMEDIATE ACTIONS', yPos);
        (chairman.immediate_actions || []).forEach(action => {
          yPos = checkNewPage(yPos);
          doc.setFillColor(41, 128, 185);
          doc.rect(margin + 2, yPos - 3, 2, 2, 'F');
          yPos = addText(action, margin + 8, yPos, { fontSize: 10 });
          yPos += 4;
        });

        // ─── FOOTER ───
        const pageCount = doc.internal.getNumberOfPages();
        for (let i = 1; i <= pageCount; i++) {
          doc.setPage(i);
          doc.setDrawColor(200, 200, 200);
          doc.line(margin, 285, pageWidth - margin, 285);
          doc.setFontSize(7);
          doc.setTextColor(128, 128, 128);
          doc.text('CONFIDENTIAL - AI-Generated Medical Report - For Clinical Review Only', margin, 290);
          doc.text(`Page ${i} of ${pageCount}`, pageWidth - margin, 290, { align: 'right' });
        }

        // ─── SAVE ───
        const filename = `medical_report_${results.patient_code || 'patient'}_${results.case_id?.substring(0, 8) || 'report'}.pdf`;
        doc.save(filename);
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
            <div 
              key={analysis.case_id} 
              onClick={() => navigate(`/analysis/${analysis.case_id}`)}
              className="card hover:shadow-lg transition-shadow duration-200 cursor-pointer"
            >
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
                    onClick={(e) => {
                      e.stopPropagation();
                      downloadPDFReport(analysis.case_id);
                    }}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-200"
                    title="Download Report"
                  >
                    <Download className="w-4 h-4" />
                  </button>

                  <button 
                    onClick={(e) => {
                      e.stopPropagation();
                      navigate(`/analysis/${analysis.case_id}`);
                    }}
                    className="p-2 text-gray-400 hover:text-gray-600 hover:bg-gray-100 rounded-lg transition-colors duration-200"
                  >
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