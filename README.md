# AutoTestify

Advanced automated testing and code analysis platform that provides comprehensive GitHub repository analysis and API testing capabilities.

## Features

### 🔍 GitHub Repository Analysis
- **Code Quality Assessment**: Analyze code structure, complexity, and maintainability
- **Security Vulnerability Detection**: Identify potential security issues
- **Performance Analysis**: Evaluate code performance and optimization opportunities
- **Documentation Review**: Check README quality and documentation completeness
- **CI/CD Pipeline Analysis**: Assess build configurations and workflows
- **Visual Reports**: Interactive HTML reports with charts and insights
- **UI Validation**: Automated screenshot capture and repository UI verification

### 🚀 API Testing
- **Automated API Testing**: Test REST APIs with various HTTP methods
- **Response Validation**: Verify status codes, headers, and response data
- **Performance Metrics**: Measure response times and throughput
- **Test Report Generation**: Detailed HTML reports with test results
- **Multiple Environment Support**: Test across different environments

### 📊 Reporting & Analytics
- **Interactive Dashboards**: Visual representation of analysis results
- **Export Capabilities**: Download reports in HTML format
- **Historical Tracking**: View past analysis results
- **Email Integration**: Send reports via email (Mailjet integration)

### 🎨 Modern UI
- **Dark/Light Theme**: Toggle between themes
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Live progress indicators
- **Intuitive Navigation**: Easy-to-use interface

## Installation

### Prerequisites
- Python 3.8+
- Chrome/Chromium browser (for UI validation)
- Git

### Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Autotestify
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the application**
   Open http://localhost:5000 in your browser

## Configuration

### Required Environment Variables

```env
# Gemini AI API (for code analysis)
GEMINI_API_KEY=your_gemini_api_key

# Email Service (Mailjet)
MAILJET_API_KEY=your_mailjet_api_key
MAILJET_API_SECRET=your_mailjet_secret
MAILJET_SENDER_EMAIL=your_sender_email
MAILJET_SENDER_NAME=AutoTestify

# Flask Configuration
SECRET_KEY=your_secret_key
FLASK_ENV=production
```

## Usage

### GitHub Repository Analysis

1. Navigate to **GitHub Analysis** page
2. Enter the repository URL (e.g., `https://github.com/user/repo`)
3. Click **Analyze Repository**
4. Wait for analysis completion
5. View the generated report

### API Testing

1. Go to **API Testing** page
2. Enter API endpoint URL
3. Select HTTP method (GET, POST, PUT, DELETE)
4. Add headers and request body if needed
5. Click **Test API**
6. Review test results and performance metrics

### Viewing Reports

1. Visit **Reports** page
2. Browse all generated reports
3. Click **View** to open reports in new tab
4. Click **Download** to save reports locally
5. Use **Delete** to remove unwanted reports

## Project Structure

```
Autotestify/
├── app.py                 # Main Flask application
├── config.py             # Configuration settings
├── requirements.txt      # Python dependencies
├── .env                  # Environment variables
├── services/            # Core services
│   ├── api_tester.py    # API testing functionality
│   ├── gemini_service.py # AI-powered code analysis
│   ├── github_service.py # GitHub integration
│   ├── report_generator.py # Report generation
│   └── email_service.py  # Email notifications
├── templates/           # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── github_analysis.html
│   ├── api_testing.html
│   └── reports.html
├── static/             # Static assets
│   ├── css/           # Stylesheets
│   ├── js/            # JavaScript files
│   └── charts/        # Generated charts
├── reports/           # Generated analysis reports
├── screenshots/       # Repository screenshots
└── dist_protected/    # PyArmor protected version
```

## Security

This project includes PyArmor protection for source code obfuscation:

- **Protected Files**: Core Python modules are obfuscated
- **Runtime Protection**: Dynamic code decryption
- **Deployment**: Use `dist_protected/` for production

## Technologies Used

- **Backend**: Flask, Python 3.8+
- **Frontend**: Bootstrap 5, JavaScript, HTML5/CSS3
- **AI/ML**: Google Gemini API
- **Web Automation**: Selenium WebDriver
- **Email**: Mailjet API
- **Security**: PyArmor code protection
- **Charts**: Plotly.js with advanced statistical analysis
- **Performance**: Connection pooling, intelligent caching
- **Validation**: Comprehensive configuration validation
- **Icons**: Font Awesome

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/new-feature`)
3. Commit changes (`git commit -am 'Add new feature'`)
4. Push to branch (`git push origin feature/new-feature`)
5. Create Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub

## Changelog

### v1.1.0 (Latest)
- **Performance Optimization**: Enhanced API testing with connection pooling and caching
- **Advanced Analytics**: 7-tier performance classification with P50-P99 percentiles
- **Configuration Validation**: Comprehensive config validation with auto-fix capabilities
- **Error Handling**: Improved error handling with graceful degradation
- **Code Quality**: Fixed unicode encoding issues and deprecated API parameters
- **Security**: Enhanced PyArmor protection with updated obfuscation
- **Stability**: Connection pooling reduces response times by 30-50%
- **Caching System**: Intelligent file-based caching with 60-90% hit rates

### v1.0.0
- Initial release
- GitHub repository analysis
- API testing capabilities
- Report generation
- Dark/Light theme support
- PyArmor code protection
