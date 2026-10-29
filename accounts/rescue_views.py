import secrets

from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import (
    FoodInterest,
    FoodPost,
    MealMateUser,
    Reservation,
    RescueOffer,
    RescueRequest,
    UserActivity,
)

from .reliability_service import (
    reliability_match_bonus,
    sync_expired_reservations,
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
# PICKUP CODE
# =========================================================

def generate_pickup_code():

    for _ in range(100):

        code = (
            f"MM-"
            f"{secrets.randbelow(9000) + 1000}"
        )

        if not Reservation.objects.filter(
            pickup_code=code
        ).exists():

            return code

    raise RuntimeError(
        "Could not generate pickup code."
    )


# =========================================================
# FOOD TYPES
# =========================================================

FOOD_TYPE_KEYWORDS = {

    "sandwich": [
        "sandwich",
        "baguette",
        "toastie",
        "panini",
        "melt",
    ],

    "pasta": [
        "pasta",
        "penne",
        "mac and cheese",
        "alfredo",
    ],

    "salad": [
        "salad",
        "fruit pot",
    ],

    "wrap": [
        "wrap",
        "burrito",
        "roll",
    ],

    "rice": [
        "rice",
        "biryani",
        "curry",
        "katsu",
    ],

    "bakery": [
        "cake",
        "muffin",
        "cookie",
        "croissant",
        "brownie",
        "doughnut",
        "cupcake",
        "cinnamon",
        "crumble",
        "loaf",
        "twist",
        "jamun",
    ],

    "hot_food": [
        "burger",
        "chicken",
        "wings",
        "grill",
        "soup",
        "fries",
        "pasty",
        "patty",
    ],
}


def detect_food_type(food):

    combined = (
        f"{food.food_name} "
        f"{food.description or ''}"
    ).lower()

    for food_type, keywords in FOOD_TYPE_KEYWORDS.items():

        for keyword in keywords:

            if keyword in combined:
                return food_type

    return None


def detect_pickup_period(food):

    hour = timezone.localtime(
        food.pickup_start
    ).hour

    if hour < 12:
        return "morning"

    if hour < 17:
        return "afternoon"

    return "evening"


def detect_area(food):

    address = (
        food.pickup_address or ""
    )

    parts = [
        part.strip()
        for part in address.split(",")
        if part.strip()
    ]

    if len(parts) >= 2:
        return parts[1]

    if parts:
        return parts[0]

    return ""


# =========================================================
# ACTIVITY
# =========================================================

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
# MATCH SCORE
# =========================================================

def calculate_match_score(
    user,
    food,
):

    score = 0

    food_name = (
        food.food_name or ""
    ).lower()

    description = (
        food.description or ""
    ).lower()

    area = detect_area(
        food
    )

    food_type = detect_food_type(
        food
    )

    pickup_period = detect_pickup_period(
        food
    )


    if FoodInterest.objects.filter(
        user_id=user.id,
        food_post_id=food.id,
    ).exists():

        score += 40


    if UserActivity.objects.filter(
        user_id=user.id,
        activity_type="view_food",
        food_post_id=food.id,
    ).exists():

        score += 20


    searches = (
        UserActivity.objects.filter(
            user_id=user.id,
            activity_type="search",
        )
        .exclude(
            value__isnull=True
        )
        .values_list(
            "value",
            flat=True,
        )
    )


    for search in searches:

        value = (
            search or ""
        ).strip().lower()

        if (
            value
            and
            (
                value in food_name
                or
                value in description
            )
        ):

            score += 15
            break


    if food_type:

        if UserActivity.objects.filter(
            user_id=user.id,
            activity_type="filter_food_type",
            value__iexact=food_type,
        ).exists():

            score += 15


    if area:

        if UserActivity.objects.filter(
            user_id=user.id,
            activity_type="filter_area",
            value__iexact=area,
        ).exists():

            score += 15


    if UserActivity.objects.filter(
        user_id=user.id,
        activity_type="filter_business",
        value=str(food.business_id),
    ).exists():

        score += 10


    if UserActivity.objects.filter(
        user_id=user.id,
        activity_type="filter_pickup",
        value__iexact=pickup_period,
    ).exists():

        score += 10


    score += reliability_match_bonus(
        user.id
    )

    return score


def find_best_matches(
    original_user,
    food,
):

    users = (
        MealMateUser.objects.filter(
            role="user",
            is_active=True,
        )
        .exclude(
            id=original_user.id
        )
    )

    results = []

    for user in users:

        score = calculate_match_score(
            user,
            food,
        )

        if score <= 0:
            continue

        results.append(
            {
                "user": user,
                "score": score,
            }
        )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:5]


