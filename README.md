# DocXP - AI-Powered Documentation Generation Platform

A premium enterprise-grade documentation generation system that automatically creates comprehensive documentation for legacy codebases using AI.

## 🚀 Features

### Core Capabilities
- **Multi-Language Support**: Python, Java, JavaScript, TypeScript, Perl, and more
- **AI-Powered Analysis**: Business rule extraction using AWS Bedrock
- **Incremental Updates**: Git-based change detection for efficient updates
- **Enterprise UI**: Premium Angular 17 + PrimeNG interface
- **Real-time Processing**: Async job processing with status tracking
- **Comprehensive Output**: Markdown docs, Mermaid diagrams, API documentation

### Key Components
- **Code Parser Engine**: AST-based parsing for accurate code analysis
- **Business Rule Extraction**: AI-driven identification of business logic
- **Documentation Generator**: Structured markdown with cross-references
- **Visualization**: Auto-generated architecture and flow diagrams
- **Analytics Dashboard**: Track documentation metrics and trends

## 📋 Prerequisites

- Python 3.10+
- Node.js 18+ and npm
- AWS Account with Bedrock access
- Git

## 🛠️ Installation

### 1. Clone the Repository
```bash
cd C:\devl\workspaces\docxp
```

### 2. Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment
Create a `.env` file in the backend directory:
```env
AWS_ACCESS_KEY_ID=your_aws_access_key
AWS_SECRET_ACCESS_KEY=your_aws_secret_key
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=anthropic.claude-v2
```

### 4. Frontend Setup

```bash
cd ../frontend

# Install dependencies
npm install

# Install Angular CLI globally if needed
npm install -g @angular/cli
```

## 🚀 Running the Application

### Start Backend Server
```bash
cd backend
python main.py
```
The API will be available at `http://localhost:8000`

### Start Frontend Development Server
```bash
cd frontend
ng serve
```
The UI will be available at `http://localhost:4200`

## 📖 Usage Guide

### 1. Initial Setup
- Open the application at `http://localhost:4200`
- Configure your AWS credentials in Settings
- Set up default documentation templates

### 2. Generate Documentation
1. Click "Generate Documentation" on the dashboard
2. Select or enter repository path
3. Configure documentation options:
   - Documentation depth (minimal/standard/comprehensive/exhaustive)
   - Include diagrams
   - Extract business rules
   - Focus areas (classes, functions, APIs, etc.)
4. Click "Generate" to start the process
5. Monitor progress in real-time
6. View and download generated documentation

### 3. Incremental Updates
- Enable "Incremental Update" for existing repositories
- System will analyze only changed files
- Maintains documentation consistency

## 🏗️ Project Structure

```
docxp/
├── backend/
│   ├── app/
│   │   ├── api/           # API endpoints
│   │   ├── core/          # Core configuration
│   │   ├── models/        # Data models
│   │   ├── services/      # Business logic
│   │   ├── parsers/       # Language parsers
│   │   └── agents/        # Strands agents
│   ├── main.py            # FastAPI application
│   └── requirements.txt   # Python dependencies
│
├── frontend/
│   ├── src/
│   │   ├── app/
│   │   │   ├── components/    # Angular components
│   │   │   ├── services/      # Angular services
│   │   │   └── models/        # TypeScript models
│   │   ├── assets/            # Static assets
│   │   └── styles.scss        # Global styles
│   ├── package.json           # Node dependencies
│   └── angular.json           # Angular configuration
│
└── output/                    # Generated documentation
```

## 🔧 Configuration Options

### Documentation Depth Levels
- **Minimal**: Basic structure and API documentation
- **Standard**: Includes business rules and key components
- **Comprehensive**: Detailed analysis with diagrams
- **Exhaustive**: Complete documentation with all details

### Focus Areas
- Classes and Objects
- Functions and Methods
- APIs and Endpoints
- Database Schemas
- Security Patterns
- Configuration Files

## 📊 API Endpoints

### Documentation Generation
- `POST /api/documentation/generate` - Start documentation generation
- `GET /api/documentation/status/{job_id}` - Check job status
- `GET /api/documentation/jobs` - List all jobs

### Repository Management
- `GET /api/repositories` - List analyzed repositories
- `POST /api/repositories/validate` - Validate repository

### Analytics
- `GET /api/analytics/metrics` - Get platform metrics
- `GET /api/analytics/trends` - Get documentation trends

## 🎨 UI Features

### Dashboard
- Real-time metrics display
- Recent job status
- Documentation trends chart
- Quick action buttons

### Generation Interface
- Visual repository validation
- Configuration wizard
- Real-time progress tracking
- Preview generated documentation

### Analytics
- Historical trends
- Success rate metrics
- Language distribution
- Complexity analysis

## 🚦 Development

### Running Tests
```bash
# Backend tests
cd backend
pytest

# Frontend tests
cd frontend
ng test
```

### Building for Production
```bash
# Backend
cd backend
# Configure production settings in .env

# Frontend
cd frontend
ng build --configuration production
```

## 📝 Next Steps

### Phase 1: MVP Enhancements
- [ ] Add more language parsers
- [ ] Implement caching for faster processing
- [ ] Add export to PDF functionality
- [ ] Integrate with GitHub/GitLab

### Phase 2: Knowledge Repository
- [ ] Implement centralized storage
- [ ] Add semantic search
- [ ] Create knowledge graph
- [ ] Build conversational interface

### Phase 3: Enterprise Features
- [ ] Add authentication/authorization
- [ ] Implement team collaboration
- [ ] Create CI/CD integration
- [ ] Add custom templates

## 🤝 Contributing

Please follow these steps:
1. Create a feature branch
2. Make your changes
3. Write/update tests
4. Submit a pull request

## 📄 License

Proprietary - For internal use only

## 💡 Tips

1. **Performance**: For large repositories, use incremental updates
2. **Accuracy**: Higher documentation depth = more processing time
3. **Business Rules**: Review AI-extracted rules for accuracy
4. **Diagrams**: Mermaid diagrams can be edited after generation

## 🆘 Troubleshooting

### Common Issues

**AWS Bedrock Connection Failed**
- Verify AWS credentials in .env
- Ensure Bedrock is enabled in your AWS region
- Check IAM permissions

**Parser Errors**
- Ensure code files are valid syntax
- Check supported language versions
- Review error logs in `backend/logs/`

**Frontend Build Issues**
- Clear npm cache: `npm cache clean --force`
- Delete node_modules and reinstall
- Ensure Angular CLI version matches

## 📞 Support

For issues or questions:
- Check documentation in `/docs`
- Review logs in `backend/logs/`
- Contact the AI Tools team

---

**DocXP** - Transforming Legacy Code into Living Documentation
