from django import template

from accounts.models import FoodInterest


register = template.Library()


@register.simple_tag
def is_food_interested(
    user_id,
    food_post_id,
):

    if not user_id:
        return False

    return FoodInterest.objects.filter(
        user_id=user_id,
        food_post_id=food_post_id,
    ).exists()