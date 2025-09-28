#!/bin/bash

echo "🚀 Starting AgentX Travel India Setup..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8+ first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed. Please install Node.js 18+ first."
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "❌ npm is not installed. Please install npm first."
    exit 1
fi

echo "✅ Prerequisites check passed!"

# Create virtual environment for Python
echo "🐍 Setting up Python virtual environment..."
cd backend
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Please create one based on env.template"
    echo "   Required: GEMINI_API_KEY"
    echo "   Copy env.template to .env and add your API keys"
fi

cd ..

# Install Node.js dependencies
echo "📦 Installing Node.js dependencies..."
cd frontend
npm install

# Check if .env.local file exists
if [ ! -f .env.local ]; then
    echo "⚠️  .env.local file not found. Please create one based on env.template"
    echo "   Copy env.template to .env.local and configure as needed"
fi

cd ..

echo ""
echo "🎉 Setup complete! Next steps:"
echo ""
echo "1. Configure environment variables:"
echo "   - Backend: Copy backend/env.template to backend/.env"
echo "   - Frontend: Copy frontend/env.template to frontend/.env.local"
echo ""
echo "2. Add your Google Gemini API key to backend/.env"
echo ""
echo "3. Start the services:"
echo "   - Backend: cd backend && source venv/bin/activate && python main.py"
echo "   - Frontend: cd frontend && npm run dev"
echo ""
echo "4. Open http://localhost:3000 in your browser"
echo ""
echo "📚 See SETUP_GUIDE.md for detailed instructions"
