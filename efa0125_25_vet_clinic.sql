CREATE DATABASE efa0125_25_vet_clinic;

USE efa0125_25_vet_clinic;

CREATE DATABASE IF NOT EXISTS efa0125_25_vet_clinic;
USE efa0125_25_vet_clinic;

-- Clientes (donos dos animais)
CREATE TABLE clientes (
  id INT AUTO_INCREMENT PRIMARY KEY,
  nome VARCHAR(120) NOT NULL,
  telefone VARCHAR(30),
  email VARCHAR(120) UNIQUE,
  morada VARCHAR(255),
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Utilizadores do sistema (admin/staff/cliente)
-- cliente_id é usado apenas quando role='cliente'
CREATE TABLE users (
  id INT AUTO_INCREMENT PRIMARY KEY,
  username VARCHAR(50) NOT NULL UNIQUE,
  password VARCHAR(255) NOT NULL,          -- <-- texto simples
  role ENUM('admin','staff','cliente') NOT NULL,
  cliente_id INT NULL,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  CONSTRAINT fk_users_cliente
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
    ON DELETE SET NULL
);


-- Animais (pacientes)
CREATE TABLE animais (
  id INT AUTO_INCREMENT PRIMARY KEY,
  cliente_id INT NOT NULL,
  nome VARCHAR(120) NOT NULL,
  especie VARCHAR(50) NOT NULL,
  raca VARCHAR(80),
  data_nascimento DATE,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (cliente_id) REFERENCES clientes(id) ON DELETE CASCADE
);

-- Consultas
CREATE TABLE consultas (
  id INT AUTO_INCREMENT PRIMARY KEY,
  animal_id INT NOT NULL,
  data_hora DATETIME NOT NULL,
  motivo VARCHAR(255),
  notas TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (animal_id) REFERENCES animais(id) ON DELETE CASCADE
);

-- Seeds (exemplo)
INSERT INTO users (username, password, role) VALUES
('admin', '1234', 'admin'),
('rececao', '1234', 'staff');

select * from users;
