import secrets
from datetime import timedelta

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from django.utils import timezone
from django.views.decorators.http import require_POST

from .extension_service import (
    get_reservation_lifecycle,
)

from .models import (
    FoodPost,
    MealMateUser,
    Notification,
    Reservation,
    UserActivity,
)


ALLOWED_EXTENSIONS = {
    5,
    10,
    20,
}


def get_current_user(
    request
):

    user_id = (
        request.session.get(
            "user_id"
        )
    )


    if not user_id:

        return None


    return (
        MealMateUser.objects.filter(
            id=user_id,
            is_active=True,
        ).first()
    )


def create_notification(
    user_id,
    notification_type,
    title,
    message,
    link=None,
    dedupe_key=None,
):

    if (
        dedupe_key
        and
        Notification.objects.filter(
            user_id=user_id,
            dedupe_key=dedupe_key,
        ).exists()
    ):

        return


    Notification.objects.create(
        user_id=user_id,
        notification_type=(
            notification_type
        ),
        title=title,
        message=message,
        link=link,
        dedupe_key=dedupe_key,
        is_read=False,
    )


def log_activity(
    user_id,
    activity_type,
    food_post_id=None,
    value=None,
):

    UserActivity.objects.create(
        user_id=user_id,
        activity_type=activity_type,
        food_post_id=food_post_id,
        value=value,
    )


# =========================================================
# BUSINESS EXTENDS EXPIRED RESERVATION
# =========================================================

@require_POST
def business_extend_reservation(
    request,
    reservation_id,
    minutes,
):

    current_user = get_current_user(
        request
    )


    if not current_user:

        return redirect(
            "login"
        )


    if current_user.role != "business":

        return redirect(
            "dashboard"
        )


    if minutes not in ALLOWED_EXTENSIONS:

        messages.error(
            request,
            "Invalid extension time."
        )

        return redirect(
            "business_dashboard"
        )


    with transaction.atomic():

        reservation = (
            Reservation.objects
            .select_for_update()
            .filter(
                id=reservation_id
            )
            .first()
        )


        if not reservation:

            messages.error(
                request,
                "Reservation not found."
            )

            return redirect(
                "business_dashboard"
            )


        food = (
            FoodPost.objects
            .select_for_update()
            .filter(
                id=reservation.food_post_id,
                business_id=current_user.id,
            )
            .first()
        )


        if not food:

            messages.error(
                request,
                "You cannot manage this reservation."
            )

            return redirect(
                "business_dashboard"
            )


        reservation.food = food


        lifecycle = (
            get_reservation_lifecycle(
                reservation
            )
        )


        if lifecycle["state"] not in {
            "expired",
            "extension_declined",
        }:

            messages.error(
                request,
                (
                    "This reservation has not "
                    "expired yet."
                )
            )

            return redirect(
                "business_dashboard"
            )


        if (
            reservation.extension_status
            == "declined"
        ):

            messages.error(
                request,
                (
                    "The customer already said "
                    "they cannot collect during "
                    "the extension."
                )
            )

            return redirect(
                "business_dashboard"
            )


        now = timezone.now()

        new_deadline = (
            now
            +
            timedelta(
                minutes=minutes
            )
        )


        reservation.status = (
            "expired"
        )

        reservation.extension_status = (
            "offered"
        )

        reservation.extension_minutes = (
            minutes
        )

        reservation.extension_offered_at = (
            now
        )

        reservation.extension_expires_at = (
            new_deadline
        )

        reservation.save(
            update_fields=[
                "status",
                "extension_status",
                "extension_minutes",
                "extension_offered_at",
                "extension_expires_at",
                "updated_at",
            ]
        )


        create_notification(
            user_id=reservation.user_id,
            notification_type=(
                "pickup_extension"
            ),
            title=(
                "Pickup time extended"
            ),
            message=(
                f"{food.food_name}: "
                f"the business has offered you "
                f"an extra {minutes} minutes "
                f"to collect your meal."
            ),
            link="/reservations/",
            dedupe_key=(
                f"extension-offer-"
                f"{reservation.id}-"
                f"{int(now.timestamp())}"
            ),
        )


        log_activity(
            user_id=reservation.user_id,
            activity_type=(
                "pickup_extension_offered"
            ),
            food_post_id=food.id,
            value=str(
                minutes
            ),
        )


    messages.success(
        request,
        (
            f"Customer offered an extra "
            f"{minutes} minutes."
        )
    )


    return redirect(
        "business_dashboard"
    )


# =========================================================
# USER ANSWERS EXTENSION
# =========================================================

