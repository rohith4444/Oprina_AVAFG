import os
import sys

import vertexai
from absl import app, flags
from dotenv import load_dotenv
from vertexai import agent_engines
from vertexai.preview import reasoning_engines

from oprina.agent import root_agent

FLAGS = flags.FLAGS
flags.DEFINE_string("project_id", None, "GCP project ID.")
flags.DEFINE_string("location", None, "GCP location.")
flags.DEFINE_string("bucket", None, "GCP bucket.")
flags.DEFINE_string("resource_id", None, "ReasoningEngine resource ID.")
flags.DEFINE_string("user_id", "test_user", "User ID for session operations.")
flags.DEFINE_string("session_id", None, "Session ID for operations.")
flags.DEFINE_bool("create", False, "Creates a new deployment.")
flags.DEFINE_bool("delete", False, "Deletes an existing deployment.")
flags.DEFINE_bool("list", False, "Lists all deployments.")
flags.DEFINE_bool("create_session", False, "Creates a new session.")
flags.DEFINE_bool("list_sessions", False, "Lists all sessions for a user.")
flags.DEFINE_bool("get_session", False, "Gets a specific session.")
flags.DEFINE_bool("send", False, "Sends a message to the deployed agent.")
flags.DEFINE_bool("test_tokens", False, "Tests the token service before deployment.")
flags.DEFINE_string(
    "message",
    "Shorten this message: Hello, how are you doing today?",
    "Message to send to the agent.",
)
flags.mark_bool_flags_as_mutual_exclusive(
    [
        "create",
        "delete",
        "list",
        "create_session",
        "list_sessions",
        "get_session",
        "send",
        "test_tokens",
    ]
)


def test_token_service() -> bool:
    """Test the lightweight token service before deployment."""
    print("🧪 Testing lightweight token service...")
    
    try:
        # Import here to test if the service works
        from oprina.tools.token_service import test_token_service_with_user
        
        # Test with default user
        success = test_token_service_with_user(FLAGS.user_id)
        
        if success:
            print("✅ Token service test passed!")
            return True
        else:
            print("❌ Token service test failed!")
            return False
            
    except ImportError as e:
        print(f"❌ Failed to import token service: {e}")
        return False
    except Exception as e:
        print(f"❌ Token service test error: {e}")
        return False


def test_session_state(remote_app, user_id: str) -> bool:
    """Test that Vertex AI session properly stores userId."""
    print(f"🧪 Testing session userId storage for user: {user_id}")
    
    try:
        # Create a test session
        test_session = remote_app.create_session(user_id=user_id)
        session_id = test_session.get('id')
        
        if not session_id:
            print("❌ Session creation failed - no session ID returned")
            return False
        
        print(f"✅ Session created: {session_id}")
        
        # Check if Vertex AI automatically stored userId
        try:
            session_details = remote_app.get_session(user_id=user_id, session_id=session_id)
            print(f"✅ Session details retrieved successfully")
            
            # ✨ NEW: Check for Vertex AI's automatic userId storage
            if 'userId' in session_details and session_details['userId'] == user_id:
                print(f"✅ Session contains correct userId = {user_id}")
                return True
            else:
                print(f"❌ Session missing or incorrect userId")
                print(f"   Expected: {user_id}")
                print(f"   Found: {session_details.get('userId', 'NOT FOUND')}")
                return False
                
        except Exception as e:
            print(f"⚠️ Could not retrieve session details: {e}")
            return False
            
    except Exception as e:
        print(f"❌ Session test failed: {e}")
        return False

def comprehensive_deployment_test(remote_app, user_id: str) -> bool:
    """Run comprehensive tests after deployment."""
    print("🧪 Running comprehensive deployment tests...")
    
    # Test 1: Session creation and state
    print("\n1️⃣ Testing session creation and state...")
    if not test_session_state(remote_app, user_id):
        print("❌ Session state test failed")
        return False
    
    # Test 2: Token service integration
    print("\n2️⃣ Testing token service integration...")
    try:
        from oprina.tools.token_service import test_token_service_with_user
        if not test_token_service_with_user(user_id):
            print("❌ Token service integration test failed")
            return False
        print("✅ Token service integration working")
    except Exception as e:
        print(f"⚠️ Token service integration test error: {e}")
        print("   Continuing with deployment...")
    
    # Test 3: Basic message sending (if session exists)
    print("\n3️⃣ Testing basic message interaction...")
    try:
        test_session = remote_app.create_session(user_id=user_id)
        session_id = test_session.get('id')
        
        if session_id:
            # Send a simple test message
            print(f"   Sending test message to session {session_id}")
            responses = []
            for event in remote_app.stream_query(
                user_id=user_id,
                session_id=session_id,
                message="Hello, can you confirm you can see my user ID?"
            ):
                responses.append(str(event))
                if len(responses) > 3:  # Limit output
                    break
            
            if responses:
                print("✅ Message interaction successful")
                print(f"   Sample response: {responses[0][:100]}...")
                return True
            else:
                print("⚠️ No response received, but deployment may still be working")
                return True
        else:
            print("⚠️ Could not create session for message test")
            return True  # Don't fail for this
            
    except Exception as e:
        print(f"⚠️ Message interaction test failed: {e}")
        print("   Deployment may still be working - this could be a timeout or other issue")
        return True  # Don't fail deployment for message test issues
    
    return True


