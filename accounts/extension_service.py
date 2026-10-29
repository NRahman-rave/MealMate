from datetime import timedelta

from django.utils import timezone

from .models import (
    FoodPost,
    Reservation,
    RescueOffer,
    RescueRequest,
)


# =========================================================
# SETTINGS
# =========================================================

BUSINESS_EXTENSION_WINDOW_MINUTES = 10


# =========================================================
# FOOD HELPER
# =========================================================

def get_food(
    reservation
):

    if hasattr(
        reservation,
        "food"
    ):

        if reservation.food:

            return reservation.food


    return (
        FoodPost.objects.filter(
            id=reservation.food_post_id
        ).first()
    )


# =========================================================
# EXPIRE RESERVATION
# =========================================================

def expire_reservation(
    reservation,
):

    if reservation.status in {
        "collected",
        "cancelled",
    }:

        return


    reservation.status = "expired"


    if reservation.extension_status in {
        "offered",
        "accepted",
    }:

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


    # -----------------------------------------------------
    # CLOSE ANY OPEN RESCUE
    # -----------------------------------------------------

    open_requests = list(
        RescueRequest.objects.filter(
            reservation_id=reservation.id,
            status="open",
        )
    )


    for rescue_request in open_requests:

        rescue_request.status = (
            "expired"
        )

        rescue_request.save(
            update_fields=[
                "status"
            ]
        )


        RescueOffer.objects.filter(
            request_id=rescue_request.id,
            status="pending",
        ).update(
            status="expired",
            responded_at=timezone.now(),
        )


# =========================================================
# EXTENSION AVAILABILITY
# =========================================================

def get_business_extension_deadline(
    food
):

    if not food:

        return None


    if not food.pickup_end:

        return None


    return (
        food.pickup_end
        +
        timedelta(
            minutes=(
                BUSINESS_EXTENSION_WINDOW_MINUTES
            )
        )
    )


def can_business_offer_extension(
    food
):

    deadline = (
        get_business_extension_deadline(
            food
        )
    )


    if not deadline:

        return False


    now = timezone.now()


    return (
        food.pickup_end
        <= now
        <
        deadline
    )


# =========================================================
# RESERVATION LIFECYCLE
# =========================================================

