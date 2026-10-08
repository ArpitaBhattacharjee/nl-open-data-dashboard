import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(page_title="NL Population Dashboard", layout="wide")
st.title("Newfoundland and Labrador Population Dashboard")

df = pd.read_csv("data/province_clean.csv")

# Sidebar filters
st.sidebar.header("Filters")
gender = st.sidebar.selectbox("Gender", ["Total", "Female", "Male"])
years = st.sidebar.slider("Year range", 2010, 2020, (2010, 2020))

filtered = df[(df["Gender"] == gender) &
              (df["year"] >= years[0]) & (df["year"] <= years[1])]

# Trend chart
fig = px.line(filtered, x="year", y="Total.Population",
              title=f"Population Trend ({gender})", markers=True)
st.plotly_chart(fig, use_container_width=True)
# Age group chart
st.subheader("Population by Age Group")
age_year = st.sidebar.selectbox("Age chart year", sorted(df["year"].unique(), reverse=True))

age_cols = [c for c in df.columns if c.startswith("Population.Aged")]
age_row = df[(df["Gender"] == gender) & (df["year"] == age_year)]
age_data = age_row[age_cols].T.reset_index()
age_data.columns = ["Age Group", "Population"]
age_data["Age Group"] = (age_data["Age Group"]
                         .str.replace("Population.Aged.", "", regex=False)
                         .str.replace(".to.", "-", regex=False)
                         .str.rstrip("."))
age_data.loc[age_data["Age Group"] == "80", "Age Group"] = "80+"

fig2 = px.bar(age_data, x="Age Group", y="Population",
              title=f"Population by Age Group ({age_year}, {gender})")
st.plotly_chart(fig2, use_container_width=True)
# Forecast
from statsmodels.tsa.arima.model import ARIMA
import plotly.graph_objects as go

st.subheader("Population Forecast to 2030")

total = df[df["Gender"] == "Total"].sort_values("year")
model = ARIMA(total["Total.Population"].values, order=(1, 1, 0)).fit()
fc = model.get_forecast(steps=10)
pred = fc.predicted_mean
ci = fc.conf_int(alpha=0.05)
future_years = list(range(2021, 2031))

fig3 = go.Figure()
fig3.add_trace(go.Scatter(x=total["year"], y=total["Total.Population"],
                          mode="lines+markers", name="Actual"))
fig3.add_trace(go.Scatter(x=future_years, y=pred,
                          mode="lines+markers", name="Forecast",
                          line=dict(dash="dash")))
fig3.add_trace(go.Scatter(x=future_years + future_years[::-1],
                          y=list(ci[:, 1]) + list(ci[:, 0][::-1]),
                          fill="toself", opacity=0.2,
                          line=dict(width=0), name="95% interval"))
fig3.update_layout(title="NL Population Forecast (ARIMA)",
                   xaxis_title="Year", yaxis_title="Population")
st.plotly_chart(fig3, use_container_width=True)