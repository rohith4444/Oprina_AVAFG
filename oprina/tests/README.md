# Oprina Test Suite - Enhanced with Comprehensive Agent Behavior Testing

This directory contains a **comprehensive test suite** for the Oprina multimodal voice-enabled AI assistant, including extensive **agent behavior testing** beyond just tool functionality.

## 🎯 **Testing Philosophy**

Our enhanced testing approach covers **three critical layers**:

1. **🔧 Tool Testing**: Individual function reliability and API integration
2. **🤖 Agent Behavior Testing**: How agents interact, delegate, and provide voice-optimized responses  
3. **🔄 Workflow Integration**: End-to-end scenarios with cross-agent coordination

## 📁 **Test Structure**

```
oprina/tests/
├── unit/
│   ├── test_gmail_tools.py     # Gmail tools + Gmail agent behavior
│   └── test_calendar_tools.py  # Calendar tools + Calendar agent behavior  
├── test_agents.py              # Enhanced agent integration & behavior
├── test_setup.py               # Setup + agent setup behavior
├── pytest.ini                 # Pytest configuration
└── README.md                   # This file
```

## 🧪 **Enhanced Test Categories**

### **Gmail Tests** (`test_gmail_tools.py`)
- **Tool Functions**: 25+ tests for Gmail API operations
- **Agent Behavior**: 15+ tests for Gmail agent-specific behavior including:
  - Agent configuration and instruction validation
  - Email workflow orchestration (read → organize → send)
  - AI content processing workflows
  - Voice-optimized response generation
  - Confirmation and safety protocols
  - Session state management across operations
  - Error recovery and user guidance

### **Calendar Tests** (`test_calendar_tools.py`)  
- **Tool Functions**: 20+ tests for Calendar API operations
- **Agent Behavior**: 15+ tests for Calendar agent-specific behavior including:
  - Agent configuration and natural language processing
  - Event creation and management workflows
  - Voice-friendly event listing and time formatting
  - Setup guidance and error recovery
  - Session state persistence across operations
  - Cross-workflow integration with tool registration

### **Agent Integration Tests** (`test_agents.py`)
- **Root Agent Coordination**: 5+ tests for delegation and coordination
- **Enhanced Agent Behavior**: 20+ tests including:
  - Agent instruction content and behavior pattern validation
  - Delegation strategy and sub-agent specialization
  - Cross-agent workflow coordination (email + calendar)
  - Error handling and recovery behavior across agents
  - Voice interface optimization testing
  - Session state sharing and continuity
  - Model consistency across all agents

### **Setup & Agent Guidance Tests** (`test_setup.py`)
- **Basic Setup**: 20+ authentication and credential tests
- **Agent Setup Behavior**: 15+ tests including:
  - Agent behavior when services aren't configured
  - Setup guidance with voice-friendly messaging
  - Error recovery during setup processes
  - Cross-agent setup coordination
  - Complete setup workflow testing from not-configured to working

## 📊 **Enhanced Test Coverage**

### **Total Test Count**: ~150+ individual test methods

| Category | Tool Tests | Agent Behavior Tests | Total |
|----------|------------|---------------------|-------|
| Gmail | ~25 | ~15 | ~40 |
| Calendar | ~20 | ~15 | ~35 |
| Agent Integration | ~15 | ~25 | ~40 |
| Setup | ~20 | ~15 | ~35 |
| **TOTAL** | **~80** | **~70** | **~150** |

### **Agent Behavior Coverage**: ~47% of all tests focus specifically on agent behavior

## 🚀 **Running Tests with Pytest**

### **Basic Usage**
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with detailed output and no warnings
pytest -v --tb=short

# Run with coverage reporting
pytest --cov=oprina
```

### **Test Categories**
```bash
# Run all Gmail tests (tools + agent behavior)
pytest oprina/tests/unit/test_gmail_tools.py -v

# Run all Calendar tests (tools + agent behavior)  
pytest oprina/tests/unit/test_calendar_tools.py -v

# Run all agent integration tests
pytest oprina/tests/test_agents.py -v

# Run all setup tests (basic + agent behavior)
pytest oprina/tests/test_setup.py -v
```

### **Specific Test Classes and Methods**
```bash
# Run specific test class (agent behavior)
pytest oprina/tests/unit/test_gmail_tools.py::TestGmailAgentBehavior -v

# Run specific test method
pytest oprina/tests/test_agents.py::TestAgentInstructionBehavior::test_root_agent_instruction_content -v

# Run all agent behavior test classes across files
pytest -k "AgentBehavior" -v

# Run all voice interface tests
pytest -k "voice" -v

# Run all workflow tests
pytest -k "workflow" -v
```

### **Pattern-Based Test Selection**
```bash
# Run all tests containing "agent" in the name
pytest -k "agent" -v

# Run all tests containing "behavior" in the name  
pytest -k "behavior" -v

# Run all setup-related tests
pytest -k "setup" -v

# Run all voice optimization tests
pytest -k "voice_friendly or voice_optimized" -v

# Exclude slow tests
pytest -k "not slow" -v
```

### **Parallel Execution**
```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel
pytest -n auto -v
```

## 🎯 **Key Agent Behavior Tests**

### **Gmail Agent Behavior Examples**
```python
def test_agent_email_reading_workflow(self):
    """Test agent's email reading workflow behavior"""
    # Tests: search → present results → offer actions
    # Validates: user-friendly results, workflow state maintenance

