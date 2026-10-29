import secrets
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.hashers import (
    check_password,
    make_password,
)
from django.db import transaction
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.utils import timezone
from django.views.decorators.http import require_POST

from .forms import (
    FoodPostForm,
    LoginForm,
    PasswordChangeForm,
    ProfileForm,
    SignupForm,
)

from .models import (
    FoodPost,
    MealMateUser,
    Reservation,
)


# =========================================================
# FOOD TYPE FILTERS
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


FOOD_TYPE_LABELS = {
    "sandwich": "Sandwiches",
    "pasta": "Pasta",
    "salad": "Salads",
    "wrap": "Wraps & Rolls",
    "rice": "Rice & Meals",
    "bakery": "Bakery & Desserts",
    "hot_food": "Hot Food",
}


# =========================================================
# SESSION HELPERS
# =========================================================

def create_login_session(request, user):

    request.session.cycle_key()

    request.session["user_id"] = user.id
    request.session["user_name"] = user.full_name
    request.session["user_email"] = user.email
    request.session["user_role"] = user.role


def get_current_user(request):

    user_id = request.session.get("user_id")

    if not user_id:
        return None

    user = MealMateUser.objects.filter(
        id=user_id,
        is_active=True
    ).first()

    if not user:

        request.session.flush()

        return None

    return user


# =========================================================
# PICKUP CODE
# =========================================================

def generate_pickup_code():

    for _ in range(100):

        number = secrets.randbelow(9000) + 1000

        code = f"MM-{number}"

        if not Reservation.objects.filter(
            pickup_code=code
        ).exists():

            return code

    raise RuntimeError(
        "Unable to generate a unique pickup code."
    )


def ensure_reservation_code(reservation):

    if (
        reservation.status == "reserved"
        and not reservation.pickup_code
    ):

        reservation.pickup_code = (
            generate_pickup_code()
        )

        reservation.save(
            update_fields=[
                "pickup_code",
                "updated_at",
            ]
        )

    return reservation


# =========================================================
# FOOD HELPERS
# =========================================================

def attach_business_names(food_posts):

    posts = list(food_posts)

    business_ids = {
        post.business_id
        for post in posts
    }

    businesses = {
        user.id: user.full_name
        for user in MealMateUser.objects.filter(
            id__in=business_ids
        )
    }

    for post in posts:

        post.business_name = businesses.get(
            post.business_id,
            "MealMate Business"
        )

    return posts


def extract_area(address):

    if not address:
        return ""

    parts = [
        part.strip()
        for part in address.split(",")
        if part.strip()
    ]

    if len(parts) >= 2:
        return parts[1]

    return address.strip()


def build_food_type_query(food_type):

    keywords = FOOD_TYPE_KEYWORDS.get(
        food_type,
        []
    )

    query = Q()

    for keyword in keywords:

        query |= Q(
            food_name__icontains=keyword
        )

        query |= Q(
            description__icontains=keyword
        )

    return query


# =========================================================
# HOME
# =========================================================

def home(request):

    return render(
        request,
        "index.html",
        {
            "current_user": get_current_user(
                request
            )
        }
    )


# =========================================================
# SIGN UP
# =========================================================

def signup_user(request):

    return _signup(
        request,
        role="user"
    )


def signup_business(request):

    return _signup(
        request,
        role="business"
    )


