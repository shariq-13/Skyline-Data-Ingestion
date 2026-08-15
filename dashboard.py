"""
Streamlit Dashboard — OpenSky Radar Pipeline (Medallion Architecture)
Run with: streamlit run dashboard.py

pip install streamlit pandas plotly snowflake-connector-python python-dotenv matplotlib seaborn
"""

import os
import pandas as pd
import streamlit as st
import plotly.express as px
import snowflake.connector
from dotenv import load_dotenv

import matplotlib.pyplot as plt
import seaborn as sns
from mpl_toolkits.mplot3d import Axes3D

# --- Page Configurations ---
st.set_page_config(
    page_title="OpenSky Radar Air Traffic Control", 
    page_icon="✈️", 
    layout="wide"
)

# Load environment configurations
load_dotenv()

# --- CUSTOM PITCH BLACK & RED NEON GLOW CSS ---
st.markdown("""
    <style>
        .main, .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] { 
            background-color: #000000 !important; 
            color: #ffffff !important; 
        }
        
        div[data-testid="stVegaLiteChart"], 
        div[data-testid="stVegaLiteChart"] > div,
        canvas.marks,
        div[data-testid="stPlotlyChart"],
        div[data-testid="stDataFrame"],
        .stTable {
            background-color: #000000 !important;
            background: #000000 !important;
            border: none !important;
            box-shadow: none !important;
        }

        h1 { color: #ff3333 !important; font-weight: 800; text-shadow: 0 0 10px rgba(255, 51, 51, 0.3); }
        h2, h3, h4, p, span, label { color: #ffffff !important; }
        small, .stCaption { color: #94a3b8 !important; }
        
        div[data-testid="stMetricValue"] { font-size: 2.2rem; font-weight: 800; color: #ff3333 !important; }
        div[data-testid="stMetricLabel"] { font-size: 0.95rem; color: #94a3b8 !important; text-transform: uppercase; letter-spacing: 0.5px; }
        
        .stAlert { border-radius: 8px; background-color: #111111 !important; border-left: 5px solid #ff3333; color: #ffffff; }
        hr { border-top: 1px solid #1e293b !important; }
    </style>
""", unsafe_allow_html=True)

# Set global Matplotlib dark mode
plt.style.use('dark_background')
sns.set_theme(style="dark")

# Flight Status Badges
STATUS_BADGE = {
    "IN_FLIGHT": "🟢 IN AIR",
    "ON_GROUND": "🟡 GROUNDED",
    "HIGH_SPEED": "🔴 SUPERSONIC/FAST",
}


@st.cache_resource
def init_snowflake_connection():
    """Establishes session handle with Snowflake warehouse using env credentials."""
    user = os.getenv("SF_USER")
    password = os.getenv("SF_PASSWORD")
    account = os.getenv("SF_ACCOUNT")
    warehouse = os.getenv("SF_WAREHOUSE")
    database = os.getenv("SF_DATABASE", "OPENSKY_ETL")

    credentials = {
        "SF_USER": user,
        "SF_PASSWORD": password,
        "SF_ACCOUNT": account,
        "SF_WAREHOUSE": warehouse,
        "SF_DATABASE": database,
    }

    missing_keys = [key for key, val in credentials.items() if not val]
    if missing_keys:
        raise ValueError(
            f"Missing configuration parameters in .env file: {', '.join(missing_keys)}."
        )

    return snowflake.connector.connect(
        user=user,
        password=password,
        account=account,
        warehouse=warehouse,
        database=database,
    )


