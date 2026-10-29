from django.db import models


class MealMateUser(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    full_name = models.CharField(
        max_length=150
    )

    email = models.EmailField(
        max_length=255,
        unique=True
    )

    password_hash = models.CharField(
        max_length=255
    )

    role = models.CharField(
        max_length=30,
        default="user"
    )

    phone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    is_active = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        managed = False
        db_table = "users"


class FoodPost(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    business_id = models.PositiveIntegerField()

    food_name = models.CharField(
        max_length=150
    )

    description = models.TextField(
        blank=True,
        null=True
    )

    quantity = models.PositiveIntegerField(
        default=1
    )

    pickup_address = models.CharField(
        max_length=255
    )

    pickup_start = models.DateTimeField()

    pickup_end = models.DateTimeField()

    status = models.CharField(
        max_length=30,
        default="available"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        managed = False
        db_table = "food_posts"


class Reservation(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    user_id = models.PositiveIntegerField()

    food_post_id = models.PositiveIntegerField()

    status = models.CharField(
        max_length=30,
        default="reserved"
    )

    pickup_code = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
        null=True
    )

    collection_intent = models.CharField(
        max_length=30,
        default="pending"
    )

    collection_confirmed_at = models.DateTimeField(
        blank=True,
        null=True
    )

    extension_status = models.CharField(
        max_length=30,
        default="none"
    )

    extension_minutes = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    extension_offered_at = models.DateTimeField(
        blank=True,
        null=True
    )

    extension_expires_at = models.DateTimeField(
        blank=True,
        null=True
    )

    reserved_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    collected_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = "reservations"


class FoodInterest(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    user_id = models.PositiveIntegerField()

    food_post_id = models.PositiveIntegerField()

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        managed = False
        db_table = "food_interests"


class UserActivity(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    user_id = models.PositiveIntegerField()

    activity_type = models.CharField(
        max_length=40
    )

    food_post_id = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    value = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        managed = False
        db_table = "user_activities"


class RescueRequest(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    reservation_id = models.PositiveIntegerField()

    original_user_id = models.PositiveIntegerField()

    food_post_id = models.PositiveIntegerField()

    status = models.CharField(
        max_length=30,
        default="open"
    )

    accepted_user_id = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    accepted_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = "rescue_requests"


class RescueOffer(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    request_id = models.PositiveIntegerField()

    user_id = models.PositiveIntegerField()

    match_score = models.PositiveIntegerField(
        default=0
    )

    status = models.CharField(
        max_length=30,
        default="pending"
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    responded_at = models.DateTimeField(
        blank=True,
        null=True
    )

    class Meta:
        managed = False
        db_table = "rescue_offers"


class Notification(models.Model):

    id = models.AutoField(
        primary_key=True
    )

    user_id = models.PositiveIntegerField()

    notification_type = models.CharField(
        max_length=50
    )

    title = models.CharField(
        max_length=150
    )

    message = models.CharField(
        max_length=500
    )

    link = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    is_read = models.BooleanField(
        default=False
    )

    dedupe_key = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        managed = False
        db_table = "notifications"