import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from app.core.time import utc_now


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    """
    Calculates retry delays using exponential backoff with jitter.
    """

    base_delay_seconds: int = 2
    max_delay_seconds: int = 60
    jitter_ratio: float = 0.2

    def get_delay_seconds(self, attempt_count: int) -> int:
        """
        Return the retry delay in seconds.

        attempt_count represents how many attempts have already happened.

        Example:
        - after attempt_count=1, delay is around 2 seconds
        - after attempt_count=2, delay is around 4 seconds
        - after attempt_count=3, delay is around 8 seconds
        """
        if attempt_count <= 0:
            attempt_count = 1

        exponential_delay = self.base_delay_seconds * (2 ** (attempt_count - 1))
        capped_delay = min(exponential_delay, self.max_delay_seconds)

        jitter_amount = capped_delay * self.jitter_ratio
        min_delay = capped_delay - jitter_amount
        max_delay = capped_delay + jitter_amount

        return max(1, int(random.uniform(min_delay, max_delay)))

    def get_next_available_at(
        self,
        attempt_count: int,
        *,
        now: datetime | None = None,
    ) -> datetime:
        """
        Return when the job should become available again.
        """
        current_time = now or utc_now()
        delay_seconds = self.get_delay_seconds(attempt_count)

        return current_time + timedelta(seconds=delay_seconds)