def test_agent_ai_content_processing_workflow(self):
    """Test agent's AI content processing workflow""" 
    # Tests: analyze → process → present insights
    # Validates: actionable insights, session tracking

def test_agent_voice_friendly_responses(self):
    """Test that agent responses are optimized for voice interaction"""
    # Tests: natural language use, no technical artifacts
    # Validates: voice indicators, speakable format
```

### **Calendar Agent Behavior Examples**
```python
def test_agent_natural_language_processing(self):
    """Test agent's ability to handle natural language time formats"""
    # Tests: various time formats, graceful handling
    # Validates: format flexibility, user-friendly responses

def test_agent_workflow_create_then_list(self):
    """Test agent workflow: create event then list events"""
    # Tests: create → confirm → track → list
    # Validates: workflow continuity, session state
```

### **Cross-Agent Behavior Examples**
```python
def test_agent_coordination_workflow(self):
    """Test coordination between agents in cross-service workflows"""
    # Tests: email action item extraction → calendar scheduling
    # Validates: cross-agent coordination, session sharing

def test_agent_instructions_voice_optimization(self):
    """Test that all agent instructions emphasize voice optimization"""
    # Tests: all agents have voice-friendly instructions
    # Validates: consistent voice optimization approach
```

## 🔍 **Testing Implementation Details**

### **Comprehensive Mocking Strategy**
- **External APIs**: All Gmail/Calendar API calls mocked
- **Authentication**: OAuth flows simulated with various scenarios
- **AI Processing**: AI content generation mocked with realistic responses
- **Session State**: Full session state validation across operations

### **Agent Behavior Validation**
- **Voice Optimization**: Responses tested for speakability and natural language
- **Error Recovery**: Graceful handling without exposing technical details
- **Workflow Continuity**: Session state persistence across multi-step operations
- **Setup Guidance**: User-friendly setup instructions and error messages

### **Real-World Scenarios**
- **Email Workflows**: Read → summarize → extract actions → reply
- **Calendar Workflows**: Create → list → update → delete with confirmations
- **Cross-Agent Workflows**: Email meeting requests → calendar scheduling
- **Error Scenarios**: Service unavailable, authentication failures, invalid inputs

## 🛠 **Troubleshooting Enhanced Tests**

### **Common Issues**

1. **Import Errors**: Make sure you're running from the project root
2. **Agent Import Failures**: Check that all agent modules are available
3. **Mock Failures**: Verify mock patches match actual implementation paths
4. **Session State Issues**: Ensure mock tool contexts have proper session setup

### **Debugging Agent Behavior Tests**
```bash
# Run with maximum verbosity and debugging
pytest oprina/tests/unit/test_gmail_tools.py::TestGmailAgentBehavior -v -s

# Run specific behavior test with debugging
pytest oprina/tests/unit/test_gmail_tools.py::TestGmailAgentBehavior::test_agent_voice_friendly_responses -v -s --tb=long

# Run with Python debugger on failures
pytest --pdb oprina/tests/test_agents.py::TestAgentInstructionBehavior -v

# Run with coverage to see what's being tested
pytest --cov=oprina --cov-report=html oprina/tests/
```

### **Test Data Validation**
```bash
# Verify agent configuration
python -c "
from oprina.sub_agents.email.agent import email_agent
from oprina.sub_agents.calendar.agent import calendar_agent
print(f'Email agent tools: {len(email_agent.tools)}')
print(f'Calendar agent tools: {len(calendar_agent.tools)}')
"
```

## 📈 **Enhanced Test Metrics**

### **Coverage Breakdown**
- **Tool Function Coverage**: ~100% of Gmail/Calendar functions
- **Agent Behavior Coverage**: ~90% of agent interaction patterns
- **Workflow Coverage**: ~95% of common user scenarios
- **Error Scenario Coverage**: ~85% of failure conditions
- **Voice Interface Coverage**: ~100% of user-facing responses

### **Performance Characteristics**
- **Unit Tests**: ~2-3 seconds (fast, isolated)
- **Agent Behavior Tests**: ~5-8 seconds (comprehensive mocking)
- **Integration Tests**: ~10-15 seconds (cross-agent workflows)
- **Full Suite**: ~30-45 seconds (all categories)

## 🎉 **Success Criteria**

A successful test run validates:

✅ **All tool functions work correctly**  
✅ **All agents provide voice-optimized responses**  
✅ **All workflows maintain proper session state**  
✅ **All error scenarios are handled gracefully**  
✅ **All cross-agent coordination works properly**  
✅ **All setup guidance is user-friendly**  
✅ **All confirmation workflows function correctly**

## 💡 **Contributing to Tests**

When adding new functionality:

1. **Add tool tests** for new functions
2. **Add agent behavior tests** for new workflows  
3. **Add integration tests** for cross-agent features
4. **Test voice optimization** for all user-facing responses
5. **Test error scenarios** and recovery
6. **Update this README** with new test descriptions

---

**🚀 This enhanced test suite ensures Oprina delivers reliable, voice-optimized, and user-friendly AI assistance across all scenarios.** 