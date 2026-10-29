from uuid import UUID

from app.domain.notifications import PermanentError, TemporaryError
from app.port.notifications import DeliveryProgress, NotificationRepository, Sender


class NotifyLead:
    def __init__(
        self,
        repository: NotificationRepository,
        senders: list[Sender],
        progress: DeliveryProgress,
    ):
        self.repository = repository
        self.senders = senders
        self.progress = progress

    def __call__(self, lead_id: UUID, done: list[str]) -> None:
        message = self.repository.get_message(lead_id)
        if message is None:
            raise PermanentError("lead not found")
        errors = []
        for sender in self.senders:
            if sender.channel in done:
                continue
            try:
                sender.send(message)
            except TemporaryError as exc:
                errors.append(f"{sender.channel}: {exc}")
                continue
            self.progress.mark_done(sender.channel)
            done.append(sender.channel)
        if errors:
            raise TemporaryError("; ".join(errors))
        self.repository.mark_sent(lead_id)
