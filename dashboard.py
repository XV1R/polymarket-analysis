import streamlit as st
import requests
import os
import pandas as pd
from dotenv import load_dotenv
from typing import Optional

load_dotenv()

# Page configuration (must be first Streamlit command)
st.set_page_config(
    page_title="Polymarket Dashboard",
    page_icon="📊",
    layout="wide"
)

# Initialize session state
if "api_url" not in st.session_state:
    st.session_state.api_url = os.getenv("APP_URL", "http://localhost:8000")
if "condition_id" not in st.session_state:
    st.session_state.condition_id = ""
if "data_cache" not in st.session_state:
    st.session_state.data_cache = {}

# Cached function for API requests
@st.cache_data(ttl=60)  # Cache for 60 seconds
def fetch_endpoint(api_url: str, endpoint: str) -> Optional[dict]:
    """Fetch data from FastAPI endpoint with caching"""
    try:
        url = f"{api_url.rstrip('/')}{endpoint}"
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        return {"error": f"Could not connect to API at {api_url}"}
    except requests.exceptions.Timeout:
        return {"error": "Request timed out. The API may be slow or unresponsive."}
    except requests.exceptions.HTTPError as e:
        error_msg = f"HTTP Error: {e}"
        if hasattr(e.response, 'status_code') and e.response.status_code == 404:
            error_msg += " - The endpoint may not exist or the condition ID might be invalid."
        return {"error": error_msg}
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}

def display_data(data: dict, title: str = "Response Data"):
    """Display data in JSON and table formats"""
    if "error" in data:
        st.error(f"❌ {data['error']}")
        return
    
    st.success("✅ Data fetched successfully!")
    st.subheader(title)
    st.json(data)
    
    # Try to display as table if it's a list
    if isinstance(data, list) and len(data) > 0:
        try:
            df = pd.json_normalize(data)
            st.subheader("Data Table")
            st.dataframe(df, use_container_width=True)
            
            # Show summary if applicable
            if len(df) > 0:
                st.caption(f"Total records: {len(df)}")
        except Exception:
            st.info("Could not convert to table format")
    
    # Display metrics if it's a dict with simple values
    elif isinstance(data, dict):
        metrics = {k: v for k, v in data.items() 
                   if not isinstance(v, (dict, list))}
        if metrics:
            st.subheader("Key Metrics")
            cols = st.columns(min(len(metrics), 3))
            for idx, (key, value) in enumerate(metrics.items()):
                with cols[idx % len(cols)]:
                    st.metric(key.replace("_", " ").title(), value)

# Main UI
st.title("📊 Polymarket Dashboard")
st.markdown("Explore Polymarket data using the FastAPI backend")

# Sidebar configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    api_url = st.text_input(
        "API URL",
        value=st.session_state.api_url,
        help="FastAPI server URL",
        key="api_url_input"
    )
    if api_url != st.session_state.api_url:
        st.session_state.api_url = api_url
        st.cache_data.clear()  # Clear cache when API URL changes
    
    st.markdown("---")
    st.markdown("### Available Endpoints")
    st.markdown("""
    - `/markets/{condition_id}` - Get market trades
    - `/markets/{condition_id}/user-distribution` - Get user distribution
    - `/markets/{condition_id}/stats` - Get market stats
    """)

st.markdown("---")

# Input section
col1, col2 = st.columns([3, 1])

with col1:
    condition_id = st.text_input(
        "Market Condition ID",
        value=st.session_state.condition_id,
        placeholder="e.g., 0x6674545cedce09e0b416c81e2d6372398213bdb75e68a2a77882863dbd5397dc",
        help="Enter a valid Polymarket condition ID",
        key="condition_id_input"
    )
    if condition_id != st.session_state.condition_id:
        st.session_state.condition_id = condition_id

with col2:
    st.write("")  # Spacing
    st.write("")  # More spacing
    fetch_all = st.button("🔍 Fetch All", type="primary", use_container_width=True)

# Main content
if not condition_id:
    st.info("👆 Enter a condition ID above to start exploring market data")
    
    with st.expander("📝 Example Usage"):
        st.code(
            "0x6674545cedce09e0b416c81e2d6372398213bdb75e68a2a77882863dbd5397dc",
            language="text"
        )
    
    with st.expander("🚀 Getting Started"):
        st.markdown("""
        1. Make sure your FastAPI server is running:
           ```bash
           fastapi dev app.py
           # or
           uvicorn app:app --reload
           ```
        
        2. Enter a valid condition ID in the input field above
        
        3. Use the tabs below to explore different endpoints
        """)
else:
    # Tabs for different endpoints
    tab1, tab2, tab3 = st.tabs([
        "📈 Market Trades",
        "👥 User Distribution",
        "📊 Market Stats"
    ])
    
    # Tab 1: Market Trades
    with tab1:
        st.subheader("Market Trades")
        st.markdown(f"**Endpoint:** `GET /markets/{condition_id}`")
        
        fetch_trades = st.button("Fetch Market Trades", key="fetch_trades", type="primary")
        
        if fetch_trades or fetch_all:
            with st.spinner("Fetching market trades..."):
                data = fetch_endpoint(
                    st.session_state.api_url,
                    f"/markets/{condition_id}"
                )
                display_data(data, "Market Trades Data")
        elif condition_id in st.session_state.data_cache.get("trades", {}):
            st.info("💡 Click 'Fetch Market Trades' to load data")
    
    # Tab 2: User Distribution
    with tab2:
        st.subheader("User Distribution")
        st.markdown(f"**Endpoint:** `GET /markets/{condition_id}/user-distribution`")
        
        fetch_dist = st.button("Fetch User Distribution", key="fetch_distribution", type="primary")
        
        if fetch_dist or fetch_all:
            with st.spinner("Fetching user distribution..."):
                data = fetch_endpoint(
                    st.session_state.api_url,
                    f"/markets/{condition_id}/user-distribution"
                )
                display_data(data, "User Distribution Data")
        else:
            st.info("💡 Click 'Fetch User Distribution' to load data")
    
    # Tab 3: Market Stats
    with tab3:
        st.subheader("Market Statistics")
        st.markdown(f"**Endpoint:** `GET /markets/{condition_id}/stats`")
        
        fetch_stats = st.button("Fetch Market Stats", key="fetch_stats", type="primary")
        
        if fetch_stats or fetch_all:
            with st.spinner("Fetching market statistics..."):
                data = fetch_endpoint(
                    st.session_state.api_url,
                    f"/markets/{condition_id}/stats"
                )
                display_data(data, "Market Statistics Data")
        else:
            st.info("💡 Click 'Fetch Market Stats' to load data")

# Footer
st.markdown("---")
with st.spinner("Fetching all market data..."):
    data = fetch_endpoint(st.session_state.api_url, "/")
    if "error" in data:
        st.error(f"❌ {data['error']}")
    else:
        try:
            df = pd.DataFrame(data)
            st.subheader("All Markets Data")
            st.dataframe(df, use_container_width=True)
            st.caption(f"Total records: {len(df)}")
        except Exception:
            st.info("Could not render market data as a table.")


st.caption("Polymarket Dashboard | FastAPI Backend")
