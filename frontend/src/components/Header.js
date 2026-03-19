import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Activity, Brain, History } from 'lucide-react';

const Header = () => {
  const location = useLocation();

  const navigation = [
    { name: 'Dashboard', href: '/', icon: Activity },
    { name: 'Analysis', href: '/analysis', icon: Brain },
    { name: 'History', href: '/history', icon: History },
  ];

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="container mx-auto px-4">
        <div className="flex justify-between items-center h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 bg-medical-600 rounded-lg flex items-center justify-center">
              <Activity className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-gray-900">Radiology Assistant</h1>
              <p className="text-xs text-gray-500">AI-Powered X-ray Analysis</p>
            </div>
          </div>

          {/* Navigation */}
          <nav className="flex space-x-1">
            {navigation.map((item) => {
              const Icon = item.icon;
              const isActive = location.pathname === item.href;
              
              return (
                <Link
                  key={item.name}
                  to={item.href}
                  className={`flex items-center space-x-2 px-4 py-2 rounded-lg text-sm font-medium transition-colors duration-200 ${
                    isActive
                      ? 'bg-medical-100 text-medical-700'
                      : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
                  }`}
                >
                  <Icon className="w-4 h-4" />
                  <span>{item.name}</span>
                </Link>
              );
            })}
          </nav>

          {/* Status Indicator */}
          <div className="flex items-center space-x-2">
            <div className="w-2 h-2 bg-success-500 rounded-full animate-pulse"></div>
            <span className="text-sm text-gray-600">System Online</span>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;