@st.cache_data(ttl=30)
def pull_dashboard_data():
    """Queries Silver and Gold views with 30-second cache TTL."""
    conn = init_snowflake_connection()
    
    with conn.cursor() as cursor:
        # Gold Layer: Business Ready Flight Analytics
        gold_analytics_query = """
            SELECT * 
            FROM OPENSKY_ETL.FINAL.BUSINESS_READY_FLIGHT_ANALYTICS 
            ORDER BY SNAPSHOT_HOUR DESC, HOURLY_SECTOR_DENSITY_RANK ASC 
            LIMIT 5000
        """
        cursor.execute(gold_analytics_query)
        df_gold = cursor.fetch_pandas_all()

        # Silver Layer: Live Telemetry Data
        silver_query = """
            SELECT 
                ICAO24, CALLSIGN, ORIGIN_COUNTRY, TIME_POSITION, 
                LONGITUDE, LATITUDE, BARO_ALTITUDE, VELOCITY, ON_GROUND, INGESTED_AT
            FROM OPENSKY_ETL.STAGED.STAGED_DATA
            ORDER BY TIME_POSITION DESC
            LIMIT 5000
        """
        cursor.execute(silver_query)
        df_silver = cursor.fetch_pandas_all()

    if not df_gold.empty:
        df_gold["SNAPSHOT_HOUR"] = pd.to_datetime(df_gold["SNAPSHOT_HOUR"])

    if not df_silver.empty:
        df_silver["TIME_POSITION"] = pd.to_datetime(df_silver["TIME_POSITION"])

    return df_gold, df_silver


# --- Main Dashboard Execution ---
st.title("OpenSky Flight Data Pipeline (Medallion Architecture) Dashboard")
st.subheader("Real-time Global Flight Radar Stream (Medallion Architecture: Silver & Gold Layers)")
st.markdown("---")

