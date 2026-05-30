import time
from dataclasses import dataclass
from uuid import uuid4


class FakeAITimeoutError(Exception):
    """
    Raised when the fake AI provider times out.
    """


class FakeAIInvalidOutputError(Exception):
    """
    Raised when the fake AI provider returns invalid output.
    """


class FakeAIRejectedRequestError(Exception):
    """
    Raised when the fake AI provider rejects the request.
    """


@dataclass(frozen=True, slots=True)
class FakeAIAnalysisResult:
    analysis_id: str
    summary: str


class FakeAIProvider:
    """
    Fake AI provider used to simulate LLM/AI analysis behavior.
    """

    def run_analysis(
        self,
        *,
        subject_ref: str,
        prompt_ref: str,
        simulation: str | None = None,
    ) -> FakeAIAnalysisResult:
        """
        Run fake AI analysis.
        """
        if simulation == "timeout":
            raise FakeAITimeoutError(
                "AI provider timed out"
            )

        if simulation == "invalid_output":
            raise FakeAIInvalidOutputError(
                "AI provider returned invalid output"
            )

        if simulation == "rejected_request":
            raise FakeAIRejectedRequestError(
                "AI provider rejected the request"
            )

        if simulation == "slow_success":
            time.sleep(10)

        return FakeAIAnalysisResult(
            analysis_id=f"fake-ai-analysis-{uuid4()}",
            summary=f"Fake analysis generated for subject_ref={subject_ref}",
        )