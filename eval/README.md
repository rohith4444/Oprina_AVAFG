# Oprina Agent Evaluation

This folder contains evaluation tests for the Oprina email and calendar agents.

## What's Included

- **test_eval.py**: Main test file that runs evaluations
- **data/**: Test data files containing conversation scenarios

### Test Files

1. **email_workflows.test.json**: Tests email operations like sending, reading, organizing emails
2. **calendar_workflows.test.json**: Tests calendar operations like creating, updating, deleting events
3. **cross_agent_workflows.test.json**: Tests complex workflows that use both email and calendar agents

## How to Run Tests

### Run All Tests
```bash
cd oprina
python -m pytest eval/test_eval.py
```

### Run Individual Test Categories

**Email tests only:**
```bash
python -m pytest eval/test_eval.py::test_email_workflows
```

**Calendar tests only:**
```bash
python -m pytest eval/test_eval.py::test_calendar_workflows
```

**Cross-agent workflow tests:**
```bash
python -m pytest eval/test_eval.py::test_cross_agent_workflows
```

## Test Structure

Each test file contains:
- **eval_cases**: Different scenarios to test
- **conversation**: User requests and expected agent responses
- **tool_uses**: Which tools the agent should use
- **session_input**: Initial state for the test

## Requirements

- Python environment with required dependencies
- Gmail and Calendar API credentials configured
- ADK (Agent Development Kit) properly installed

## Test Scenarios

### Email Tests
- Sending emails
- Listing recent emails
- Searching and organizing emails
- AI-powered email generation and analysis

### Calendar Tests
- Creating calendar events
- Listing events for specific date ranges
- Updating existing events
- Deleting events
- Recurring event management

### Cross-Agent Tests
- Coordinating email and calendar for meeting scheduling
- Processing emails to create calendar events
- Managing deadlines across both systems 