# =========================================================
# CANCEL OPEN RESCUE
# =========================================================

def cancel_open_rescue(
    reservation_id,
    status="cancelled",
):

    now = timezone.now()

    requests = list(
        RescueRequest.objects.filter(
            reservation_id=reservation_id,
            status="open",
        )
    )

    for rescue_request in requests:

        rescue_request.status = status

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
            responded_at=now,
        )


# =========================================================
# START RESCUE
# =========================================================

def start_rescue_match(
    current_user,
    reservation,
    food,
):

    existing = (
        RescueRequest.objects.filter(
            reservation_id=reservation.id,
            status="open",
        )
        .order_by(
            "-created_at"
        )
        .first()
    )

    if existing:

        return (
            existing,
            RescueOffer.objects.filter(
                request_id=existing.id,
                status="pending",
            ).count()
        )


    rescue_request = (
        RescueRequest.objects.create(
            reservation_id=reservation.id,
            original_user_id=current_user.id,
            food_post_id=food.id,
            status="open",
        )
    )


    matches = find_best_matches(
        current_user,
        food,
    )


    created_count = 0


    for match in matches:

        RescueOffer.objects.create(
            request_id=rescue_request.id,
            user_id=match["user"].id,
            match_score=match["score"],
            status="pending",
        )

        created_count += 1


    log_activity(
        user_id=current_user.id,
        activity_type="rescue_started",
        food_post_id=food.id,
        value=str(created_count),
    )


    return (
        rescue_request,
        created_count,
    )


# =========================================================
# COLLECTION CHECK-IN
# =========================================================

