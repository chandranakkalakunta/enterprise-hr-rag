"""
Query Router - ChandraAILabs HR RAG Platform
Detects query intent and routes to correct handler
"""
import logging
import re

logger = logging.getLogger(__name__)


class QueryRouter:
    """
    Routes queries to:
    1. Personal HR DB (leave balance, CTC, rating)
    2. Policy RAG (general HR policies)
    3. Hybrid (personal + policy context)
    """

    PERSONAL_PATTERNS = [
        r"\bmy\b.*(leave|leaves|balance|remaining|available)",
        r"\bmy\b.*(ctc|salary|compensation|pay|package|income)",
        r"\bmy\b.*(rating|performance|review|score|appraisal)",
        r"\bmy\b.*(manager|reporting|boss|lead)",
        r"\bmy\b.*(team|reportees|subordinates)",
        r"\bmy\b.*(notice period|joining date|anniversary)",
        r"how many.*(leave|leaves|days).*\b(i|me|my)\b",
        r"\b(i|me|my)\b.*(have|got|get).*(leave|leaves|days)",
        r"when.*my.*(review|appraisal|increment)",
        r"what.*my.*(designation|role|title|department)",
        r"(do i|am i).*(eligible|entitled|qualified)",
        r"how much.*(i|me|my).*(earn|get|receive|paid)",
    ]

    HYBRID_PATTERNS = [
        r"(am i|am i eligible).*(wfh|work from home|remote)",
        r"(can i|can i take).*(leave|wfh|work from home|remote)",
        r"(when|how).*(get promoted|promotion|next level)",
        r"\b(my|i)\b.*(pip|performance improvement)",
        r"(am i|will i).*(bonus|increment|hike)",
    ]

    def __init__(self):
        self.personal_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.PERSONAL_PATTERNS
        ]
        self.hybrid_patterns = [
            re.compile(p, re.IGNORECASE)
            for p in self.HYBRID_PATTERNS
        ]

    def detect_intent(self, query: str) -> str:
        """
        Detect query intent.
        Returns: 'personal', 'hybrid', or 'policy'
        """
        query_lower = query.lower()

        # Check hybrid first (more specific)
        for pattern in self.hybrid_patterns:
            if pattern.search(query_lower):
                logger.info(f"Hybrid query detected: {query[:50]}")
                return "hybrid"

        # Check personal
        for pattern in self.personal_patterns:
            if pattern.search(query_lower):
                logger.info(f"Personal query detected: {query[:50]}")
                return "personal"

        # Default to policy
        logger.info(f"Policy query detected: {query[:50]}")
        return "policy"

    def get_personal_context(
        self,
        query: str,
        employee: dict,
        db_client
    ) -> str:
        """
        Fetch relevant personal data based on query.
        Returns formatted context string.
        """
        emp_id = employee.get("employee_id", "")
        name = employee.get("name", "")
        context_parts = []

        query_lower = query.lower()

        # Leave balance
        if any(w in query_lower for w in
               ["leave", "leaves", "days", "casual", "sick", "annual"]):
            leaves = db_client.get_leave_balance(emp_id)
            if leaves:
                leave_text = f"Leave Balance for {name} (2024):\n"
                for l in leaves:
                    leave_text += (
                        f"  {l['leave_type'].title()} Leave: "
                        f"{l['remaining_days']} days remaining "
                        f"(used {l['used_days']} of {l['total_days']})\n"
                    )
                context_parts.append(leave_text)

        # Performance rating
        if any(w in query_lower for w in
               ["rating", "performance", "review", "appraisal", "score"]):
            perf = db_client.get_performance_rating(emp_id)
            if perf:
                perf_text = (
                    f"Performance Rating for {name} (2024):\n"
                    f"  Rating: {perf['rating']}/5.0 "
                    f"({perf['rating_label']})\n"
                    f"  Review Date: {perf['review_date']}\n"
                    f"  Comments: {perf.get('comments', 'N/A')}\n"
                )
                context_parts.append(perf_text)

        # Compensation
        if any(w in query_lower for w in
               ["ctc", "salary", "compensation", "pay",
                "package", "earn", "income", "hike", "increment"]):
            comp = db_client.get_compensation(emp_id)
            if comp:
                comp_text = (
                    f"Compensation for {name}:\n"
                    f"  Gross CTC: INR {comp['gross_ctc']:,.0f}/year\n"
                    f"  Basic: INR {comp['basic_salary']:,.0f}/month\n"
                    f"  HRA: INR {comp['hra']:,.0f}/month\n"
                )
                context_parts.append(comp_text)

        # Manager/Team
        if any(w in query_lower for w in
               ["manager", "reporting", "boss", "team", "reportees"]):
            manager_name = employee.get("manager_name", "")
            if manager_name:
                context_parts.append(
                    f"Manager of {name}: {manager_name}\n"
                )
            team = db_client.get_team_members(emp_id)
            if team:
                team_text = f"Team Members reporting to {name}:\n"
                for member in team:
                    team_text += f"  - {member['name']} ({member['designation']})\n"
                context_parts.append(team_text)

        # Employee profile
        context_parts.insert(0,
            f"Employee Profile:\n"
            f"  Name: {name}\n"
            f"  Employee ID: {emp_id}\n"
            f"  Role: {employee.get('designation', '')}\n"
            f"  Department: {employee.get('department', '')}\n"
            f"  Join Date: {employee.get('join_date', '')}\n"
        )

        return "\n".join(context_parts)


if __name__ == "__main__":
    router = QueryRouter()

    test_queries = [
        "How many annual leave days do I have?",
        "What is my performance rating?",
        "What is the WFH policy?",
        "Am I eligible for WFH?",
        "What is my CTC?",
        "Who is my manager?",
        "How do I apply for leave?",
    ]

    print("Query Router Test")
    print("=" * 40)
    for q in test_queries:
        intent = router.detect_intent(q)
        print(f"{intent.upper():10} | {q}")
