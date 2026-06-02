# HR Management System — Dataflow Description
**Project:** HR Management System  
**Team:** Abia Saeed, Hajia Akhlaq, Noora Imran | BSCS 'B'  
**Date:** May 2026

---

## 1. Overview

This document describes how data flows through the HR Management System — from the moment a candidate applies for a job, through the recruitment and testing pipeline, to hiring, onboarding, and training. The system is backed by a relational MySQL database with 9 normalized tables.

---

## 2. Database Tables Summary

| Table | Rows | Description |
|---|---|---|
| Departments | 4 | Organizational units (Operations, Legal, Admin, Public Health) |
| Job_Postings | 4 | Open and closed job roles |
| Candidates | 953 | All applicants who submitted a CV |
| Applications | 953 | One application per candidate linking to a job posting |
| Interviews | 1,213 | Two-stage assessment records (English Test + 1st Interview) |
| Employees | 152 | Candidates who were successfully hired |
| Trainers | 3 | Staff responsible for onboarding new hires |
| Training_Programs | 2 | Defined onboarding programs (SystemONE, EMIS/Docman) |
| Employee_Training | 59 | Records of which employee attended which training program |

---

## 3. Step-by-Step Dataflow

### Stage 1 — Job Posting
The HR department creates a job posting. This record is stored in **Job_Postings** and linked to a **Department**. Each posting has a Job_ID (e.g., J001 = Clinical Coder) and a status (Active/Closed).

```
Departments ──────> Job_Postings
(D001: Operations)   (J001: Clinical Coder)
```

---

### Stage 2 — Candidate Registration
A candidate submits their CV through a source (LinkedIn, Rozee.pk, HR Desk, referral, etc.). Their personal and professional details are recorded in the **Candidates** table. Each candidate gets a unique Candidate_ID (e.g., CC-001).

**Data captured:**
- Full Name, Country, Email, WhatsApp Number
- Qualification, Experience Summary
- CV Source (where they came from)
- Resume Received Date

```
Candidate submits CV ──> Candidates table
(CC-001: khairul Asad, Pakistan, LinkedIn)
```

---

### Stage 3 — Application Submission
Each candidate is linked to the job they applied for through the **Applications** table. This is a bridge between **Candidates** and **Job_Postings**. One candidate = one application record.

**Data captured:**
- Application_ID (e.g., APP-0001)
- Candidate_ID → Job_ID
- Application Date
- Final Status (Hired / Rejected / No Response / Pending / Amber / Hired but Left)
- Additional Remarks

```
Candidates ──────> Applications <────── Job_Postings
(CC-001)           (APP-0001)           (J001)
```

---

### Stage 4 — Assessment / Interview Process
Candidates go through a two-stage selection process recorded in the **Interviews** table:

**Stage A — English Test**
- An English proficiency test is emailed to the candidate
- Scores are recorded: Core Skills Score, Speaking Score, Writing Score
- Results are received by email and logged

**Stage B — 1st Interview (if Stage A passed)**
- Interview is scheduled (date + time slot)
- Interviewer records a score or status (Pass/Fail/Hold)

Each stage creates a separate row in Interviews, linked back to the Application_ID and Candidate_ID.

```
Applications ──> Interviews (Stage A: English Test)
              └> Interviews (Stage B: 1st Interview)
```

---

### Stage 5 — Hiring Decision
After interviews, HR updates the **Applications** table Final_Status field. Candidates marked **"Hired"** are promoted to the **Employees** table.

**Data carried forward from Candidates to Employees:**
- Full Name, Country, Email, Qualification
- Department_ID assigned (D001 = Operations for clinical coders)
- Hiring Date recorded
- Employment_Status set to "Active"

```
Applications (Final_Status = 'Hired')
        │
        ▼
Employees table  ◄──── Departments (D001: Operations)
(EMP-0001: ...)
```

---

### Stage 6 — Training / Onboarding
New employees are enrolled in an onboarding training program. The system has two defined programs in **Training_Programs**:
- **TP001:** SystemONE Onboarding (GP records system)
- **TP002:** EMIS/Docman Onboarding (document management)

Each training session is assigned a **Trainer** from the **Trainers** table (Saman Taufiq, Ayesha Kareem, Saad Ali).

The enrollment record is stored in **Employee_Training**, which is the link between Employees, Training_Programs, and Trainers.

**Data captured:**
- Employee_ID → Program_ID → Trainer_ID
- Training Start Date
- Country, Qualifications
- Completion_Status (Completed / In Progress)

```
Employees ────────> Employee_Training <──── Training_Programs
(EMP-0001)          (ET-0001)               (TP001: SystemONE)
                         │
                    Trainers (TR001: Saman Taufiq)
```

---

## 4. Entity Relationship Summary

```
Departments
    │
    ├──< Job_Postings
    │         │
    │         └──< Applications >──── Candidates
    │                   │
    │                   └──< Interviews
    │
    └──< Employees
              │
              └──< Employee_Training >──── Training_Programs
                                    │
                                  Trainers
```

**Key Relationships:**
- A **Department** has many **Job_Postings**
- A **Job_Posting** receives many **Applications**
- A **Candidate** submits one **Application** (per posting)
- An **Application** has multiple **Interview** stages
- A hired **Candidate** becomes one **Employee**
- An **Employee** can attend one or more **Training Programs**
- A **Trainer** conducts many **Employee_Training** sessions

---

## 5. Data Sources

| Source File | Description | Mapped To |
|---|---|---|
| `Recruitment_Data_Set.csv` | Raw recruitment tracker with 953 candidate records | Candidates, Applications, Interviews, Employees |
| `2026_Hiring_cohorts.xlsx` (Jan 2026 sheet) | 24 employees onboarded in January 2026 | Employee_Training |
| `2026_Hiring_cohorts.xlsx` (Feb 2026 sheet) | 35 employees onboarded in February 2026 | Employee_Training |

---

## 6. Data Cleaning Applied

| Issue Found | How It Was Fixed |
|---|---|
| Inconsistent Final Status values ("Hired ", "Hired but left", "Hired But Left") | Standardized to: Hired, Hired but Left, No Response, Rejected, etc. |
| Typo in job title ("Clinal Coder" instead of "Clinical Coder") | Mapped to J001 (Clinical Coder) |
| Non-breaking space characters (`\xa0`) in CV Source and Final Status | Replaced with "Unknown" |
| LinkedIn spelled as "LinkedIN" and "Linked IN" | Normalized to "LinkedIn" |
| Rozee.pk and Rozee treated separately | Normalized to "Rozee.pk" |
| Trailing unnamed columns in CSV | Dropped |
| NaT (not-a-time) values in training dates | Stored as NULL |

---

## 7. Exported CSV Files

```
Departments.csv          — 4 rows
Job_Postings.csv         — 4 rows
Candidates.csv           — 953 rows
Applications.csv         — 953 rows
Interviews.csv           — 1,213 rows
Employees.csv            — 152 rows
Trainers.csv             — 3 rows
Training_Programs.csv    — 2 rows
Employee_Training.csv    — 59 rows
```

Each CSV file represents one database table and can be directly imported into MySQL using `LOAD DATA INFILE` or phpMyAdmin's import feature.
