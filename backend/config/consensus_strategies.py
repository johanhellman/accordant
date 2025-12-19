import logging
import os

from sqlalchemy.orm import Session

from backend.config.paths import PROJECT_ROOT
from backend.models import ConsensusStrategy

logger = logging.getLogger(__name__)

CONSENSUS_PROMPTS_DIR = os.path.join(PROJECT_ROOT, "data", "defaults", "consensus")


class ConsensusStrategyService:
    """Service for managing Consensus Strategies (System + Custom)."""

    @staticmethod
    def get_all_strategies(session: Session, org_id: str) -> list[dict]:
        """
        Get all available consensus strategies.
        Merges System Strategies (MD files) and Custom Strategies (DB).
        """
        strategies = {}

        # 1. Load System Strategies (Files)
        if os.path.exists(CONSENSUS_PROMPTS_DIR):
            for filename in os.listdir(CONSENSUS_PROMPTS_DIR):
                if filename.endswith(".md"):
                    strat_id = filename.replace(".md", "")
                    try:
                        filepath = os.path.join(CONSENSUS_PROMPTS_DIR, filename)
                        with open(filepath) as f:
                            content = f.read()
                            strategies[strat_id] = {
                                "id": strat_id,
                                "display_name": strat_id.replace("_", " ").title(),
                                "description": "System strategy",
                                "prompt_content": content,
                                "source": "system",
                                "is_editable": False,  # Only true for Instance Admin (future)
                            }
                    except Exception as e:
                        logger.error(f"Failed to load system strategy {filename}: {e}")

        # 2. Load Custom Strategies (DB)
        db_strats = session.query(ConsensusStrategy).all()
        for s in db_strats:
            strategies[s.id] = {
                "id": s.id,
                "display_name": s.display_name,
                "description": s.description,
                "prompt_content": s.prompt_content,
                "source": "custom",
                "is_editable": True,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }

        return list(strategies.values())

    @staticmethod
    def get_strategy(session: Session, strategy_id: str) -> dict | None:
        """Resolve a strategy by ID."""
        # 1. Check DB
        db_strat = session.query(ConsensusStrategy).filter_by(id=strategy_id).first()
        if db_strat:
            return {
                "id": db_strat.id,
                "display_name": db_strat.display_name,
                "description": db_strat.description,
                "prompt_content": db_strat.prompt_content,
                "source": "custom",
                "is_editable": True,
            }

        # 2. Check File
        filepath = os.path.join(CONSENSUS_PROMPTS_DIR, f"{strategy_id}.md")
        if os.path.exists(filepath):
            try:
                with open(filepath) as f:
                    content = f.read()
                    return {
                        "id": strategy_id,
                        "display_name": strategy_id.replace("_", " ").title(),
                        "description": "System strategy",
                        "prompt_content": content,
                        "source": "system",
                        "is_editable": False,
                    }
            except Exception as e:
                logger.error(f"Failed to load strategy file {strategy_id}: {e}")

        return None

    @staticmethod
    def create_custom_strategy(
        session: Session, id: str, display_name: str, prompt_content: str, description: str = None
    ) -> dict:
        """Create a new custom strategy in the DB."""
        # Check collision with system files
        if os.path.exists(os.path.join(CONSENSUS_PROMPTS_DIR, f"{id}.md")):
            raise ValueError(f"Strategy ID '{id}' conflicts with a system strategy.")

        if session.query(ConsensusStrategy).filter_by(id=id).first():
            raise ValueError(f"Strategy ID '{id}' already exists.")

        new_strat = ConsensusStrategy(
            id=id,
            display_name=display_name,
            description=description,
            prompt_content=prompt_content,
        )
        session.add(new_strat)
        session.commit()
        session.refresh(new_strat)

        return {
            "id": new_strat.id,
            "display_name": new_strat.display_name,
            "description": new_strat.description,
            "prompt_content": new_strat.prompt_content,
            "source": "custom",
            "is_editable": True,
        }
