# Oprina - AI Agent System

Multi-agent conversational AI system for Gmail and Calendar management using Google's Agent Development Kit (ADK).

## 🧠 Agent Architecture

### Root Agent
The `root_agent` coordinates between specialized sub-agents to handle complex user requests involving both email and calendar operations.

### Sub-Agents
- **Email Agent** - Specialized for Gmail operations (read, send, organize, analyze)
- **Calendar Agent** - Specialized for Google Calendar operations (create, update, delete events)

### Multi-Modal Capabilities
- **Voice Input** - Speech-to-text processing
- **Voice Output** - Text-to-speech responses
- **Text Chat** - Traditional text-based interaction
- **Context Awareness** - Maintains conversation context across agents

## 📁 Folder Structure

```
oprina/
├── agent.py                     # Root agent configuration
├── prompt.py                    # Agent instructions and prompts
├── __init__.py                  # Package initialization
├── credentials.json             # Google API credentials (local)
├── gmail_token.pickle           # Gmail OAuth token (local)
├── calendar_token.pickle        # Calendar OAuth token (local)
├── setup_gmail.py              # Gmail setup utility
├── setup_calendar.py           # Calendar setup utility
├── sub_agents/
│   ├── __init__.py             # Agent exports
│   ├── email/
│   │   ├── __init__.py
│   │   ├── agent.py            # Email specialist agent
│   │   └── prompt.py           # Email agent instructions
│   └── calendar/
│       ├── __init__.py
│       ├── agent.py            # Calendar specialist agent
│       └── prompt.py           # Calendar agent instructions
├── tools/                      # Local development tools
│   ├── __init__.py
│   ├── auth_utils.py          # OAuth authentication
│   ├── gmail.py               # Gmail API operations
│   ├── calendar.py            # Calendar API operations
│   └── workflows.py           # Cross-agent workflows
├── tools_prod/                # Production tools (database-integrated)
│   ├── __init__.py
│   ├── auth_utils.py          # Production OAuth with database
│   ├── gmail.py               # Gmail tools for production
│   └── calendar.py            # Calendar tools for production
├── common/
│   ├── __init__.py
│   ├── utils.py               # Shared utilities
│   └── session_keys.py        # Session state constants
├── services/
│   ├── __init__.py
│   └── logging/
│       ├── __init__.py
│       ├── logger.py          # Custom logging
│       └── log_server.py      # Log server utility
├── tests/                     # Testing framework
│   ├── README.md              # Testing documentation
│   ├── pytest.ini            # Test configuration
│   └── unit/                  # Unit tests
│       ├── test_calendar_tools.py
│       └── test_gmail_tools.py
└── eval/                      # Agent evaluation
    ├── test_eval.py           # Evaluation runner
    └── data/                  # Test scenarios
        ├── email_workflows.test.json
        ├── calendar_workflows.test.json
        ├── cross_agent_workflows.test.json
        └── test_config.json
```

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Google Cloud project with ADK access
- Gmail and Calendar API credentials
- Configured `.env` file in project root

### Local Testing

```bash
# From project root (oprina_avafg/)
source venv/bin/activate

# Set local mode in .env
OPRINA_TOOLS_MODE=local

# Start ADK web interface
adk web
```

Access the interface at `http://localhost:8080` and test voice commands:
- "Check my recent emails"
- "What's on my calendar today?"
- "Send an email to john@example.com about our meeting"

### Production Deployment

```bash
# Set production mode in .env
OPRINA_TOOLS_MODE=prod

# Deploy to Vertex AI
python -m vertex-deployment.deploy --create
```

## 🛠️ Tool System

### Tool Modes

**Local Mode (`OPRINA_TOOLS_MODE=local`)**
- Uses `oprina/tools/` directory
- OAuth tokens stored as local pickle files
- Single-user development environment
- Ideal for testing and development

**Production Mode (`OPRINA_TOOLS_MODE=prod`)**
- Uses `oprina/tools_prod/` directory
- OAuth tokens stored in Supabase database
- Multi-user production environment
- Session-based user authentication

### Available Tools

#### Gmail Tools (`gmail.py`)
```python
# Email listing and search
gmail_list_messages(query="", max_results=10)
gmail_search_messages(query="from:sender@example.com")

# Email operations
gmail_get_message(message_id)
gmail_send_message(to, subject, body)
gmail_reply_to_message(message_id, reply_text)

# Email management
gmail_mark_as_read(message_ids)
gmail_archive_messages(message_ids)
gmail_delete_messages(message_ids)

# AI-powered features
gmail_generate_email(recipient, purpose, style)
gmail_extract_action_items(email_content)
gmail_analyze_sentiment(email_content)
```

#### Calendar Tools (`calendar.py`)
```python
# Event management
calendar_list_events(start_date, end_date)
calendar_create_event(title, start_time, end_time, attendees)
calendar_update_event(event_id, updates)
calendar_delete_event(event_id)

# Advanced features
calendar_find_available_slots(duration_minutes, date_range)
calendar_check_conflicts(proposed_time, duration)
calendar_get_busy_times(start_date, end_date)
```

