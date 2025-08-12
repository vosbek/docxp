# DocXP Quick Setup Guide

## 🚀 Quick Start (Windows)

1. **Configure AWS Credentials**
   ```
   cd backend
   copy .env.template .env
   ```
   Edit `.env` with your AWS credentials

2. **Run the Application**
   ```
   start.bat
   ```

3. **Access DocXP**
   - Open browser to http://localhost:4200
   - Backend API at http://localhost:8000

## 🐧 Quick Start (Linux/Mac)

1. **Configure AWS Credentials**
   ```bash
   cd backend
   cp .env.template .env
   nano .env  # Edit with your AWS credentials
   ```

2. **Make script executable and run**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

3. **Access DocXP**
   - Open browser to http://localhost:4200
   - Backend API at http://localhost:8000

## ⚙️ Manual Setup

### Backend
```bash
cd backend
python -m venv venv
# Windows: venv\Scripts\activate
# Linux/Mac: source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend
npm install
ng serve
```

## 🔧 Configuration

1. **AWS Bedrock Access**
   - Ensure your AWS account has Bedrock access enabled
   - Configure region in `.env` file
   - Set appropriate IAM permissions

2. **First Repository Analysis**
   - Click "Generate Documentation" on dashboard
   - Enter repository path (e.g., `C:\projects\my-repo`)
   - Select documentation options
   - Click "Generate"

## 📝 Testing Without AWS

The application includes mock data for development. If AWS Bedrock is not configured:
- Business rules extraction will return sample data
- Documentation generation will use placeholder content
- All other features work normally

## 🆘 Troubleshooting

### Backend won't start
- Check Python version: `python --version` (needs 3.10+)
- Verify virtual environment is activated
- Check `.env` file exists

### Frontend won't start
- Check Node version: `node --version` (needs 18+)
- Clear npm cache: `npm cache clean --force`
- Reinstall: `rm -rf node_modules && npm install`

### AWS Bedrock errors
- Verify AWS credentials in `.env`
- Check Bedrock is available in your region
- Ensure IAM user has `bedrock:InvokeModel` permission

## 📚 Next Steps

1. **Generate Your First Documentation**
   - Select a repository
   - Choose "comprehensive" depth for best results
   - Enable business rules extraction
   - Review generated markdown files

2. **Configure Templates**
   - Go to Settings
   - Create custom templates for different project types
   - Save frequently used configurations

3. **View Analytics**
   - Monitor documentation generation metrics
   - Track processing times
   - Analyze language distributions

## 🔗 Useful Links

- API Documentation: http://localhost:8000/docs
- Frontend: http://localhost:4200
- Output Directory: `backend/output/`

## 💡 Tips

- Start with smaller repositories for testing
- Use "incremental update" for existing documentation
- Higher depth levels = more processing time
- Review AI-extracted business rules for accuracy

---

For detailed documentation, see README.md