@require_POST
def extension_response(
    request,
    reservation_id,
    answer,
):

    current_user = get_current_user(
        request
    )


    if not current_user:

        return redirect(
            "login"
        )


    if current_user.role != "user":

        return redirect(
            "business_dashboard"
        )


    if answer not in {
        "coming",
        "cant_collect",
    }:

        messages.error(
            request,
            "Invalid response."
        )

        return redirect(
            "my_reservations"
        )


    with transaction.atomic():

        reservation = (
            Reservation.objects
            .select_for_update()
            .filter(
                id=reservation_id,
                user_id=current_user.id,
            )
            .first()
        )


        if not reservation:

            messages.error(
                request,
                "Reservation not found."
            )

            return redirect(
                "my_reservations"
            )


        food = (
            FoodPost.objects
            .select_for_update()
            .filter(
                id=reservation.food_post_id
            )
            .first()
        )


        if not food:

            messages.error(
                request,
                "Food post no longer exists."
            )

            return redirect(
                "my_reservations"
            )


        if (
            reservation.extension_status
            != "offered"
            or
            not reservation.extension_expires_at
        ):

            messages.error(
                request,
                (
                    "This extension offer is "
                    "no longer available."
                )
            )

            return redirect(
                "my_reservations"
            )


        now = timezone.now()


        if (
            now
            >=
            reservation.extension_expires_at
        ):

            reservation.status = "expired"

            reservation.extension_status = (
                "expired"
            )

            reservation.save(
                update_fields=[
                    "status",
                    "extension_status",
                    "updated_at",
                ]
            )


            messages.error(
                request,
                (
                    "The extended pickup time "
                    "has already ended."
                )
            )

            return redirect(
                "my_reservations"
            )


        # =================================================
        # I'M COMING
        # =================================================

        if answer == "coming":

            reservation.status = (
                "reserved"
            )

            reservation.extension_status = (
                "accepted"
            )

            reservation.collection_intent = (
                "coming"
            )

            reservation.collection_confirmed_at = (
                now
            )


            reservation.save(
                update_fields=[
                    "status",
                    "extension_status",
                    "collection_intent",
                    "collection_confirmed_at",
                    "updated_at",
                ]
            )


            create_notification(
                user_id=food.business_id,
                notification_type=(
                    "extension_confirmed"
                ),
                title=(
                    "Customer confirmed extension"
                ),
                message=(
                    f"The customer confirmed "
                    f"they are coming for "
                    f"{food.food_name} during "
                    f"the extended pickup window."
                ),
                link="/business/dashboard/",
                dedupe_key=(
                    f"extension-confirmed-"
                    f"{reservation.id}-"
                    f"{int(now.timestamp())}"
                ),
            )


            log_activity(
                user_id=current_user.id,
                activity_type=(
                    "pickup_extension_accepted"
                ),
                food_post_id=food.id,
                value=str(
                    reservation.extension_minutes
                    or ""
                ),
            )


            messages.success(
                request,
                (
                    "Extension confirmed. "
                    "Please collect before the "
                    "new deadline."
                )
            )


            return redirect(
                "my_reservations"
            )


        # =================================================
        # CAN'T MAKE IT
        # =================================================

        reservation.status = (
            "expired"
        )

        reservation.extension_status = (
            "declined"
        )

        reservation.collection_intent = (
            "cant_collect"
        )

        reservation.collection_confirmed_at = (
            now
        )


        reservation.save(
            update_fields=[
                "status",
                "extension_status",
                "collection_intent",
                "collection_confirmed_at",
                "updated_at",
            ]
        )


        create_notification(
            user_id=food.business_id,
            notification_type=(
                "extension_declined"
            ),
            title=(
                "Customer cannot collect"
            ),
            message=(
                f"The customer cannot collect "
                f"{food.food_name} during the "
                f"extended pickup window."
            ),
            link="/business/dashboard/",
            dedupe_key=(
                f"extension-declined-"
                f"{reservation.id}-"
                f"{int(now.timestamp())}"
            ),
        )


        log_activity(
            user_id=current_user.id,
            activity_type=(
                "pickup_extension_declined"
            ),
            food_post_id=food.id,
            value="cant_collect",
        )


    messages.success(
        request,
        (
            "Thanks for letting the business know. "
            "This reservation is now expired."
        )
    )


    return redirect(
        "my_reservations"
    )


# =========================================================
# BUSINESS PICKUP VERIFICATION
# =========================================================

@require_POST
def business_verify_pickup_code(
    request,
    reservation_id,
):

    current_user = get_current_user(
        request
    )


    if not current_user:

        return redirect(
            "login"
        )


    if current_user.role != "business":

        return redirect(
            "dashboard"
        )


    entered_code = (
        request.POST.get(
            "pickup_code",
            ""
        )
        .strip()
        .upper()
        .replace(
            " ",
            ""
        )
    )


    if not entered_code:

        messages.error(
            request,
            "Enter the customer's pickup code."
        )

        return redirect(
            "business_dashboard"
        )


    with transaction.atomic():

        reservation = (
            Reservation.objects
            .select_for_update()
            .filter(
                id=reservation_id
            )
            .first()
        )


        if not reservation:

            messages.error(
                request,
                "Reservation not found."
            )

            return redirect(
                "business_dashboard"
            )


        food = (
            FoodPost.objects
            .select_for_update()
            .filter(
                id=reservation.food_post_id,
                business_id=current_user.id,
            )
            .first()
        )


        if not food:

            messages.error(
                request,
                "You cannot manage this reservation."
            )

            return redirect(
                "business_dashboard"
            )


        reservation.food = food


        lifecycle = (
            get_reservation_lifecycle(
                reservation
            )
        )


        if lifecycle["state"] not in {
            "active",
            "extended",
        }:

            messages.error(
                request,
                (
                    "The pickup window has expired. "
                    "Extend the collection time first."
                )
            )

            return redirect(
                "business_dashboard"
            )


        correct_code = (
            reservation.pickup_code
            or ""
        ).upper()


        if not secrets.compare_digest(
            entered_code,
            correct_code
        ):

            messages.error(
                request,
                "Incorrect pickup code."
            )

            return redirect(
                "business_dashboard"
            )


        reservation.status = (
            "collected"
        )

        reservation.collected_at = (
            timezone.now()
        )


        reservation.save(
            update_fields=[
                "status",
                "collected_at",
                "updated_at",
            ]
        )


    messages.success(
        request,
        (
            "Pickup code verified. "
            "Food marked as collected."
        )
    )


    return redirect(
        "business_dashboard"
    )