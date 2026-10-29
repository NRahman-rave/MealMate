from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from .models import (
    FoodPost,
    Notification,
    Reservation,
)


# =========================================================
# CREATE NOTIFICATION
# =========================================================

def create_notification(
    user_id,
    notification_type,
    title,
    message,
    link=None,
    dedupe_key=None,
):

    if dedupe_key:

        existing = Notification.objects.filter(
            user_id=user_id,
            dedupe_key=dedupe_key,
        ).first()

        if existing:
            return existing


    return Notification.objects.create(

        user_id=user_id,

        notification_type=notification_type,

        title=title,

        message=message,

        link=link,

        is_read=False,

        dedupe_key=dedupe_key,
    )


# =========================================================
# CREATE PICKUP REMINDERS
# =========================================================

def sync_pickup_reminders(user_id):

    now = timezone.now()

    reminder_limit = (
        now
        + timedelta(
            minutes=45
        )
    )


    reservations = (
        Reservation.objects.filter(
            user_id=user_id,
            status="reserved",
        )
    )


    food_ids = {
        reservation.food_post_id
        for reservation in reservations
    }


    foods = {

        food.id: food

        for food in FoodPost.objects.filter(
            id__in=food_ids
        )
    }


    for reservation in reservations:

        food = foods.get(
            reservation.food_post_id
        )

        if not food:
            continue


        if food.pickup_end <= now:
            continue


        if food.pickup_end > reminder_limit:
            continue


        remaining = (
            food.pickup_end
            - now
        )


        minutes = max(
            1,
            int(
                remaining.total_seconds()
                / 60
            )
        )


        create_notification(

            user_id=user_id,

            notification_type=(
                "pickup_reminder"
            ),

            title="Pickup Ending Soon",

            message=(
                f"Your pickup for "
                f"{food.food_name} ends in "
                f"about {minutes} minutes."
            ),

            link=reverse(
                "my_reservations"
            ),

            dedupe_key=(
                f"pickup-reminder-"
                f"{reservation.id}"
            ),
        )