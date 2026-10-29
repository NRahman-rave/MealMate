from django import template

from accounts.models import Notification

from accounts.notification_service import (
    sync_pickup_reminders,
)

from accounts.reliability_service import (
    sync_expired_reservations,
)


register = template.Library()


@register.inclusion_tag(
    "notification_bell.html",
    takes_context=True,
)
def notification_bell(context):

    request = context.get(
        "request"
    )


    if not request:

        return {
            "logged_in": False
        }


    user_id = request.session.get(
        "user_id"
    )


    if not user_id:

        return {
            "logged_in": False
        }


    # =====================================================
    # RESCUEGUARD
    #
    # Automatically identify expired reservations.
    # =====================================================

    try:

        sync_expired_reservations(
            user_id
        )

    except Exception:

        pass


    # =====================================================
    # PICKUP REMINDERS
    # =====================================================

    try:

        sync_pickup_reminders(
            user_id
        )

    except Exception:

        pass


    unread_count = (
        Notification.objects.filter(
            user_id=user_id,
            is_read=False,
        ).count()
    )


    return {

        "logged_in":
            True,

        "unread_count":
            unread_count,
    }