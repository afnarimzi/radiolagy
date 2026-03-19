# Medical AI Frontend

A modern React-based frontend for the Multi-Agent Medical AI System, featuring real-time analysis monitoring, comprehensive analytics, and an intuitive user interface.

## 🚀 Features

### Core Functionality
- **Medical Image Analysis**: Upload and analyze X-ray images using AI agents
- **Real-time Monitoring**: Live progress tracking with detailed agent status
- **Comprehensive Results**: Detailed analysis results from all 5 AI agents
- **Analysis History**: Complete history with search and filtering capabilities
- **System Analytics**: Performance metrics and trend analysis

### UI Components
- **Responsive Design**: Mobile-first approach with Tailwind CSS
- **Interactive Charts**: Real-time analytics using Recharts
- **Live Updates**: WebSocket-like polling for real-time data
- **Error Handling**: Comprehensive error boundaries and user feedback
- **Loading States**: Smooth loading experiences with skeletons

### Advanced Features
- **Live Analysis Monitor**: Real-time pipeline monitoring with logs
- **System Metrics**: CPU, memory, and performance monitoring
- **Settings Management**: Comprehensive system configuration
- **Multi-theme Support**: Light/dark theme switching
- **Accessibility**: WCAG-compliant components

## 🏗️ Architecture

### Component Structure
```
src/
├── components/           # Reusable UI components
│   ├── AgentStatusCard.js       # Individual agent status display
│   ├── AnalysisProgress.js      # Pipeline progress visualization
│   ├── AnalysisResults.js       # Comprehensive results display
│   ├── AnalyticsChart.js        # Interactive data visualization
│   ├── ErrorBoundary.js         # Error handling wrapper
│   ├── Header.js                # Navigation header
│   ├── LiveAnalysisMonitor.js   # Real-time monitoring
│   ├── LoadingSpinner.js        # Loading states
│   └── SystemMetrics.js         # System performance metrics
├── pages/                # Main application pages
│   ├── About.js                 # System information
│   ├── Analysis.js              # Image upload and analysis
│   ├── Dashboard.js             # Main overview page
│   ├── History.js               # Analysis history
│   └── Settings.js              # System configuration
└── App.js                # Main application component
```

### State Management
- **Local State**: React hooks for component-level state
- **API Integration**: RESTful API calls with error handling
- **Real-time Updates**: Polling-based live data updates
- **Caching**: Intelligent data caching for performance

## 🎨 Design System

### Color Palette
- **Medical Blue**: Primary brand color (`medical-*`)
- **Success Green**: Positive states (`success-*`)
- **Warning Orange**: Caution states (`warning-*`)
- **Danger Red**: Error states (`danger-*`)

### Typography
- **Font**: Inter font family for modern readability
- **Hierarchy**: Consistent heading and body text scales
- **Accessibility**: High contrast ratios and readable sizes

### Components
- **Cards**: Consistent container styling with shadows
- **Buttons**: Primary, secondary, and utility button styles
- **Forms**: Accessible form controls with validation states
- **Status Badges**: Color-coded status indicators

## 📊 Analytics & Monitoring

### Real-time Metrics
- **Agent Performance**: Individual agent processing times
- **System Health**: CPU, memory, and response time monitoring
- **Analysis Volume**: Success/failure rates and throughput
- **Error Tracking**: Comprehensive error logging and reporting

### Visualization Types
- **Line Charts**: Performance trends over time
- **Bar Charts**: Volume and accuracy comparisons
- **Pie Charts**: Distribution analysis
- **Progress Bars**: Real-time processing status

## 🔧 Configuration

### Environment Variables
```bash
REACT_APP_API_URL=http://localhost:8000
REACT_APP_WS_URL=ws://localhost:8000/ws
REACT_APP_VERSION=1.0.0
```

### Build Configuration
- **Development**: Hot reloading with React Scripts
- **Production**: Optimized builds with code splitting
- **Proxy**: API proxy configuration for development

## 🚦 Getting Started

### Prerequisites
- Node.js 16+ and npm/yarn
- Backend API running on port 8000

