-- MealMate custom application tables for MySQL 8.4+
-- Safe to run more than once.

CREATE DATABASE IF NOT EXISTS mealmate
CHARACTER SET utf8mb4
COLLATE utf8mb4_unicode_ci;

USE mealmate;

CREATE TABLE IF NOT EXISTS users (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    full_name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    role VARCHAR(30) NOT NULL DEFAULT 'user',
    phone VARCHAR(30) DEFAULT NULL,
    is_active TINYINT(1) NOT NULL DEFAULT 1,
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_users_role (role)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS food_posts (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    business_id INT UNSIGNED NOT NULL,
    food_name VARCHAR(150) NOT NULL,
    description TEXT DEFAULT NULL,
    quantity INT UNSIGNED NOT NULL DEFAULT 1,
    pickup_address VARCHAR(255) NOT NULL,
    pickup_start DATETIME NOT NULL,
    pickup_end DATETIME NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'available',
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_food_business (business_id),
    INDEX idx_food_status_pickup (status, pickup_end),
    CONSTRAINT fk_food_business FOREIGN KEY (business_id)
        REFERENCES users(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS reservations (
    id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
    user_id INT UNSIGNED NOT NULL,
    food_post_id INT UNSIGNED NOT NULL,
    status VARCHAR(30) NOT NULL DEFAULT 'reserved',
    reserved_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_reservation_user (user_id),
    INDEX idx_reservation_food (food_post_id),
    INDEX idx_reservation_status (status),
    CONSTRAINT fk_reservation_user FOREIGN KEY (user_id)
        REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_reservation_food FOREIGN KEY (food_post_id)
        REFERENCES food_posts(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
