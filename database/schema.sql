-- BloodConnect schema (MySQL 8 / TiDB Cloud compatible)
-- Usage: mysql -u USER -p DATABASE < database/schema.sql
SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS users (
  user_id     INT AUTO_INCREMENT PRIMARY KEY,
  email       VARCHAR(255) NOT NULL UNIQUE,
  password    VARCHAR(255) NOT NULL,
  role        ENUM('donor','hospital','admin') NOT NULL DEFAULT 'donor',
  is_verified BOOLEAN NOT NULL DEFAULT TRUE,
  created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  last_login  TIMESTAMP NULL
);

CREATE TABLE IF NOT EXISTS donors (
  donor_id       INT AUTO_INCREMENT PRIMARY KEY,
  user_id        INT NOT NULL,
  full_name      VARCHAR(255) NOT NULL,
  age            INT,
  blood_group    VARCHAR(5) NOT NULL,
  weight_kg      DECIMAL(5,1),
  phone          VARCHAR(20),
  city           VARCHAR(100),
  donation_count INT NOT NULL DEFAULT 0,
  created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS hospitals (
  hospital_id    INT AUTO_INCREMENT PRIMARY KEY,
  user_id        INT NOT NULL,
  name           VARCHAR(255) NOT NULL,
  license_number VARCHAR(100),
  address        VARCHAR(500),
  city           VARCHAR(100),
  phone          VARCHAR(20),
  is_verified    BOOLEAN NOT NULL DEFAULT FALSE,
  created_at     TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS blood_banks (
  bank_id       INT AUTO_INCREMENT PRIMARY KEY,
  name          VARCHAR(255) NOT NULL,
  city          VARCHAR(100),
  a_positive    INT NOT NULL DEFAULT 0,
  a_negative    INT NOT NULL DEFAULT 0,
  b_positive    INT NOT NULL DEFAULT 0,
  b_negative    INT NOT NULL DEFAULT 0,
  ab_positive   INT NOT NULL DEFAULT 0,
  ab_negative   INT NOT NULL DEFAULT 0,
  o_positive    INT NOT NULL DEFAULT 0,
  o_negative    INT NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS appointments (
  appointment_id   INT AUTO_INCREMENT PRIMARY KEY,
  donor_id         INT NOT NULL,
  hospital_id      INT NOT NULL,
  appointment_date DATE NOT NULL,
  appointment_time VARCHAR(20),
  notes            TEXT,
  status           VARCHAR(20) NOT NULL DEFAULT 'pending',
  created_at       TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (donor_id)    REFERENCES donors(donor_id)       ON DELETE CASCADE,
  FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS donations (
  donation_id    INT AUTO_INCREMENT PRIMARY KEY,
  donor_id       INT NOT NULL,
  hospital_id    INT NOT NULL,
  appointment_id INT NULL,
  quantity_ml    INT NOT NULL DEFAULT 450,
  test_type      VARCHAR(100),
  test_result    TEXT,
  donation_date  DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (donor_id)    REFERENCES donors(donor_id)       ON DELETE CASCADE,
  FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS blood_tests (
  test_id           INT AUTO_INCREMENT PRIMARY KEY,
  appointment_id    INT NULL,
  donor_id          INT NOT NULL,
  hospital_id       INT NOT NULL,
  image_path        VARCHAR(500),
  ml_cell_type      VARCHAR(100),
  ml_confidence     DECIMAL(6,2),
  diseases_detected TEXT,
  is_healthy        BOOLEAN,
  tested_at         TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (donor_id)    REFERENCES donors(donor_id)       ON DELETE CASCADE,
  FOREIGN KEY (hospital_id) REFERENCES hospitals(hospital_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS badges (
  badge_id      INT AUTO_INCREMENT PRIMARY KEY,
  donor_id      INT NOT NULL,
  badge_name    VARCHAR(100) NOT NULL,
  badge_icon    VARCHAR(20),
  badge_message VARCHAR(500),
  awarded_at    TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS alerts (
  alert_id   INT AUTO_INCREMENT PRIMARY KEY,
  donor_id   INT NOT NULL,
  test_id    INT NULL,
  alert_type VARCHAR(30) NOT NULL,
  title      VARCHAR(255),
  message    TEXT,
  details    TEXT,
  is_read    BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (donor_id) REFERENCES donors(donor_id) ON DELETE CASCADE
);
