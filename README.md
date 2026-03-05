# Veterinary Clinic Management System

Sistema web desenvolvido em **Python** para gestão de uma clínica veterinária.  
O sistema permite gerir clientes, animais e consultas através de uma interface web simples.

Projeto desenvolvido no âmbito do curso **Programador/a de Informática (IEFP Braga)**.

---

# Tecnologias Utilizadas

- Python
- Flask
- HTML
- CSS
- SQL (base de dados)

---

# Funcionalidades

O sistema permite:

### Gestão de Clientes
- Criar clientes
- Listar clientes
- Editar clientes
- Consultar informação dos clientes

### Gestão de Animais
- Registar animais
- Associar animais aos seus donos
- Listar animais registados

### Gestão de Consultas
- Registar consultas veterinárias
- Listar consultas
- Visualizar consultas por cliente

### Sistema de Utilizadores
- Login de utilizador
- Área pessoal
- Dashboard

---

# Estrutura do Projeto

projeto_clinica_vet_python
│
├── clinica_vet.py # aplicação principal Flask
├── efa0125_25_vet_clinic.sql # script da base de dados
│
├── templates # páginas HTML
│ ├── base.html
│ ├── dashboard.html
│ ├── login.html
│ ├── clientes_.html
│ ├── animais_.html
│ ├── consultas_.html
│
├── static # ficheiros estáticos (CSS / imagens)
