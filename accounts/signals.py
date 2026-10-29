from django.db.models.signals import (
    post_save,
)

from django.dispatch import receiver
from django.urls import reverse

from .models import (
    FoodPost,
    Notification,
    RescueOffer,
    RescueRequest,
)

from .notification_service import (
    create_notification,
)


# =========================================================
# NEW SMART RESCUE OFFER
# =========================================================

@receiver(
    post_save,
    sender=RescueOffer
)
def rescue_offer_created(
    sender,
    instance,
    created,
    **kwargs,
):

    if not created:
        return


    if instance.status != "pending":
        return


    rescue_request = (
        RescueRequest.objects.filter(
            id=instance.request_id
        ).first()
    )


    if not rescue_request:
        return


    food = (
        FoodPost.objects.filter(
            id=rescue_request.food_post_id
        ).first()
    )


    if not food:
        return


    create_notification(

        user_id=instance.user_id,

        notification_type=(
            "rescue_offer"
        ),

        title="New Rescue Opportunity",

        message=(
            f"MealMate matched you with "
            f"{food.food_name}. "
            f"Match score: "
            f"{instance.match_score}."
        ),

        link=reverse(
            "rescue_offers"
        ),

        dedupe_key=(
            f"rescue-offer-"
            f"{instance.id}"
        ),
    )


# =========================================================
# RESCUE TRANSFER ACCEPTED
# =========================================================

@receiver(
    post_save,
    sender=RescueRequest
)
def rescue_request_updated(
    sender,
    instance,
    created,
    **kwargs,
):

    if created:
        return


    if instance.status != "accepted":
        return


    if not instance.accepted_user_id:
        return


    food = (
        FoodPost.objects.filter(
            id=instance.food_post_id
        ).first()
    )


    if food:

        food_name = (
            food.food_name
        )

    else:

        food_name = (
            "your reserved food"
        )


    # -----------------------------------------------------
    # ORIGINAL USER
    # -----------------------------------------------------

    create_notification(

        user_id=instance.original_user_id,

        notification_type=(
            "rescue_transferred"
        ),

        title="Rescue Successfully Passed",

        message=(
            f"{food_name} has been accepted "
            f"by another MealMate user. "
            f"You no longer need to collect it."
        ),

        link=reverse(
            "my_reservations"
        ),

        dedupe_key=(
            f"rescue-transfer-original-"
            f"{instance.id}"
        ),
    )


    # -----------------------------------------------------
    # NEW USER
    # -----------------------------------------------------

    create_notification(

        user_id=instance.accepted_user_id,

        notification_type=(
            "rescue_accepted"
        ),

        title="Rescue Accepted",

        message=(
            f"You are now responsible for "
            f"collecting {food_name}. "
            f"Your new pickup code is available."
        ),

        link=reverse(
            "my_reservations"
        ),

        dedupe_key=(
            f"rescue-transfer-new-"
            f"{instance.id}"
        ),
    )