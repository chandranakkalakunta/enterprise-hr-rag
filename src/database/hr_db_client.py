"""
HR Database Client - ChandraAILabs HR RAG Platform
Connects to Cloud SQL PostgreSQL for personal HR data
"""
import logging
import os
from datetime import date, datetime

logger = logging.getLogger(__name__)


class HRDBClient:
    """
    Cloud SQL PostgreSQL client for HR data.
    Uses Cloud SQL Python Connector for secure connection.
    """

    def __init__(
        self,
        project_id: str,
        instance_name: str,
        db_name: str,
        db_user: str,
        db_password: str,
        region: str = "asia-south1"
    ):
        self.project_id = project_id
        self.instance_name = instance_name
        self.db_name = db_name
        self.db_user = db_user
        self.db_password = db_password
        self.region = region
        self.connection_name = f"{project_id}:{region}:{instance_name}"
        self._engine = None
        logger.info(f"HR DB client initialized: {self.connection_name}")

    def _get_engine(self):
        """Get SQLAlchemy engine with Cloud SQL connector."""
        if self._engine:
            return self._engine

        from google.cloud.sql.connector import Connector
        from sqlalchemy import create_engine

        connector = Connector()

        def getconn():
            return connector.connect(
                self.connection_name,
                "pg8000",
                user=self.db_user,
                password=self.db_password,
                db=self.db_name
            )

        self._engine = create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            pool_size=5,
            pool_recycle=1800
        )
        return self._engine

    def create_schema(self):
        """Create HR database schema."""
        from sqlalchemy import text

        schema_sql = """
        -- Employees
        CREATE TABLE IF NOT EXISTS employees (
            employee_id     VARCHAR(20) PRIMARY KEY,
            name            VARCHAR(100) NOT NULL,
            email           VARCHAR(100) UNIQUE NOT NULL,
            department      VARCHAR(50),
            designation     VARCHAR(50),
            manager_id      VARCHAR(20),
            join_date       DATE,
            employment_type VARCHAR(20) DEFAULT 'full-time',
            status          VARCHAR(20) DEFAULT 'active',
            google_id       VARCHAR(100)
        );

        -- Leave balances
        CREATE TABLE IF NOT EXISTS leave_balances (
            id              SERIAL PRIMARY KEY,
            employee_id     VARCHAR(20) REFERENCES employees(employee_id),
            leave_type      VARCHAR(20),
            total_days      INT,
            used_days       INT DEFAULT 0,
            remaining_days  INT,
            year            INT,
            UNIQUE(employee_id, leave_type, year)
        );

        -- Compensation
        CREATE TABLE IF NOT EXISTS compensation (
            id              SERIAL PRIMARY KEY,
            employee_id     VARCHAR(20) REFERENCES employees(employee_id),
            basic_salary    DECIMAL(12,2),
            hra             DECIMAL(12,2),
            ta              DECIMAL(12,2),
            special_allowance DECIMAL(12,2),
            gross_ctc       DECIMAL(12,2),
            effective_date  DATE,
            UNIQUE(employee_id, effective_date)
        );

        -- Performance ratings
        CREATE TABLE IF NOT EXISTS performance_ratings (
            id              SERIAL PRIMARY KEY,
            employee_id     VARCHAR(20) REFERENCES employees(employee_id),
            year            INT,
            rating          DECIMAL(3,1),
            rating_label    VARCHAR(30),
            reviewer_id     VARCHAR(20),
            review_date     DATE,
            comments        TEXT,
            UNIQUE(employee_id, year)
        );
        """

        engine = self._get_engine()
        with engine.connect() as conn:
            conn.execute(text(schema_sql))
            conn.commit()
        logger.info("Schema created!")

    def load_sample_data(self):
        """Load sample ChandraAILabs employee data."""
        from sqlalchemy import text

        # Sample employees (realistic AI company team)
        employees = [
            ("EMP001", "Chandra Nakkalakunta", "chandra@chandraailabs.com",
             "Engineering", "Principal Architect", None, "2024-01-15", "full-time"),
            ("EMP002", "Priya Sharma", "priya@chandraailabs.com",
             "Engineering", "Senior ML Engineer", "EMP001", "2024-02-01", "full-time"),
            ("EMP003", "Rahul Verma", "rahul@chandraailabs.com",
             "Engineering", "Cloud Engineer", "EMP001", "2024-03-01", "full-time"),
            ("EMP004", "Anjali Singh", "anjali@chandraailabs.com",
             "Product", "Product Manager", "EMP001", "2024-01-20", "full-time"),
            ("EMP005", "Kiran Kumar", "kiran@chandraailabs.com",
             "Engineering", "ML Engineer", "EMP002", "2024-04-01", "full-time"),
            ("EMP006", "Deepa Reddy", "deepa@chandraailabs.com",
             "HR", "HR Manager", "EMP001", "2024-01-15", "full-time"),
            ("EMP007", "Arun Patel", "arun@chandraailabs.com",
             "Engineering", "DevOps Engineer", "EMP003", "2024-05-01", "full-time"),
            ("EMP008", "Sneha Joshi", "sneha@chandraailabs.com",
             "Design", "UI/UX Designer", "EMP004", "2024-03-15", "full-time"),
            ("EMP009", "Vikram Nair", "vikram@chandraailabs.com",
             "Engineering", "Data Engineer", "EMP002", "2024-06-01", "full-time"),
            ("EMP010", "Meera Iyer", "meera@chandraailabs.com",
            "Sales", "Business Development", "EMP001", "2024-02-15", "full-time"),
            ("DEMO01", "Demo User", "demo@chandraailabs.com",
             "Engineering", "Software Engineer", "EMP001", "2024-06-01", "full-time"),
            ("DEMO02", "Guest User", "guest@chandraailabs.com",
             "Product", "Product Analyst", "EMP004", "2024-07-01", "full-time"),
        ]

        # Leave balances (2024)
        leave_balances = []
        for emp in employees:
            emp_id = emp[0]
            leave_balances.extend([
                (emp_id, "annual",   21, 8,  13, 2024),
                (emp_id, "sick",     10, 2,  8,  2024),
                (emp_id, "casual",   7,  1,  6,  2024),
            ])

        # Customize for Chandra
        leave_balances = [
            lb for lb in leave_balances
            if not (lb[0] == "EMP001")
        ]
        leave_balances.extend([
            ("EMP001", "annual",  21, 5,  16, 2024),
            ("EMP001", "sick",    10, 0,  10, 2024),
            ("EMP001", "casual",  7,  2,  5,  2024),
        ])

        # Compensation (monthly in INR)
        compensation = [
            ("EMP001", 150000, 60000, 10000, 80000, 3600000, "2024-01-15"),
            ("EMP002", 100000, 40000, 8000,  52000,  2400000, "2024-02-01"),
            ("EMP003", 90000,  36000, 7000,  47000,  2160000, "2024-03-01"),
            ("EMP004", 95000,  38000, 7500,  49500,  2280000, "2024-01-20"),
            ("EMP005", 80000,  32000, 6000,  42000,  1920000, "2024-04-01"),
            ("EMP006", 75000,  30000, 5000,  40000,  1800000, "2024-01-15"),
            ("EMP007", 85000,  34000, 6500,  44500,  2040000, "2024-05-01"),
            ("EMP008", 70000,  28000, 5000,  37000,  1680000, "2024-03-15"),
            ("EMP009", 82000,  32800, 6200,  43000,  1968000, "2024-06-01"),
            ("EMP010", 78000,  31200, 5800,  41000,  1872000, "2024-02-15"),
        ]

        # Performance ratings (2024)
        performance = [
            ("EMP001", 2024, 4.8, "Exceeds Expectations", None,     "2024-12-01", "Exceptional leadership in AI platform development"),
            ("EMP002", 2024, 4.5, "Exceeds Expectations", "EMP001", "2024-12-01", "Outstanding ML model development"),
            ("EMP003", 2024, 4.2, "Meets Expectations",   "EMP001", "2024-12-01", "Good cloud infrastructure work"),
            ("EMP004", 2024, 4.6, "Exceeds Expectations", "EMP001", "2024-12-01", "Excellent product roadmap delivery"),
            ("EMP005", 2024, 3.8, "Meets Expectations",   "EMP002", "2024-12-01", "Good progress on ML tasks"),
            ("EMP006", 2024, 4.3, "Meets Expectations",   "EMP001", "2024-12-01", "Strong HR operations"),
            ("EMP007", 2024, 4.0, "Meets Expectations",   "EMP003", "2024-12-01", "Reliable DevOps support"),
            ("EMP008", 2024, 4.4, "Meets Expectations",   "EMP004", "2024-12-01", "Creative UI designs"),
            ("EMP009", 2024, 3.9, "Meets Expectations",   "EMP002", "2024-12-01", "Solid data pipeline work"),
            ("EMP010", 2024, 4.1, "Meets Expectations",   "EMP001", "2024-12-01", "Good business development"),
        ]

        engine = self._get_engine()
        with engine.connect() as conn:
            # Insert employees
            for emp in employees:
                conn.execute(text("""
                    INSERT INTO employees
                    (employee_id, name, email, department, designation,
                     manager_id, join_date, employment_type)
                    VALUES (:id, :name, :email, :dept, :desig,
                            :mgr, :join, :type)
                    ON CONFLICT (employee_id) DO NOTHING
                """), {
                    "id": emp[0], "name": emp[1], "email": emp[2],
                    "dept": emp[3], "desig": emp[4], "mgr": emp[5],
                    "join": emp[6], "type": emp[7]
                })

            # Insert leave balances
            for lb in leave_balances:
                conn.execute(text("""
                    INSERT INTO leave_balances
                    (employee_id, leave_type, total_days, used_days,
                     remaining_days, year)
                    VALUES (:emp, :type, :total, :used, :rem, :year)
                    ON CONFLICT (employee_id, leave_type, year) DO NOTHING
                """), {
                    "emp": lb[0], "type": lb[1], "total": lb[2],
                    "used": lb[3], "rem": lb[4], "year": lb[5]
                })

            # Insert compensation
            for comp in compensation:
                conn.execute(text("""
                    INSERT INTO compensation
                    (employee_id, basic_salary, hra, ta,
                     special_allowance, gross_ctc, effective_date)
                    VALUES (:emp, :basic, :hra, :ta, :sa, :ctc, :date)
                    ON CONFLICT (employee_id, effective_date) DO NOTHING
                """), {
                    "emp": comp[0], "basic": comp[1], "hra": comp[2],
                    "ta": comp[3], "sa": comp[4], "ctc": comp[5],
                    "date": comp[6]
                })

            # Insert performance ratings
            for perf in performance:
                conn.execute(text("""
                    INSERT INTO performance_ratings
                    (employee_id, year, rating, rating_label,
                     reviewer_id, review_date, comments)
                    VALUES (:emp, :year, :rating, :label,
                            :reviewer, :date, :comments)
                    ON CONFLICT (employee_id, year) DO NOTHING
                """), {
                    "emp": perf[0], "year": perf[1], "rating": perf[2],
                    "label": perf[3], "reviewer": perf[4],
                    "date": perf[5], "comments": perf[6]
                })

            conn.commit()
        logger.info("Sample data loaded!")

    def get_employee_by_email(self, email: str) -> dict:
        """Get employee record by email."""
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT e.*,
                       m.name as manager_name
                FROM employees e
                LEFT JOIN employees m ON e.manager_id = m.employee_id
                WHERE e.email = :email AND e.status = 'active'
            """), {"email": email})
            row = result.fetchone()
            if row:
                return dict(zip(result.keys(), row))
        return {}

    def get_leave_balance(self, employee_id: str, year: int = None) -> list:
        """Get leave balance for employee."""
        from sqlalchemy import text
        if not year:
            year = datetime.now().year
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT leave_type, total_days, used_days, remaining_days
                FROM leave_balances
                WHERE employee_id = :emp AND year = :year
                ORDER BY leave_type
            """), {"emp": employee_id, "year": year})
            return [dict(zip(result.keys(), row)) for row in result]

    def get_compensation(self, employee_id: str) -> dict:
        """Get latest compensation for employee."""
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT basic_salary, hra, ta,
                       special_allowance, gross_ctc, effective_date
                FROM compensation
                WHERE employee_id = :emp
                ORDER BY effective_date DESC LIMIT 1
            """), {"emp": employee_id})
            row = result.fetchone()
            if row:
                return dict(zip(result.keys(), row))
        return {}

    def get_performance_rating(
        self, employee_id: str, year: int = None
    ) -> dict:
        """Get performance rating for employee."""
        from sqlalchemy import text
        if not year:
            year = datetime.now().year
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT pr.year, pr.rating, pr.rating_label,
                       pr.review_date, pr.comments,
                       m.name as reviewer_name
                FROM performance_ratings pr
                LEFT JOIN employees m ON pr.reviewer_id = m.employee_id
                WHERE pr.employee_id = :emp AND pr.year = :year
            """), {"emp": employee_id, "year": year})
            row = result.fetchone()
            if row:
                return dict(zip(result.keys(), row))
        return {}

    def get_team_members(self, manager_id: str) -> list:
        """Get team members for a manager."""
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("""
                SELECT employee_id, name, email,
                       department, designation
                FROM employees
                WHERE manager_id = :mgr AND status = 'active'
                ORDER BY name
            """), {"mgr": manager_id})
            return [dict(zip(result.keys(), row)) for row in result]

    def get_stats(self) -> dict:
        """Get database statistics."""
        from sqlalchemy import text
        engine = self._get_engine()
        with engine.connect() as conn:
            stats = {}
            for table in ["employees", "leave_balances",
                         "compensation", "performance_ratings"]:
                result = conn.execute(
                    text(f"SELECT COUNT(*) FROM {table}")
                )
                stats[table] = result.fetchone()[0]
        return stats
