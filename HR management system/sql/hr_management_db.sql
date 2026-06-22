CREATE DATABASE IF NOT EXISTS hr_management_db;
USE hr_management_db;

CREATE TABLE IF NOT EXISTS Departments (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    department_name VARCHAR(255),
    description TEXT
);

CREATE TABLE IF NOT EXISTS Candidates (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    phone VARCHAR(50),
    status VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS Job_Postings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255),
    job_title VARCHAR(255),
    department_id INT,
    description TEXT,
    status VARCHAR(100),
    posted_at DATE,
    FOREIGN KEY (department_id) REFERENCES Departments(id)
);

CREATE TABLE IF NOT EXISTS Applications (
    id INT AUTO_INCREMENT PRIMARY KEY,
    candidate_id INT NOT NULL,
    job_posting_id INT,
    application_date DATE,
    status VARCHAR(100),
    FOREIGN KEY (candidate_id) REFERENCES Candidates(id),
    FOREIGN KEY (job_posting_id) REFERENCES Job_Postings(id)
);

CREATE TABLE IF NOT EXISTS Interviews (
    id INT AUTO_INCREMENT PRIMARY KEY,
    application_id INT NOT NULL,
    interview_date DATE,
    interviewer VARCHAR(255),
    interview_status VARCHAR(100),
    notes TEXT,
    FOREIGN KEY (application_id) REFERENCES Applications(id)
);

CREATE TABLE IF NOT EXISTS Employees (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    department_id INT,
    hire_date DATE,
    job_title VARCHAR(255),
    FOREIGN KEY (department_id) REFERENCES Departments(id)
);

CREATE TABLE IF NOT EXISTS Trainers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    first_name VARCHAR(255) NOT NULL,
    last_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) UNIQUE,
    expertise VARCHAR(255)
);

CREATE TABLE IF NOT EXISTS Training_Programs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255),
    title VARCHAR(255),
    description TEXT,
    start_date DATE,
    end_date DATE,
    status VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS Employee_Training (
    id INT AUTO_INCREMENT PRIMARY KEY,
    employee_id INT NOT NULL,
    training_program_id INT NOT NULL,
    completion_date DATE,
    status VARCHAR(100),
    FOREIGN KEY (employee_id) REFERENCES Employees(id),
    FOREIGN KEY (training_program_id) REFERENCES Training_Programs(id)
);
