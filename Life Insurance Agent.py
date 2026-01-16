import os
import json
from datetime import datetime
from typing import Dict, Any, Optional

import streamlit as st
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.tools.e2b import E2BTools
from agno.tools.firecrawl import FirecrawlTools

st.set_page_config(
    page_title="Life Insurance Agent",
    page_icon="🧠🛡️",
    layout="centered"
)

st.title("🧠🛡️ Life Insurance Agent")
st.caption(
    "AI-driven life insurance coverage calculation with explainable math and real-time product discovery."
)

with st.sidebar:
    st.header("🔐 API Configuration")

    openai_key = st.text_input("OpenAI API Key", type="password")
    firecrawl_key = st.text_input("Firecrawl API Key", type="password")
    e2b_key = st.text_input("E2B API Key", type="password")

    st.caption("Keys remain local and are never stored.")

def to_float(value: Any) -> float:
    try:
        return float(str(value).replace(",", "").replace("$", "").strip())
    except:
        return 0.0

def calculate_coverage(profile: Dict[str, Any], rate: float = 0.02) -> Dict[str, float]:
    income = to_float(profile["annual_income"])
    years = int(profile["income_years"])
    debt = to_float(profile["debt"])
    savings = to_float(profile["savings"])
    existing = to_float(profile["existing_cover"])

    annuity = (1 - (1 + rate) ** -years) / rate if years else 0
    income_value = income * annuity

    recommended = max(0, income_value + debt - savings - existing)

    return {
        "income_value": income_value,
        "annuity_factor": annuity,
        "recommended": recommended
    }
def load_agent(openai_key, firecrawl_key, e2b_key) -> Agent:
    os.environ["OPENAI_API_KEY"] = openai_key
    os.environ["FIRECRAWL_API_KEY"] = firecrawl_key
    os.environ["E2B_API_KEY"] = e2b_key

    return Agent(
        name="Life Insurance Agent",
        model=OpenAIChat(id="gpt-5-mini-2025-08-07"),
        tools=[
            E2BTools(timeout=120),
            FirecrawlTools(enable_search=True)
        ],
        instructions=[
            "Calculate life insurance coverage using income replacement logic.",
            "Explain assumptions clearly.",
            "Recommend up to 3 term-life products relevant to the user location.",
            "Return ONLY valid JSON."
        ],
        markdown=False
    )
st.subheader("📋 Personal & Financial Details")

with st.form("insurance_form"):
    age = st.number_input("Age", 18, 80, 30)
    income = st.number_input("Annual Income", 0.0, step=1000.0)
    debt = st.number_input("Total Debt", 0.0)
    savings = st.number_input("Savings", 0.0)
    existing = st.number_input("Existing Insurance", 0.0)
    years = st.selectbox("Income Replacement Years", [5, 10, 15])
    country = st.text_input("Country", "United States")

    submit = st.form_submit_button("Generate Recommendation")
if submit:
    profile = {
        "annual_income": income,
        "income_years": years,
        "debt": debt,
        "savings": savings,
        "existing_cover": existing,
        "location": country,
        "timestamp": datetime.utcnow().isoformat()
    }

    agent = load_agent(openai_key, firecrawl_key, e2b_key)
    response = agent.run(json.dumps(profile))

    result = json.loads(response.content)

    st.metric(
        "Recommended Coverage",
        f"${int(result['coverage_amount']):,}"
    )

    with st.expander("📐 How this was calculated"):
        st.json(result["breakdown"])

