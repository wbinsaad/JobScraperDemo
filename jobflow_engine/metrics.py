from dataclasses import dataclass


@dataclass
class PipelineMetrics:
    fetched_count: int = 0
    queued_count: int = 0
    processed_count: int = 0
    failed_count: int = 0

    def record_fetched(self, count: int) -> None:
        self.fetched_count += count

    def record_queued(self, count: int) -> None:
        self.queued_count += count

    def record_processed(self) -> None:
        self.processed_count += 1

    def record_failed(self) -> None:
        self.failed_count += 1

    def snapshot(self, queue_depth: int) -> dict[str, int]:
        return {
            "fetched_count": self.fetched_count,
            "queued_count": self.queued_count,
            "processed_count": self.processed_count,
            "failed_count": self.failed_count,
            "queue_depth": queue_depth,
        }