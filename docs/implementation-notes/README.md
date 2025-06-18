# Oprina - Voice-Powered Gmail Assistant

Oprina is an AI-powered voice assistant that allows users to manage their Gmail inbox using natural spoken language. It features an animated avatar with lip-sync capabilities and provides a seamless hands-free email experience.

## 🎯 Project Overview

- **Voice-First Interface**: Interact with Gmail using natural speech
- **Animated Avatar**: Real-time lip-sync and visual feedback
- **Multi-Agent Architecture**: Specialized AI agents for different tasks
- **Gmail Integration**: Secure OAuth-based Gmail API access
- **Chat Interface**: Visual conversation history

## 🏗️ Architecture

```
Voice Agent (Root) → Coordinator Agent → [Email Agent, Content Agent]
```

- **Voice Agent**: Handles STT/TTS and avatar animation
- **Coordinator Agent**: Orchestrates task routing and workflow
- **Email Agent**: Manages Gmail API operations via MCP
- **Content Agent**: Processes email content and generates responses

## 🚀 Quick Start

### Prerequisites

- Python 3.9+
- Node.js 18+
- Redis server
- Google Cloud account with Speech-to-Text and Text-to-Speech APIs
- Firebase project
- Gmail API credentials

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd {project_name}
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and configuration
```

4. Start Redis server:
```bash
redis-server
```

5. Run the development setup:
```bash
python scripts/setup_env.py
```

6. Start the backend:
```bash
python -m agents.voice  # Start voice agent
python backend/main.py  # Start FastAPI backend
```

7. Start the frontend (Bolt.new):
```bash
cd app
# Follow Bolt.new setup instructions
```

## 📁 Project Structure

```
{project_name}/
├── agents/          # AI Agents (Voice, Coordinator, Email, Content)
├── app/            # Frontend (Bolt.new)
├── backend/        # FastAPI Backend
├── memory/         # Memory Management
├── mcp/           # Model Context Protocol for Gmail
├── services/      # External Services Integration
├── config/        # Configuration Management
└── tests/         # Testing Suite
```


## 📚 Documentation

- [Architecture Documentation](docs/architecture.md)
- [API Documentation](docs/api.md)
- [Setup Guide](docs/setup.md)


## 📄 License

This project is licensed under the MIT License.

## 👥 Team

- Bharath Kumar (@abharathkumarr)
- Hieu Hoang Calvin (@calvinhoang203)
- Rohith Reddy Mandala (@rohith4444)
"""