def get_reservation_lifecycle(
    reservation,
    save=True,
):

    now = timezone.now()

    food = get_food(
        reservation
    )


    # =====================================================
    # COLLECTED
    # =====================================================

    if reservation.status == "collected":

        return {

            "state":
                "collected",

            "label":
                "Collected",

            "css":
                "collected",

            "deadline":
                reservation.collected_at,

            "extension_minutes":
                None,

            "extension_window_deadline":
                None,

        }


    # =====================================================
    # CANCELLED
    # =====================================================

    if reservation.status == "cancelled":

        return {

            "state":
                "cancelled",

            "label":
                "Cancelled",

            "css":
                "cancelled",

            "deadline":
                None,

            "extension_minutes":
                None,

            "extension_window_deadline":
                None,

        }


    # =====================================================
    # EXTENSION OFFERED
    # WAITING FOR CUSTOMER RESPONSE
    # =====================================================

    if (
        reservation.extension_status
        == "offered"
        and
        reservation.extension_expires_at
    ):

        if (
            now
            <
            reservation.extension_expires_at
        ):

            return {

                "state":
                    "extension_offered",

                "label":
                    "Extension Offered",

                "css":
                    "extension",

                "deadline":
                    reservation.extension_expires_at,

                "extension_minutes":
                    reservation.extension_minutes,

                "extension_window_deadline":
                    None,

            }


        if save:

            expire_reservation(
                reservation
            )


        return {

            "state":
                "extension_closed",

            "label":
                "Expired",

            "css":
                "expired",

            "deadline":
                reservation.extension_expires_at,

            "extension_minutes":
                reservation.extension_minutes,

            "extension_window_deadline":
                None,

        }


    # =====================================================
    # EXTENSION ACCEPTED
    # =====================================================

    if (
        reservation.extension_status
        == "accepted"
        and
        reservation.extension_expires_at
    ):

        if (
            reservation.status == "reserved"
            and
            now
            <
            reservation.extension_expires_at
        ):

            return {

                "state":
                    "extended",

                "label":
                    "Extended",

                "css":
                    "extended",

                "deadline":
                    reservation.extension_expires_at,

                "extension_minutes":
                    reservation.extension_minutes,

                "extension_window_deadline":
                    None,

            }


        if save:

            expire_reservation(
                reservation
            )


        return {

            "state":
                "extension_closed",

            "label":
                "Expired",

            "css":
                "expired",

            "deadline":
                reservation.extension_expires_at,

            "extension_minutes":
                reservation.extension_minutes,

            "extension_window_deadline":
                None,

        }


    # =====================================================
    # CUSTOMER DECLINED EXTENSION
    # =====================================================

    if (
        reservation.extension_status
        == "declined"
    ):

        if (
            save
            and
            reservation.status
            != "expired"
        ):

            reservation.status = (
                "expired"
            )

            reservation.save(
                update_fields=[
                    "status",
                    "updated_at",
                ]
            )


        return {

            "state":
                "extension_declined",

            "label":
                "Expired",

            "css":
                "expired",

            "deadline":
                reservation.extension_expires_at,

            "extension_minutes":
                reservation.extension_minutes,

            "extension_window_deadline":
                None,

        }


    # =====================================================
    # NORMAL ACTIVE RESERVATION
    # =====================================================

    if (
        reservation.status == "reserved"
        and
        food
        and
        food.pickup_end
        >
        now
    ):

        return {

            "state":
                "active",

            "label":
                "Reserved",

            "css":
                "reserved",

            "deadline":
                food.pickup_end,

            "extension_minutes":
                None,

            "extension_window_deadline":
                (
                    get_business_extension_deadline(
                        food
                    )
                ),

        }


    # =====================================================
    # ORIGINAL PICKUP WINDOW ENDED
    # =====================================================

    if (
        food
        and
        food.pickup_end
        <=
        now
    ):

        if (
            reservation.status
            == "reserved"
            and
            save
        ):

            expire_reservation(
                reservation
            )


        extension_deadline = (
            get_business_extension_deadline(
                food
            )
        )


        # -------------------------------------------------
        # BUSINESS STILL HAS 10 MINUTES TO EXTEND
        # -------------------------------------------------

        if (
            extension_deadline
            and
            now
            <
            extension_deadline
        ):

            return {

                "state":
                    "expired",

                "label":
                    "Expired",

                "css":
                    "expired",

                "deadline":
                    food.pickup_end,

                "extension_minutes":
                    None,

                "extension_window_deadline":
                    extension_deadline,

            }


        # -------------------------------------------------
        # 10 MINUTE BUSINESS WINDOW HAS ENDED
        # -------------------------------------------------

        return {

            "state":
                "extension_closed",

            "label":
                "Expired",

            "css":
                "expired",

            "deadline":
                food.pickup_end,

            "extension_minutes":
                None,

            "extension_window_deadline":
                extension_deadline,

        }


    # =====================================================
    # FALLBACK EXPIRED
    # =====================================================

    if reservation.status == "expired":

        return {

            "state":
                "extension_closed",

            "label":
                "Expired",

            "css":
                "expired",

            "deadline":
                (
                    reservation.extension_expires_at
                    if
                    reservation.extension_expires_at
                    else (
                        food.pickup_end
                        if food
                        else None
                    )
                ),

            "extension_minutes":
                reservation.extension_minutes,

            "extension_window_deadline":
                None,

        }


    # =====================================================
    # FALLBACK ACTIVE
    # =====================================================

    return {

        "state":
            "active",

        "label":
            "Reserved",

        "css":
            "reserved",

        "deadline":
            (
                food.pickup_end
                if food
                else None
            ),

        "extension_minutes":
            None,

        "extension_window_deadline":
            (
                get_business_extension_deadline(
                    food
                )
                if food
                else None
            ),

    }


# =========================================================
# SYNC EXPIRED RESERVATIONS
# =========================================================

def sync_expired_reservations(
    user_id=None,
):

    queryset = (
        Reservation.objects.filter(
            status__in=[
                "reserved",
                "expired",
            ]
        )
    )


    if user_id is not None:

        queryset = (
            queryset.filter(
                user_id=user_id
            )
        )


    changed = 0


    for reservation in queryset:

        old_status = (
            reservation.status
        )

        old_extension_status = (
            reservation.extension_status
        )


        get_reservation_lifecycle(
            reservation,
            save=True,
        )


        if (
            reservation.status
            != old_status
            or
            reservation.extension_status
            != old_extension_status
        ):

            changed += 1


    return changed