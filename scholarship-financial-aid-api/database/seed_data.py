"""Seed data taken directly from the Group 5 case analysis (3NF tables).

Every row below matches the normalized tables in the case study document,
including the rows marked "(Extra Sample)" (SP04, SCH03).

[Unit II] Built-in Data Structures: each table is stored as a list of
tuples - one tuple per row - and SEED_TABLES keeps them in foreign-key
order so the database can be filled in a single pass.
"""

STUDENT_COLUMNS = (
    "Student_ID", "Student_Name", "Program", "Year_Level",
    "Email", "Contact_No", "Household_Income", "GPA",
)
STUDENTS = [
    ("S001", "Juan Dela Cruz", "BS Information Technology", "2nd Year",
     "juan.delacruz@student.edu.ph", "0917-111-2233", 18000.00, 1.75),
    ("S002", "Maria Santos", "BS Nursing", "3rd Year",
     "maria.santos@student.edu.ph", "0918-222-3344", 12000.00, 1.50),
    ("S003", "Jose Reyes", "BS Accountancy", "1st Year",
     "jose.reyes@student.edu.ph", "0919-333-4455", 25000.00, 2.00),
    ("S004", "Ana Villanueva", "BS Education", "4th Year",
     "ana.villanueva@student.edu.ph", "0920-444-5566", 9000.00, 1.25),
    ("S005", "Mark Bautista", "BS Civil Engineering", "2nd Year",
     "mark.bautista@student.edu.ph", "0921-555-6677", 15000.00, 2.25),
]

SCHOLARSHIP_COLUMNS = (
    "Scholarship_ID", "Scholarship_Name", "Scholarship_Type",
    "Scholarship_Slots", "Max_GPA_Allowed", "Max_Household_Income",
)
SCHOLARSHIPS = [
    ("SCH01", "Academic Excellence Scholarship", "Merit-Based", 50, 1.75, 30000.00),
    ("SCH02", "Need-Based Grant", "Need-Based", 100, 2.50, 15000.00),
    ("SCH03", "Alumni Legacy Scholarship", "Sponsored", 20, 2.00, 25000.00),  # (Extra Sample)
]

TERM_COLUMNS = ("Term_ID", "Term_Name", "Academic_Year")
TERMS = [
    ("T01", "1st Semester", "2025-2026"),
    ("T02", "2nd Semester", "2025-2026"),
    ("T03", "1st Semester", "2026-2027"),
]

EVALUATOR_COLUMNS = ("Evaluator_ID", "Evaluator_Name")
EVALUATORS = [
    ("E01", "Dr. Elena Ramirez"),
    ("E02", "Prof. Carlo Mendoza"),
    ("E03", "Ms. Liza Fernandez"),
]

REQUIREMENT_COLUMNS = ("Requirement_ID", "Requirement_Name")
REQUIREMENTS = [
    ("R01", "Application Form"),
    ("R02", "Certificate of Registration"),
    ("R03", "Grade Report"),
    ("R04", "Certificate of Indigency / Income"),
    ("R05", "Recommendation Letter"),
]

SPONSOR_COLUMNS = (
    "Sponsor_ID", "Sponsor_Name", "Sponsor_Type",
    "Sponsor_Email", "Sponsor_Contact_No", "Sponsor_Budget",
)
SPONSORS = [
    ("SP01", "University Financial Aid Office", "Institutional",
     "finaid@university.edu.ph", "(02) 8123-4567", 2000000.00),
    ("SP02", "Bayanihan Foundation", "Private Foundation",
     "grants@bayanihan.org.ph", "0917-555-0101", 1500000.00),
    ("SP03", "Metro Savings Bank", "Corporate",
     "csr@metrosavings.com.ph", "(02) 8555-0202", 800000.00),
    ("SP04", "Rizal Alumni Association", "Alumni Association",
     "alumni@rizalalumni.org.ph", "0922-777-8899", 500000.00),  # (Extra Sample)
]

FINANCIAL_AID_COLUMNS = ("Aid_ID", "Sponsor_ID", "Aid_Type", "Aid_Description")
FINANCIAL_AIDS = [
    ("FA01", "SP01", "Tuition", "Tuition fee assistance per semester"),
    ("FA02", "SP02", "Books", "Book and learning materials allowance"),
    ("FA03", "SP01", "Emergency", "One-time emergency financial support"),
    ("FA04", "SP03", "Tuition", "Tuition support for partner-bank scholars"),
]

