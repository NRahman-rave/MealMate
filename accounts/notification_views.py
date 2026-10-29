from django.contrib import messages

from django.shortcuts import (
    redirect,
    render,
)

from django.views.decorators.http import (
    require_POST,
)

from .models import (
    MealMateUser,
    Notification,
)

from .notification_service import (
    sync_pickup_reminders,
)


# =========================================================
# CURRENT USER
# =========================================================

def get_current_user(request):

    user_id = request.session.get(
        "user_id"
    )

    if not user_id:
        return None


    return MealMateUser.objects.filter(
        id=user_id,
        is_active=True,
    ).first()


# =========================================================
# NOTIFICATION PAGE
# =========================================================

def notifications_page(request):

    current_user = get_current_user(
        request
    )


    if not current_user:

        return redirect(
            "login"
        )


    if current_user.role == "user":

        sync_pickup_reminders(
            current_user.id
        )


    notifications = list(

        Notification.objects.filter(
            user_id=current_user.id
        ).order_by(
            "-created_at"
        )[:100]
    )


    unread_count = (
        Notification.objects.filter(
            user_id=current_user.id,
            is_read=False,
        ).count()
    )


    return render(
        request,
        "notifications.html",
        {
            "current_user": (
                current_user
            ),

            "notifications": (
                notifications
            ),

            "unread_count": (
                unread_count
            ),
        }
    )


# =========================================================
# OPEN NOTIFICATION
# =========================================================

def open_notification(
    request,
    notification_id,
):

    current_user = get_current_user(
        request
    )


    if not current_user:

        return redirect(
            "login"
        )


    notification = (
        Notification.objects.filter(
            id=notification_id,
            user_id=current_user.id,
        ).first()
    )


    if not notification:

        messages.error(
            request,
            "Notification not found."
        )

        return redirect(
            "notifications"
        )


    if not notification.is_read:

        notification.is_read = True

        notification.save(
            update_fields=[
                "is_read"
            ]
        )


    if notification.link:

        return redirect(
            notification.link
        )


    return redirect(
        "notifications"
    )


# =========================================================
# MARK ALL READ
# =========================================================

@require_POST
def mark_all_notifications_read(
    request,
):

    current_user = get_current_user(
        request
    )


    if not current_user:

        return redirect(
            "login"
        )


    Notification.objects.filter(
        user_id=current_user.id,
        is_read=False,
    ).update(
        is_read=True
    )


    messages.success(
        request,
        "All notifications marked as read."
    )


    return redirect(
        "notifications"
    )


# =========================================================
# CLEAR READ NOTIFICATIONS
# =========================================================

@require_POST
def clear_read_notifications(
    request,
):

    current_user = get_current_user(
        request
    )


    if not current_user:

        return redirect(
            "login"
        )


    Notification.objects.filter(
        user_id=current_user.id,
        is_read=True,
    ).delete()


    messages.success(
        request,
        "Read notifications cleared."
    )


    return redirect(
        "notifications"
    )