#### Cross-Agent Workflows (`workflows.py`)
```python
# Meeting coordination
schedule_meeting_with_invitation(attendee_email, subject, duration)
process_meeting_request_email(email_content)

# Email-to-calendar integration
create_events_from_email_deadlines(email_content)
sync_email_signatures_with_calendar()

# Batch operations
process_multiple_meeting_requests(email_list)
coordinate_availability_across_attendees(attendee_emails, duration)
```

## 🧪 Testing Framework

### Test Categories

**Unit Tests** (`tests/unit/`)
- **`test_gmail_tools.py`** - Gmail tool function testing with mocked API calls
- **`test_calendar_tools.py`** - Calendar tool function testing with mocked API calls
- Input validation and error handling
- Individual tool function verification

**Evaluation Tests** (`eval/`)
- **`test_eval.py`** - Comprehensive agent evaluation runner
- **`data/`** - Test scenario data files:
  - `email_workflows.test.json` - Email operation scenarios
  - `calendar_workflows.test.json` - Calendar operation scenarios  
  - `cross_agent_workflows.test.json` - Multi-agent workflow scenarios
- Performance benchmarking and quality assurance

### Running Tests

```bash
# All unit tests
cd oprina
python -m pytest tests/

# Specific test files
python -m pytest tests/unit/test_gmail_tools.py -v      # Gmail tools only
python -m pytest tests/unit/test_calendar_tools.py -v   # Calendar tools only

# Evaluation tests
python -m pytest eval/test_eval.py                      # Full evaluation

# Specific test markers (defined in pytest.ini)
python -m pytest -m gmail               # Gmail-related tests
python -m pytest -m calendar            # Calendar-related tests
python -m pytest -m agents              # Agent behavior tests
```

### Test Configuration

The `pytest.ini` file configures test discovery and markers:

```ini
# pytest.ini
[tool:pytest]
testpaths = .
python_files = test_*.py
python_classes = Test*
python_functions = test_*

markers =
    gmail: Gmail tool and agent behavior tests
    calendar: Calendar tool and agent behavior tests
    agents: Agent integration and behavior tests
    setup: Setup and authentication tests
    behavior: All agent behavior tests
    tools: All tool function tests
    integration: Integration tests between components
    voice: Voice interface optimization tests
    slow: Slow-running tests
```

## 🔧 Development

### Adding New Tools

1. **Create tool function** in appropriate file:
```python
def new_gmail_feature(param1: str, tool_context=None) -> str:
    """New Gmail functionality."""
    validate_tool_context(tool_context, "new_gmail_feature")
    
    # Implementation
    result = perform_operation(param1)
    
    # Update session state
    tool_context.state["last_operation"] = result
    
    return result
```

2. **Add to agent configuration**:
```python
# In sub_agents/email/agent.py
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

### Session State Management

```python
# Session keys in common/session_keys.py
EMAIL_LAST_SENT = "email_last_sent"
CALENDAR_LAST_EVENT = "calendar_last_event"
USER_PREFERENCES = "user_preferences"

# Usage in tools
def gmail_send_message(to, subject, body, tool_context=None):
    # ... send logic ...
    
    # Update session state
    tool_context.state[EMAIL_LAST_SENT] = {
        "to": to,
        "subject": subject,
        "sent_at": datetime.now()
    }
```

### Cross-Agent Coordination

```python
# Pass data between agents
pass_data_between_agents(
    tool_context,
    from_agent="email_agent",
    to_agent="calendar_agent",
    data={"meeting_details": meeting_info},
    operation="create_calendar_event"
)
```

## 🚨 Troubleshooting

### Common Issues

**Agent Not Loading**
```bash
# Check agent import
python -c "from oprina.agent import root_agent; print(root_agent.name)"

# Verify tool loading
python -c "from oprina.sub_agents.email.agent import email_agent; print(len(email_agent.tools))"
```

**OAuth Errors**
```bash
# Check credentials files (local mode)
ls oprina/*.pickle

# Verify environment variables
echo $GOOGLE_CLIENT_ID
echo $GOOGLE_CLIENT_SECRET
```

**Tool Import Errors**
```bash
# Check tools mode
echo $OPRINA_TOOLS_MODE

# Verify tool directory exists
ls oprina/tools/        # Local mode
ls oprina/tools_prod/   # Production mode
```

**ADK Issues**
```bash
# Reinstall ADK
pip install --upgrade google-cloud-aiplatform[adk]

# Check ADK version
python -c "import google.adk; print('ADK available')"
```

### Debug Mode

```python
# Enable debug logging
import logging
logging.getLogger("oprina").setLevel(logging.DEBUG)

# Tool context debugging
def debug_tool_context(tool_context):
    print(f"Session state keys: {list(tool_context.state.keys())}")
    print(f"User email: {tool_context.state.get('user_email', 'Not set')}")
```


For advanced configuration and deployment, see the [vertex-deployment](../vertex-deployment/) folder documentation.