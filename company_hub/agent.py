"""
Level 6: Multi-Agent Transfer — Company Hub

This agent demonstrates MULTI-AGENT SYSTEMS in Google ADK.

KEY CONCEPT: AGENT DELEGATION (Transfer)
  Instead of one agent doing everything, you create SPECIALIST agents
  and a ROOT AGENT that routes questions to the right specialist.

  Think of it like a company reception desk:
  ┌─────────────────────────────────────────────────────────┐
  │                    RECEPTION (Root Agent)                │
  │   "How can I help you today?"                           │
  │                                                         │
  │   Routes you to the right department:                   │
  │                                                         │
  │   ┌──────────┐  ┌──────────┐  ┌──────────────┐         │
  │   │    HR    │  │  TECH    │  │   SALES      │         │
  │   │ Specialist│  │ Specialist│  │  Specialist  │         │
  │   │          │  │          │  │              │         │
  │   │ Leave,   │  │ IT help, │  │ Products,    │         │
  │   │ Benefits,│  │ Passwords│  │ Pricing,     │         │
  │   │ Policies │  │ Software │  │ Demos        │         │
  │   └──────────┘  └──────────┘  └──────────────┘         │
  └─────────────────────────────────────────────────────────┘

HOW IT WORKS:
  1. User asks a question to the root agent
  2. Root agent reads sub-agent descriptions and picks the best match
  3. ADK TRANSFERS the conversation to that sub-agent
  4. Sub-agent answers with its own instruction, tools, and knowledge
  5. Control returns to root agent for the next question

Try these in the ADK Web UI:
  ✅ "How many sick days do I get?"          → Routes to HR Specialist
  ✅ "My laptop is running slow"             → Routes to Tech Specialist
  ✅ "What products do you sell?"             → Routes to Sales Specialist
  ✅ "Hello, who are you?"                   → Root agent answers directly
"""

import os
import random
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from google.adk.agents import Agent

MODEL = os.getenv("MODEL", "gemini-2.5-flash")


# ══════════════════════════════════════════════════════════════
# SPECIALIST 1: HR Agent (with tools + knowledge)
# ══════════════════════════════════════════════════════════════
def check_leave_balance(employee_name: str) -> dict:
    """Check the remaining leave balance for an employee.

    Args:
        employee_name: The name of the employee.

    Returns:
        A dictionary with leave balance details.
    """
    return {
        "employee": employee_name,
        "annual_leave_remaining": random.randint(5, 18),
        "sick_leave_remaining": random.randint(3, 10),
        "total_used_this_year": random.randint(2, 12),
    }


hr_agent = Agent(
    name="hr_specialist",
    model=MODEL,
    description=(
        "Handles all HR-related questions: leave policies, benefits, "
        "payroll, holidays, employee handbook, work-from-home policy, "
        "and leave balance inquiries."
    ),
    instruction=(
        "You are the HR Specialist for Acme Corp.\n\n"
        "COMPANY POLICIES:\n"
        "• Annual Leave: 20 days/year\n"
        "• Sick Leave: 10 days/year (doctor's note after 3 days)\n"
        "• Work From Home: Up to 3 days/week with manager approval\n"
        "• Health Insurance: Employee + spouse + 2 children covered\n"
        "• Maternity: 26 weeks paid | Paternity: 2 weeks paid\n"
        "• Notice Period: 30 days (regular), 90 days (managers)\n\n"
        "RULES:\n"
        "- Use the check_leave_balance tool when asked about specific leave balance.\n"
        "- Answer policy questions from the knowledge above.\n"
        "- End each response with: 'For more details, contact hr@acmecorp.com'\n"
    ),
    tools=[check_leave_balance],
)


# ══════════════════════════════════════════════════════════════
# SPECIALIST 2: Tech Support Agent (with tools)
# ══════════════════════════════════════════════════════════════
def reset_password(username: str) -> dict:
    """Reset the password for a user account.

    Args:
        username: The username to reset password for.

    Returns:
        A dictionary with the reset status and temporary password.
    """
    import string
    temp_pwd = ''.join(random.choices(string.ascii_letters + string.digits, k=10))
    return {
        "username": username,
        "status": "Password reset successful",
        "temporary_password": temp_pwd,
        "note": "Please change this password on first login.",
    }


def check_system_status(service_name: str) -> dict:
    """Check the status of a company IT service.

    Args:
        service_name: Name of the service (e.g. "email", "vpn", "erp").

    Returns:
        A dictionary with the service status.
    """
    services = {
        "email": {"status": "operational", "uptime": "99.9%"},
        "vpn": {"status": "operational", "uptime": "99.5%"},
        "erp": {"status": "maintenance", "note": "Scheduled maintenance until 6 PM"},
        "slack": {"status": "operational", "uptime": "99.8%"},
    }
    svc = services.get(service_name.lower())
    if svc:
        return {"service": service_name, **svc}
    return {"service": service_name, "status": "unknown", "note": "Service not found in monitoring"}


