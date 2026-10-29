from django import template

from accounts.extension_service import (
    get_reservation_lifecycle,
)

from accounts.models import (
    FoodPost,
    Reservation,
)


register = template.Library()


@register.simple_tag
def reservation_lifecycle(
    reservation
):

    return get_reservation_lifecycle(
        reservation,
        save=True,
    )


@register.simple_tag
def business_active_reservations(
    business_id
):

    food_ids = list(
        FoodPost.objects.filter(
            business_id=business_id
        ).values_list(
            "id",
            flat=True,
        )
    )


    reservations = list(
        Reservation.objects.filter(
            food_post_id__in=food_ids,
            status__in=[
                "reserved",
                "expired",
            ],
        )
    )


    total = 0


    for reservation in reservations:

        lifecycle = (
            get_reservation_lifecycle(
                reservation,
                save=True,
            )
        )


        if lifecycle["state"] in {
            "active",
            "extended",
        }:

            total += 1


    return total