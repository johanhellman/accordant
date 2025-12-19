import json
from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.config.packs import PackService
from backend.models import CouncilConfiguration, CouncilPack, TenantBase


# Setup in-memory SQLite DB for testing
@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    TenantBase.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_custom_pack(session):
    config = {"personalities": ["a", "b"], "consensus_strategy": "strat_1"}
    result = PackService.create_custom_pack(session, "My Pack", config, "Desc")

    assert result["display_name"] == "My Pack"
    assert result["is_system"] is False
    assert result["config"] == config

    # Verify DB
    db_pack = session.query(CouncilPack).first()
    assert db_pack.display_name == "My Pack"
    assert json.loads(db_pack.config_json) == config


def test_get_all_packs_merges_sources(session):
    # 1. Create a custom pack
    PackService.create_custom_pack(session, "Custom Pack", {"p": []})

    # 2. Mock system packs
    with patch("os.path.exists", return_value=True):
        with patch("os.listdir", return_value=["sys_pack.yaml"]):
            with patch("builtins.open", new_callable=MagicMock):
                # Mock YAML content
                mock_file = MagicMock()
                mock_file.read.return_value = "id: sys_pack\ndisplay_name: System Pack"
                # We need to mock yaml.safe_load actually, or ensure open returns something safe_loadable
                with patch(
                    "yaml.safe_load",
                    return_value={
                        "id": "sys_pack",
                        "display_name": "System Pack",
                        "personalities": ["sys"],
                    },
                ):
                    packs = PackService.get_all_packs(session, "org_1")

                    assert len(packs) == 2
                    ids = {p["id"] for p in packs}
                    assert "sys_pack" in ids
                    # Custom pack ID is UUID so we check count mostly


def test_apply_custom_pack(session):
    # Create pack
    c_pack = PackService.create_custom_pack(
        session, "C Pack", {"personalities": ["p1"], "consensus_strategy": "strat_c"}
    )
    pack_id = c_pack["id"]

    # Apply
    config = PackService.apply_pack(session, "user_1", pack_id, "org_1")

    assert config["user_id"] == "user_1"
    assert config["active_pack_id"] == pack_id
    assert config["active_personalities"] == ["p1"]

    # Verify DB
    db_config = session.query(CouncilConfiguration).filter_by(user_id="user_1").first()
    assert db_config.active_pack_id == pack_id


@patch("backend.config.packs.DEFAULTS_PACKS_DIR", "/mock/dir")
def test_apply_system_pack(session):
    # Mock system pack existence
    with patch("os.path.exists", return_value=True):
        with patch("os.listdir", return_value=["sys_pack.yaml"]):
            with patch("builtins.open"):
                with patch(
                    "yaml.safe_load",
                    return_value={
                        "id": "sys_pack",
                        "personalities": ["sys_p"],
                        "consensus_strategy": "sys_s",
                    },
                ):
                    config = PackService.apply_pack(session, "user_2", "sys_pack", "org_1")

                    assert config["active_pack_id"] == "sys_pack"
                    assert config["active_strategy_id"] == "sys_s"


def test_get_active_configuration_fallback(session):
    # No config exists
    with patch(
        "backend.config.packs.get_all_personalities",
        return_value=[{"id": "p1", "enabled": True}, {"id": "p2", "enabled": False}],
    ):
        config = PackService.get_active_configuration(session, "user_new", "org_1")

        assert config["active_pack_id"] is None
        assert config["personalities"] == ["p1"]


def test_get_active_configuration_existing(session):
    # Setup config
    db_config = CouncilConfiguration(
        user_id="user_exist",
        active_pack_id="pack_x",
        active_personalities_json=json.dumps(["px"]),
        active_strategy_id="sx",
    )
    session.add(db_config)
    session.commit()

    config = PackService.get_active_configuration(session, "user_exist", "org_1")
    assert config["active_pack_id"] == "pack_x"
    assert config["personalities"] == ["px"]
    assert config["strategy_id"] == "sx"
