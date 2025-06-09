"""Simplified deployment script for Oprina Agent to Vertex AI Agent Engine."""

import sys
from pathlib import Path

import vertexai
from dotenv import load_dotenv
from vertexai import agent_engines
from vertexai.preview.reasoning_engines import AdkApp

# Add the parent directory to sys.path to import oprina
sys.path.insert(0, str(Path(__file__).parent.parent))
from oprina.agent import root_agent
from oprina.config import get_config


def load_requirements():
    """Load requirements from deployment/requirements.txt"""
    req_file = Path(__file__).parent / "requirements.txt"
    
    if not req_file.exists():
        print(f"Requirements file not found: {req_file}")
        print("Please create deployment/requirements.txt with your dependencies")
        return []
    
    requirements = []
    with open(req_file, 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#'):
                requirements.append(line)
    
    print(f"Loaded {len(requirements)} requirements from {req_file.name}")
    return requirements


def create_deployment(config: dict) -> str:
    """Creates a new Agent Engine deployment."""
    print("Creating Oprina deployment...")
    
    # Load requirements from file
    requirements = load_requirements()
    if not requirements:
        print("No requirements found. Cannot proceed with deployment.")
        return None
    
    # Prepare environment variables for deployment
    env_vars = {
        "GOOGLE_CLOUD_PROJECT": config["google_cloud_project"],
        "GOOGLE_CLOUD_LOCATION": config["google_cloud_location"],
        "GOOGLE_CLOUD_STORAGE_BUCKET": config["google_cloud_storage_bucket"],
        "GOOGLE_GENAI_USE_VERTEXAI": "1",
        "AGENT_MODEL": config["agent_model"],
    }
    
    print(f"🔧 Environment variables: {list(env_vars.keys())}")
    
    # Create AdkApp with environment variables
    app = AdkApp(
        agent=root_agent,
        enable_tracing=True,
        env_vars=env_vars,
    )
    
    # Deploy to Agent Engine - CORRECTED SYNTAX
    print("Deploying to Vertex AI Agent Engine (this may take several minutes)...")
    remote_agent = agent_engines.create(
        app,  # Pass the app, not named parameter
        display_name="Oprina-Voice-Assistant",
        description="Multimodal voice-enabled Gmail and Calendar assistant",
        requirements=requirements,
        extra_packages=[
            "../oprina_dep",  # The main package
        ],
    )
    
    print(f"Created remote agent: {remote_agent.resource_name}")
    print(f"Save this resource ID for testing: {remote_agent.resource_name}")
    
    return remote_agent.resource_name


def delete_deployment(resource_id: str) -> None:
    """Deletes an existing deployment."""
    if not resource_id:
        print("Resource ID is required for deletion")
        print("Usage: python deploy.py delete <resource_id>")
        return
    
    print(f"Deleting deployment: {resource_id}")
    
    try:
        remote_agent = agent_engines.get(resource_id)
        remote_agent.delete(force=True)
        print(f"Deleted deployment: {resource_id}")
    except Exception as e:
        print(f"Error deleting deployment: {e}")


def print_usage():
    """Print usage instructions."""
    print("Usage:")
    print("  python deploy.py create                    # Create new deployment")
    print("  python deploy.py delete <resource_id>      # Delete existing deployment")
    print("  python deploy.py help                      # Show this help")
    print("")
    print("Examples:")
    print("  python deploy.py create")
    print("  python deploy.py delete projects/my-project/locations/us-central1/reasoningEngines/123")


def main():
    """Main function to handle deployment operations."""
    load_dotenv()
    
    # Check command line arguments
    if len(sys.argv) < 2:
        print_usage()
        return
    
    command = sys.argv[1].lower()
    
    if command == "help" or command == "--help" or command == "-h":
        print_usage()
        return

    config = get_config()
    
    # Initialize Vertex AI
    print(f"PROJECT: {config['google_cloud_project']}")
    print(f"LOCATION: {config['google_cloud_location']}")
    print(f"BUCKET: {config['google_cloud_storage_bucket']}")
    
    vertexai.init(
        project=config["google_cloud_project"],
        location=config["google_cloud_location"],
        staging_bucket=f"gs://{config['google_cloud_storage_bucket']}",
    )
    
    # Execute command
    if command == "create":
        create_deployment(config)
    
    elif command == "delete":
        if len(sys.argv) < 3:
            print("Resource ID is required for delete command")
            print("Usage: python deploy.py delete <resource_id>")
            return
        resource_id = sys.argv[2]
        delete_deployment(resource_id)
    
    else:
        print(f"Unknown command: {command}")
        print_usage()


if __name__ == "__main__":
    main()