def _signup(request, role):

    current_user = get_current_user(request)

    if current_user:

        if current_user.role == "business":

            return redirect(
                "business_dashboard"
            )

        return redirect(
            "dashboard"
        )

    form = SignupForm(
        request.POST or None
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        user = MealMateUser.objects.create(

            full_name=form.cleaned_data[
                "full_name"
            ],

            email=form.cleaned_data[
                "email"
            ],

            phone=(
                form.cleaned_data["phone"]
                or None
            ),

            password_hash=make_password(
                form.cleaned_data[
                    "password"
                ]
            ),

            role=role,

            is_active=True,
        )

        create_login_session(
            request,
            user
        )

        messages.success(
            request,
            "Your MealMate account has been created."
        )

        if role == "business":

            return redirect(
                "business_dashboard"
            )

        return redirect(
            "dashboard"
        )

    return render(
        request,
        "signup.html",
        {
            "form": form,
            "business_signup": (
                role == "business"
            ),
        }
    )


# =========================================================
# LOGIN
# =========================================================

def login_user(request):

    current_user = get_current_user(request)

    if current_user:

        if current_user.role == "business":

            return redirect(
                "business_dashboard"
            )

        return redirect(
            "dashboard"
        )

    form = LoginForm(
        request.POST or None
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        user = MealMateUser.objects.filter(
            email__iexact=form.cleaned_data[
                "email"
            ]
        ).first()

        if (
            user
            and check_password(
                form.cleaned_data["password"],
                user.password_hash
            )
        ):

            if not user.is_active:

                form.add_error(
                    None,
                    "This account is inactive."
                )

            else:

                create_login_session(
                    request,
                    user
                )

                if user.role == "business":

                    return redirect(
                        "business_dashboard"
                    )

                return redirect(
                    "dashboard"
                )

        else:

            form.add_error(
                None,
                "Incorrect email or password."
            )

    return render(
        request,
        "login.html",
        {
            "form": form
        }
    )


# =========================================================
# LOGOUT
# =========================================================

@require_POST
def logout_user(request):

    request.session.flush()

    return redirect(
        "home"
    )


# =========================================================
# USER DASHBOARD
# SEARCH + FILTER
# =========================================================

def dashboard(request):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    if current_user.role == "business":

        return redirect(
            "business_dashboard"
        )

    query = request.GET.get(
        "q",
        ""
    ).strip()

    selected_area = request.GET.get(
        "area",
        ""
    ).strip()

    selected_food_type = request.GET.get(
        "food_type",
        ""
    ).strip()

    selected_business = request.GET.get(
        "business",
        ""
    ).strip()

    selected_pickup = request.GET.get(
        "pickup",
        ""
    ).strip()


    # -----------------------------------------------------
    # BASE LIST OF AVAILABLE FOOD
    # -----------------------------------------------------

    base_food_posts = FoodPost.objects.filter(
        status="available",
        quantity__gt=0,
        pickup_end__gte=timezone.now(),
    )


    # -----------------------------------------------------
    # BUILD AREA FILTER OPTIONS
    # -----------------------------------------------------

    all_addresses = (
        base_food_posts
        .values_list(
            "pickup_address",
            flat=True
        )
        .distinct()
    )

    areas = sorted(
        {
            extract_area(address)
            for address in all_addresses
            if extract_area(address)
        }
    )


    # -----------------------------------------------------
    # BUILD BUSINESS FILTER OPTIONS
    # -----------------------------------------------------

    business_ids = (
        base_food_posts
        .values_list(
            "business_id",
            flat=True
        )
        .distinct()
    )

    businesses = (
        MealMateUser.objects
        .filter(
            id__in=business_ids,
            role="business",
            is_active=True,
        )
        .order_by(
            "full_name"
        )
    )


    food_posts = base_food_posts


    # -----------------------------------------------------
    # SEARCH
    # Searches:
    # - food
    # - description
    # - address / area
    # - business name
    # -----------------------------------------------------

    if query:

        matching_business_ids = list(

            MealMateUser.objects.filter(
                role="business",
                full_name__icontains=query
            ).values_list(
                "id",
                flat=True
            )
        )

        food_posts = food_posts.filter(

            Q(
                food_name__icontains=query
            )

            | Q(
                description__icontains=query
            )

            | Q(
                pickup_address__icontains=query
            )

            | Q(
                business_id__in=matching_business_ids
            )
        )


    # -----------------------------------------------------
    # AREA FILTER
    # -----------------------------------------------------

    if selected_area:

        food_posts = food_posts.filter(
            pickup_address__icontains=(
                selected_area
            )
        )


    # -----------------------------------------------------
    # BUSINESS FILTER
    # -----------------------------------------------------

    if selected_business:

        try:

            business_id = int(
                selected_business
            )

            food_posts = food_posts.filter(
                business_id=business_id
            )

        except ValueError:

            pass


    # -----------------------------------------------------
    # FOOD TYPE FILTER
    # -----------------------------------------------------

    if selected_food_type:

        food_type_query = (
            build_food_type_query(
                selected_food_type
            )
        )

        if food_type_query:

            food_posts = (
                food_posts.filter(
                    food_type_query
                )
            )


    # -----------------------------------------------------
    # PICKUP TIME FILTER
    # -----------------------------------------------------

    now = timezone.localtime()

    today = now.date()

    tomorrow = (
        today
        + timedelta(days=1)
    )


    if selected_pickup == "today":

        food_posts = food_posts.filter(
            pickup_start__date=today
        )


    elif selected_pickup == "tomorrow":

        food_posts = food_posts.filter(
            pickup_start__date=tomorrow
        )


    elif selected_pickup == "morning":

        food_posts = food_posts.filter(
            pickup_start__hour__lt=12
        )


    elif selected_pickup == "afternoon":

        food_posts = food_posts.filter(
            pickup_start__hour__gte=12,
            pickup_start__hour__lt=17,
        )


    elif selected_pickup == "evening":

        food_posts = food_posts.filter(
            pickup_start__hour__gte=17
        )


    # -----------------------------------------------------
    # FINAL RESULTS
    # -----------------------------------------------------

    food_posts = attach_business_names(

        food_posts.order_by(
            "pickup_start",
            "food_name"
        )
    )

    available_count = len(
        food_posts
    )


    active_filter_count = sum(
        1
        for value in [
            selected_area,
            selected_food_type,
            selected_business,
            selected_pickup,
        ]
        if value
    )


    return render(
        request,
        "dashboard.html",
        {
            "current_user": current_user,

            "food_posts": food_posts,

            "available_count": (
                available_count
            ),

            "query": query,

            "areas": areas,

            "businesses": businesses,

            "food_type_labels": (
                FOOD_TYPE_LABELS
            ),

            "selected_area": (
                selected_area
            ),

            "selected_food_type": (
                selected_food_type
            ),

            "selected_business": (
                selected_business
            ),

            "selected_pickup": (
                selected_pickup
            ),

            "active_filter_count": (
                active_filter_count
            ),
        }
    )


# =========================================================
# FOOD DETAILS
# =========================================================

def food_detail(request, food_id):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    food = get_object_or_404(
        FoodPost,
        id=food_id
    )

    business = MealMateUser.objects.filter(
        id=food.business_id
    ).first()

    if business:

        food.business_name = (
            business.full_name
        )

    else:

        food.business_name = (
            "MealMate Business"
        )

    already_reserved = False

    if current_user.role == "user":

        already_reserved = (
            Reservation.objects.filter(
                user_id=current_user.id,
                food_post_id=food.id,
                status="reserved",
            ).exists()
        )

    return render(
        request,
        "food_detail.html",
        {
            "current_user": current_user,
            "food": food,
            "already_reserved": (
                already_reserved
            ),
        }
    )


# =========================================================
# RESERVE FOOD
# =========================================================

@require_POST
def reserve_food(request, food_id):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    if current_user.role != "user":

        messages.error(
            request,
            "Only user accounts can reserve food."
        )

        return redirect(
            "business_dashboard"
        )

    with transaction.atomic():

        food = (
            FoodPost.objects
            .select_for_update()
            .filter(
                id=food_id
            )
            .first()
        )

        if not food:

            messages.error(
                request,
                "This food post no longer exists."
            )

            return redirect(
                "dashboard"
            )

        if (
            food.status != "available"
            or food.quantity < 1
            or food.pickup_end < timezone.now()
        ):

            messages.error(
                request,
                "This food is no longer available."
            )

            return redirect(
                "food_detail",
                food_id=food.id
            )

        existing = Reservation.objects.filter(
            user_id=current_user.id,
            food_post_id=food.id,
            status="reserved",
        ).first()

        if existing:

            ensure_reservation_code(
                existing
            )

            messages.info(
                request,
                "You already have an active reservation for this food."
            )

            return redirect(
                "my_reservations"
            )

        pickup_code = (
            generate_pickup_code()
        )

        Reservation.objects.create(

            user_id=current_user.id,

            food_post_id=food.id,

            status="reserved",

            pickup_code=pickup_code,
        )

        food.quantity -= 1

        if food.quantity == 0:

            food.status = "sold_out"

        food.save(
            update_fields=[
                "quantity",
                "status",
            ]
        )

    messages.success(
        request,
        "Food reserved successfully. Your unique pickup code is shown below."
    )

    return redirect(
        "my_reservations"
    )


# =========================================================
# MY RESERVATIONS
# =========================================================

def my_reservations(request):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    if current_user.role != "user":

        return redirect(
            "business_dashboard"
        )

    reservations = list(

        Reservation.objects.filter(
            user_id=current_user.id
        ).order_by(
            "-reserved_at"
        )
    )

    for reservation in reservations:

        ensure_reservation_code(
            reservation
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

    business_ids = {
        food.business_id
        for food in foods.values()
    }

    businesses = {
        business.id: business.full_name
        for business in MealMateUser.objects.filter(
            id__in=business_ids
        )
    }

    for reservation in reservations:

        food = foods.get(
            reservation.food_post_id
        )

        reservation.food = food

        if food:

            reservation.business_name = (
                businesses.get(
                    food.business_id,
                    "MealMate Business"
                )
            )

        else:

            reservation.business_name = (
                "MealMate Business"
            )

    return render(
        request,
        "reservations.html",
        {
            "current_user": current_user,
            "reservations": reservations,
        }
    )


# =========================================================
# USER CANCEL RESERVATION
# =========================================================

@require_POST
def cancel_reservation(
    request,
    reservation_id
):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    if current_user.role != "user":

        return redirect(
            "business_dashboard"
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

        if (
            not reservation
            or reservation.status
            != "reserved"
        ):

            messages.error(
                request,
                "That reservation cannot be cancelled."
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

        reservation.status = (
            "cancelled"
        )

        reservation.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        if food:

            food.quantity += 1

            if (
                food.status == "sold_out"
                and food.pickup_end
                >= timezone.now()
            ):

                food.status = (
                    "available"
                )

            food.save(
                update_fields=[
                    "quantity",
                    "status",
                ]
            )

    messages.success(
        request,
        "Reservation cancelled."
    )

    return redirect(
        "my_reservations"
    )


# =========================================================
# BUSINESS DASHBOARD
# =========================================================

def business_dashboard(request):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    if current_user.role != "business":

        return redirect(
            "dashboard"
        )

    form = FoodPostForm(
        request.POST or None
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        food = form.save(
            commit=False
        )

        food.business_id = (
            current_user.id
        )

        food.status = (
            "available"
        )

        food.save()

        messages.success(
            request,
            f"{food.food_name} has been posted."
        )

        return redirect(
            "business_dashboard"
        )

    posts = list(

        FoodPost.objects.filter(
            business_id=current_user.id
        ).order_by(
            "-created_at"
        )
    )

    post_ids = [
        post.id
        for post in posts
    ]

    reservations = list(

        Reservation.objects.filter(
            food_post_id__in=post_ids
        ).order_by(
            "-reserved_at"
        )
    )

    for reservation in reservations:

        ensure_reservation_code(
            reservation
        )

    users = {

        user.id: user

        for user in MealMateUser.objects.filter(
            id__in={
                reservation.user_id
                for reservation
                in reservations
            }
        )
    }

    foods = {
        post.id: post
        for post in posts
    }

    for reservation in reservations:

        reservation.user = users.get(
            reservation.user_id
        )

        reservation.food = foods.get(
            reservation.food_post_id
        )

    stats = {

        "active_posts": sum(
            1
            for post in posts
            if (
                post.status == "available"
                and post.quantity > 0
            )
        ),

        "available_items": sum(
            post.quantity
            for post in posts
            if post.status in {
                "available",
                "sold_out",
            }
        ),

        "reserved": sum(
            1
            for reservation
            in reservations
            if reservation.status
            == "reserved"
        ),

        "collected": sum(
            1
            for reservation
            in reservations
            if reservation.status
            == "collected"
        ),
    }

    return render(
        request,
        "business_dashboard.html",
        {
            "current_user": current_user,
            "form": form,
            "my_food_posts": posts,
            "reservations": reservations,
            "stats": stats,
        }
    )


# =========================================================
# BUSINESS EDIT FOOD
# =========================================================

def business_food_edit(
    request,
    food_id
):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    if current_user.role != "business":

        return redirect(
            "dashboard"
        )

    food = get_object_or_404(
        FoodPost,
        id=food_id,
        business_id=current_user.id
    )

    form = FoodPostForm(
        request.POST or None,
        instance=food
    )

    if (
        request.method == "POST"
        and form.is_valid()
    ):

        updated = form.save(
            commit=False
        )

        updated.business_id = (
            current_user.id
        )

        if (
            updated.status == "sold_out"
            and updated.quantity > 0
        ):

            updated.status = (
                "available"
            )

        updated.save()

        messages.success(
            request,
            "Food post updated."
        )

        return redirect(
            "business_dashboard"
        )

    return render(
        request,
        "business_food_form.html",
        {
            "current_user": current_user,
            "form": form,
            "food": food,
        }
    )


# =========================================================
# BUSINESS PAUSE / ACTIVATE
# =========================================================

@require_POST
def business_food_toggle(
    request,
    food_id
):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    if current_user.role != "business":

        return redirect(
            "dashboard"
        )

    food = get_object_or_404(
        FoodPost,
        id=food_id,
        business_id=current_user.id
    )

    if food.status == "available":

        food.status = "paused"

        messages.success(
            request,
            "Listing paused."
        )

    elif (
        food.quantity > 0
        and food.pickup_end
        >= timezone.now()
    ):

        food.status = "available"

        messages.success(
            request,
            "Listing is available again."
        )

    else:

        messages.error(
            request,
            "This listing cannot be reactivated. Check the quantity and pickup time."
        )

        return redirect(
            "business_dashboard"
        )

    food.save(
        update_fields=[
            "status"
        ]
    )

    return redirect(
        "business_dashboard"
    )


# =========================================================
# BUSINESS DELETE FOOD
# =========================================================

@require_POST
def business_food_delete(
    request,
    food_id
):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    if current_user.role != "business":

        return redirect(
            "dashboard"
        )

    food = get_object_or_404(
        FoodPost,
        id=food_id,
        business_id=current_user.id
    )

    has_reservations = (
        Reservation.objects.filter(
            food_post_id=food.id,
            status="reserved"
        ).exists()
    )

    if has_reservations:

        messages.error(
            request,
            "You cannot delete a listing with active reservations."
        )

        return redirect(
            "business_dashboard"
        )

    food.delete()

    messages.success(
        request,
        "Food post deleted."
    )

    return redirect(
        "business_dashboard"
    )


# =========================================================
# BUSINESS VERIFY PICKUP CODE
# =========================================================

@require_POST
def business_verify_pickup_code(
    request,
    reservation_id
):

    current_user = get_current_user(request)

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

        if reservation.status != "reserved":

            messages.info(
                request,
                "This reservation has already been completed or cancelled."
            )

            return redirect(
                "business_dashboard"
            )

        ensure_reservation_code(
            reservation
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
        "Pickup code verified. Food marked as collected."
    )

    return redirect(
        "business_dashboard"
    )


# =========================================================
# BUSINESS CANCEL RESERVATION
# =========================================================

@require_POST
def business_reservation_update(
    request,
    reservation_id,
    action
):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    if current_user.role != "business":

        return redirect(
            "dashboard"
        )

    if action != "cancelled":

        messages.error(
            request,
            "Collection must be confirmed using the customer's pickup code."
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

        if reservation.status != "reserved":

            messages.info(
                request,
                "This reservation has already been completed or cancelled."
            )

            return redirect(
                "business_dashboard"
            )

        reservation.status = (
            "cancelled"
        )

        reservation.save(
            update_fields=[
                "status",
                "updated_at",
            ]
        )

        food.quantity += 1

        if (
            food.status == "sold_out"
            and food.pickup_end
            >= timezone.now()
        ):

            food.status = (
                "available"
            )

        food.save(
            update_fields=[
                "quantity",
                "status",
            ]
        )

    messages.success(
        request,
        "Reservation cancelled and quantity restored."
    )

    return redirect(
        "business_dashboard"
    )


# =========================================================
# ACCOUNT
# =========================================================

def account(request):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    profile_form = ProfileForm(

        initial={
            "full_name": (
                current_user.full_name
            ),

            "phone": (
                current_user.phone
                or ""
            ),
        }
    )

    password_form = (
        PasswordChangeForm()
    )

    return render(
        request,
        "account.html",
        {
            "current_user": current_user,
            "profile_form": profile_form,
            "password_form": password_form,
        }
    )


# =========================================================
# UPDATE PROFILE
# =========================================================

@require_POST
def update_profile(request):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    form = ProfileForm(
        request.POST
    )

    if form.is_valid():

        current_user.full_name = (
            form.cleaned_data[
                "full_name"
            ]
        )

        current_user.phone = (
            form.cleaned_data[
                "phone"
            ]
            or None
        )

        current_user.save(
            update_fields=[
                "full_name",
                "phone",
            ]
        )

        request.session[
            "user_name"
        ] = current_user.full_name

        messages.success(
            request,
            "Profile updated."
        )

    else:

        messages.error(
            request,
            "Please correct the profile form."
        )

    return redirect(
        "account"
    )


# =========================================================
# CHANGE PASSWORD
# =========================================================

@require_POST
def change_password(request):

    current_user = get_current_user(request)

    if not current_user:

        return redirect(
            "login"
        )

    form = PasswordChangeForm(
        request.POST
    )

    if form.is_valid():

        current_password = (
            form.cleaned_data[
                "current_password"
            ]
        )

        if not check_password(
            current_password,
            current_user.password_hash
        ):

            messages.error(
                request,
                "Your current password is incorrect."
            )

        else:

            current_user.password_hash = (
                make_password(
                    form.cleaned_data[
                        "new_password"
                    ]
                )
            )

            current_user.save(
                update_fields=[
                    "password_hash"
                ]
            )

            messages.success(
                request,
                "Password changed successfully."
            )

    else:

        if form.errors:

            first_error = next(
                iter(
                    form.errors.values()
                )
            )[0]

        else:

            first_error = (
                "Please check the password form."
            )

        messages.error(
            request,
            first_error
        )

    return redirect(
        "account"
    )