from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):

    help = "Prepare MealMate database."


    def table_exists(
        self,
        cursor,
        table_name,
    ):

        cursor.execute(
            "SHOW TABLES LIKE %s",
            [
                table_name
            ]
        )

        return (
            cursor.fetchone()
            is not None
        )


    def column_exists(
        self,
        cursor,
        table_name,
        column_name,
    ):

        cursor.execute(
            f"""
            SHOW COLUMNS
            FROM `{table_name}`
            LIKE %s
            """,
            [
                column_name
            ]
        )

        return (
            cursor.fetchone()
            is not None
        )


    def index_exists(
        self,
        cursor,
        table_name,
        index_name,
    ):

        cursor.execute(
            f"""
            SHOW INDEX
            FROM `{table_name}`
            WHERE Key_name = %s
            """,
            [
                index_name
            ]
        )

        return (
            cursor.fetchone()
            is not None
        )


    def create_tracking_tables(
        self,
        cursor,
    ):

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS food_interests (

                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

                user_id INT UNSIGNED NOT NULL,

                food_post_id INT UNSIGNED NOT NULL,

                created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

                UNIQUE KEY uq_food_interest (
                    user_id,
                    food_post_id
                )

            ) ENGINE=InnoDB
            DEFAULT CHARSET=utf8mb4
            """
        )


        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS user_activities (

                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

                user_id INT UNSIGNED NOT NULL,

                activity_type VARCHAR(40) NOT NULL,

                food_post_id INT UNSIGNED NULL,

                value VARCHAR(255) NULL,

                created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

                INDEX idx_activity_user (
                    user_id
                ),

                INDEX idx_activity_type (
                    activity_type
                )

            ) ENGINE=InnoDB
            DEFAULT CHARSET=utf8mb4
            """
        )


    def create_rescue_tables(
        self,
        cursor,
    ):

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rescue_requests (

                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

                reservation_id INT UNSIGNED NOT NULL,

                original_user_id INT UNSIGNED NOT NULL,

                food_post_id INT UNSIGNED NOT NULL,

                status VARCHAR(30)
                NOT NULL
                DEFAULT 'open',

                accepted_user_id INT UNSIGNED NULL,

                created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

                accepted_at DATETIME NULL,

                INDEX idx_rescue_reservation (
                    reservation_id
                ),

                INDEX idx_rescue_status (
                    status
                )

            ) ENGINE=InnoDB
            DEFAULT CHARSET=utf8mb4
            """
        )


        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS rescue_offers (

                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

                request_id INT UNSIGNED NOT NULL,

                user_id INT UNSIGNED NOT NULL,

                match_score INT UNSIGNED
                NOT NULL
                DEFAULT 0,

                status VARCHAR(30)
                NOT NULL
                DEFAULT 'pending',

                created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

                responded_at DATETIME NULL,

                UNIQUE KEY uq_rescue_offer (
                    request_id,
                    user_id
                ),

                INDEX idx_rescue_offer_user (
                    user_id,
                    status
                )

            ) ENGINE=InnoDB
            DEFAULT CHARSET=utf8mb4
            """
        )


    def create_notifications(
        self,
        cursor,
    ):

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications (

                id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,

                user_id INT UNSIGNED NOT NULL,

                notification_type VARCHAR(50) NOT NULL,

                title VARCHAR(150) NOT NULL,

                message VARCHAR(500) NOT NULL,

                link VARCHAR(255) NULL,

                is_read TINYINT(1)
                NOT NULL
                DEFAULT 0,

                dedupe_key VARCHAR(255) NULL,

                created_at TIMESTAMP
                DEFAULT CURRENT_TIMESTAMP,

                INDEX idx_notification_user (
                    user_id
                ),

                INDEX idx_notification_unread (
                    user_id,
                    is_read
                ),

                UNIQUE KEY uq_notification_dedupe (
                    user_id,
                    dedupe_key
                )

            ) ENGINE=InnoDB
            DEFAULT CHARSET=utf8mb4
            """
        )


    def remove_old_rescue_unique_index(
        self,
        cursor,
    ):

        if not self.table_exists(
            cursor,
            "rescue_requests",
        ):

            return


        cursor.execute(
            """
            SHOW INDEX
            FROM rescue_requests
            """
        )


        rows = cursor.fetchall()

        indexes_to_drop = set()


        for row in rows:

            non_unique = row[1]
            key_name = row[2]
            column_name = row[4]


            if (
                column_name == "reservation_id"
                and
                non_unique == 0
                and
                key_name != "PRIMARY"
            ):

                indexes_to_drop.add(
                    key_name
                )


        for index_name in indexes_to_drop:

            cursor.execute(
                f"""
                ALTER TABLE rescue_requests
                DROP INDEX `{index_name}`
                """
            )


        if not self.index_exists(
            cursor,
            "rescue_requests",
            "idx_rescue_reservation",
        ):

            cursor.execute(
                """
                ALTER TABLE rescue_requests

                ADD INDEX idx_rescue_reservation (
                    reservation_id
                )
                """
            )


    def update_reservations(
        self,
        cursor,
    ):

        if not self.table_exists(
            cursor,
            "reservations",
        ):

            return


        columns = [

            (
                "pickup_code",
                """
                ALTER TABLE reservations
                ADD COLUMN pickup_code
                VARCHAR(20) NULL
                """
            ),

            (
                "collected_at",
                """
                ALTER TABLE reservations
                ADD COLUMN collected_at
                DATETIME NULL
                """
            ),

            (
                "collection_intent",
                """
                ALTER TABLE reservations
                ADD COLUMN collection_intent
                VARCHAR(30)
                NOT NULL
                DEFAULT 'pending'
                """
            ),

            (
                "collection_confirmed_at",
                """
                ALTER TABLE reservations
                ADD COLUMN collection_confirmed_at
                DATETIME NULL
                """
            ),

            (
                "extension_status",
                """
                ALTER TABLE reservations
                ADD COLUMN extension_status
                VARCHAR(30)
                NOT NULL
                DEFAULT 'none'
                """
            ),

            (
                "extension_minutes",
                """
                ALTER TABLE reservations
                ADD COLUMN extension_minutes
                INT UNSIGNED NULL
                """
            ),

            (
                "extension_offered_at",
                """
                ALTER TABLE reservations
                ADD COLUMN extension_offered_at
                DATETIME NULL
                """
            ),

            (
                "extension_expires_at",
                """
                ALTER TABLE reservations
                ADD COLUMN extension_expires_at
                DATETIME NULL
                """
            ),
        ]


        for (
            column_name,
            sql,
        ) in columns:

            if not self.column_exists(
                cursor,
                "reservations",
                column_name,
            ):

                cursor.execute(
                    sql
                )


        if not self.index_exists(
            cursor,
            "reservations",
            "uq_reservation_pickup_code",
        ):

            cursor.execute(
                """
                ALTER TABLE reservations

                ADD UNIQUE INDEX
                uq_reservation_pickup_code (
                    pickup_code
                )
                """
            )


    def handle(
        self,
        *args,
        **options,
    ):

        if connection.vendor != "mysql":

            self.stdout.write(
                self.style.ERROR(
                    "MealMate requires MySQL."
                )
            )

            return


        with connection.cursor() as cursor:

            self.create_tracking_tables(
                cursor
            )

            self.create_rescue_tables(
                cursor
            )

            self.create_notifications(
                cursor
            )

            self.remove_old_rescue_unique_index(
                cursor
            )

            self.update_reservations(
                cursor
            )


        self.stdout.write(
            self.style.SUCCESS(
                "MealMate database ready."
            )
        )

        self.stdout.write(
            "Immediate expiry: ready"
        )

        self.stdout.write(
            "5/10/20 minute extensions: ready"
        )

        self.stdout.write(
            "Extension confirmation: ready"
        )

        self.stdout.write(
            "Extension decline notification: ready"
        )