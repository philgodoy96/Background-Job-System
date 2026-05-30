from app.domain.jobs.entities import Job
from app.domain.jobs.errors import NonRetryableJobError, RetryableJobError
from app.handlers.base import HandlerResult
from app.providers.fake_ai_provider import (
    FakeAIInvalidOutputError,
    FakeAIProvider,
    FakeAIRejectedRequestError,
    FakeAITimeoutError,
)


class RunAIAnalysisHandler:
    """
    Handler for run_ai_analysis jobs.
    """

    def __init__(self, *, ai_provider: FakeAIProvider) -> None:
        self.ai_provider = ai_provider

    def handle(self, job: Job) -> HandlerResult:
        """
        Execute a run_ai_analysis job.

        Expected payload:
        {
            "subject_ref": "user_123",
            "prompt_ref": "risk_analysis_v1",
            "simulation": "success | slow_success | timeout | invalid_output | rejected_request"
        }
        """
        payload = job.payload

        subject_ref = payload.get("subject_ref")
        prompt_ref = payload.get("prompt_ref")
        simulation = payload.get("simulation")

        if not subject_ref:
            raise NonRetryableJobError(
                "run_ai_analysis payload requires subject_ref",
                code="MISSING_SUBJECT_REF",
            )

        if not prompt_ref:
            raise NonRetryableJobError(
                "run_ai_analysis payload requires prompt_ref",
                code="MISSING_PROMPT_REF",
            )

        try:
            result = self.ai_provider.run_analysis(
                subject_ref=subject_ref,
                prompt_ref=prompt_ref,
                simulation=simulation,
            )
        except FakeAITimeoutError as exc:
            raise RetryableJobError(
                str(exc),
                code="AI_TIMEOUT",
            ) from exc
        except FakeAIInvalidOutputError as exc:
            raise RetryableJobError(
                str(exc),
                code="AI_INVALID_OUTPUT",
            ) from exc
        except FakeAIRejectedRequestError as exc:
            raise NonRetryableJobError(
                str(exc),
                code="AI_REJECTED_REQUEST",
            ) from exc

        return HandlerResult(
            message="AI analysis completed successfully",
            metadata={
                "analysis_id": result.analysis_id,
                "summary": result.summary,
            },
        )