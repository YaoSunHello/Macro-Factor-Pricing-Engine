import streamlit as st
import pandas as pd

# Mocking internal imports to ensure compliance with your described codebase
# In production, replace these with your actual imports:
# from macro_factor_pricing_engine import universe, regimes, policy

st.set_page_config(
    page_title="Macro Factor Pricing Engine",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------------------------------------------------------
# SIDEBAR & SYSTEM STATUS
# -----------------------------------------------------------------------------
st.sidebar.title("🛠 Engine Control Panel")

# Mimicking universe.has_tradeable_instruments()
# Replace with: HAS_TRADEABLE = universe.has_tradeable_instruments()
HAS_TRADEABLE = False 

st.sidebar.markdown("### System Status")
if not HAS_TRADEABLE:
    st.sidebar.error("🔴 SYSTEM LOCKED: Non-Tradeable")
    st.sidebar.caption("Reason: Asset-class universe ticker dictionary is empty. No live or paper allocations permitted.")
else:
    st.sidebar.success("🟢 SYSTEM ACTIVE: Tradeable")

st.sidebar.divider()
st.sidebar.markdown("### Strategy Governance")
st.sidebar.info(
    "**Objective:** Maximize risk-adjusted return (Sharpe/Calmar).\n\n"
    "⚠️ **Mandatory Rule:** No-lookahead data handling is strictly enforced."
)

# -----------------------------------------------------------------------------
# MAIN DASHBOARD INTERFACE
# -----------------------------------------------------------------------------
st.title("📈 Macro-Factor Pricing Engine")
st.subheader("Probabilistic Macro Regime & Governance Framework")

tabs = st.tabs(["🌍 Macro Regimes", "🗂 Universe Scaffold", "📜 Policy & Approvals"])

# --- TAB 1: MACRO REGIMES ---
with tabs[0]:
    st.header("Transmission Channels & Regime Layer")
    
    # Visualizing the 4 transmission channels
    st.markdown("### Current Transmission Channel Metrics (Data Scoring Pending)")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Growth Factor", "Pending Data", delta=None)
    col2.metric("Inflation Factor", "Pending Data", delta=None)
    col3.metric("Policy / Liquidity", "Pending Data", delta=None)
    col4.metric("Risk Appetite", "Pending Data", delta=None)
    
    st.divider()
    
    st.markdown("### Observable Regime Definitions")
    regime_choice = st.selectbox(
        "Select an Observable Regime to view Causal Dynamics:",
        ["Goldilocks", "Reflation", "Stagflation", "Disinflationary Slowdown", "Crisis Liquidity Stress", "Policy Tightening Shock"]
    )
    
    # Mock definitions mapping directly to regimes.py descriptions
    regime_data = {
        "Goldilocks": {"story": "High growth, low inflation. Ideal environment for risk assets.", "lead": "US Equities, High Yield Credit", "lag": "Cash, Short Duration Bonds"},
        "Reflation": {"story": "Accelerating growth and rising inflation. Synchronized global expansion.", "lead": "Broad Commodities, EM Equities", "lag": "Long Duration Bonds"},
        "Stagflation": {"story": "Stagnant or declining growth paired with sticky inflation pressures.", "lead": "Gold, Inflation-Linked Bonds", "lag": "US Equities, IG Credit"},
        "Disinflationary Slowdown": {"story": "Growth is slowing down while inflation pressures subside.", "lead": "Long Duration Bonds, Cash", "lag": "Broad Commodities, High Yield"},
        "Crisis Liquidity Stress": {"story": "Systemic shock causing sudden dash for cash and margin liquidations.", "lead": "USD Proxy, Cash", "lag": "All Risk Assets, Emerging Markets"},
        "Policy Tightening Shock": {"story": "Central banks aggressively withdrawing liquidity faster than expected.", "lead": "Short Duration Bonds, Cash", "lag": "Equities, Gold"}
    }
    
    selected_meta = regime_data[regime_choice]
    
    st.info(f"**Causal Story:** {selected_meta['story']}")
    
    c1, c2 = st.columns(2)
    with c1:
        st.success(f"🟢 **Expected Leading Assets:**\n{selected_meta['lead']}")
    with c2:
        st.warning(f"🔴 **Expected Lagging Assets:**\n{selected_meta['lag']}")

# --- TAB 2: UNIVERSE SCAFFOLD ---
with tabs[1]:
    st.header("Asset-Class Universe Setup")
    st.markdown("Every asset category below must be explicitly populated and approved before capital deployment.")
    
    # Asset classes list from universe.py
    asset_classes = [
        "us_equities", "global_developed_equities", "emerging_market_equities",
        "short_duration_government_bonds", "intermediate_duration_government_bonds",
        "long_duration_government_bonds", "inflation_linked_bonds",
        "investment_grade_credit", "high_yield_credit", "gold",
        "broad_commodities", "usd_proxy", "cash"
    ]
    
    # Building a status table
    universe_df = pd.DataFrame({
        "Asset Class Category": asset_classes,
        "Assigned Tickers": ["{} (Empty Scaffold)" for _ in range(len(asset_classes))],
        "Status": ["❌ Unapproved" for _ in range(len(asset_classes))]
    })
    
    st.table(universe_df)
    
    st.divider()
    st.subheader("Populate Ticker Dictionary (Human-Input Workspace)")
    
    with st.form("ticker_form"):
        target_class = st.selectbox("Select Asset Class to Populate", asset_classes)
        ticker_input = st.text_input("Enter Tickers (comma separated, e.g., SPY, IVV)", "")
        submitted = st.form_submit_with_button("Submit Tickers for Verification")
        
        if submitted:
            if ticker_input.strip() == "":
                st.error("Please enter at least one valid ticker symbol.")
            else:
                st.warning(f"Submission Received! Asset class `{target_class}` updated with `{ticker_input}`. This change is currently **PENDING** and requires human confirmation in the Policy Hub.")

# --- TAB 3: POLICY & APPROVALS ---
with tabs[2]:
    st.header("Strategy Governance & Audit Log")
    
    st.markdown("### Operational Confirmation Queue")
    st.write("Human-in-the-loop confirmation is strictly required to move the portfolio from a pending adjustment state.")
    
    # Active system triggers listed in policy.py
    st.markdown("#### System Triggers Monitor")
    col_t1, col_t2, col_t3 = st.columns(3)
    col_t1.button("📅 Scheduled Monthly Review", disabled=True)
    col_t2.button("🔄 Regime Transition Alert", disabled=True)
    col_t3.button("⚡ Policy Shock Event", disabled=True)
    
    st.markdown("#### Triggers Requiring Manual Sign-off")
    
    # Interactive demo of your human_input_pending rule
    with st.expander("⚠️ Trigger: instrument_universe_change / human_input_pending", expanded=True):
        st.write("**Details:** A user has requested a change to the underlying asset universe dictionaries.")
        st.code("Proposed Change: Map 'us_equities' -> ['SPY', 'QQQ']", language="python")
        
        c_btn1, c_btn2, _ = st.columns([1, 1, 4])
        if c_btn1.button("✅ Approve & Initialize Weights", type="primary"):
            st.balloons()
            st.success("Change authorized. System updated.")
        if c_btn2.button("❌ Reject Request"):
            st.error("Change rejected. System reverted to safe state.")
            
    st.divider()
    st.subheader("🔒 Risk Controls Sandbox (Module 4 Placeholder)")
    st.caption("The features below are locked until the risk model configuration and implementation pass are completed.")
    
    disabled_cols = st.columns(4)
    disabled_cols[0].text_input("Vol Target (%)", value="10.0", disabled=True)
    disabled_cols[1].text_input("Concentration Cap (%)", value="25.0", disabled=True)
    disabled_cols[2].text_input("Turnover Budget ($)", value="10,000", disabled=True)
    disabled_cols[3].text_input("Risk Framework", value="Pending Module 4", disabled=True)