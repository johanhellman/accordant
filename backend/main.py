"""FastAPI backend for LLM Council."""

import json
import logging
import mimetypes
import os
import uuid
from datetime import datetime, timedelta
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from fastapi.security import OAuth2PasswordRequestForm

# Register MIME types explicitly to ensure correct content types are served
# This is critical for CSS and JS files to be properly recognized by browsers
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('application/javascript', '.mjs')
mimetypes.add_type('application/json', '.json')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('image/png', '.png')
mimetypes.add_type('image/jpeg', '.jpg')
mimetypes.add_type('image/jpeg', '.jpeg')
mimetypes.add_type('image/gif', '.gif')
mimetypes.add_type('image/webp', '.webp')
mimetypes.add_type('font/woff', '.woff')
mimetypes.add_type('font/woff2', '.woff2')
mimetypes.add_type('font/ttf', '.ttf')
mimetypes.add_type('font/otf', '.otf')
mimetypes.add_type('application/x-font-ttf', '.ttf')
mimetypes.add_type('application/font-woff', '.woff')

from . import admin_routes, admin_users_routes, org_routes, storage

from .auth import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    Token,
    create_access_token,
    get_current_admin_user,
    get_current_user,
    get_password_hash,
    verify_password,
)
from .council import (
    generate_conversation_title,
    run_full_council,
)
from .logging_config import setup_logging
from .organizations import get_org_api_config, list_orgs
from .schema import (
    Conversation,
    ConversationMetadata,
    CreateConversationRequest,
    SendMessageRequest,
)
from .streaming import run_council_streaming
from .users import User, UserCreate, UserInDB, UserResponse, create_user, get_user
from .voting_history import record_votes

# --- Helper Functions ---


async def _handle_conversation_title(
    conversation_id: str,
    user_message: str,
    is_first_message: bool,
    org_id: str,
    api_key: str,
    base_url: str,
) -> None:
    """
    Generate and update conversation title if this is the first message.

    Args:
        conversation_id: The conversation ID
        user_message: The user's message content
        is_first_message: Whether this is the first message in the conversation
        org_id: Organization ID
        api_key: API key for LLM service
        base_url: Base URL for LLM service
    """
    if is_first_message:
        title = await generate_conversation_title(
            user_message, org_id=org_id, api_key=api_key, base_url=base_url
        )
        storage.update_conversation_title(conversation_id, title, org_id=org_id)


def _record_voting_history(
    conversation_id: str,
    conversation: dict[str, Any],
    stage2_results: list[dict[str, Any]],
    label_to_model: dict[str, str],
    user_id: str,
    org_id: str,
) -> None:
    """
    Record voting history for the current turn.

    Args:
        conversation_id: The conversation ID
        conversation: The conversation dict with messages
        stage2_results: Results from Stage 2 (peer rankings)
        label_to_model: Mapping from anonymous labels to model names
        user_id: User ID
        org_id: Organization ID
    """
    try:
        # Calculate turn number: (len(messages) + 1) // 2
        # messages includes the latest user message, so len is odd (1, 3, 5...)
        # Turn 1: len=1 -> (1+1)//2 = 1
        # Turn 2: len=3 -> (3+1)//2 = 2
        turn_number = (len(conversation["messages"]) + 1) // 2

        record_votes(
            conversation_id,
            stage2_results,
            label_to_model,
            conversation_title=conversation.get("title", "Unknown"),
            turn_number=turn_number,
            user_id=user_id,
            org_id=org_id,
        )
    except Exception as e:
        logger.error(f"Error recording votes: {e}")


# Initialize logging
setup_logging()
logger = logging.getLogger(__name__)

# Validate API key at startup - REMOVED for multi-tenancy
# API keys are now configured per organization.
# if not OPENROUTER_API_KEY:
#     raise ValueError(
#         "OPENROUTER_API_KEY or LLM_API_KEY environment variable is required. "
#         "Please set it in your .env file. See .env.example for reference."
#     )

app = FastAPI(title="Accordant API")

# Include Admin Routes
app.include_router(admin_routes.router)
app.include_router(admin_users_routes.router)
app.include_router(org_routes.router)

# Configure CORS from environment variables
_cors_origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000")
if isinstance(_cors_origins_env, str):
    # Support both comma-separated and JSON array formats
    try:
        cors_origins = json.loads(_cors_origins_env)
    except json.JSONDecodeError:
        cors_origins = [origin.strip() for origin in _cors_origins_env.split(",") if origin.strip()]
else:
    cors_origins = _cors_origins_env

