# Oprina - AI Agent System

Conversational AI system for Gmail and Calendar management using Google's Agent Development Kit (ADK).

## 🧠 Agent Architecture

```
Root Agent (oprina)
├── Email Agent → Gmail Tools
└── Calendar Agent → Calendar Tools
```

### Root Agent
The `root_agent` coordinates between specialized sub-agents to handle complex user requests involving both email and calendar operations.

### Sub-Agents
- **Email Agent** - Specialized for Gmail operations (read, send, organize, analyze)
- **Calendar Agent** - Specialized for Google Calendar operations (create, update, delete events)

### Capabilities
- **Text-to-Text** - Conversational text-based interaction
- **Context Awareness** - Maintains conversation context across agents
- **Cross-Agent Coordination** - Seamlessly handles tasks requiring both email and calendar

## 📁 Folder Structure

```
oprina/
├── agent.py                    # Root agent configuration
├── prompt.py                   # Agent instructions and prompts
├── setup_gmail.py             # Gmail setup utility
├── setup_calendar.py          # Calendar setup utility
├── sub_agents/                # Specialized agents
│   ├── email/                 # Email agent
│   └── calendar/              # Calendar agent
├── tools/                     # Tool implementations
│   ├── gmail.py              # Gmail API operations
│   ├── calendar.py           # Calendar API operations
│   └── workflows.py          # Cross-agent workflows
├── common/                    # Shared utilities
├── services/                  # Supporting services
├── tests/                     # Testing framework
└── eval/                      # Agent evaluation
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud project with ADK access
- Gmail and Calendar API credentials
- Configured `.env` file in project root

### Local Testing

```bash
# From project root directory
source venv/bin/activate

# Start ADK web interface
adk web
```

Access the interface at `http://localhost:8080` and test commands:
- "Check my recent emails"
- "What's on my calendar today?"
- "Send an email to john@example.com about our meeting"

### Production Deployment

```bash
# Deploy to Vertex AI
python -m vertex-deployment.deploy --create
```

## 🛠️ Tool System

### Gmail Tools
- Email listing and search
- Send, reply, and manage emails
- AI-powered email generation and analysis

### Calendar Tools
- Event management (create, update, delete)
- Schedule checking and availability
- Meeting coordination

### Cross-Agent Workflows
- Meeting coordination with email invitations
- Email-to-calendar integration
- Multi-step workflows combining both services

## 🧪 Testing Framework

### Test Categories

**Unit Tests** (`tests/unit/`)
- Gmail tool function testing with mocked API calls
- Calendar tool function testing with mocked API calls
- Input validation and error handling

**Evaluation Tests** (`eval/`)
- Comprehensive agent evaluation runner
- Test scenario data files for different workflows
- Performance benchmarking and quality assurance

### Running Tests

```bash
# All unit tests
cd oprina
python -m pytest tests/

# Specific test categories
python -m pytest tests/unit/test_gmail_tools.py -v      # Gmail tools only
python -m pytest tests/unit/test_calendar_tools.py -v   # Calendar tools only

# Evaluation tests
python -m pytest eval/test_eval.py                      # Full evaluation

# Specific test markers
python -m pytest -m gmail               # Gmail-related tests
python -m pytest -m calendar            # Calendar-related tests
python -m pytest -m agents              # Agent behavior tests
```

## 🔧 Development

### Adding New Tools

1. **Create tool function** in appropriate tools file:
```python
def new_gmail_feature(param1: str, tool_context=None) -> str:
    """New Gmail functionality."""
    # Implementation
    result = perform_operation(param1)
    return result
```

2. **Add to agent tools list**:
```python
# In sub_agents/email/agent.py
from oprina.tools.gmail import new_gmail_feature

email_agent = Agent(
    tools=[
        # existing tools...
        new_gmail_feature,
    ]
)
```

3. **Add tests**:
```python
# Add to tests/unit/test_gmail_tools.py
def test_new_gmail_feature():
    result = new_gmail_feature("test_param", mock_context)
    assert result == expected_result
```

### Agent Configuration

Each sub-agent imports its tools directly:

```python
# Email Agent
from oprina.tools.gmail import GMAIL_TOOLS

# Calendar Agent  
from oprina.tools.calendar import CALENDAR_TOOLS
```

The root agent coordinates between sub-agents without needing to know tool details.

## 🚨 Troubleshooting

### Common Issues

**Agent Not Loading**
```bash
# Check agent import
python -c "from oprina.agent import root_agent; print(root_agent.name)"

# Verify sub-agent loading
python -c "from oprina.sub_agents.email.agent import email_agent; print(len(email_agent.tools))"
```

**OAuth Errors**
```bash
# Check credentials files (local development)
ls oprina/*.pickle

# Run setup scripts if needed
python oprina/setup_gmail.py
python oprina/setup_calendar.py
```

**ADK Issues**
```bash
# Reinstall ADK
pip install --upgrade google-cloud-aiplatform[adk]

# Check ADK version
python -c "import google.adk; print('ADK available')"
```

**Environment Issues**
```bash
# Check required environment variables
echo $GOOGLE_CLOUD_PROJECT
echo $GOOGLE_CLOUD_LOCATION

# Verify authentication
gcloud auth application-default login
```

### Setup Process

1. **Gmail Setup**: Run `python oprina/setup_gmail.py` for Gmail authentication
2. **Calendar Setup**: Run `python oprina/setup_calendar.py` for Calendar authentication  
3. **Verify Setup**: Test with `adk web` to ensure agents can access both services
4. **Deploy**: Use `python -m vertex-deployment.deploy --create` for production

For deployment configuration and advanced usage, see the [vertex-deployment](../vertex-deployment/) folder documentation.