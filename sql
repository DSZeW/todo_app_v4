-- Création de la base de données
CREATE DATABASE IF NOT EXISTS plash_db;
USE plash_db;

-- Table : users (ajout de l'e-mail unique)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL
);

-- Table : categories (liée à chaque user, nom de catégorie réutilisable par d'autres users)
CREATE TABLE IF NOT EXISTS categories (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    user_id INT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table : priorities (3 niveaux)
CREATE TABLE IF NOT EXISTS priorities (
    id INT AUTO_INCREMENT PRIMARY KEY,
    level VARCHAR(50) NOT NULL
);

-- Table : statuses (3 statuts)
CREATE TABLE IF NOT EXISTS statuses (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

-- Table : tasks (liée aux users, catégories, priorités, statuts)
CREATE TABLE IF NOT EXISTS tasks (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    title VARCHAR(255) NOT NULL,
    category_id INT NOT NULL,
    priority_id INT NOT NULL,
    status_id INT DEFAULT 1,
    completed BOOLEAN DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY(category_id) REFERENCES categories(id) ON DELETE CASCADE,
    FOREIGN KEY(priority_id) REFERENCES priorities(id),
    FOREIGN KEY(status_id) REFERENCES statuses(id)
);

-- Table : comments (liée aux tâches)
CREATE TABLE IF NOT EXISTS comments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    task_id INT NOT NULL,
    comment TEXT NOT NULL,
    FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE
);

-- Table : connections_log (historique des connexions)
CREATE TABLE IF NOT EXISTS connections_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    login_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Données initiales : Priorités
INSERT INTO priorities (id, level) VALUES
(1, 'Basse'),
(2, 'Moyenne'),
(3, 'Haute')
ON DUPLICATE KEY UPDATE level = VALUES(level);

-- Données initiales : Statuts
INSERT INTO statuses (id, name) VALUES
(1, 'Non commencée'),
(2, 'En cours'),
(3, 'Terminée')
ON DUPLICATE KEY UPDATE name = VALUES(name);
