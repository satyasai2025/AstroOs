from dataclasses import dataclass

from apps.api.models.notification import (
    EmailDeliveryStatus,
    EmailLogModel,
    NotificationPreferenceModel,
)
from apps.api.models.payment import (
    PaymentCustomerModel,
    PaymentModel,
    PaymentProviderType,
    PaymentStatus,
    PaymentWebhookEventModel,
)


@dataclass
class JobRequest:
    task_type: str
    payload: dict

# Add additional fields as needed