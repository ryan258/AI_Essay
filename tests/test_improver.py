"""Tests for EssayImprover."""

from src.improver import EssayImprover
from src.models.base import AIModel


RAW_ESSAY = (
    "this essay will explore why renewable energy matters and how policy changes are shaping adoption across economies "
    "it argues that policy consistency accelerates transition.\n\n"
    "additionally renewable energy reduces emissions and creates jobs communities benefit when governments invest in infrastructure "
    "and pair incentives with education this paragraph mixes ideas without clear stops and has double  spaces\n\n"
    "in conclusion renewable energy is essential for a sustainable future and coordinated action can accelerate progress"
)


class MockModel(AIModel):
    """Simple synchronous mock model."""

    def __init__(self, response: str):
        super().__init__("mock-model")
        self.response = response
        self.called = 0

    def call(self, prompt: str):
        self.called += 1
        return True, self.response, ""

    async def acall(self, prompt: str):
        return True, self.response, ""


def test_improver_reaches_target_with_heuristics():
    """Heuristic improver should raise the score enough to hit the target."""
    improver = EssayImprover()
    result = improver.improve(RAW_ESSAY, cycles=3, target_score=60)

    assert result.iterations  # At least one iteration ran
    assert result.reached_target is True
    assert result.final_scores.overall >= 60

    # Verify improvement from the first cycle
    first = result.iterations[0]
    assert first.scores_after.overall >= first.scores_before.overall
    assert first.after_text != first.before_text


def test_improver_uses_model_when_available():
    """Improver should delegate to the provided model before falling back."""
    mock = MockModel("Improved essay text with clearer sentences.")
    improver = EssayImprover(model=mock)

    result = improver.improve("original text needs work", cycles=1, target_score=80)

    assert mock.called == 1
    assert result.iterations
    assert result.iterations[0].applied_model == "mock-model"
    assert "Improved essay text" in result.final_text


def test_improver_early_exit_when_target_met():
    """If the essay already meets the target, no iterations should run."""
    improver = EssayImprover()
    high_quality = (
        "This essay will explore the benefits of clean energy adoption, outlining the thesis that "
        "consistent policy support accelerates transition.\n\n"
        "Clean energy reduces emissions, spurs innovation, and improves public health. Governments can "
        "pair incentives with infrastructure to drive adoption.\n\n"
        "In conclusion, aligned policy and investment create a faster path to a resilient energy future."
    )

    result = improver.improve(high_quality, cycles=3, target_score=50)

    assert result.reached_target is True
    assert result.iterations == []


def test_improver_handles_empty_text():
    """Empty essays should not crash and should report no target reached."""
    improver = EssayImprover()

    result = improver.improve("", cycles=2, target_score=50)

    assert result.reached_target is False
    assert result.final_text == ""
    assert result.iterations  # Should still attempt improvements
