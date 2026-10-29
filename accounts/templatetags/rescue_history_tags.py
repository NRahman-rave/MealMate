from django import template
from django.utils import timezone

from accounts.models import (
    FoodPost,
    MealMateUser,
    Reservation,
    RescueRequest,
)


register = template.Library()


@register.simple_tag
def original_rescue_history(user_id):

    if not user_id:
        return []


    rescue_requests = (
        RescueRequest.objects.filter(
            original_user_id=user_id,
            status="accepted",
        )
        .order_by(
            "-accepted_at",
            "-created_at",
        )
    )


    history = []


    for rescue_request in rescue_requests:

        food = (
            FoodPost.objects.filter(
                id=rescue_request.food_post_id
            ).first()
        )


        if not food:
            continue


        reservation = (
            Reservation.objects.filter(
                id=rescue_request.reservation_id
            ).first()
        )


        business = (
            MealMateUser.objects.filter(
                id=food.business_id
            ).first()
        )


        accepted_user = None


        if rescue_request.accepted_user_id:

            accepted_user = (
                MealMateUser.objects.filter(
                    id=rescue_request.accepted_user_id
                ).first()
            )


        can_reserve_again = (
            food.status == "available"
            and
            food.quantity > 0
            and
            food.pickup_end > timezone.now()
        )


        no_longer_available = (
            not can_reserve_again
        )


        history.append(
            {
                "request":
                    rescue_request,

                "reservation":
                    reservation,

                "food":
                    food,

                "business_name":
                    (
                        business.full_name
                        if business
                        else "Business"
                    ),

                "accepted_user":
                    accepted_user,

                "can_reserve_again":
                    can_reserve_again,

                "no_longer_available":
                    no_longer_available,
            }
        )


    return history