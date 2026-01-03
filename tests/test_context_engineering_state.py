"""Tests for context engineering state models."""

import pytest
import yaml
from pydantic import ValidationError

from src.context_engineering.models.state import (
    AnalysisMode,
    ContextEngineeringState,
    FileRef,
    FocusArea,
    ImmutableState,
    MutableState,
)


class TestFocusArea:
    """Tests for FocusArea enum."""

    def test_all_values(self):
        """Test that all focus area values can be instantiated."""
        assert FocusArea.ALL == "all"
        assert FocusArea.CONTEXT == "context"
        assert FocusArea.ORCHESTRATION == "orchestration"
        assert FocusArea.HANDOFF == "handoff"

    def test_from_string(self):
        """Test creating FocusArea from string."""
        assert FocusArea("all") == FocusArea.ALL
        assert FocusArea("context") == FocusArea.CONTEXT


class TestAnalysisMode:
    """Tests for AnalysisMode enum."""

    def test_all_values(self):
        """Test that all analysis mode values can be instantiated."""
        assert AnalysisMode.QUICK == "quick"
        assert AnalysisMode.STANDARD == "standard"
        assert AnalysisMode.DEEP == "deep"

    def test_from_string(self):
        """Test creating AnalysisMode from string."""
        assert AnalysisMode("quick") == AnalysisMode.QUICK
        assert AnalysisMode("standard") == AnalysisMode.STANDARD


class TestFileRef:
    """Tests for FileRef model."""

    def test_valid_without_content(self):
        """Test FileRef without content."""
        ref = FileRef(
            id="file1",
            path="/path/to/file.py",
            loaded=False,
            token_estimate=100,
        )
        assert ref.id == "file1"
        assert ref.path == "/path/to/file.py"
        assert not ref.loaded
        assert ref.content is None
        assert ref.token_estimate == 100

    def test_valid_with_content(self):
        """Test FileRef with content."""
        ref = FileRef(
            id="file2",
            path="/path/to/file.py",
            loaded=True,
            content="print('hello')",
            token_estimate=50,
        )
        assert ref.id == "file2"
        assert ref.loaded
        assert ref.content == "print('hello')"

    def test_missing_required_field(self):
        """Test FileRef with missing required field."""
        with pytest.raises(ValidationError) as exc_info:
            FileRef(
                id="file3",
                path="/path/to/file.py",
                loaded=True,
                # Missing token_estimate
            )
        assert "token_estimate" in str(exc_info.value)


class TestImmutableState:
    """Tests for ImmutableState model."""

    def test_valid_instantiation(self):
        """Test creating valid ImmutableState."""
        state = ImmutableState(
            plugin_path="/path/to/plugin",
            focus_area=FocusArea.CONTEXT,
            mode=AnalysisMode.STANDARD,
            user_request="Analyze context patterns",
            session_id="session-123",
        )
        assert state.plugin_path == "/path/to/plugin"
        assert state.focus_area == FocusArea.CONTEXT
        assert state.mode == AnalysisMode.STANDARD
        assert state.user_request == "Analyze context patterns"
        assert state.session_id == "session-123"

    def test_immutable_frozen(self):
        """Test that ImmutableState is frozen and cannot be modified."""
        state = ImmutableState(
            plugin_path="/path/to/plugin",
            focus_area=FocusArea.ALL,
            mode=AnalysisMode.QUICK,
            user_request="Test request",
            session_id="session-456",
        )

        with pytest.raises(ValidationError) as exc_info:
            state.plugin_path = "/new/path"  # type: ignore

        assert "frozen" in str(exc_info.value).lower()

    def test_with_enum_strings(self):
        """Test creating ImmutableState with enum string values."""
        state = ImmutableState(
            plugin_path="/path/to/plugin",
            focus_area="orchestration",  # type: ignore
            mode="deep",  # type: ignore
            user_request="Test",
            session_id="session-789",
        )
        assert state.focus_area == FocusArea.ORCHESTRATION
        assert state.mode == AnalysisMode.DEEP


class TestMutableState:
    """Tests for MutableState model."""

    def test_default_instantiation(self):
        """Test creating MutableState with defaults."""
        state = MutableState()
        assert state.file_cache == {}
        assert state.intermediate_results == {}
        assert state.phase_completed == []
        assert state.user_selections == {}

    def test_with_data(self):
        """Test MutableState with initial data."""
        file_ref = FileRef(
            id="file1",
            path="/path/to/file.py",
            loaded=True,
            token_estimate=100,
        )
        state = MutableState(
            file_cache={"file1": file_ref},
            intermediate_results={"analysis": {"result": "data"}},
            phase_completed=["grounding", "analysis"],
            user_selections={"focus": "context"},
        )
        assert "file1" in state.file_cache
        assert state.file_cache["file1"] == file_ref
        assert state.intermediate_results["analysis"]["result"] == "data"
        assert len(state.phase_completed) == 2
        assert state.user_selections["focus"] == "context"

    def test_update_operations(self):
        """Test updating MutableState fields."""
        state = MutableState()

        # Add to file cache
        state.file_cache["file1"] = FileRef(
            id="file1", path="/test.py", loaded=False, token_estimate=50
        )
        assert "file1" in state.file_cache

        # Add intermediate result
        state.intermediate_results["step1"] = {"data": "value"}
        assert state.intermediate_results["step1"]["data"] == "value"

        # Add completed phase
        state.phase_completed.append("phase1")
        assert "phase1" in state.phase_completed

        # Add user selection
        state.user_selections["choice"] = "option1"
        assert state.user_selections["choice"] == "option1"


