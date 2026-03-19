import React, { createContext, useContext, useState } from 'react';

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

  const updateAnalysis = (updates) => {
    setCurrentAnalysis(prev => ({ ...prev, ...updates }));
  };

  const clearAnalysis = () => {
    setCurrentAnalysis({
      results: null,
      progress: {},
      isAnalyzing: false,
      selectedFile: null,
      patientCode: '',
      additionalInfo: '',
      patientHistory: ''
    });
  };

  const startNewAnalysis = () => {
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
  };

  return (
    <AnalysisContext.Provider value={{
      currentAnalysis,
      updateAnalysis,
      clearAnalysis,
      startNewAnalysis
    }}>
      {children}
    </AnalysisContext.Provider>
  );
};