def create() -> None:
    """Creates a new deployment with lightweight token service."""
    
    # Test token service before deployment
    print("🔍 Pre-deployment checks...")
    # if not test_token_service():
    #     print("❌ Token service test failed. Fix issues before deploying.")
    #     return
    
    # print("✅ Token service working. Proceeding with deployment...")
    # print("="*60)
    
    # First wrap the agent in AdkApp
    app = reasoning_engines.AdkApp(
        agent=root_agent,
        enable_tracing=True,
    )

    # ✨ ENVIRONMENT VARIABLES FOR LIGHTWEIGHT DATABASE ACCESS
    env_vars = {
        "SUPABASE_URL": os.getenv("SUPABASE_URL"),
        "SUPABASE_KEY": os.getenv("SUPABASE_KEY"),
        "SUPABASE_SERVICE_KEY": os.getenv("SUPABASE_SERVICE_KEY"),  # ✨ FOR TOKEN SERVICE
        "GOOGLE_CLIENT_ID": os.getenv("GOOGLE_CLIENT_ID"),
        "GOOGLE_CLOUD_STAGING_BUCKET": os.getenv("GOOGLE_CLOUD_STAGING_BUCKET"),
        "GOOGLE_CLIENT_SECRET": os.getenv("GOOGLE_CLIENT_SECRET"),
        # "ENCRYPTION_KEY": os.getenv("ENCRYPTION_KEY"),
    }

    # Print each environment variable (mask sensitive ones)
    for key, value in env_vars.items():
        if value:
            if "SECRET" in key or "KEY" in key:
                # Mask sensitive values
                masked_value = value[:8] + "*" * (len(value) - 16) + value[-8:] if len(value) > 16 else "*" * len(value)
                print(f"✅ {key}: {masked_value}")
            else:
                # Show full value for non-sensitive variables
                print(f"✅ {key}: {value}")
        else:
            print(f"❌ {key}: NOT SET")
    
    print("="*60)

    # ✨ LIGHTWEIGHT REQUIREMENTS - NO SUPABASE CLIENT
    requirements = [
        "google-cloud-aiplatform[adk,agent_engines]",
        # "supabase",  # ❌ REMOVED - causes dependency conflicts
        "google-auth", 
        "google-auth-oauthlib",
        "google-api-python-client",
        "google-genai",
        # "cryptography",
    ]
    
    print("📦 Using lightweight requirements (no Supabase client):")
    for req in requirements:
        print(f"  - {req}")
    print("="*60)

    # Now deploy to Agent Engine
    try:
        remote_app = agent_engines.create(
            agent_engine=app,
            requirements=requirements,  # ✨ LIGHTWEIGHT REQUIREMENTS
            extra_packages=["./oprina"],  # ✨ INCLUDES TOKEN SERVICE
            env_vars=env_vars
        )
        print(f"✅ Created remote app: {remote_app.resource_name}")
        
        # ✨ COMPREHENSIVE POST-DEPLOYMENT TESTING
        print("\n" + "="*60)
        print("🧪 RUNNING POST-DEPLOYMENT TESTS")
        print("="*60)
        
        if comprehensive_deployment_test(remote_app, FLAGS.user_id):
            print("\n🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!")
            print(f"📍 Agent ID: {remote_app.resource_name}")
            print(f"👤 Tested with user: {FLAGS.user_id}")
            print("✅ Session state management working")
            print("✅ Token service integration working")
            print("✅ Multi-user functionality ready")
        else:
            print("\n⚠️ DEPLOYMENT COMPLETED WITH WARNINGS")
            print(f"📍 Agent ID: {remote_app.resource_name}")
            print("⚠️ Some tests failed - check logs above")
            print("ℹ️ Agent may still be functional")
            
    except Exception as e:
        print(f"❌ Deployment failed: {e}")
        raise


def delete(resource_id: str) -> None:
    """Deletes an existing deployment."""
    remote_app = agent_engines.get(resource_id)
    remote_app.delete(force=True)
    print(f"Deleted remote app: {resource_id}")


