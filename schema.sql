CREATE DATABASE IF NOT EXISTS microdebt;
USE microdebt;

CREATE TABLE Users (
    user_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE
);

CREATE TABLE Expenses (
    expense_id INT AUTO_INCREMENT PRIMARY KEY,
    description VARCHAR(255),
    amount DECIMAL(10,2) NOT NULL,
    paid_by INT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (paid_by) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Splits (
    split_id INT AUTO_INCREMENT PRIMARY KEY,
    expense_id INT NOT NULL,
    user_id INT NOT NULL,
    share DECIMAL(10,2) NOT NULL,
    FOREIGN KEY (expense_id) REFERENCES Expenses(expense_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES Users(user_id) ON DELETE CASCADE
);

CREATE TABLE Payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    payer_id INT NOT NULL,
    payee_id INT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (payer_id) REFERENCES Users(user_id) ON DELETE CASCADE,
    FOREIGN KEY (payee_id) REFERENCES Users(user_id) ON DELETE CASCADE
);