class TestContextEngineeringState:
    """Tests for ContextEngineeringState model."""

    @pytest.fixture
    def immutable_state(self) -> ImmutableState:
        """Fixture for ImmutableState."""
        return ImmutableState(
            plugin_path="/path/to/plugin",
            focus_area=FocusArea.ALL,
            mode=AnalysisMode.STANDARD,
            user_request="Test request",
            session_id="session-123",
        )

    @pytest.fixture
    def mutable_state(self) -> MutableState:
        """Fixture for MutableState."""
        return MutableState(
            phase_completed=["grounding"],
            user_selections={"mode": "standard"},
        )

    def test_valid_instantiation(
        self, immutable_state: ImmutableState, mutable_state: MutableState
    ):
        """Test creating valid ContextEngineeringState."""
        state = ContextEngineeringState(
            immutable=immutable_state,
            mutable=mutable_state,
        )
        assert state.immutable == immutable_state
        assert state.mutable == mutable_state
        assert state.lock_holder is None
        assert state.version == 1

    def test_with_lock(self, immutable_state: ImmutableState):
        """Test ContextEngineeringState with lock holder."""
        state = ContextEngineeringState(
            immutable=immutable_state,
            mutable=MutableState(),
            lock_holder="grounding-agent",
        )
        assert state.lock_holder == "grounding-agent"

    def test_version_incrementing(self, immutable_state: ImmutableState):
        """Test version incrementing for optimistic locking."""
        state = ContextEngineeringState(
            immutable=immutable_state,
            mutable=MutableState(),
        )
        assert state.version == 1

        # Simulate version increment
        state.version += 1
        assert state.version == 2

        state.version += 1
        assert state.version == 3

    def test_serialization(
        self, immutable_state: ImmutableState, mutable_state: MutableState
    ):
        """Test state serialization to dict."""
        state = ContextEngineeringState(
            immutable=immutable_state,
            mutable=mutable_state,
            lock_holder="test-agent",
            version=5,
        )

        data = state.model_dump()
        assert data["immutable"]["plugin_path"] == "/path/to/plugin"
        assert data["immutable"]["focus_area"] == "all"
        assert data["immutable"]["mode"] == "standard"
        assert data["mutable"]["phase_completed"] == ["grounding"]
        assert data["lock_holder"] == "test-agent"
        assert data["version"] == 5

    def test_deserialization(self):
        """Test state deserialization from dict."""
        data = {
            "immutable": {
                "plugin_path": "/test/plugin",
                "focus_area": "context",
                "mode": "quick",
                "user_request": "Test",
                "session_id": "session-999",
            },
            "mutable": {
                "file_cache": {},
                "intermediate_results": {"test": "data"},
                "phase_completed": ["phase1", "phase2"],
                "user_selections": {},
            },
            "lock_holder": "coordinator",
            "version": 3,
        }

        state = ContextEngineeringState(**data)
        assert state.immutable.plugin_path == "/test/plugin"
        assert state.immutable.focus_area == FocusArea.CONTEXT
        assert state.immutable.mode == AnalysisMode.QUICK
        assert state.mutable.intermediate_results["test"] == "data"
        assert len(state.mutable.phase_completed) == 2
        assert state.lock_holder == "coordinator"
        assert state.version == 3


class TestStateYAMLSerialization:
    """Tests for YAML serialization of state models."""

    def test_round_trip_serialization(self):
        """Test that state can be serialized to YAML and back."""
        # Create state
        original = ContextEngineeringState(
            immutable=ImmutableState(
                plugin_path="/test/plugin",
                focus_area=FocusArea.ORCHESTRATION,
                mode=AnalysisMode.DEEP,
                user_request="Analyze plugin",
                session_id="session-yaml-test",
            ),
            mutable=MutableState(
                file_cache={
                    "file1": FileRef(
                        id="file1",
                        path="/test/file.py",
                        loaded=True,
                        content="print('test')",
                        token_estimate=25,
                    )
                },
                phase_completed=["grounding", "analysis"],
                user_selections={"focus": "orchestration"},
            ),
            lock_holder="test-agent",
            version=7,
        )

        # Serialize to YAML (use mode='json' for safe serialization)
        yaml_str = yaml.dump(original.model_dump(mode="json"), default_flow_style=False)

        # Deserialize back
        data = yaml.safe_load(yaml_str)
        restored = ContextEngineeringState(**data)

        # Verify
        assert restored.immutable.plugin_path == original.immutable.plugin_path
        assert restored.immutable.focus_area == original.immutable.focus_area
        assert restored.immutable.mode == original.immutable.mode
        assert restored.lock_holder == original.lock_holder
        assert restored.version == original.version
        assert "file1" in restored.mutable.file_cache
        assert (
            restored.mutable.file_cache["file1"].content
            == original.mutable.file_cache["file1"].content
        )
        assert len(restored.mutable.phase_completed) == 2
