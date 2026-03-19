import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import ErrorBoundary from './components/ErrorBoundary';
import { AnalysisProvider } from './contexts/AnalysisContext';
import Header from './components/Header';
import Dashboard from './pages/Dashboard';
import Analysis from './pages/Analysis';
import History from './pages/History';

function App() {
  return (
    <ErrorBoundary>
      <AnalysisProvider>
        <Router>
          <div className="min-h-screen bg-gray-50">
            <Header />
            <main className="container mx-auto px-4 py-8">
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/analysis" element={<Analysis />} />
                <Route path="/history" element={<History />} />
              </Routes>
            </main>
          </div>
        </Router>
      </AnalysisProvider>
    </ErrorBoundary>
  );
}

export default App;