try:
    df_gold, df_silver = pull_dashboard_data()

    if df_gold.empty and df_silver.empty:
        st.warning("⚠️ Connection active, but no records found in Snowflake. Check your ingestion tasks.")
    else:
        # ==========================================
        # 1. METRIC CARDS LAYER (Gold Aggregates)
        # ==========================================
        st.markdown("### 📊 Key Performance Indicators (Gold Analytics)")
        col1, col2, col3, col4 = st.columns(4)

        total_aircraft = df_gold["UNIQUE_AIRCRAFT_COUNT"].sum() if not df_gold.empty else 0
        total_airborne = df_gold["AIRBORNE_AIRCRAFT_COUNT"].sum() if not df_gold.empty else 0
        avg_speed = df_gold["AVG_GROUND_SPEED_KNOTS"].mean() if not df_gold.empty else 0
        top_country = df_gold["ORIGIN_COUNTRY"].mode()[0] if not df_gold.empty else "N/A"

        col1.metric("Total Tracked Aircraft", f"{int(total_aircraft):,}")
        col2.metric("Airborne Aircraft Volume", f"{int(total_airborne):,}")
        col3.metric("Busiest Country Domain", f"{top_country}")
        col4.metric("Avg Ground Speed", f"{avg_speed:.1f} knots" if pd.notnull(avg_speed) else "N/A")

        st.markdown("---")

        # Visual Split
        chart_col1, chart_col2 = st.columns(2)

        # ==========================================
        # 2. BAR CHART LAYER (Busiest Origin Countries)
        # ==========================================
        with chart_col1:
            st.markdown("### ✈️ Aircraft Volume by Origin Country")
            if not df_gold.empty:
                country_counts = (
                    df_gold.groupby("ORIGIN_COUNTRY")["UNIQUE_AIRCRAFT_COUNT"]
                    .sum()
                    .reset_index()
                    .sort_values(by="UNIQUE_AIRCRAFT_COUNT", ascending=False)
                    .head(10)
                )

                fig_bar = px.bar(
                    country_counts,
                    x="ORIGIN_COUNTRY",
                    y="UNIQUE_AIRCRAFT_COUNT",
                    color="UNIQUE_AIRCRAFT_COUNT",
                    color_continuous_scale=px.colors.sequential.Reds,
                    labels={"UNIQUE_AIRCRAFT_COUNT": "Aircraft Count", "ORIGIN_COUNTRY": "Country"},
                    text_auto=True,
                )
                fig_bar.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#000000",
                    plot_bgcolor="#000000",
                    margin=dict(l=20, r=20, t=30, b=20),
                    coloraxis_showscale=False
                )
                st.plotly_chart(fig_bar, use_container_width=True, key="flight_bar_chart")

        # ==========================================
        # 3. LINE CHART LAYER (Hourly Density Trends)
        # ==========================================
        with chart_col2:
            st.markdown("### ⏱️ Hourly Airborne vs Ground Traffic")
            if not df_gold.empty:
                hourly_trend = (
                    df_gold.groupby("SNAPSHOT_HOUR")[["AIRBORNE_AIRCRAFT_COUNT", "GROUND_AIRCRAFT_COUNT"]]
                    .sum()
                    .reset_index()
                )

                fig_line = px.line(
                    hourly_trend,
                    x="SNAPSHOT_HOUR",
                    y=["AIRBORNE_AIRCRAFT_COUNT", "GROUND_AIRCRAFT_COUNT"],
                    labels={"value": "Aircraft Count", "SNAPSHOT_HOUR": "Snapshot Hour", "variable": "Status"},
                    color_discrete_map={
                        "AIRBORNE_AIRCRAFT_COUNT": "#ff3333",
                        "GROUND_AIRCRAFT_COUNT": "#ffaa00"
                    }
                )
                fig_line.update_layout(
                    template="plotly_dark",
                    paper_bgcolor="#000000",
                    plot_bgcolor="#000000",
                    margin=dict(l=20, r=20, t=30, b=20),
                )
                st.plotly_chart(fig_line, use_container_width=True, key="traffic_line_chart")
            else:
                st.info("Awaiting Gold analytics dataset.")

        st.markdown("---")

        # Secondary Split
        dist_col1, dist_col2 = st.columns(2)

        # ==========================================
        # 4. 3D FLIGHT CORRIDOR ARRAY (Gold Spatial Sectors)
        # ==========================================
        with dist_col1:
            st.markdown("### 🧊 3D Sector Center & Altitude Array")

            fig_3d = plt.figure(figsize=(10, 6), facecolor="#000000")
            ax = fig_3d.add_subplot(111, projection="3d", facecolor="#000000")

            clean_geo = df_gold.dropna(subset=["SECTOR_CENTER_LON", "SECTOR_CENTER_LAT", "AVG_AIRBORNE_ALTITUDE_FT"])
            top_countries = clean_geo["ORIGIN_COUNTRY"].value_counts().head(5).index
            filtered_geo = clean_geo[clean_geo["ORIGIN_COUNTRY"].isin(top_countries)]

            color_palette = sns.color_palette("Set2", len(top_countries))
            city_color_map = dict(zip(top_countries, color_palette))

            for country_name, group in filtered_geo.groupby("ORIGIN_COUNTRY"):
                ax.scatter(
                    group["SECTOR_CENTER_LON"],
                    group["SECTOR_CENTER_LAT"],
                    group["AVG_AIRBORNE_ALTITUDE_FT"],
                    label=country_name,
                    color=city_color_map[country_name],
                    s=30,
                    alpha=0.8,
                    edgecolors="w",
                    linewidth=0.3,
                )

            ax.xaxis.set_pane_color((0.0, 0.0, 0.0, 1.0))
            ax.yaxis.set_pane_color((0.0, 0.0, 0.0, 1.0))
            ax.zaxis.set_pane_color((0.0, 0.0, 0.0, 1.0))

            ax.set_xlabel("Longitude", fontsize=9, color="#ffffff")
            ax.set_ylabel("Latitude", fontsize=9, color="#ffffff")
            ax.set_zlabel("Avg Altitude (ft)", fontsize=9, color="#ffffff")
            ax.set_title("3D Spatial Sector Sectoring", fontsize=11, color="#ffffff")
            ax.legend(title="Top Origin Countries", loc="upper left", bbox_to_anchor=(1.05, 1), fontsize=8, facecolor="#000000", edgecolor="#1e293b")
            plt.tight_layout()
            st.pyplot(fig_3d)

        # ==========================================
        # 5. SEABORN SPEED DENSITY PROFILE
        # ==========================================
        with dist_col2:
            st.markdown("### 📊 Ground Speed Density Curves")

            fig_density, ax_density = plt.subplots(figsize=(10, 8.5), facecolor="#000000")
            ax_density.set_facecolor("#000000")

            sns.histplot(
                data=filtered_geo,
                x="AVG_GROUND_SPEED_KNOTS",
                hue="ORIGIN_COUNTRY",
                element="step",
                stat="density",
                common_norm=False,
                kde=True,
                palette="Set2",
                alpha=0.4,
                ax=ax_density,
            )
            ax_density.set_xlabel("Avg Speed (knots)", fontsize=10, color="#ffffff")
            ax_density.set_ylabel("Data Density", fontsize=10, color="#ffffff")
            ax_density.set_title("Ground Speed Profiles across Spatial Sectors", fontsize=11, color="#ffffff")
            plt.tight_layout()
            st.pyplot(fig_density)

        st.markdown("---")

        stat_col1, stat_col2 = st.columns(2)

        # ==========================================
        # 6. NULL QUALITY MATRIX
        # ==========================================
        with stat_col1:
            st.markdown("### 🔍 Gold Layer Data Integrity (Null Matrix)")

            fig_heatmap, ax_heatmap = plt.subplots(figsize=(10, 6), facecolor="#000000")
            ax_heatmap.set_facecolor("#000000")

            sns.heatmap(
                df_gold.isnull(),
                cmap="viridis",
                cbar=False,
                yticklabels=False,
                ax=ax_heatmap,
            )
            ax_heatmap.set_title("BUSINESS_READY_FLIGHT_ANALYTICS Null Matrix", fontsize=11, color="#ffffff")
            plt.tight_layout()
            st.pyplot(fig_heatmap)

        # ==========================================
        # 7. ALTITUDE SPREAD BY FLIGHT PHASE
        # ==========================================
        with stat_col2:
            st.markdown("### 📦 Altitude Distribution Across Flight Phases")

            fig_box, ax_box = plt.subplots(figsize=(10, 6), facecolor="#000000")
            ax_box.set_facecolor("#000000")

            sns.boxplot(
                data=df_gold,
                x="FLIGHT_PHASE",
                y="AVG_AIRBORNE_ALTITUDE_FT",
                hue="FLIGHT_PHASE",
                legend=False,
                palette="Set2",
                ax=ax_box,
                fliersize=4,
            )
            ax_box.set_xlabel("Flight Phase", fontsize=10, color="#ffffff")
            ax_box.set_ylabel("Avg Altitude (ft)", fontsize=10, color="#ffffff")
            ax_box.set_title("Altitude IQR Across Flight Phases", fontsize=11, color="#ffffff")
            plt.tight_layout()
            st.pyplot(fig_box)

        st.markdown("---")

        # ==========================================
        # 8. LIVE AUDIT DATA GRID (GOLD LAYER)
        # ==========================================
        st.markdown("### 🔍 Flight_Records: `FLIGHT_ANALYTICS` Data Table")

        st.dataframe(
            df_gold.style.background_gradient(
                cmap="Reds", 
                subset=["UNIQUE_AIRCRAFT_COUNT", "AIRBORNE_AIRCRAFT_COUNT", "AVG_GROUND_SPEED_KNOTS"]
            ),
            use_container_width=True
        )
        st.caption("🔄 Direct query from OPENSKY_ETL.FINAL.BUSINESS_READY_FLIGHT_ANALYTICS.")

except Exception as pipeline_err:
    st.error(f"❌ Dashboard connection error: {pipeline_err}")
    st.info("Verify your Snowflake credentials in `.env` and schema permissions for `OPENSKY_ETL`.")