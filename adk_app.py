"""
Oprina ADK Application Entry Point

This module configures and runs the Oprina voice assistant using ADK's
web interface and API server capabilities.
"""

import sys
import os
import asyncio
from typing import Optional

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import settings
from services.logging.logger import setup_logger
from memory.adk_memory_manager import get_adk_memory_manager

# Configure logging
logger = setup_logger("oprina_app", console_output=True)

# ADK imports
try:
    from google.adk.sessions import DatabaseSessionService, InMemorySessionService
    from google.adk.memory import InMemoryMemoryService, VertexAiRagMemoryService
    from google.adk.runners import Runner
    ADK_AVAILABLE = True
except ImportError as e:
    ADK_AVAILABLE = False
    ADK_IMPORT_ERROR = str(e)

def create_adk_services():
    """
    Create and configure ADK services based on settings.
    
    Returns:
        Tuple[SessionService, MemoryService]: Configured ADK services
    """
    try:
        logger.info("Initializing ADK services...")
        
        # Initialize Session Service
        if settings.SESSION_SERVICE_TYPE == "database":
            logger.info("Using DatabaseSessionService with Supabase")
            session_service = DatabaseSessionService(
                db_url=settings.adk_database_url
            )
        else:
            logger.info("Using InMemorySessionService")
            session_service = InMemorySessionService()
        
        # Initialize Memory Service
        if settings.MEMORY_SERVICE_TYPE == "vertexai_rag":
            logger.info("Using VertexAiRagMemoryService")
            memory_service = VertexAiRagMemoryService(
                rag_corpus=settings.vertex_ai_rag_corpus_name
            )
        else:
            logger.info("Using InMemoryMemoryService")
            memory_service = InMemoryMemoryService()
        
        logger.info("✅ ADK services initialized successfully")
        return session_service, memory_service
        
    except Exception as e:
        logger.error(f"Failed to initialize ADK services: {e}")
        raise

def create_adk_runner():
    """
    Create ADK Runner with Oprina root agent and services.
    
    Returns:
        Runner: Configured ADK Runner
    """
    try:
        logger.info("Creating ADK Runner for Oprina...")
        
        # Import root agent
        from agents.root_agent import root_agent
        
        # Create ADK services
        session_service, memory_service = create_adk_services()
        
        # Create Runner
        runner = Runner(
            agent=root_agent,
            app_name=settings.ADK_APP_NAME,
            session_service=session_service,
            memory_service=memory_service
        )
        
        logger.info(f"✅ ADK Runner created for app: {settings.ADK_APP_NAME}")
        logger.info(f"Root Agent: {root_agent.name}")
        logger.info(f"Session Service: {settings.SESSION_SERVICE_TYPE}")
        logger.info(f"Memory Service: {settings.MEMORY_SERVICE_TYPE}")
        
        return runner
        
    except Exception as e:
        logger.error(f"Failed to create ADK Runner: {e}")
        raise