APPLICATION_COLUMNS = (
    "Application_ID", "Student_ID", "Scholarship_ID", "Aid_ID", "Term_ID",
    "Evaluator_ID", "Previous_Application_ID", "Application_Date",
    "Status", "Award_Amount",
)
APPLICATIONS = [
    ("A001", "S001", "SCH01", "FA01", "T01", "E01", None, "2025-06-10", "Approved", 25000.00),
    ("A002", "S002", "SCH02", "FA02", "T01", "E02", None, "2025-06-12", "Approved", 8000.00),
    ("A003", "S003", None, "FA03", "T01", "E01", None, "2025-06-20", "Rejected", 0.00),
    ("A004", "S001", "SCH01", "FA01", "T02", "E01", "A001", "2025-11-05", "Approved", 25000.00),
    ("A005", "S004", "SCH02", "FA04", "T02", "E03", None, "2025-11-08", "Approved", 30000.00),
    ("A006", "S005", "SCH02", "FA02", "T03", "E02", None, "2026-06-15", "Pending", None),
]

APPLICATION_REQUIREMENT_COLUMNS = (
    "Application_ID", "Requirement_ID", "Requirement_Status", "Submitted_Date",
)
APPLICATION_REQUIREMENTS = [
    ("A001", "R01", "Verified", "2025-06-08"),
    ("A001", "R02", "Verified", "2025-06-08"),
    ("A001", "R03", "Verified", "2025-06-09"),
    ("A001", "R05", "Verified", "2025-06-09"),
    ("A002", "R01", "Verified", "2025-06-11"),
    ("A002", "R02", "Verified", "2025-06-11"),
    ("A002", "R03", "Verified", "2025-06-11"),
    ("A002", "R04", "Verified", "2025-06-12"),
    ("A003", "R01", "Verified", "2025-06-18"),
    ("A003", "R04", "Missing", None),
    ("A004", "R01", "Verified", "2025-11-03"),
    ("A004", "R02", "Verified", "2025-11-03"),
    ("A004", "R03", "Verified", "2025-11-04"),
    ("A005", "R01", "Verified", "2025-11-06"),
    ("A005", "R03", "Verified", "2025-11-06"),
    ("A005", "R04", "Verified", "2025-11-07"),
    ("A006", "R01", "Submitted", "2026-06-14"),
    ("A006", "R02", "Submitted", "2026-06-14"),
    ("A006", "R04", "Pending", None),
]

DISBURSEMENT_COLUMNS = (
    "Disbursement_ID", "Application_ID", "Disbursement_Date",
    "Disbursement_Amount", "Payment_Method", "Payment_Reference_No",
    "Disbursement_Note",
)
DISBURSEMENTS = [
    ("D001", "A001", "2025-07-15", 12500.00, "Bank Transfer", "REF-2025-0715-001", "1st installment"),
    ("D002", "A001", "2025-09-15", 12500.00, "Bank Transfer", "REF-2025-0915-002", "2nd installment"),
    ("D003", "A002", "2025-07-20", 8000.00, "GCash", "GC-0720-778", "Full book allowance"),
    ("D004", "A004", "2025-12-10", 12500.00, "Bank Transfer", "REF-2025-1210-004", "1st installment"),
    ("D005", "A004", "2026-02-10", 12500.00, "Bank Transfer", "REF-2026-0210-005", "2nd installment"),
    ("D006", "A005", "2025-12-15", 15000.00, "Check", "CHK-004512", "1st installment"),
    ("D007", "A005", "2026-02-15", 15000.00, "Check", "CHK-004513", "2nd installment"),
]

# Tables in foreign-key order: parents first, children last, so a single
# pass can insert everything without violating any constraint.
SEED_TABLES = [
    ("Students", STUDENT_COLUMNS, STUDENTS),
    ("Scholarship", SCHOLARSHIP_COLUMNS, SCHOLARSHIPS),
    ("Academic_Terms", TERM_COLUMNS, TERMS),
    ("Evaluators", EVALUATOR_COLUMNS, EVALUATORS),
    ("Requirements", REQUIREMENT_COLUMNS, REQUIREMENTS),
    ("Sponsors", SPONSOR_COLUMNS, SPONSORS),
    ("Financial_Aid", FINANCIAL_AID_COLUMNS, FINANCIAL_AIDS),
    ("Applications", APPLICATION_COLUMNS, APPLICATIONS),
    ("Application_Requirements", APPLICATION_REQUIREMENT_COLUMNS, APPLICATION_REQUIREMENTS),
    ("Disbursements", DISBURSEMENT_COLUMNS, DISBURSEMENTS),
]

# Table names used by the /api/health row counter
ALL_TABLES = [name for name, _columns, _rows in SEED_TABLES]
