from django.urls import path

from . import (
    business_analytics_views,
    extension_views,
    impact_views,
    interest_views,
    notification_views,
    reliability_views,
    rescue_views,
    views,
)


urlpatterns = [

    path(
        "",
        views.home,
        name="home"
    ),

    path(
        "signup/",
        views.signup_user,
        name="signup_user"
    ),

    path(
        "signup/business/",
        views.signup_business,
        name="signup_business"
    ),

    path(
        "login/",
        views.login_user,
        name="login"
    ),

    path(
        "logout/",
        views.logout_user,
        name="logout"
    ),


    # =====================================================
    # USER
    # =====================================================

    path(
        "dashboard/",
        views.dashboard,
        name="dashboard"
    ),

    path(
        "food/<int:food_id>/",
        views.food_detail,
        name="food_detail"
    ),

    path(
        "food/<int:food_id>/reserve/",
        views.reserve_food,
        name="reserve_food"
    ),

    path(
        "reservations/",
        views.my_reservations,
        name="my_reservations"
    ),

    path(
        "reservations/<int:reservation_id>/cancel/",
        views.cancel_reservation,
        name="cancel_reservation"
    ),


    # =====================================================
    # INTERESTS
    # =====================================================

    path(
        "discover/",
        interest_views.track_dashboard_search,
        name="track_dashboard_search"
    ),

    path(
        "discover/food/<int:food_id>/",
        interest_views.track_food_view,
        name="track_food_view"
    ),

    path(
        "food/<int:food_id>/interest/",
        interest_views.toggle_food_interest,
        name="toggle_food_interest"
    ),

    path(
        "interests/",
        interest_views.interest_profile,
        name="interest_profile"
    ),


    # =====================================================
    # IMPACT
    # =====================================================

    path(
        "impact/",
        impact_views.impact_dashboard,
        name="impact"
    ),


    # =====================================================
    # RELIABILITY
    # =====================================================

    path(
        "reliability/",
        reliability_views.reliability_page,
        name="reliability"
    ),


    # =====================================================
    # COLLECTION CHECK-IN
    # =====================================================

    path(
        "reservations/<int:reservation_id>/check-in/<str:answer>/",
        rescue_views.collection_checkin,
        name="collection_checkin"
    ),


    # =====================================================
    # PICKUP EXTENSION
    # =====================================================

    path(
        "reservations/<int:reservation_id>/extension/<str:answer>/",
        extension_views.extension_response,
        name="extension_response"
    ),


    # =====================================================
    # RESCUE
    # =====================================================

    path(
        "reservations/<int:reservation_id>/rescue/",
        rescue_views.create_rescue_request,
        name="create_rescue_request"
    ),

    path(
        "rescue-offers/",
        rescue_views.rescue_offers,
        name="rescue_offers"
    ),

    path(
        "rescue-offers/<int:offer_id>/accept/",
        rescue_views.accept_rescue_offer,
        name="accept_rescue_offer"
    ),

    path(
        "rescue-offers/<int:offer_id>/decline/",
        rescue_views.decline_rescue_offer,
        name="decline_rescue_offer"
    ),


    # =====================================================
    # NOTIFICATIONS
    # =====================================================

    path(
        "notifications/",
        notification_views.notifications_page,
        name="notifications"
    ),

    path(
        "notifications/<int:notification_id>/open/",
        notification_views.open_notification,
        name="open_notification"
    ),

    path(
        "notifications/read-all/",
        notification_views.mark_all_notifications_read,
        name="mark_all_notifications_read"
    ),

    path(
        "notifications/clear-read/",
        notification_views.clear_read_notifications,
        name="clear_read_notifications"
    ),


    # =====================================================
    # BUSINESS
    # =====================================================

    path(
        "business/dashboard/",
        views.business_dashboard,
        name="business_dashboard"
    ),

    path(
        "business/analytics/",
        business_analytics_views.business_analytics,
        name="business_analytics"
    ),

    path(
        "business/food/<int:food_id>/edit/",
        views.business_food_edit,
        name="business_food_edit"
    ),

    path(
        "business/food/<int:food_id>/toggle/",
        views.business_food_toggle,
        name="business_food_toggle"
    ),

    path(
        "business/food/<int:food_id>/delete/",
        views.business_food_delete,
        name="business_food_delete"
    ),


    # Verification now uses expiry-aware logic

    path(
        "business/reservations/<int:reservation_id>/verify/",
        extension_views.business_verify_pickup_code,
        name="business_verify_pickup_code"
    ),


    # Extend expired reservation

    path(
        "business/reservations/<int:reservation_id>/extend/<int:minutes>/",
        extension_views.business_extend_reservation,
        name="business_extend_reservation"
    ),


    path(
        "business/reservations/<int:reservation_id>/<str:action>/",
        views.business_reservation_update,
        name="business_reservation_update"
    ),


    # =====================================================
    # ACCOUNT
    # =====================================================

    path(
        "account/",
        views.account,
        name="account"
    ),

    path(
        "account/profile/",
        views.update_profile,
        name="update_profile"
    ),

    path(
        "account/password/",
        views.change_password,
        name="change_password"
    ),
]