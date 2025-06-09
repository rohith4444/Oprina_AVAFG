"""Test deployment script for Oprina Agent."""

import asyncio
import sys
from pathlib import Path

import vertexai
from dotenv import load_dotenv
from google.adk.sessions import VertexAiSessionService
from vertexai import agent_engines

# Add the parent directory to sys.path to import oprina
sys.path.insert(0, str(Path(__file__).parent.parent))

from oprina.config import get_config


def print_usage():
    """Print usage instructions."""
    print("Usage:")
    print("  python test_deployment.py <resource_id> [user_id]")
    print("")
    print("Examples:")
    print("  python test_deployment.py projects/my-project/locations/us-central1/reasoningEngines/123")
    print("  python test_deployment.py projects/my-project/locations/us-central1/reasoningEngines/123 test_user")


async def interactive_test(resource_id: str, user_id: str = "oprina_test_user") -> None:
    """Interactive testing with deployed agent."""
    print(f"Testing Oprina deployment: {resource_id}")
    
    config = get_config()
    project_id = config["google_cloud_project"]
    location = config["google_cloud_location"]
    bucket = config["google_cloud_storage_bucket"]
    
    # Initialize Vertex AI
    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=f"gs://{bucket}",
    )
    
    # Create session service
    session_service = VertexAiSessionService(project_id, location)
    
    # Create session
    print(f" Creating session for user: {user_id}")
    session = await session_service.create_session(
        app_name=resource_id,
        user_id=user_id
    )
    
    # Get agent
    agent = agent_engines.get(resource_id)
    
    print(f" Found agent: {resource_id}")
    print(f" Created session: {session.id}")
    print("Type 'quit' to exit, 'help' for example commands")
    print("Note: Gmail/Calendar setup may not work in deployed environment")
    print("\n--- Oprina Voice Assistant Test Session ---")
    
    while True:
        try:
            user_input = input("\n🎤 You: ").strip()
            
            if user_input.lower() == "quit":
                break
            elif user_input.lower() == "help":
                print("Example commands to try:")
                print("  - 'Hello, what can you help me with?'")
                print("  - 'Tell me about your capabilities'")
                print("  - 'What services do you integrate with?'")
                print("  - 'How do I set up Gmail?'")
                print("  - 'quit' to exit")
                continue
            elif not user_input:
                continue
            
            print("Oprina: ", end="", flush=True)
            
            # Stream response
            response_received = False
            for event in agent.stream_query(
                user_id=user_id,
                session_id=session.id,
                message=user_input,
            ):
                if "content" in event:
                    if "parts" in event["content"]:
                        parts = event["content"]["parts"]
                        for part in parts:
                            if "text" in part:
                                print(part["text"], end="", flush=True)
                                response_received = True
            
            if not response_received:
                print("(No response received)")
            
            print()  # New line after response
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")
            print("This might be due to Gmail/Calendar authentication in deployed environment")
    
    # Clean up session
    try:
        await session_service.delete_session(
            app_name=resource_id,
            user_id=user_id,
            session_id=session.id
        )
        print(f"Cleaned up session for user: {user_id}")
    except Exception as e:
        print(f"Warning: Could not clean up session: {e}")


def main():
    """Main function."""
    load_dotenv()
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print_usage()
        return
    
    resource_id = sys.argv[1]
    user_id = sys.argv[2] if len(sys.argv) > 2 else "oprina_test_user"
    
    # Validate resource ID format
    if not resource_id.startswith("projects/"):
        print("Invalid resource ID format")
        print("Expected format: projects/PROJECT_ID/locations/LOCATION/reasoningEngines/ENGINE_ID")
        return
    
    try:
        asyncio.run(interactive_test(resource_id, user_id))
    except KeyboardInterrupt:
        print("\nGoodbye!")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()