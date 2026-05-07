import React, { useState, useCallback, useEffect } from 'react';
import jsPDF from 'jspdf';
import { useParams } from 'react-router-dom';
import { useDropzone } from 'react-dropzone';
import { 
  Upload, 
  FileImage, 
  X, 
  Play, 
  Activity,
  Download
} from 'lucide-react';
import { useAnalysis } from '../contexts/AnalysisContext';
import AnalysisProgress from '../components/AnalysisProgress';
import AnalysisResults from '../components/AnalysisResults';

const Analysis = () => {
  const { caseId } = useParams();
  const { currentAnalysis, updateAnalysis, startNewAnalysis } = useAnalysis();
  
  // Fetch results if caseId is provided in URL
  useEffect(() => {
    if (caseId && (!currentAnalysis.results || currentAnalysis.results.case_id !== caseId)) {
      const fetchResults = async () => {
        try {
          const response = await fetch(`/api/cases/${caseId}`);
          if (response.ok) {
            const results = await response.json();
            updateAnalysis({
              results: results,
              isAnalyzing: false,
              selectedFile: null,
              patientCode: results.patient_code,
              additionalInfo: results.additional_info || '',
              patientHistory: results.patient_history || ''
            });
            
            // Also sync local state
            setPatientCode(results.patient_code);
            setAdditionalInfo(results.additional_info || '');
            setPatientHistory(results.patient_history || '');
          }
        } catch (error) {
          console.error('Failed to fetch case results:', error);
        }
      };
      
      fetchResults();
    }
  }, [caseId, updateAnalysis, currentAnalysis.results]);

  const [selectedFile, setSelectedFile] = useState(currentAnalysis.selectedFile);
  const [patientCode, setPatientCode] = useState(currentAnalysis.patientCode);
  const [additionalInfo, setAdditionalInfo] = useState(currentAnalysis.additionalInfo);
  const [patientHistory, setPatientHistory] = useState(currentAnalysis.patientHistory);
  const [useDualModel, setUseDualModel] = useState(true);

  // Use global state for analysis data
  const isAnalyzing = currentAnalysis.isAnalyzing;
  const analysisResults = currentAnalysis.results;
  const analysisProgress = currentAnalysis.progress;

  // Update global state when local form data changes
  useEffect(() => {
    updateAnalysis({
      selectedFile,
      patientCode,
      additionalInfo,
      patientHistory
    });
  }, [selectedFile, patientCode, additionalInfo, patientHistory, updateAnalysis]);

  const onDrop = useCallback((acceptedFiles) => {
    const file = acceptedFiles[0];
    if (file) {
      setSelectedFile(file);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/*': ['.jpeg', '.jpg', '.png', '.bmp', '.tiff']
    },
    multiple: false
  });

  const removeFile = () => {
    setSelectedFile(null);
  };

  const startAnalysis = async () => {
    // Force rebuild - using real backend timing data only
    if (!selectedFile || !patientCode) {
      alert('Please select an X-ray image and enter a patient code');
      return;
    }

    // Start new analysis using global state
    startNewAnalysis();

    // Start new analysis
    startNewAnalysis();

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('patient_code', patientCode);
      formData.append('additional_info', additionalInfo);
      formData.append('patient_history', patientHistory);
      formData.append('use_dual_model', useDualModel ? 'true' : 'false');

      // Start the analysis
      const response = await fetch('/api/upload-complete-pipeline-with-chairman', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const results = await response.json();
        
        // Extract timing data from backend response
        const stageTimings = results.processing_summary?.stage_timings || {};
        
        // Update with real results and mark as complete
        updateAnalysis({
          results: results,
          isAnalyzing: false,
          progress: {
            radiology: { 
              status: 'completed', 
              time: stageTimings.radiology ? `${stageTimings.radiology}s` : null
            },
            clinical: { 
              status: 'completed', 
              time: stageTimings.parallel_analysis ? `${stageTimings.parallel_analysis}s` : null
            },
            evidence: { 
              status: 'completed', 
              time: stageTimings.parallel_analysis ? `${stageTimings.parallel_analysis}s` : null
            },
            risk: { 
              status: 'completed', 
              time: stageTimings.parallel_analysis ? `${stageTimings.parallel_analysis}s` : null
            },
            chairman: { 
              status: 'completed', 
              time: stageTimings.chairman ? `${stageTimings.chairman}s` : null
            }
          }
        });
      } else {
        throw new Error('Analysis failed');
      }
    } catch (error) {
      console.error('Analysis error:', error);
      alert('Analysis failed. Please try again.');
      
      // Update progress to show error
      updateAnalysis({
        progress: {
          radiology: { status: 'error', time: null },
          clinical: { status: 'pending', time: null },
          evidence: { status: 'pending', time: null },
          risk: { status: 'pending', time: null },
          chairman: { status: 'pending', time: null }
        },
        isAnalyzing: false
      });
    }
  };

  const downloadPDFReport = () => {
    if (!analysisResults) return;
    const results = analysisResults;
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

    const checkNewPage = (y, space = 60) => {
      if (y > 230 || (y + space > 280)) {
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
    yPos = checkNewPage(yPos, 80);
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
  };


  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-4">
          X-ray Analysis
        </h1>
        <p className="text-lg text-gray-600">
          Upload an X-ray image for AI-powered medical analysis and diagnosis
        </p>
      </div>

      {/* Upload Section - Show when no results or analyzing */}
      {(!analysisResults || isAnalyzing) && (
        <div className="card">
          <h2 className="text-xl font-semibold text-gray-900 mb-6">Upload X-ray Image</h2>
        
        {/* File Upload */}
        <div
          {...getRootProps()}
          className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors duration-200 ${
            isDragActive
              ? 'border-medical-400 bg-medical-50'
              : selectedFile
              ? 'border-success-400 bg-success-50'
              : 'border-gray-300 hover:border-gray-400'
          }`}
        >
          <input {...getInputProps()} />
          
          {selectedFile ? (
            <div className="space-y-4">
              <div className="flex items-center justify-center space-x-3">
                <FileImage className="w-8 h-8 text-success-600" />
                <div className="text-left">
                  <p className="font-medium text-gray-900">{selectedFile.name}</p>
                  <p className="text-sm text-gray-500">
                    {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeFile();
                  }}
                  className="p-1 text-gray-400 hover:text-gray-600"
                >
                  <X className="w-5 h-5" />
                </button>
              </div>
              <p className="text-sm text-success-600">File ready for analysis</p>
            </div>
          ) : (
            <div className="space-y-4">
              <Upload className="w-12 h-12 text-gray-400 mx-auto" />
              <div>
                <p className="text-lg font-medium text-gray-900">
                  {isDragActive ? 'Drop the X-ray image here' : 'Upload X-ray image'}
                </p>
                <p className="text-gray-500">
                  Drag and drop or click to select • JPEG, PNG, BMP, TIFF
                </p>
              </div>
            </div>
          )}
        </div>

        {/* Patient Information */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Patient Code *
            </label>
            <input
              type="text"
              value={patientCode}
              onChange={(e) => setPatientCode(e.target.value)}
              placeholder="e.g., PATIENT_001"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-medical-500 focus:border-medical-500"
              required
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Additional Information
            </label>
            <input
              type="text"
              value={additionalInfo}
              onChange={(e) => setAdditionalInfo(e.target.value)}
              placeholder="e.g., Patient symptoms, concerns"
              className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-medical-500 focus:border-medical-500"
            />
          </div>
        </div>

        <div className="mt-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Patient History
          </label>
          <textarea
            value={patientHistory}
            onChange={(e) => setPatientHistory(e.target.value)}
            placeholder="Enter relevant medical history..."
            rows={3}
            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-medical-500 focus:border-medical-500"
          />
        </div>

        {/* Dual Model Toggle */}
        <div className="mt-4 flex items-center gap-3 p-3 bg-purple-50 rounded-lg border border-purple-200">
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={useDualModel}
              onChange={(e) => setUseDualModel(e.target.checked)}
              className="sr-only peer"
            />
            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-purple-600"></div>
          </label>
          <div>
            <span className="text-sm font-semibold text-purple-800">Dual-Model Validation</span>
            <p className="text-xs text-purple-600">Runs Gemini + Groq in parallel with consensus validation</p>
          </div>
        </div>

        {/* Start Analysis Button */}
        <div className="mt-6 flex justify-center space-x-4">          <button
            onClick={startAnalysis}
            disabled={!selectedFile || !patientCode || isAnalyzing}
            className={`flex items-center space-x-2 px-8 py-3 rounded-lg font-medium transition-colors duration-200 ${
              !selectedFile || !patientCode || isAnalyzing
                ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                : 'bg-medical-600 hover:bg-medical-700 text-white'
            }`}
          >
            {isAnalyzing ? (
              <>
                <Activity className="w-5 h-5 animate-spin" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <Play className="w-5 h-5" />
                <span>Start Analysis</span>
              </>
            )}
          </button>

          {analysisResults && !isAnalyzing && (
            <button
              onClick={() => {
                setSelectedFile(null);
                setPatientCode('');
                setAdditionalInfo('');
                setPatientHistory('');
                startNewAnalysis();
              }}
              className="btn-secondary flex items-center space-x-2"
            >
              <Upload className="w-5 h-5" />
              <span>New Analysis</span>
            </button>
          )}
          </div>
        </div>
      )}

      {/* Analysis Progress */}
      {(isAnalyzing || analysisResults) && (
        <AnalysisProgress 
          progress={analysisProgress} 
          isAnalyzing={isAnalyzing}
        />
      )}

      {/* Analysis Results */}
      {analysisResults && (
        <div className="space-y-6">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold text-gray-900">Analysis Results</h2>
            <div className="flex space-x-4">
              <button
                onClick={() => {
                  setSelectedFile(null);
                  setPatientCode('');
                  setAdditionalInfo('');
                  setPatientHistory('');
                  startNewAnalysis();
                }}
                className="bg-medical-600 hover:bg-medical-700 text-white font-medium py-2 px-6 rounded-lg transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-medical-500 focus:ring-offset-2 flex items-center space-x-2"
              >
                <Upload className="w-5 h-5" />
                <span>New Analysis</span>
              </button>
              <button
                onClick={downloadPDFReport}
                className="btn-secondary flex items-center space-x-2"
              >
                <Download className="w-4 h-4" />
                <span>Download Report</span>
              </button>
            </div>
          </div>
          
          <AnalysisResults results={analysisResults} />
        </div>
      )}
    </div>
  );
};

export default Analysis;