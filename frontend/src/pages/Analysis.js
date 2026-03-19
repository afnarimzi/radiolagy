import React, { useState, useCallback, useEffect } from 'react';
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
  const { currentAnalysis, updateAnalysis, startNewAnalysis } = useAnalysis();
  
  const [selectedFile, setSelectedFile] = useState(currentAnalysis.selectedFile);
  const [patientCode, setPatientCode] = useState(currentAnalysis.patientCode);
  const [additionalInfo, setAdditionalInfo] = useState(currentAnalysis.additionalInfo);
  const [patientHistory, setPatientHistory] = useState(currentAnalysis.patientHistory);

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

  const simulateRealTimeProgress = () => {
    // Simulate radiology agent completion after 3 seconds
    setTimeout(() => {
      updateAnalysis({
        progress: {
          ...currentAnalysis.progress,
          radiology: { status: 'completed', time: '14.1s' }
        }
      });
    }, 3000);

    // Simulate clinical agent completion after 5 seconds
    setTimeout(() => {
      updateAnalysis({
        progress: {
          ...currentAnalysis.progress,
          radiology: { status: 'completed', time: '14.1s' },
          clinical: { status: 'completed', time: '1.7s' }
        }
      });
    }, 5000);

    // Simulate evidence agent completion after 8 seconds
    setTimeout(() => {
      updateAnalysis({
        progress: {
          ...currentAnalysis.progress,
          radiology: { status: 'completed', time: '14.1s' },
          clinical: { status: 'completed', time: '1.7s' },
          evidence: { status: 'completed', time: '19.2s' }
        }
      });
    }, 8000);

    // Simulate risk agent completion after 10 seconds
    setTimeout(() => {
      updateAnalysis({
        progress: {
          ...currentAnalysis.progress,
          radiology: { status: 'completed', time: '14.1s' },
          clinical: { status: 'completed', time: '1.7s' },
          evidence: { status: 'completed', time: '19.2s' },
          risk: { status: 'completed', time: '14.1s' }
        }
      });
    }, 10000);

    // Simulate chairman agent completion after 12 seconds
    setTimeout(() => {
      updateAnalysis({
        progress: {
          ...currentAnalysis.progress,
          radiology: { status: 'completed', time: '14.1s' },
          clinical: { status: 'completed', time: '1.7s' },
          evidence: { status: 'completed', time: '19.2s' },
          risk: { status: 'completed', time: '14.1s' },
          chairman: { status: 'completed', time: '2.3s' }
        }
      });
    }, 12000);
  };

  const startAnalysis = async () => {
    if (!selectedFile || !patientCode) {
      alert('Please select an X-ray image and enter a patient code');
      return;
    }

    // Start new analysis using global state
    startNewAnalysis();

    // Start simulating real-time progress
    simulateRealTimeProgress();

    try {
      const formData = new FormData();
      formData.append('file', selectedFile);
      formData.append('patient_code', patientCode);
      formData.append('additional_info', additionalInfo);
      formData.append('patient_history', patientHistory);

      // Start the analysis
      const response = await fetch('/upload-complete-pipeline-with-chairman', {
        method: 'POST',
        body: formData,
      });

      if (response.ok) {
        const results = await response.json();
        updateAnalysis({
          results: results,
          isAnalyzing: false
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
          ...currentAnalysis.progress,
          radiology: { ...currentAnalysis.progress.radiology, status: 'error' }
        },
        isAnalyzing: false
      });
    }
  };

  const downloadReport = () => {
    if (!analysisResults) return;
    
    const reportData = {
      patient_code: patientCode,
      case_id: analysisResults.case_id,
      analysis_date: new Date().toISOString(),
      radiology_analysis: analysisResults.radiology_analysis,
      clinical_analysis: analysisResults.clinical_analysis,
      evidence_research: analysisResults.evidence_research,
      risk_assessment: analysisResults.risk_assessment,
      chairman_report: analysisResults.chairman_report
    };

    const blob = new Blob([JSON.stringify(reportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `medical_analysis_${patientCode}_${analysisResults.case_id}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
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

      {/* Upload Section */}
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

        {/* Start Analysis Button */}
        <div className="mt-6 flex justify-center space-x-4">
          <button
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
            <button
              onClick={downloadReport}
              className="btn-secondary flex items-center space-x-2"
            >
              <Download className="w-4 h-4" />
              <span>Download Report</span>
            </button>
          </div>
          
          <AnalysisResults results={analysisResults} />
        </div>
      )}
    </div>
  );
};

export default Analysis;