_cors_methods_env = os.getenv("CORS_METHODS", "*")
cors_methods = _cors_methods_env.split(",") if _cors_methods_env != "*" else ["*"]

_cors_headers_env = os.getenv("CORS_HEADERS", "*")
cors_headers = _cors_headers_env.split(",") if _cors_headers_env != "*" else ["*"]

# Enable CORS with configurable settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=os.getenv("CORS_CREDENTIALS", "true").lower() == "true",
    allow_methods=cors_methods,
    allow_headers=cors_headers,
)

# Warn if CORS is permissive in production
if os.getenv("ENVIRONMENT", "").lower() in ("production", "prod") and (
    cors_origins == ["*"] or "*" in cors_origins
):
    logger.warning(
        "⚠️  SECURITY WARNING: CORS is configured to allow all origins (*) in production. "
        "This is insecure and should be restricted to specific domains. "
        "Set CORS_ORIGINS environment variable to a comma-separated list of allowed origins."
    )


from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# ... (Auth Routes and others) ...

@app.get("/api/health")
async def health_check():
    """
    Health check endpoint for Docker/Kubernetes.
    Checks backend responsiveness and storage writability.
    """
    import time
    from pathlib import Path
    from datetime import datetime

    start_time = time.time()
    
    # Check storage
    storage_status = "ok"
    writable = False
    data_dir = os.path.join(os.getcwd(), "data")
    try:
        # Try to write a temp file to data dir
        test_file = os.path.join(data_dir, ".healthcheck")
        with open(test_file, "w") as f:
            f.write("ok")
        os.remove(test_file)
        writable = True
    except Exception as e:
        storage_status = f"error: {str(e)}"
        logger.error(f"Health check storage error: {e}")

    # Response time
    process_time = (time.time() - start_time) * 1000

    status_overall = "healthy" if writable else "unhealthy"
    
    # Service Unavailable if unhealthy
    if status_overall == "unhealthy":
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service unhealthy"
        )

    return {
        "status": status_overall,
        "service": "Accordant API",
        "version": "0.2.1",  # Should ideally match config
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "checks": {
            "backend": {
                "status": "ok",
                "response_time_ms": round(process_time, 2)
            },
            "storage": {
                "status": storage_status,
                "writable": writable,
                "data_dir": data_dir
            }
        },
        "response_time_ms": round(process_time, 2)
    }


# Mount Static Files (Frontend)
# Only if the build directory exists (i.e. inside Docker or after manual build)
static_dir = os.getenv("STATIC_DIR", "frontend/dist")
if os.path.isdir(static_dir):
    logger.info(f"Serving static files from {static_dir}")
    app.mount("/assets", StaticFiles(directory=f"{static_dir}/assets"), name="assets")
    
    # Root route for SPA - must be defined before catch-all
    @app.get("/")
    async def root():
        """Serve the index page for the SPA."""
        return FileResponse(os.path.join(static_dir, "index.html"))
    
    # Catch-all for SPA routes (must be last route)
    @app.get("/{full_path:path}")
    async def serve_spa(full_path: str):
        # Don't intercept API routes (they should have matched above, but just in case of 404s)
        if full_path.startswith("api/"):
             raise HTTPException(status_code=404, detail="API endpoint not found")
        
        # Check if file exists in root of dist (e.g. favicon.ico, vite.svg)
        file_path = os.path.join(static_dir, full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
            
        # Otherwise serve index.html for SPA routing
        return FileResponse(os.path.join(static_dir, "index.html"))
else:
    logger.warning(f"Static directory {static_dir} not found. Running in API-only mode.")
    
    @app.get("/")
    async def root():
        """Retrieve health info if static not served."""
        return {"status": "ok", "service": "Accordant API (Dev Mode)"}


# --- Auth Routes ---


@app.post("/api/auth/register", response_model=Token)
async def register(user_data: UserCreate):
    # Check if user exists
    if get_user(user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already registered"
        )

    # Create user without assigning to any organization
    # User will create or join an organization after registration
    # The first organization created becomes the "default" organization

    # Edge case check: if orgs exist but no users, flag as data inconsistency
    orgs = list_orgs()
    if orgs:
        from .users import get_all_users

        existing_users = get_all_users()
        if not existing_users:
            logger.warning(
                "Data inconsistency detected: Organizations exist but no users. "
                "This should not happen in normal operation. "
                "Please check data consistency."
            )

    # Create user object (org_id will be None initially)
    hashed_password = get_password_hash(user_data.password)
    user_in_db = UserInDB(
        id=str(uuid.uuid4()),
        username=user_data.username,
        password_hash=hashed_password,
        org_id=None,  # User will create/join org after registration
    )

    user = create_user(user_in_db)

    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/api/auth/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """Login to get access token."""
    user = get_user(form_data.username)
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/api/auth/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    """Get current user details."""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        is_admin=current_user.is_admin,
        is_instance_admin=current_user.is_instance_admin,
        org_id=current_user.org_id,
    )


