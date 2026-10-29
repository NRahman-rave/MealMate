from collections import Counter
from urllib.parse import urlencode

from django.contrib import messages
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)

from django.urls import reverse

from django.utils import timezone

from django.utils.http import (
    url_has_allowed_host_and_scheme,
)

from django.views.decorators.http import (
    require_POST,
)

from .models import (
    FoodInterest,
    FoodPost,
    MealMateUser,
    Reservation,
    UserActivity,
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
        is_active=True
    ).first()


# =========================================================
# ACTIVITY LOGGER
# =========================================================

def log_activity(
    user,
    activity_type,
    value=None,
    food_post_id=None,
):

    if not user:
        return

    # Avoid recording the exact same action repeatedly
    # when somebody refreshes a page several times.

    recent_time = (
        timezone.now()
        - timezone.timedelta(
            minutes=10
        )
    )

    duplicate = UserActivity.objects.filter(
        user_id=user.id,
        activity_type=activity_type,
        value=value,
        food_post_id=food_post_id,
        created_at__gte=recent_time,
    ).exists()

    if duplicate:
        return

    UserActivity.objects.create(

        user_id=user.id,

        activity_type=activity_type,

        value=value,

        food_post_id=food_post_id,
    )


# =========================================================
# TRACK SEARCH + FILTER
# =========================================================

def track_dashboard_search(request):

    user = get_current_user(request)

    if not user:

        return redirect(
            "login"
        )


    query = request.GET.get(
        "q",
        ""
    ).strip()


    area = request.GET.get(
        "area",
        ""
    ).strip()


    food_type = request.GET.get(
        "food_type",
        ""
    ).strip()


    pickup = request.GET.get(
        "pickup",
        ""
    ).strip()


    business = request.GET.get(
        "business",
        ""
    ).strip()


    if query:

        log_activity(
            user,
            "search",
            value=query.lower()
        )


    if area:

        log_activity(
            user,
            "filter_area",
            value=area
        )


    if food_type:

        log_activity(
            user,
            "filter_food_type",
            value=food_type
        )


    if pickup:

        log_activity(
            user,
            "filter_pickup",
            value=pickup
        )


    if business:

        try:

            business_user = (
                MealMateUser.objects
                .filter(
                    id=int(business),
                    role="business",
                )
                .first()
            )

            business_name = (

                business_user.full_name

                if business_user

                else business
            )

        except ValueError:

            business_name = business


        log_activity(
            user,
            "filter_business",
            value=business_name
        )


    params = {}


    if query:
        params["q"] = query

    if area:
        params["area"] = area

    if food_type:
        params[
            "food_type"
        ] = food_type

    if pickup:
        params["pickup"] = pickup

    if business:
        params[
            "business"
        ] = business


    destination = reverse(
        "dashboard"
    )


    if params:

        destination += (
            "?"
            + urlencode(params)
        )


    return redirect(
        destination
    )


# =========================================================
# TRACK FOOD VIEW
# =========================================================

def track_food_view(
    request,
    food_id
):

    user = get_current_user(request)

    if not user:

        return redirect(
            "login"
        )


    food = get_object_or_404(
        FoodPost,
        id=food_id
    )


    log_activity(
        user,
        "view_food",
        value=food.food_name,
        food_post_id=food.id,
    )


    return redirect(
        "food_detail",
        food_id=food.id
    )


# =========================================================
# INTERESTED / SAVE FOOD
# =========================================================

@require_POST
def toggle_food_interest(
    request,
    food_id
):

    user = get_current_user(request)

    if not user:

        return redirect(
            "login"
        )


    if user.role != "user":

        return redirect(
            "business_dashboard"
        )


    food = get_object_or_404(
        FoodPost,
        id=food_id
    )


    existing = (
        FoodInterest.objects
        .filter(
            user_id=user.id,
            food_post_id=food.id,
        )
        .first()
    )


    if existing:

        existing.delete()

        log_activity(
            user,
            "uninterested",
            value=food.food_name,
            food_post_id=food.id,
        )

        messages.info(
            request,
            "Removed from your interests."
        )

    else:

        FoodInterest.objects.create(
            user_id=user.id,
            food_post_id=food.id,
        )

        log_activity(
            user,
            "interested",
            value=food.food_name,
            food_post_id=food.id,
        )

        messages.success(
            request,
            "Added to your interests."
        )


    next_url = request.POST.get(
        "next",
        ""
    )


    if (
        next_url
        and url_has_allowed_host_and_scheme(
            next_url,
            allowed_hosts={
                request.get_host()
            },
            require_https=(
                request.is_secure()
            ),
        )
    ):

        return redirect(
            next_url
        )


    return redirect(
        "dashboard"
    )


# =========================================================
# USER INTEREST PROFILE
# =========================================================

def interest_profile(request):

    user = get_current_user(request)

    if not user:

        return redirect(
            "login"
        )


    if user.role != "user":

        return redirect(
            "business_dashboard"
        )


    activities = list(

        UserActivity.objects.filter(
            user_id=user.id
        ).order_by(
            "-created_at"
        )
    )


    searches = Counter()

    areas = Counter()

    food_types = Counter()

    businesses = Counter()

    pickup_times = Counter()

    viewed_foods = Counter()


    for activity in activities:

        if not activity.value:
            continue


        if activity.activity_type == "search":

            searches[
                activity.value
            ] += 1


        elif (
            activity.activity_type
            == "filter_area"
        ):

            areas[
                activity.value
            ] += 1


        elif (
            activity.activity_type
            == "filter_food_type"
        ):

            food_types[
                activity.value
            ] += 1


        elif (
            activity.activity_type
            == "filter_business"
        ):

            businesses[
                activity.value
            ] += 1


        elif (
            activity.activity_type
            == "filter_pickup"
        ):

            pickup_times[
                activity.value
            ] += 1


        elif (
            activity.activity_type
            == "view_food"
        ):

            viewed_foods[
                activity.value
            ] += 1


    interests = list(

        FoodInterest.objects.filter(
            user_id=user.id
        ).order_by(
            "-created_at"
        )
    )


    interest_food_ids = {
        item.food_post_id
        for item in interests
    }


    interested_foods = {

        food.id: food

        for food in FoodPost.objects.filter(
            id__in=interest_food_ids
        )
    }


    business_ids = {

        food.business_id

        for food
        in interested_foods.values()
    }


    business_names = {

        business.id:
            business.full_name

        for business
        in MealMateUser.objects.filter(
            id__in=business_ids
        )
    }


    interest_cards = []


    for interest in interests:

        food = interested_foods.get(
            interest.food_post_id
        )

        if not food:
            continue


        food.business_name = (
            business_names.get(
                food.business_id,
                "MealMate Business"
            )
        )


        interest_cards.append(
            food
        )


    reservation_count = (
        Reservation.objects.filter(
            user_id=user.id
        ).count()
    )


    collected_count = (
        Reservation.objects.filter(
            user_id=user.id,
            status="collected"
        ).count()
    )


    context = {

        "current_user": user,

        "top_searches":
            searches.most_common(5),

        "top_areas":
            areas.most_common(5),

        "top_food_types":
            food_types.most_common(5),

        "top_businesses":
            businesses.most_common(5),

        "top_pickup_times":
            pickup_times.most_common(5),

        "top_viewed_foods":
            viewed_foods.most_common(5),

        "interest_cards":
            interest_cards,

        "interest_count":
            len(interest_cards),

        "activity_count":
            len(activities),

        "reservation_count":
            reservation_count,

        "collected_count":
            collected_count,
    }


    return render(
        request,
        "interest_profile.html",
        context
    )