@require_POST
def collection_checkin(
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


    sync_expired_reservations(
        current_user.id
    )


    reservation = (
        Reservation.objects.filter(
            id=reservation_id,
            user_id=current_user.id,
            status="reserved",
        ).first()
    )


    if not reservation:

        messages.error(
            request,
            "This reservation is no longer active."
        )

        return redirect(
            "my_reservations"
        )


    food = (
        FoodPost.objects.filter(
            id=reservation.food_post_id
        ).first()
    )


    if not food:

        messages.error(
            request,
            "Food post not found."
        )

        return redirect(
            "my_reservations"
        )


    # =====================================================
    # YES - I'M COMING
    # =====================================================

    if answer == "coming":

        cancel_open_rescue(
            reservation.id,
            status="cancelled",
        )


        reservation.collection_intent = (
            "coming"
        )

        reservation.collection_confirmed_at = (
            timezone.now()
        )


        reservation.save(
            update_fields=[
                "collection_intent",
                "collection_confirmed_at",
                "updated_at",
            ]
        )


        log_activity(
            user_id=current_user.id,
            activity_type="pickup_confirmed",
            food_post_id=food.id,
            value="coming",
        )


        messages.success(
            request,
            (
                "Collection confirmed. "
                "We'll keep your meal reserved."
            )
        )


        return redirect(
            "my_reservations"
        )


    # =====================================================
    # CAN'T MAKE IT
    # =====================================================

    if answer == "cant_collect":

        reservation.collection_intent = (
            "cant_collect"
        )

        reservation.collection_confirmed_at = (
            timezone.now()
        )


        reservation.save(
            update_fields=[
                "collection_intent",
                "collection_confirmed_at",
                "updated_at",
            ]
        )


        log_activity(
            user_id=current_user.id,
            activity_type="pickup_cannot_collect",
            food_post_id=food.id,
            value="rescue",
        )


        (
            rescue_request,
            match_count,
        ) = start_rescue_match(
            current_user,
            reservation,
            food,
        )


        messages.success(
            request,
            (
                "Thanks for letting us know. "
                "MealMate will try to find another "
                "collector for this meal."
            )
        )


        return redirect(
            "my_reservations"
        )


    messages.error(
        request,
        "Invalid collection response."
    )


    return redirect(
        "my_reservations"
    )


# =========================================================
# MANUAL PASS MY RESCUE
# =========================================================

@require_POST
def create_rescue_request(
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


    sync_expired_reservations(
        current_user.id
    )


    reservation = (
        Reservation.objects.filter(
            id=reservation_id,
            user_id=current_user.id,
            status="reserved",
        ).first()
    )


    if not reservation:

        messages.error(
            request,
            "Reservation not found or no longer active."
        )

        return redirect(
            "my_reservations"
        )


    food = (
        FoodPost.objects.filter(
            id=reservation.food_post_id
        ).first()
    )


    if not food:

        messages.error(
            request,
            "Food post not found."
        )

        return redirect(
            "my_reservations"
        )


    reservation.collection_intent = (
        "cant_collect"
    )

    reservation.collection_confirmed_at = (
        timezone.now()
    )


    reservation.save(
        update_fields=[
            "collection_intent",
            "collection_confirmed_at",
            "updated_at",
        ]
    )


    (
        rescue_request,
        match_count,
    ) = start_rescue_match(
        current_user,
        reservation,
        food,
    )


    if match_count:

        messages.success(
            request,
            (
                f"Rescue Relay started. "
                f"{match_count} matched user"
                f"{'s' if match_count != 1 else ''} "
                f"received an opportunity."
            )
        )

    else:

        messages.warning(
            request,
            (
                "Rescue Relay started, but "
                "no suitable match was found yet."
            )
        )


    return redirect(
        "my_reservations"
    )


# =========================================================
# RESCUE OFFERS
# =========================================================

def rescue_offers(request):

    current_user = get_current_user(
        request
    )


    if not current_user:

        return redirect(
            "login"
        )


    sync_expired_reservations(
        current_user.id
    )


    offers = list(
        RescueOffer.objects.filter(
            user_id=current_user.id,
            status="pending",
        ).order_by(
            "-created_at"
        )
    )


    offer_data = []


    for offer in offers:

        rescue_request = (
            RescueRequest.objects.filter(
                id=offer.request_id,
                status="open",
            ).first()
        )


        if not rescue_request:

            offer.status = "expired"

            offer.save(
                update_fields=[
                    "status"
                ]
            )

            continue


        reservation = (
            Reservation.objects.filter(
                id=rescue_request.reservation_id,
                status="reserved",
            ).first()
        )


        if not reservation:

            offer.status = "expired"

            offer.save(
                update_fields=[
                    "status"
                ]
            )

            continue


        food = (
            FoodPost.objects.filter(
                id=rescue_request.food_post_id
            ).first()
        )


        if not food:
            continue


        business = (
            MealMateUser.objects.filter(
                id=food.business_id
            ).first()
        )


        offer_data.append(
            {
                "offer": offer,
                "food": food,
                "business": business,
                "request": rescue_request,
            }
        )


    return render(
        request,
        "rescue_offers.html",
        {
            "current_user":
                current_user,

            "offer_data":
                offer_data,
        }
    )


# =========================================================
# ACCEPT
# =========================================================

@require_POST
def accept_rescue_offer(
    request,
    offer_id,
):

    current_user = get_current_user(
        request
    )


    if not current_user:

        return redirect(
            "login"
        )


    sync_expired_reservations(
        current_user.id
    )


    with transaction.atomic():

        offer = (
            RescueOffer.objects
            .select_for_update()
            .filter(
                id=offer_id,
                user_id=current_user.id,
                status="pending",
            )
            .first()
        )


        if not offer:

            messages.error(
                request,
                (
                    "This rescue opportunity "
                    "is no longer available."
                )
            )

            return redirect(
                "rescue_offers"
            )


        rescue_request = (
            RescueRequest.objects
            .select_for_update()
            .filter(
                id=offer.request_id,
                status="open",
            )
            .first()
        )


        if not rescue_request:

            offer.status = "expired"

            offer.responded_at = timezone.now()

            offer.save(
                update_fields=[
                    "status",
                    "responded_at",
                ]
            )

            messages.error(
                request,
                (
                    "Another user has already "
                    "taken this rescue."
                )
            )

            return redirect(
                "rescue_offers"
            )


        reservation = (
            Reservation.objects
            .select_for_update()
            .filter(
                id=rescue_request.reservation_id,
                status="reserved",
            )
            .first()
        )


        if not reservation:

            messages.error(
                request,
                (
                    "The original reservation "
                    "is no longer active."
                )
            )

            return redirect(
                "rescue_offers"
            )


        food = (
            FoodPost.objects.filter(
                id=rescue_request.food_post_id
            ).first()
        )


        if (
            not food
            or
            food.pickup_end <= timezone.now()
        ):

            rescue_request.status = "expired"

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

            messages.error(
                request,
                (
                    "The pickup window "
                    "has already ended."
                )
            )

            return redirect(
                "rescue_offers"
            )


        previous_user_id = (
            reservation.user_id
        )


        reservation.user_id = (
            current_user.id
        )

        reservation.pickup_code = (
            generate_pickup_code()
        )

        reservation.collection_intent = (
            "pending"
        )

        reservation.collection_confirmed_at = (
            None
        )


        reservation.save(
            update_fields=[
                "user_id",
                "pickup_code",
                "collection_intent",
                "collection_confirmed_at",
                "updated_at",
            ]
        )


        rescue_request.status = (
            "accepted"
        )

        rescue_request.accepted_user_id = (
            current_user.id
        )

        rescue_request.accepted_at = (
            timezone.now()
        )


        rescue_request.save(
            update_fields=[
                "status",
                "accepted_user_id",
                "accepted_at",
            ]
        )


        offer.status = "accepted"

        offer.responded_at = (
            timezone.now()
        )


        offer.save(
            update_fields=[
                "status",
                "responded_at",
            ]
        )


        RescueOffer.objects.filter(
            request_id=rescue_request.id,
            status="pending",
        ).exclude(
            id=offer.id
        ).update(
            status="expired",
            responded_at=timezone.now(),
        )


        log_activity(
            user_id=current_user.id,
            activity_type="rescue_accepted",
            food_post_id=food.id,
            value=str(
                previous_user_id
            ),
        )


    messages.success(
        request,
        (
            "Rescue accepted. "
            "Your new pickup code is ready."
        )
    )


    return redirect(
        "my_reservations"
    )


# =========================================================
# DECLINE
# =========================================================

@require_POST
def decline_rescue_offer(
    request,
    offer_id,
):

    current_user = get_current_user(
        request
    )


    if not current_user:

        return redirect(
            "login"
        )


    offer = (
        RescueOffer.objects.filter(
            id=offer_id,
            user_id=current_user.id,
            status="pending",
        ).first()
    )


    if not offer:

        messages.error(
            request,
            (
                "This rescue opportunity "
                "is no longer available."
            )
        )

        return redirect(
            "rescue_offers"
        )


    offer.status = "declined"

    offer.responded_at = timezone.now()


    offer.save(
        update_fields=[
            "status",
            "responded_at",
        ]
    )


    rescue_request = (
        RescueRequest.objects.filter(
            id=offer.request_id
        ).first()
    )


    log_activity(
        user_id=current_user.id,
        activity_type="rescue_declined",
        food_post_id=(
            rescue_request.food_post_id
            if rescue_request
            else None
        ),
        value=str(
            offer.match_score
        ),
    )


    messages.success(
        request,
        "Rescue opportunity declined."
    )


    return redirect(
        "rescue_offers"
    )