async def health_check():
    """
    Perform application health check.
    
    Returns:
        Dict: Health check results
    """
    health = {
        "app": "oprina",
        "status": "unhealthy",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    try:
        # Check ADK availability
        health["checks"]["adk_available"] = ADK_AVAILABLE
        
        if not ADK_AVAILABLE:
            health["checks"]["adk_error"] = ADK_IMPORT_ERROR
            return health
        
        # Check root agent
        try:
            from agents.root_agent import root_agent
            health["checks"]["root_agent"] = root_agent is not None
            health["checks"]["root_agent_name"] = root_agent.name if root_agent else None
        except Exception as e:
            health["checks"]["root_agent"] = False
            health["checks"]["root_agent_error"] = str(e)
        
        # Check services
        try:
            session_service, memory_service = create_adk_services()
            health["checks"]["session_service"] = session_service is not None
            health["checks"]["memory_service"] = memory_service is not None
        except Exception as e:
            health["checks"]["services"] = False
            health["checks"]["services_error"] = str(e)
        
        # Check configuration
        health["checks"]["configuration"] = {
            "app_name": settings.ADK_APP_NAME,
            "session_type": settings.SESSION_SERVICE_TYPE,
            "memory_type": settings.MEMORY_SERVICE_TYPE,
            "environment": settings.ENVIRONMENT
        }
        
        # Overall status
        critical_checks = ["adk_available", "root_agent", "session_service", "memory_service"]
        all_critical_passed = all(health["checks"].get(check, False) for check in critical_checks)
        
        health["status"] = "healthy" if all_critical_passed else "degraded"
        
    except Exception as e:
        health["checks"]["error"] = str(e)
        health["status"] = "unhealthy"
    
    return health

def run_web_interface():
    """
    Run Oprina with ADK web interface.
    This starts the web UI for Oprina.
    """
    try:
        logger.info("Starting Oprina Web Interface...")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        logger.info(f"Host: {settings.API_HOST}:{settings.API_PORT}")
        
        # Create runner
        runner = create_adk_runner()
        
        # This would typically use ADK's web command
        # For now, we'll provide instructions
        logger.info("🌐 To start the web interface, run:")
        logger.info(f"   adk web --port {settings.API_PORT}")
        logger.info("🚀 Oprina Voice Assistant ready!")
        
        return runner
        
    except Exception as e:
        logger.error(f"Failed to start web interface: {e}")
        raise

def run_api_server():
    """
    Run Oprina as API server.
    This starts the REST API for Oprina.
    """
    try:
        logger.info("Starting Oprina API Server...")
        
        # Create runner
        runner = create_adk_runner()
        
        # This would typically use ADK's api_server command
        logger.info("🔌 To start the API server, run:")
        logger.info(f"   adk api_server --port {settings.API_PORT}")
        logger.info("🚀 Oprina API Server ready!")
        
        return runner
        
    except Exception as e:
        logger.error(f"Failed to start API server: {e}")
        raise

async def main():
    """Main application entry point."""
    try:
        logger.info(f"🎙️ Starting Oprina Voice Assistant...")
        logger.info(f"Version: ADK-native with voice interface")
        logger.info(f"Environment: {settings.ENVIRONMENT}")
        
        # Perform health check
        health = await health_check()
        logger.info(f"Health Status: {health['status']}")
        
        if health["status"] != "healthy":
            logger.warning("Some health checks failed:")
            for check, result in health["checks"].items():
                if isinstance(result, bool) and not result:
                    logger.warning(f"  ❌ {check}")
                elif isinstance(result, bool) and result:
                    logger.info(f"  ✅ {check}")
        
        # Show available commands
        print(f"\n🎯 Oprina ADK Integration Ready!")
        print(f"📋 Available Commands:")
        print(f"   🌐 Web Interface: adk web --port {settings.API_PORT}")
        print(f"   🔌 API Server: adk api_server --port {settings.API_PORT}")
        print(f"   🧪 Health Check: python app.py --health")
        print(f"\n🎙️ Voice Agent Hierarchy:")
        
        # Show agent hierarchy
        from agents.root_agent import root_agent
        print(f"  └── {root_agent.name} (Root)")
        for sub_agent in root_agent.sub_agents:
            print(f"      └── {sub_agent.name}")
            if hasattr(sub_agent, 'sub_agents') and sub_agent.sub_agents:
                for sub_sub_agent in sub_agent.sub_agents:
                    print(f"          └── {sub_sub_agent.name}")
        
        print(f"\n🚀 Oprina is ready for voice-powered Gmail and Calendar assistance!")
        
    except Exception as e:
        logger.error(f"Application startup failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    import argparse
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Oprina Voice Assistant")
    parser.add_argument("--health", action="store_true", help="Run health check")
    parser.add_argument("--web", action="store_true", help="Start web interface")
    parser.add_argument("--api", action="store_true", help="Start API server")
    
    args = parser.parse_args()
    
    if args.health:
        async def run_health():
            health = await health_check()
            print(f"Health Status: {health['status']}")
            for check, result in health["checks"].items():
                status = "✅" if result else "❌"
                print(f"  {status} {check}: {result}")
        
        asyncio.run(run_health())
    elif args.web:
        run_web_interface()
    elif args.api:
        run_api_server()
    else:
        asyncio.run(main())