@app.get("/api/admin/stats/voting")
async def get_voting_statistics(current_user: User = Depends(get_current_admin_user)):
    """Get aggregated voting statistics."""
    from .voting_history import load_voting_history

    return load_voting_history(current_user.org_id)


# --- Conversation Routes ---


@app.get("/api/conversations", response_model=list[ConversationMetadata])
async def list_conversations(current_user: User = Depends(get_current_user)):
    """List all conversations for the current user."""
    return storage.list_conversations(user_id=current_user.id, org_id=current_user.org_id)


@app.post("/api/conversations", response_model=Conversation)
async def create_conversation(
    request: CreateConversationRequest, current_user: User = Depends(get_current_user)
):
    """Create a new conversation."""
    conversation_id = str(uuid.uuid4())
    conversation = storage.create_conversation(
        conversation_id, user_id=current_user.id, org_id=current_user.org_id
    )
    return conversation


@app.get("/api/conversations/{conversation_id}", response_model=Conversation)
async def get_conversation(conversation_id: str, current_user: User = Depends(get_current_user)):
    """Get a specific conversation with all its messages."""
    conversation = storage.get_conversation(conversation_id, org_id=current_user.org_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Verify ownership
    if conversation.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this conversation")

    return conversation


@app.post("/api/conversations/{conversation_id}/message", response_model=dict[str, Any])
async def send_message(
    conversation_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send a message and run the 3-stage council process.
    Returns the complete response with all stages.
    """
    # Load conversation to verify existence and ownership
    conversation = storage.get_conversation(conversation_id, org_id=current_user.org_id)
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    if conversation.get("user_id") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    # Check if this is the first message
    is_first_message = len(conversation["messages"]) == 0

    # Add user message
    storage.add_user_message(conversation_id, request.content, org_id=current_user.org_id)

    # FIX: Update in-memory conversation to include the new message so it's not stale
    conversation["messages"].append({"role": "user", "content": request.content})

    # Get Org API Config
    api_key, base_url = get_org_api_config(current_user.org_id)

    # Generate title if this is the first message
    await _handle_conversation_title(
        conversation_id,
        request.content,
        is_first_message,
        current_user.org_id,
        api_key,
        base_url,
    )

    # Run the 3-stage council process
    # Pass the full conversation history (which now includes the user's latest message)
    stage1_results, stage2_results, stage3_result, metadata = await run_full_council(
        request.content,
        conversation["messages"],
        org_id=current_user.org_id,
        api_key=api_key,
        base_url=base_url,
    )

    # Record voting history
    _record_voting_history(
        conversation_id,
        conversation,
        stage2_results,
        metadata["label_to_model"],
        current_user.id,
        current_user.org_id,
    )

    # Add assistant message with all stages
    storage.add_assistant_message(
        conversation_id, stage1_results, stage2_results, stage3_result, org_id=current_user.org_id
    )

    # Return the complete response with metadata
    return {
        "stage1": stage1_results,
        "stage2": stage2_results,
        "stage3": stage3_result,
        "metadata": metadata,
    }


@app.post("/api/conversations/{conversation_id}/message/stream")
async def send_message_stream(
    conversation_id: str,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
):
    """
    Send a message and stream the 3-stage council process.
    Returns Server-Sent Events as each stage completes.
    """
    # Check if conversation exists
    conversation = storage.get_conversation(conversation_id, org_id=current_user.org_id)
    if conversation is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Check ownership
    if conversation.get("user_id") and conversation.get("user_id") != current_user.id:
        raise HTTPException(status_code=404, detail="Conversation not found")

    # Get Org API Config
    api_key, base_url = get_org_api_config(current_user.org_id)

    return StreamingResponse(
        run_council_streaming(
            conversation_id,
            request.content,
            conversation,
            org_id=current_user.org_id,
            api_key=api_key,
            base_url=base_url,
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


if __name__ == "__main__":
    import os

    import uvicorn

    # Host configuration: Use HOST env var or default to 0.0.0.0 for development
    # For production, set HOST=127.0.0.1 or specific IP address
    host = os.getenv("HOST", "0.0.0.0")  # nosec B104
    port = int(os.getenv("PORT", "8001"))
    uvicorn.run(app, host=host, port=port)