### Installation
```bash
# Install dependencies
npm install

# Start development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

### Development Workflow
1. **Component Development**: Create reusable components in `/components`
2. **Page Development**: Build full pages in `/pages`
3. **Styling**: Use Tailwind CSS classes and custom components
4. **Testing**: Write tests for critical functionality
5. **Integration**: Connect with backend API endpoints

## 📱 Responsive Design

### Breakpoints
- **Mobile**: 320px - 768px
- **Tablet**: 768px - 1024px
- **Desktop**: 1024px+

### Mobile Optimizations
- Touch-friendly interface elements
- Optimized image loading and display
- Responsive navigation and layouts
- Performance optimizations for mobile networks

## 🔒 Security Features

### Data Protection
- **Input Validation**: Client-side validation for all forms
- **XSS Prevention**: Sanitized user inputs and outputs
- **CSRF Protection**: Token-based request validation
- **Secure Headers**: Content Security Policy implementation

### Privacy Compliance
- **HIPAA Considerations**: Medical data handling best practices
- **Data Minimization**: Only collect necessary information
- **Audit Logging**: Track user actions and system events

## 🧪 Testing Strategy

### Test Types
- **Unit Tests**: Component and utility function testing
- **Integration Tests**: API integration and user flows
- **E2E Tests**: Complete user journey testing
- **Accessibility Tests**: WCAG compliance validation

### Testing Tools
- **Jest**: Unit and integration testing framework
- **React Testing Library**: Component testing utilities
- **Cypress**: End-to-end testing (optional)

## 🚀 Deployment

### Production Build
```bash
# Create optimized production build
npm run build

# Serve static files
npx serve -s build
```

### Docker Deployment
```dockerfile
FROM node:16-alpine
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production
COPY . .
RUN npm run build
EXPOSE 3000
CMD ["npx", "serve", "-s", "build"]
```

### Performance Optimizations
- **Code Splitting**: Lazy loading for route components
- **Image Optimization**: WebP format and responsive images
- **Caching**: Service worker for offline functionality
- **Bundle Analysis**: Webpack bundle analyzer integration

## 🔄 API Integration

### Endpoints
- `POST /upload-complete-pipeline-with-chairman` - Start analysis
- `GET /analysis-status/{caseId}` - Get analysis progress
- `GET /cases` - Retrieve analysis history
- `GET /system-metrics` - System performance data
- `GET /analytics/{type}` - Analytics data

### Error Handling
- **Network Errors**: Retry logic and user feedback
- **API Errors**: Structured error responses and logging
- **Validation Errors**: Form validation and field-level errors

## 🎯 Future Enhancements

### Planned Features
- **WebSocket Integration**: True real-time updates
- **Advanced Analytics**: Machine learning insights
- **Multi-language Support**: Internationalization
- **Offline Mode**: Progressive Web App capabilities
- **Advanced Filtering**: Complex search and filter options

### Performance Improvements
- **Virtual Scrolling**: Large dataset handling
- **Image Lazy Loading**: Optimized image rendering
- **State Management**: Redux or Zustand integration
- **Caching Strategy**: Advanced caching mechanisms

## 📚 Documentation

### Component Documentation
Each component includes:
- **Props Interface**: TypeScript-style prop definitions
- **Usage Examples**: Code examples and best practices
- **Accessibility Notes**: ARIA labels and keyboard navigation
- **Performance Considerations**: Optimization tips

### API Documentation
- **OpenAPI Specification**: Complete API documentation
- **Request/Response Examples**: Sample data structures
- **Error Codes**: Comprehensive error handling guide

## 🤝 Contributing

### Development Guidelines
1. **Code Style**: Follow ESLint and Prettier configurations
2. **Component Design**: Reusable, accessible, and performant
3. **Testing**: Write tests for new features and bug fixes
4. **Documentation**: Update README and component docs
5. **Performance**: Consider bundle size and runtime performance

### Pull Request Process
1. Fork the repository and create a feature branch
2. Implement changes with appropriate tests
3. Update documentation as needed
4. Submit pull request with detailed description
5. Address review feedback and merge when approved

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For technical support or questions:
- **Issues**: GitHub Issues for bug reports and feature requests
- **Documentation**: Comprehensive guides and API documentation
- **Community**: Discord/Slack channels for real-time support

---

Built with ❤️ using React, Tailwind CSS, and modern web technologies.