tech_agent = Agent(
    name="tech_specialist",
    model=MODEL,
    description=(
        "Handles IT and technical support: password resets, software issues, "
        "VPN setup, laptop problems, system status checks, and general "
        "tech troubleshooting."
    ),
    instruction=(
        "You are the Tech Support Specialist for Acme Corp.\n\n"
        "COMMON SOLUTIONS:\n"
        "• Slow laptop: Restart, clear cache, check RAM usage\n"
        "• VPN issue: Use AnyConnect, server: vpn.acmecorp.com\n"
        "• Email not working: Check Outlook settings, server: mail.acmecorp.com\n"
        "• Software install: Submit request on IT portal at it.acmecorp.com\n\n"
        "TOOLS:\n"
        "- Use reset_password when someone needs a password reset.\n"
        "- Use check_system_status to check if a service is running.\n\n"
        "RULES:\n"
        "- Be friendly and step-by-step in troubleshooting.\n"
        "- End each response with: 'Need more help? Call IT helpdesk: ext 5555'\n"
    ),
    tools=[reset_password, check_system_status],
)


# ══════════════════════════════════════════════════════════════
# SPECIALIST 3: Sales Agent (with tools)
# ══════════════════════════════════════════════════════════════
def get_product_info(product_name: str) -> dict:
    """Get details about a company product.

    Args:
        product_name: Name of the product (e.g. "CloudSuite", "DataPro", "SecureShield").

    Returns:
        A dictionary with product details and pricing.
    """
    products = {
        "cloudsuite": {
            "name": "CloudSuite",
            "description": "All-in-one cloud collaboration platform",
            "pricing": "₹999/user/month (Basic), ₹1999/user/month (Pro)",
            "features": ["File sharing", "Video calls", "Project management", "AI assistant"],
        },
        "datapro": {
            "name": "DataPro",
            "description": "Enterprise data analytics platform",
            "pricing": "₹2499/user/month",
            "features": ["Real-time dashboards", "SQL workspace", "ML models", "Data catalog"],
        },
        "secureshield": {
            "name": "SecureShield",
            "description": "Cybersecurity protection suite",
            "pricing": "₹1499/endpoint/month",
            "features": ["Firewall", "Threat detection", "DLP", "Zero trust"],
        },
    }
    product = products.get(product_name.lower())
    if product:
        return product
    return {
        "error": f"Product '{product_name}' not found.",
        "available_products": ["CloudSuite", "DataPro", "SecureShield"],
    }


sales_agent = Agent(
    name="sales_specialist",
    model=MODEL,
    description=(
        "Handles sales inquiries: product information, pricing, demos, "
        "feature comparisons, and purchase requests for CloudSuite, "
        "DataPro, and SecureShield products."
    ),
    instruction=(
        "You are the Sales Specialist for Acme Corp.\n\n"
        "PRODUCTS: CloudSuite, DataPro, SecureShield\n"
        "Use the get_product_info tool for product details.\n\n"
        "RULES:\n"
        "- Be enthusiastic but honest about products.\n"
        "- Always offer to schedule a demo.\n"
        "- End each response with: 'Schedule a demo at sales@acmecorp.com'\n"
    ),
    tools=[get_product_info],
)


# ══════════════════════════════════════════════════════════════
# ROOT AGENT — The Reception Desk
# ══════════════════════════════════════════════════════════════
# The root agent's job is to understand the user's intent and
# delegate to the right specialist. It uses the sub_agents field.
root_agent = Agent(
    name="company_hub",
    model=MODEL,
    description="Acme Corp's central assistant that routes questions to the right specialist.",
    instruction=(
        "You are the main reception assistant for Acme Corp.\n\n"
        "YOUR JOB:\n"
        "- Greet users warmly.\n"
        "- Figure out what they need help with.\n"
        "- Route them to the right specialist:\n"
        "  • HR questions (leave, benefits, policies) → hr_specialist\n"
        "  • Tech issues (passwords, software, VPN) → tech_specialist\n"
        "  • Sales inquiries (products, pricing, demos) → sales_specialist\n\n"
        "- If the question is general (hello, who are you, etc.), answer directly.\n"
        "- NEVER try to answer specialist questions yourself — always transfer.\n"
    ),

    # ← THIS is the multi-agent magic: just list sub-agents!
    # ADK reads each sub-agent's `description` to decide routing.
    sub_agents=[hr_agent, tech_agent, sales_agent],
)
