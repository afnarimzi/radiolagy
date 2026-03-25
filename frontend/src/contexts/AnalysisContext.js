import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';

const AnalysisContext = createContext();

export const useAnalysis = () => {
  const context = useContext(AnalysisContext);
  if (!context) {
    throw new Error('useAnalysis must be used within an AnalysisProvider');
  }
  return context;
};

export const AnalysisProvider = ({ children }) => {
  const [currentAnalysis, setCurrentAnalysis] = useState({
    results: null,
    progress: {},
    isAnalyzing: false,
    selectedFile: null,
    patientCode: '',
    additionalInfo: '',
    patientHistory: ''
  });

  const updateAnalysis = useCallback((updates) => {
    setCurrentAnalysis(prev => ({ ...prev, ...updates }));
  }, []);

  const clearAnalysis = useCallback(() => {
    setCurrentAnalysis({
      results: null,
      progress: {},
      isAnalyzing: false,
      selectedFile: null,
      patientCode: '',
      additionalInfo: '',
      patientHistory: ''
    });
  }, []);

  const startNewAnalysis = useCallback(() => {
    setCurrentAnalysis(prev => ({
      ...prev,
      results: null,
      progress: {
        radiology: { status: 'pending', time: null },
        clinical: { status: 'pending', time: null },
        evidence: { status: 'pending', time: null },
        risk: { status: 'pending', time: null },
        chairman: { status: 'pending', time: null }
      },
      isAnalyzing: true
    }));

    // Simulate the actual pipeline execution flow with individual timing
    setTimeout(() => {
      // Stage 1: Radiology starts
      setCurrentAnalysis(prev => ({
        ...prev,
        progress: {
          ...prev.progress,
          radiology: { status: 'processing', time: null }
        }
      }));
    }, 500);

    setTimeout(() => {
      // Stage 2: Radiology completes with timing, parallel agents start
      setCurrentAnalysis(prev => ({
        ...prev,
        progress: {
          ...prev.progress,
          radiology: { status: 'completed', time: 'Processing...' },
          clinical: { status: 'processing', time: null },
          evidence: { status: 'processing', time: null },
          risk: { status: 'processing', time: null }
        }
      }));
    }, 2000);

    // Simulate individual agent completions at different times
    setTimeout(() => {
      // Clinical completes first (fastest)
      setCurrentAnalysis(prev => ({
        ...prev,
        progress: {
          ...prev.progress,
          clinical: { status: 'completed', time: 'Processing...' }
        }
      }));
    }, 3500);

    setTimeout(() => {
      // Risk completes next
      setCurrentAnalysis(prev => ({
        ...prev,
        progress: {
          ...prev.progress,
          risk: { status: 'completed', time: 'Processing...' }
        }
      }));
    }, 4500);

    setTimeout(() => {
      // Evidence completes last (slowest), Chairman starts
      setCurrentAnalysis(prev => ({
        ...prev,
        progress: {
          ...prev.progress,
          evidence: { status: 'completed', time: 'Processing...' },
          chairman: { status: 'processing', time: null }
        }
      }));
    }, 5500);
  }, []);

  const contextValue = useMemo(() => ({
    currentAnalysis,
    updateAnalysis,
    clearAnalysis,
    startNewAnalysis
  }), [currentAnalysis, updateAnalysis, clearAnalysis, startNewAnalysis]);

  return (
    <AnalysisContext.Provider value={contextValue}>
      {children}
    </AnalysisContext.Provider>
  );
};