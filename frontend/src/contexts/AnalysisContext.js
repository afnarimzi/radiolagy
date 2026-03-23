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