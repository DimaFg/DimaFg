from dataclasses import replace
from datetime import UTC, datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from app.application.leads.create import (
    CreateLead,
    CreateLeadCommand,
    LeadPolicy,
    RateLimitError,
    UnknownServiceError,
)
from app.application.notifications.notify_lead import NotifyLead
from app.domain.leads.entities import LeadReceipt, LeadStatus, NotificationStatus
from app.domain.notifications import LeadMessage, PermanentError, TemporaryError


@pytest.fixture
def use_case():
    leads = Mock()
    leads.find_by_key.return_value = None
    leads.find_duplicate.return_value = None
    leads.count_by_ip.return_value = 0
    leads.count_by_contact.return_value = 0
    leads.next_public_number.return_value = "2026-00001"
    return CreateLead(
        leads=leads,
        services=Mock(),
        outbox=Mock(),
        uow=Mock(),
        clock=Mock(now=lambda: datetime(2026, 10, 29, tzinfo=UTC)),
        policy=LeadPolicy(3, 5, 3, 10, "policy-v1", 8),
    )


@pytest.fixture
def command():
    return CreateLeadCommand(
        name="Анна",
        contact="@Anna_Photo",
        message="Портрет",
        elapsed_ms=15000,
        ip_hash="ip-hash",
    )


def test_creation_saves_lead_and_outbox_in_one_uow(use_case, command):
    result = use_case(command)
    lead = use_case.leads.add.call_args.args[0]
    assert result.created and result.lead.public_number == "2026-00001"
    assert lead.contact_normalized == "@anna_photo"
    assert lead.status == LeadStatus.new
    assert lead.notification_status == NotificationStatus.pending
    assert lead.privacy_policy_version == "policy-v1"
    use_case.outbox.enqueue.assert_called_once_with("lead.notify", {"lead_id": str(lead.id)}, 8)
    use_case.uow.commit.assert_called_once()


@pytest.mark.parametrize("field", ["website", "elapsed_ms"])
def test_spam_is_saved_without_notification(use_case, command, field):
    use_case(replace(command, **{field: "spam" if field == "website" else 1}))
    lead = use_case.leads.add.call_args.args[0]
    assert lead.status == LeadStatus.spam
    assert lead.notification_status == NotificationStatus.skipped
    use_case.outbox.enqueue.assert_not_called()


def test_duplicate_returned_before_limits(use_case, command):
    use_case.leads.find_duplicate.return_value = LeadReceipt("2026-00042")
    use_case.leads.count_by_contact.return_value = 100
    result = use_case(command)
    assert not result.created and result.lead.public_number == "2026-00042"
    use_case.leads.count_by_contact.assert_not_called()
    use_case.leads.add.assert_not_called()


def test_same_key_returns_original_even_if_payload_changed(use_case, command):
    use_case.leads.find_by_key.return_value = LeadReceipt("2026-00042")
    result = use_case(replace(command, idempotency_key="same-key", service="unknown"))
    assert not result.created
    use_case.services.find_active_id.assert_not_called()


def test_unknown_service_does_not_match_duplicate(use_case, command):
    use_case.services.find_active_id.return_value = None
    use_case.leads.find_duplicate.return_value = LeadReceipt("2026-00042")
    with pytest.raises(UnknownServiceError):
        use_case(replace(command, service="unknown"))
    use_case.leads.find_duplicate.assert_not_called()
    use_case.uow.rollback.assert_called_once()


def test_duplicate_search_includes_resolved_service(use_case, command):
    service_id = uuid4()
    use_case.services.find_active_id.return_value = service_id
    use_case(replace(command, service="personal"))
    assert use_case.leads.find_duplicate.call_args.args[2] == service_id


@pytest.mark.parametrize("by_contact", [True, False])
def test_limits_do_not_write_lead_or_outbox(use_case, command, by_contact):
    if by_contact:
        use_case.leads.count_by_contact.return_value = 3
    else:
        use_case.leads.count_by_ip.return_value = 5
    with pytest.raises(RateLimitError) as exc:
        use_case(command)
    assert exc.value.per_contact == by_contact
    use_case.leads.add.assert_not_called()
    use_case.outbox.enqueue.assert_not_called()
    use_case.uow.rollback.assert_called_once()


@pytest.mark.parametrize("failure_at", ["add", "outbox", "commit"])
def test_write_failures_rollback_whole_transaction(use_case, command, failure_at):
    target = {
        "add": use_case.leads.add,
        "outbox": use_case.outbox.enqueue,
        "commit": use_case.uow.commit,
    }[failure_at]
    target.side_effect = RuntimeError("write failed")
    with pytest.raises(RuntimeError, match="write failed"):
        use_case(command)
    use_case.uow.rollback.assert_called_once()


def test_notification_retry_preserves_successful_channels():
    repository = Mock()
    repository.get_message.return_value = LeadMessage("1", "Анна", "@anna", None, "", "/admin")
    tg = Mock(channel="telegram")
    tg.send.side_effect = TemporaryError("unavailable")
    email = Mock(channel="email")
    progress = Mock()
    notify = NotifyLead(repository, [tg, email], progress)
    done = []
    lead_id = uuid4()
    with pytest.raises(TemporaryError):
        notify(lead_id, done)
    assert done == ["email"]
    progress.mark_done.assert_called_once_with("email")
    repository.mark_sent.assert_not_called()
    tg.send.side_effect = None
    notify(lead_id, done)
    assert done == ["email", "telegram"]
    email.send.assert_called_once()
    repository.mark_sent.assert_called_once_with(lead_id)


def test_missing_lead_is_permanent_notification_failure():
    repository = Mock()
    repository.get_message.return_value = None
    sender = Mock(channel="telegram")
    with pytest.raises(PermanentError):
        NotifyLead(repository, [sender], Mock())(uuid4(), [])
    sender.send.assert_not_called()
