-- Table des utilisateurs (Formateurs et Apprentis)
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(50) NOT NULL UNIQUE,
    role ENUM('admin', 'apprenti') DEFAULT 'apprenti',
    enrollment_token VARCHAR(100) UNIQUE, -- Le token à usage unique pour le QR Code
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table pour stocker les clés d'accès (WebAuthn / Passkeys)
CREATE TABLE IF NOT EXISTS passkeys (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    credential_id TEXT NOT NULL,
    public_key TEXT NOT NULL,
    sign_count INT DEFAULT 0,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- Table des modules physiques du banc KLX
CREATE TABLE IF NOT EXISTS modules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT
);

-- Table de la documentation liée aux modules
CREATE TABLE IF NOT EXISTS documentation (
    id INT AUTO_INCREMENT PRIMARY KEY,
    module_id INT NOT NULL,
    title VARCHAR(150) NOT NULL,
    file_path VARCHAR(255) NOT NULL, -- Le chemin vers le fichier PDF ou la page
    FOREIGN KEY (module_id) REFERENCES modules(id) ON DELETE CASCADE
);

-- Ajout d'un compte formateur par défaut pour vos tests
INSERT INTO users (username, role) VALUES ('formateur_test', 'admin');
-- Ajout de modules pour tester l'interface
INSERT INTO modules (name, description) VALUES 
('MODULE STATION MÉTÉO MD1A3028', 'Assigné pour TP : TP #12 Câblage KNX'),
('MODULE DALI GATEWAY MD1A3020', 'Assigné pour TP : TP #12 Câblage KNX'),
('MODULE VARIATEUR MD1A3046', 'Assigné pour TP : TP #14 Paramétrage');
