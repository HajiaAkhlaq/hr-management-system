
DROP DATABASE IF EXISTS HR_Management;
CREATE DATABASE HR_Management;
USE HR_Management;

-- =========================
-- DEPARTMENTS
-- =========================
CREATE TABLE Departments (
    Department_ID VARCHAR(10) PRIMARY KEY,
    Department_Name VARCHAR(100) NOT NULL,
    Description TEXT
);

-- =========================
-- CANDIDATES
-- =========================
CREATE TABLE Candidates (
    Candidate_ID VARCHAR(20) PRIMARY KEY,
    Full_Name VARCHAR(200) NOT NULL,
    Email VARCHAR(200),
    Phone_Number VARCHAR(30)
);

-- =========================
-- JOB POSTINGS
-- =========================
CREATE TABLE Job_Postings (
    Job_ID VARCHAR(10) PRIMARY KEY,
    Job_Title VARCHAR(200) NOT NULL,
    Department_ID VARCHAR(10),
    Description TEXT,
    Posted_Date DATE,

    FOREIGN KEY (Department_ID)
        REFERENCES Departments(Department_ID)
);

-- =========================
-- APPLICATIONS
-- =========================
CREATE TABLE Applications (
    Application_ID VARCHAR(20) PRIMARY KEY,
    Candidate_ID VARCHAR(20),
    Job_ID VARCHAR(10),
    Final_Status VARCHAR(50),
    Application_Date DATE,

    FOREIGN KEY (Candidate_ID)
        REFERENCES Candidates(Candidate_ID),

    FOREIGN KEY (Job_ID)
        REFERENCES Job_Postings(Job_ID)
);

-- =========================
-- INTERVIEWS
-- =========================
CREATE TABLE Interviews (
    Interview_ID VARCHAR(20) PRIMARY KEY,
    Application_ID VARCHAR(20),
    Candidate_ID VARCHAR(20),
    Stage VARCHAR(50),
    Overall_Score_Rating VARCHAR(50),

    FOREIGN KEY (Application_ID)
        REFERENCES Applications(Application_ID),

    FOREIGN KEY (Candidate_ID)
        REFERENCES Candidates(Candidate_ID)
);

-- =========================
-- EMPLOYEES
-- =========================
CREATE TABLE Employees (
    Employee_ID VARCHAR(15) PRIMARY KEY,
    Candidate_ID VARCHAR(20),
    Department_ID VARCHAR(10),
    Full_Name VARCHAR(200),
    Hiring_Date DATE,

    FOREIGN KEY (Candidate_ID)
        REFERENCES Candidates(Candidate_ID),

    FOREIGN KEY (Department_ID)
        REFERENCES Departments(Department_ID)
);

-- =========================
-- TRAINERS
-- =========================
CREATE TABLE Trainers (
    Trainer_ID VARCHAR(10) PRIMARY KEY,
    Department_ID VARCHAR(10),
    Trainer_Name VARCHAR(200),
    Specialization VARCHAR(100),

    FOREIGN KEY (Department_ID)
        REFERENCES Departments(Department_ID)
);

-- =========================
-- TRAINING PROGRAMS
-- =========================
CREATE TABLE Training_Programs (
    Program_ID VARCHAR(10) PRIMARY KEY,
    Program_Name VARCHAR(200),
    Duration_Weeks INT
);

-- =========================
-- EMPLOYEE TRAINING
-- =========================
CREATE TABLE Employee_Training (
    ET_ID VARCHAR(15) PRIMARY KEY,
    Employee_ID VARCHAR(15),
    Program_ID VARCHAR(10),
    Trainer_ID VARCHAR(10),
    Department_ID VARCHAR(10),
    Training_Start_Date DATE,
    Completion_Status VARCHAR(50),

    FOREIGN KEY (Employee_ID)
        REFERENCES Employees(Employee_ID),

    FOREIGN KEY (Program_ID)
        REFERENCES Training_Programs(Program_ID),

    FOREIGN KEY (Trainer_ID)
        REFERENCES Trainers(Trainer_ID),

    FOREIGN KEY (Department_ID)
        REFERENCES Departments(Department_ID)
);