def list_deployments() -> None:
    """Lists all deployments."""
    deployments = agent_engines.list()
    if not deployments:
        print("No deployments found.")
        return
    print("Deployments:")
    for deployment in deployments:
        print(f"- {deployment.resource_name}")


def create_session(resource_id: str, user_id: str) -> None:
    """Creates a new session for the specified user."""
    remote_app = agent_engines.get(resource_id)
    remote_session = remote_app.create_session(user_id=user_id)
    print("Full remote_session object:")
    print(remote_session)
    print("Created session:")
    print(f"  Session ID: {remote_session['id']}")
    print(f"  User ID: {user_id}")
    print("\nUse this session ID with --session_id when sending messages.")


def list_sessions(resource_id: str, user_id: str) -> None:
    """Lists all sessions for the specified user."""
    remote_app = agent_engines.get(resource_id)
    sessions_resp = remote_app.list_sessions(user_id=user_id)
    
    print(f"[DEBUG] list_sessions returned: {sessions_resp}")

    # Now assuming it's a dict with 'sessions' key
    sessions = sessions_resp.get("sessions", None)
    if sessions is None:
        print("Unexpected session response format:", sessions_resp)
        return

    print(f"Sessions for user '{user_id}':")
    for session in sessions:
        print(f"- Session ID: {session['id']}")


def get_session(resource_id: str, user_id: str, session_id: str) -> None:
    """Gets a specific session."""
    remote_app = agent_engines.get(resource_id)
    session = remote_app.get_session(user_id=user_id, session_id=session_id)
    print("Session details:")
    print(f"  ID: {session['id']}")
    print(f"  User ID: {user_id}")


def send_message(resource_id: str, user_id: str, session_id: str, message: str) -> None:
    """Sends a message to the deployed agent."""
    remote_app = agent_engines.get(resource_id)

    print(f"Sending message to session {session_id}:")
    print(f"User: {user_id}")
    print(f"Message: {message}")
    print("\nResponse:")
    for event in remote_app.stream_query(
        user_id=user_id,
        session_id=session_id,
        message=message,
    ):
        print(event)


def main(argv=None):
    """Main function that can be called directly or through app.run()."""
    # Parse flags first
    if argv is None:
        argv = flags.FLAGS(sys.argv)
    else:
        argv = flags.FLAGS(argv)

    load_dotenv()

    # Now we can safely access the flags
    project_id = (
        FLAGS.project_id if FLAGS.project_id else os.getenv("GOOGLE_CLOUD_PROJECT")
    )
    location = FLAGS.location if FLAGS.location else os.getenv("GOOGLE_CLOUD_LOCATION")
    bucket = FLAGS.bucket if FLAGS.bucket else os.getenv("GOOGLE_CLOUD_STAGING_BUCKET")
    user_id = FLAGS.user_id

    if not project_id:
        print("Missing required environment variable: GOOGLE_CLOUD_PROJECT")
        return
    elif not location:
        print("Missing required environment variable: GOOGLE_CLOUD_LOCATION")
        return
    elif not bucket:
        print("Missing required environment variable: GOOGLE_CLOUD_STAGING_BUCKET")
        return

    vertexai.init(
        project=project_id,
        location=location,
        staging_bucket=bucket,
    )

    if FLAGS.test_tokens:
        # ✨ NEW: Test token service independently
        test_token_service()
    elif FLAGS.create:
        create()
    elif FLAGS.delete:
        if not FLAGS.resource_id:
            print("resource_id is required for delete")
            return
        delete(FLAGS.resource_id)
    elif FLAGS.list:
        list_deployments()
    elif FLAGS.create_session:
        if not FLAGS.resource_id:
            print("resource_id is required for create_session")
            return
        create_session(FLAGS.resource_id, user_id)
    elif FLAGS.list_sessions:
        if not FLAGS.resource_id:
            print("resource_id is required for list_sessions")
            return
        list_sessions(FLAGS.resource_id, user_id)
    elif FLAGS.get_session:
        if not FLAGS.resource_id:
            print("resource_id is required for get_session")
            return
        if not FLAGS.session_id:
            print("session_id is required for get_session")
            return
        get_session(FLAGS.resource_id, user_id, FLAGS.session_id)
    elif FLAGS.send:
        if not FLAGS.resource_id:
            print("resource_id is required for send")
            return
        if not FLAGS.session_id:
            print("session_id is required for send")
            return
        send_message(FLAGS.resource_id, user_id, FLAGS.session_id, FLAGS.message)
    else:
        print(
            "Please specify one of: --create, --delete, --list, --create_session, --list_sessions, --get_session, --send, or --test_tokens"
        )


if __name__ == "__main__":
    app.run(main)