from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse, RedirectResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from mcp import mcp_discovery
import io
import base64
import os
import json
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import traceback
import secrets
import time

app = FastAPI(title="Gmail MCP API")

# Add CORS middleware to allow frontend to access the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define OAuth2 scopes
SCOPES = [
    'https://www.googleapis.com/auth/gmail.modify',
    'https://www.googleapis.com/auth/userinfo.profile',
    'https://www.googleapis.com/auth/userinfo.email',
    'openid'
]

# Store authorization states to prevent CSRF attacks
auth_states = {}

# In production, use a proper domain
REDIRECT_URI = os.environ.get("GMAIL_REDIRECT_URI")

@app.get("/")
async def root():
    """
    Root endpoint for health check or landing page.
    """
    return {"message": "Gmail MCP API is running"}

# --- OAuth2 Callback Endpoint ---
@app.get("/auth/callback")
async def auth_callback(code: str = None, state: str = None, error: str = None):
    """
    Handles the OAuth2 callback from Google.
    This endpoint automatically processes the authorization code and stores the token.
    """
    # Check for errors
    if error:
        return HTMLResponse(f"""
        <html>
            <head>
                <title>Authentication Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                    .error {{ color: #d9534f; }}
                    .button {{ background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Authentication Error</h1>
                    <p class="error">There was an error during authentication: {error}</p>
                    <p>Please try again or contact support if the problem persists.</p>
                    <a href="/" class="button">Return to Home</a>
                </div>
            </body>
        </html>
        """)
    # Validate state to prevent CSRF attacks
    if not state or state not in auth_states:
        return HTMLResponse("""
        <html>
            <head>
                <title>Authentication Error</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                    .error { color: #d9534f; }
                    .button { background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Authentication Error</h1>
                    <p class="error">Invalid state parameter. This could be a security issue.</p>
                    <p>Please try again or contact support if the problem persists.</p>
                    <a href="/" class="button">Return to Home</a>
                </div>
            </body>
        </html>
        """)
    # Mark state as used
    auth_states[state]["used"] = True
    # Process the authorization code
    client_secret_file = 'client_secret_7774023189-5ga9j3epn8nja2aumfnmf09mh10osquh.apps.googleusercontent.com.json'
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
    flow.redirect_uri = REDIRECT_URI
    try:
        flow.fetch_token(code=code)
        creds = flow.credentials
        # Store the credentials
        with open('token.json', 'w') as token:
            token.write(creds.to_json())
        # Return a success page
        return HTMLResponse("""
        <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }
                    .success { color: #5cb85c; }
                    .button { background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; }
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Authentication Successful</h1>
                    <p class="success">Your Gmail account has been successfully connected!</p>
                    <p>You can now close this window and return to the application.</p>
                    <a href="/" class="button">Return to Home</a>
                </div>
            </body>
        </html>
        """)
    except Exception as e:
        return HTMLResponse(f"""
        <html>
            <head>
                <title>Authentication Error</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
                    .error {{ color: #d9534f; }}
                    .button {{ background-color: #4CAF50; color: white; padding: 10px 15px; text-decoration: none; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1>Authentication Error</h1>
                    <p class="error">There was an error during authentication: {str(e)}</p>
                    <p>Please try again or contact support if the problem persists.</p>
                    <a href="/" class="button">Return to Home</a>
                </div>
            </body>
        </html>
        """)

@app.get("/is_authenticated")
async def is_authenticated():
    token_file = 'token.json'
    if os.path.exists(token_file):
        try:
            creds = Credentials.from_authorized_user_file(token_file, SCOPES)
            if creds and creds.valid:
                return {"authenticated": True}
        except Exception:
            pass
    return {"authenticated": False}

