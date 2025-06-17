import pathlib
import dotenv
from google.adk.evaluation.agent_evaluator import AgentEvaluator
import pytest


@pytest.fixture(scope="session", autouse=True)
def load_env():
    dotenv.load_dotenv()


@pytest.mark.asyncio
async def test_email_workflows():
    """Test the email agent's basic operations and workflows."""
    await AgentEvaluator.evaluate(
        "oprina.sub_agents.email",
        str(pathlib.Path(__file__).parent / "data/email_workflows.test.json"),
        num_runs=3
    )


@pytest.mark.asyncio
async def test_calendar_workflows():
    """Test the calendar agent's event management capabilities."""
    await AgentEvaluator.evaluate(
        "oprina.sub_agents.calendar",
        str(pathlib.Path(__file__).parent / "data/calendar_workflows.test.json"),
        num_runs=3
    )


@pytest.mark.asyncio
async def test_cross_agent_workflows():
    """Test workflows that coordinate between email and calendar agents."""
    await AgentEvaluator.evaluate(
        "oprina",
        str(pathlib.Path(__file__).parent / "data/cross_agent_workflows.test.json"),
        num_runs=2
    )
