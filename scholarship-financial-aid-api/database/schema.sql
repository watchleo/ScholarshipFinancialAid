-- ============================================================================
--  Scholarship and Financial Aid Management System (Group 5 case analysis)
--  Database schema, normalized to Third Normal Form (3NF).
--
--  * Every table holds data about exactly one entity.
--  * PK  = Primary Key
--  * FK  = Foreign Key (REFERENCES ...) - enforces the relationships
--          defined in the case study ERD (Crow's Foot notation).
--  * CHECK constraints protect the most important business rules.
--  * Seeded with the exact sample rows from the case study document.
-- ============================================================================

CREATE TABLE IF NOT EXISTS Students (
    Student_ID        TEXT PRIMARY KEY,
    Student_Name      TEXT NOT NULL,
    Program           TEXT NOT NULL,
    Year_Level        TEXT NOT NULL,
    Email             TEXT NOT NULL UNIQUE,
    Contact_No        TEXT NOT NULL,
    Household_Income  REAL NOT NULL CHECK (Household_Income >= 0),
    GPA               REAL NOT NULL CHECK (GPA >= 1.0 AND GPA <= 5.0)
);

CREATE TABLE IF NOT EXISTS Scholarship (
    Scholarship_ID         TEXT PRIMARY KEY,
    Scholarship_Name       TEXT NOT NULL,
    Scholarship_Type       TEXT NOT NULL,
    Scholarship_Slots      INTEGER NOT NULL CHECK (Scholarship_Slots >= 1),
    Max_GPA_Allowed        REAL NOT NULL CHECK (Max_GPA_Allowed >= 1.0 AND Max_GPA_Allowed <= 5.0),
    Max_Household_Income   REAL NOT NULL CHECK (Max_Household_Income >= 0)
);

CREATE TABLE IF NOT EXISTS Academic_Terms (
    Term_ID        TEXT PRIMARY KEY,
    Term_Name      TEXT NOT NULL,
    Academic_Year  TEXT NOT NULL,
    UNIQUE (Term_Name, Academic_Year)
);

CREATE TABLE IF NOT EXISTS Evaluators (
    Evaluator_ID    TEXT PRIMARY KEY,
    Evaluator_Name  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Requirements (
    Requirement_ID    TEXT PRIMARY KEY,
    Requirement_Name  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Sponsors (
    Sponsor_ID           TEXT PRIMARY KEY,
    Sponsor_Name         TEXT NOT NULL,
    Sponsor_Type         TEXT NOT NULL,
    Sponsor_Email        TEXT NOT NULL,
    Sponsor_Contact_No   TEXT NOT NULL,
    Sponsor_Budget       REAL NOT NULL CHECK (Sponsor_Budget >= 0)
);

-- Each financial aid type is funded by exactly one sponsor (FK).
CREATE TABLE IF NOT EXISTS Financial_Aid (
    Aid_ID           TEXT PRIMARY KEY,
    Sponsor_ID       TEXT NOT NULL,
    Aid_Type         TEXT NOT NULL,
    Aid_Description  TEXT NOT NULL,
    FOREIGN KEY (Sponsor_ID) REFERENCES Sponsors(Sponsor_ID)
);

-- Central entity. Nullable FKs: Scholarship (emergency aid need not be under
-- a scholarship program) and Previous_Application_ID (first application).
-- Previous_Application_ID is a self-referencing FK used by renewals.
CREATE TABLE IF NOT EXISTS Applications (
    Application_ID           TEXT PRIMARY KEY,
    Student_ID               TEXT NOT NULL,
    Scholarship_ID           TEXT,
    Aid_ID                   TEXT NOT NULL,
    Term_ID                  TEXT NOT NULL,
    Evaluator_ID             TEXT NOT NULL,
    Previous_Application_ID  TEXT,
    Application_Date         TEXT NOT NULL,
    Status                   TEXT NOT NULL
                             CHECK (Status IN ('Pending', 'Approved', 'Rejected')),
    Award_Amount             REAL CHECK (Award_Amount IS NULL OR Award_Amount >= 0),
    FOREIGN KEY (Student_ID)              REFERENCES Students(Student_ID),
    FOREIGN KEY (Scholarship_ID)          REFERENCES Scholarship(Scholarship_ID),
    FOREIGN KEY (Aid_ID)                  REFERENCES Financial_Aid(Aid_ID),
    FOREIGN KEY (Term_ID)                 REFERENCES Academic_Terms(Term_ID),
    FOREIGN KEY (Evaluator_ID)            REFERENCES Evaluators(Evaluator_ID),
    FOREIGN KEY (Previous_Application_ID) REFERENCES Applications(Application_ID)
);

-- Composite PK: an application + requirement pair appears at most once.
CREATE TABLE IF NOT EXISTS Application_Requirements (
    Application_ID     TEXT NOT NULL,
    Requirement_ID     TEXT NOT NULL,
    Requirement_Status TEXT NOT NULL
                       CHECK (Requirement_Status IN ('Submitted', 'Verified', 'Missing', 'Pending')),
    Submitted_Date     TEXT,
    PRIMARY KEY (Application_ID, Requirement_ID),
    FOREIGN KEY (Application_ID) REFERENCES Applications(Application_ID) ON DELETE CASCADE,
    FOREIGN KEY (Requirement_ID) REFERENCES Requirements(Requirement_ID)
);

-- Multi-installment disbursements per application.
CREATE TABLE IF NOT EXISTS Disbursements (
    Disbursement_ID       TEXT PRIMARY KEY,
    Application_ID        TEXT NOT NULL,
    Disbursement_Date     TEXT NOT NULL,
    Disbursement_Amount   REAL NOT NULL CHECK (Disbursement_Amount > 0),
    Payment_Method        TEXT NOT NULL,
    Payment_Reference_No  TEXT NOT NULL,
    Disbursement_Note     TEXT,
    FOREIGN KEY (Application_ID) REFERENCES Applications(Application_ID) ON DELETE CASCADE
);

-- Indexes for the most common join/filter columns
CREATE INDEX IF NOT EXISTS idx_applications_student     ON Applications(Student_ID);
CREATE INDEX IF NOT EXISTS idx_applications_term        ON Applications(Term_ID);
CREATE INDEX IF NOT EXISTS idx_disbursements_application ON Disbursements(Application_ID);