@app.get("/connect_gmail")
async def connect_gmail():
    """
    Initiates the Gmail OAuth2 flow with a more user-friendly approach.
    Returns a URL that the frontend can use to redirect the user.
    """
    client_secret_file = 'client_secret_7774023189-5ga9j3epn8nja2aumfnmf09mh10osquh.apps.googleusercontent.com.json'
    
    # Generate a random state to prevent CSRF attacks
    state = secrets.token_urlsafe(16)
    auth_states[state] = {
        "created_at": time.time(),
        "used": False
    }
    
    flow = InstalledAppFlow.from_client_secrets_file(client_secret_file, SCOPES)
    flow.redirect_uri = REDIRECT_URI
    
    auth_url, _ = flow.authorization_url(
        prompt='consent',
        access_type='offline',
        include_granted_scopes='true',
        state=state
    )
    
    return {
        "auth_url": auth_url,
        "instructions": "Click the link to connect your Gmail account. You'll be redirected to Google to grant permission, then back to our application."
    }

@app.get("/list_emails")
async def list_emails(q: str = ""):
    try:
        result = mcp_discovery.run_tool("gmail_list_messages", query=q)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_email/{msg_id}")
async def get_email(msg_id: str):
    try:
        result = mcp_discovery.run_tool("gmail_get_message", msg_id=msg_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/search_emails")
async def search_emails(q: str):
    try:
        result = mcp_discovery.run_tool("gmail_search", query=q)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_thread/{thread_id}")
async def get_thread(thread_id: str):
    try:
        result = mcp_discovery.run_tool("gmail_read_thread", thread_id=thread_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/get_attachment/{msg_id}/{attachment_id}")
async def get_attachment(msg_id: str, attachment_id: str):
    try:
        attachments = mcp_discovery.run_tool("gmail_get_attachments", msg_id=msg_id)
        result = None
        for att in attachments:
            if att['filename'] and att['data']:
                result = att
                break
        if not result:
            raise HTTPException(status_code=404, detail="Attachment not found")
        return StreamingResponse(
            io.BytesIO(result['data']),
            media_type=result['mimeType'],
            headers={"Content-Disposition": f"attachment; filename={result['filename']}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/ask_agent")
async def ask_agent(query: str):
    from adk_agent.agent import run_agent
    try:
        result = await run_agent(query)
        return result
    except Exception as e:
        print("Exception in /ask_agent:", e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# =========================================================
# Example: How to connect to an external MCP toolset or memory service
# =========================================================
#
# The following is a template for connecting to an external MCP toolset,
# memory service, or any modular component using an async factory pattern.
#
# This pattern is useful for integrating Redis-backed memory, external tool servers,
# or microservices into your agent or backend. It is especially useful for
# session/long-term memory, distributed toolsets, or advanced modularity.
#
# Usage:
# 1. Import the relevant classes (e.g., MCPToolset, StdioServerParameters).
# 2. Use the async factory to connect to the service, passing command, args, and env as needed.
# 3. Use the returned 'tools' object to access registered tools or memory APIs.
# 4. Use 'exit_stack' for resource cleanup (context management).
#
# Example (uncomment and adapt as needed):
#
# from some_module import MCPToolset, StdioServerParameters
#
# tools, exit_stack = await MCPToolset.from_server(
#     connection_params=StdioServerParameters(
#         command='uvx',
#         args=['--from', 'git+https://github.com/adhikasp/mcp-reddit.git', 'mcp-reddit'],
#         # Optional: Add environment variables if needed by the MCP server,
#         # e.g., credentials if mcp-reddit required them.
#         # env=os.environ.copy()
#     )
# )
#
# # Now you can use 'tools' to access the toolset or memory service.
# # Remember to use 'exit_stack' for cleanup if needed.
#
# To adapt this for your memory module:
# - Replace MCPToolset with your memory manager class (e.g., MemoryManager, SessionMemory).
# - Replace the command/args/env with those needed for your memory or tool service.
# - Use the returned object to load/save session or long-term memory as needed.
#
# This pattern enables modular, scalable, and maintainable integration of external services.




