import streamlit as st
import pandas as pd
import requests
import altair as alt

st.set_page_config(page_title="Personal Net Worth Dashboard", layout="wide")

st.title("🏛️ Personal Net Worth Dashboard")

# -----------------------
# FX FUNCTION (USD/THB)
# -----------------------
def get_fx_rate():
    try:
        url = "https://api.exchangerate-api.com/v4/latest/USD"
        data = requests.get(url, timeout=5).json()
        return data["rates"]["THB"], "live"
    except:
        return 35.0, "fallback"

# -----------------------
# GOLD FUNCTION (MULTI-SOURCE)
# -----------------------
def get_gold_price_per_gram():

    try:
        url = "https://query1.finance.yahoo.com/v7/finance/quote?symbols=XAUUSD=X"
        data = requests.get(url, timeout=5).json()
        result = data["quoteResponse"]["result"]

        if result and result[0]["regularMarketPrice"]:
            return result[0]["regularMarketPrice"] / 31.1035, "Yahoo"
    except:
        pass

    try:
        url = "https://api.metals.live/v1/spot/gold"
        data = requests.get(url, timeout=5).json()
        if data and "price" in data[0]:
            return data[0]["price"] / 31.1035, "Metals API"
    except:
        pass

    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=tether-gold&vs_currencies=usd"
        data = requests.get(url, timeout=5).json()
        if "tether-gold" in data:
            return data["tether-gold"]["usd"] / 31.1035, "CoinGecko"
    except:
        pass

    return None, "error"

# -----------------------
# SESSION STATE
# -----------------------
if "run_calc" not in st.session_state:
    st.session_state.run_calc = False

# -----------------------
# INPUTS
# -----------------------
st.sidebar.header("📥 Assets Input")

cash_usd = st.sidebar.number_input("USD Cash", value=0.0)
cash_thb = st.sidebar.number_input("THB Cash", value=0.0)

gold_grams = st.sidebar.number_input("Gold (grams)", value=0.0)

real_estate = st.sidebar.number_input("Real Estate Value (USD)", value=0.0)

st.sidebar.subheader("Private Investments")

company_names = st.sidebar.text_input("Company Names", "Rangoon Tech, Mekongverse")
invested_amounts = st.sidebar.text_input("Invested Amounts (USD)", "150000,150000")
ownership_percents = st.sidebar.text_input("Ownership % (e.g. 12 for 12%)", "33,33")
company_valuations = st.sidebar.text_input("Company Valuations (USD)", "1000000,1200000")

# -----------------------
# BUTTON
# -----------------------
if st.button("🔄 Recalculate"):
    st.session_state.run_calc = True

# -----------------------
# MAIN
# -----------------------
if st.session_state.run_calc:

    # FX
    usd_thb, _ = get_fx_rate()
    st.write(f"USD/THB: {usd_thb:,.2f}")

    thb_to_usd = 1 / usd_thb
    cash_total = cash_usd + (cash_thb * thb_to_usd)

    # GOLD
    gold_price, source = get_gold_price_per_gram()

    if gold_price is None:
        st.error("❌ Unable to fetch gold price")
        st.stop()

    st.write(f"Gold Spot: {gold_price:,.2f} USD/gram")

    gold_value = gold_grams * gold_price

    # PRIVATE
    private_total = 0
    private_data = []

    names = company_names.split(",")
    invests = invested_amounts.split(",")
    ownerships = ownership_percents.split(",")
    valuations = company_valuations.split(",")

    for n, i, o, v in zip(names, invests, ownerships, valuations):
        n = n.strip()
        i = float(i.strip())
        o_pct = float(o.strip())
        o = o_pct / 100
        v = float(v.strip())

        current_value = o * v
        gain = current_value - i
        moic = round(current_value / i, 1)

        private_total += current_value

        private_data.append([
            n,
            f"{i:,.0f}",
            f"{o_pct:.0f}%",
            f"{v:,.0f}",
            f"{current_value:,.0f}",
            f"{gain:,.0f}",
            f"{moic:.1f}x"
        ])

    net_worth = cash_total + gold_value + real_estate + private_total

    # -----------------------
    # METRICS
    # -----------------------
    col1, col2, col3 = st.columns(3)
    col1.metric("💰 Net Worth (USD)", f"{net_worth:,.0f}")
    col2.metric("💧 Liquid Assets (USD)", f"{cash_total:,.0f}")
    col3.metric("🏠 Illiquid Assets (USD)", f"{real_estate + private_total:,.0f}")

    # -----------------------
    # ASSET TABLE (FIXED ALIGNMENT)
    # -----------------------
    st.subheader("📊 Asset Allocation")

    df = pd.DataFrame({
        "Asset": ["Cash", "Gold", "Real Estate", "Private Investments"],
        "Value (USD)": [cash_total, gold_value, real_estate, private_total]
    })

    df.index = df.index + 1

    styled_df = df.style.format({"Value (USD)": "{:,.0f}"}) \
        .set_properties(subset=["Value (USD)"], **{"text-align": "right"}) \
        .set_table_styles([
            {"selector": "th.col_heading.level0.col1", "props": [("text-align", "right")]}
        ])

    st.dataframe(styled_df)

    # -----------------------
    # BAR CHART
    # -----------------------
    color_map = {
        "Cash": "green",
        "Gold": "gold",
        "Real Estate": "purple",
        "Private Investments": "red"
    }

    chart = alt.Chart(df.reset_index()).mark_bar().encode(
        x="Asset",
        y=alt.Y("Value (USD):Q", axis=alt.Axis(title="USD")),
        color=alt.Color("Asset", scale=alt.Scale(
            domain=list(color_map.keys()),
            range=list(color_map.values())
        ), legend=None)
    )

    st.altair_chart(chart, use_container_width=True)

    # -----------------------
    # PRIVATE TABLE
    # -----------------------
    st.subheader("🏢 Private Portfolio")

    pe_df = pd.DataFrame(private_data, columns=[
        "Company",
        "Invested (USD)",
        "Ownership %",
        "Valuation (USD)",
        "Current Value (USD)",
        "Gain/Loss (USD)",
        "MOIC"
    ])

    pe_df.index = pe_df.index + 1

    st.dataframe(pe_df)

else:
    st.info("👉 Enter data and click Recalculate")