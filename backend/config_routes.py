from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.auth import get_current_user
from backend.config.consensus_strategies import ConsensusStrategyService
from backend.config.packs import PackService
from backend.database import get_tenant_session
from backend.users import User

router = APIRouter(prefix="/api/config", tags=["Configuration"])


# Dependency to get organization-scoped session
def get_org_session(current_user: User = Depends(get_current_user)):
    db = get_tenant_session(current_user.org_id)
    try:
        yield db
    finally:
        db.close()


# --- Pydantic Models ---


class PackConfigModel(BaseModel):
    personalities: list[str]
    consensus_strategy: str | None = None
    system_prompts: dict[str, str] = {}


class CreatePackRequest(BaseModel):
    display_name: str
    description: str | None = None
    config: PackConfigModel


class PackResponse(BaseModel):
    id: str
    display_name: str
    description: str | None
    is_system: bool
    source: str
    config: PackConfigModel
    created_at: str | None


class ActiveConfigResponse(BaseModel):
    active_pack_id: str | None
    personalities: list[str]
    strategy_id: str | None
    system_prompts: dict[str, str]


class StrategyResponse(BaseModel):
    id: str
    display_name: str
    description: str | None
    prompt_content: str
    source: str
    is_editable: bool


class CreateStrategyRequest(BaseModel):
    id: str
    display_name: str
    description: str | None
    prompt_content: str


# --- Routes ---


@router.get("/packs", response_model=list[PackResponse])
async def list_packs(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_org_session)
):
    """List all available council packs (System + Custom)."""
    return PackService.get_all_packs(db, current_user.org_id)


@router.post("/packs", response_model=PackResponse)
async def create_pack(
    request: CreatePackRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_org_session),
):
    """Create a new custom pack."""
    # Only admins? Or any user? ADR didn't specify strict RBAC for packs.
    # Assuming any user can create packs for now, or restrict to Admins.
    # Let's restrict to Org Admins for safety to match ADR-016 spirit.
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can create custom packs")

    return PackService.create_custom_pack(
        db, request.display_name, request.config.model_dump(), request.description
    )


@router.post("/packs/{pack_id}/apply")
async def apply_pack(
    pack_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_org_session),
):
    """Apply a pack to the current user's active configuration."""
    try:
        result = PackService.apply_pack(db, current_user.id, pack_id, current_user.org_id)
        return {"status": "success", "message": f"Pack {pack_id} applied", "active_state": result}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/active", response_model=ActiveConfigResponse)
async def get_active_config(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_org_session)
):
    """Get the current active configuration for the user."""
    return PackService.get_active_configuration(db, current_user.id, current_user.org_id)


@router.get("/strategies", response_model=list[StrategyResponse])
async def list_strategies(
    current_user: User = Depends(get_current_user), db: Session = Depends(get_org_session)
):
    """List available consensus strategies."""
    return ConsensusStrategyService.get_all_strategies(db, current_user.org_id)


@router.post("/strategies", response_model=StrategyResponse)
async def create_strategy(
    request: CreateStrategyRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_org_session),
):
    """Create a new custom consensus strategy."""
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Only admins can create custom strategies")

    try:
        return ConsensusStrategyService.create_custom_strategy(
            db, request.id, request.display_name, request.prompt_content, request.description
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/strategies/{strategy_id}", response_model=StrategyResponse)
async def get_strategy(
    strategy_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_org_session),
):
    """Get details of a specific strategy."""
    strat = ConsensusStrategyService.get_strategy(db, strategy_id)
    if not strat:
        raise HTTPException(status_code=404, detail="Strategy not found")
    return strat
