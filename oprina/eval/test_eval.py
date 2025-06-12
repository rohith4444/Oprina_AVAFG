import pathlib
import dotenv
from google.adk.evaluation import AgentEvaluator
import pytest


@pytest.fixture(scope="session", autouse=True)
def load_env():
    dotenv.load_dotenv()


@pytest.mark.asyncio
async def test_email_workflows():
    """Test the email agent's basic operations and workflows."""
    await AgentEvaluator.evaluate(
        "email_agent",
        str(pathlib.Path(__file__).parent / "data/email_workflows.test.json"),
        num_runs=3
    )


@pytest.mark.asyncio
async def test_calendar_workflows():
    """Test the calendar agent's event management capabilities."""
    await AgentEvaluator.evaluate(
        "calendar_agent",
        str(pathlib.Path(__file__).parent / "data/calendar_workflows.test.json"),
        num_runs=3
    )


@pytest.mark.asyncio
async def test_cross_agent_workflows():
    """Test workflows that coordinate between email and calendar agents."""
    await AgentEvaluator.evaluate(
        "oprina_root_agent",
        str(pathlib.Path(__file__).parent / "data/cross_agent_workflows.test.json"),
        num_runs=2
    )
