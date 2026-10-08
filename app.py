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
# Aging chart: share of population aged 65+
st.subheader("Aging Population: Share Aged 65+")

old_cols = ["Population.Aged.65.to.69", "Population.Aged.70.to.74",
            "Population.Aged.75.to.79", "Population.Aged.80."]
aging = df[df["Gender"] == "Total"].sort_values("year").copy()
aging["Share 65+ (%)"] = aging[old_cols].sum(axis=1) / aging["Total.Population"] * 100

fig4 = px.line(aging, x="year", y="Share 65+ (%)", markers=True,
               title="Share of NL Population Aged 65+ (%)")
st.plotly_chart(fig4, use_container_width=True)
# Population pyramid
st.subheader("Population Pyramid")
pyr = df[(df["year"] == age_year) & (df["Gender"].isin(["Male", "Female"]))]
labels = [c.replace("Population.Aged.", "").replace(".to.", "-").rstrip(".") for c in age_cols]
labels = ["80+" if l == "80" else l for l in labels]
male = pyr[pyr["Gender"] == "Male"][age_cols].iloc[0].values
female = pyr[pyr["Gender"] == "Female"][age_cols].iloc[0].values

fig5 = go.Figure()
fig5.add_trace(go.Bar(y=labels, x=-male, name="Male", orientation="h"))
fig5.add_trace(go.Bar(y=labels, x=female, name="Female", orientation="h"))
fig5.update_layout(barmode="relative", title=f"Population Pyramid ({age_year})",
                   xaxis_title="Population (Male left, Female right)",
                   yaxis_title="Age Group")
st.plotly_chart(fig5, use_container_width=True)
# Community risk analysis
st.header("Community Risk: Shrinking and Aging Communities")
st.caption("175 communities with reliable 2010 and 2020 data. "
           "Risk score (0-100) combines population loss and share aged 65+.")

risk = pd.read_csv("data/community_risk.csv")

top_n = st.slider("Show top N highest-risk communities", 5, 30, 10)
top = risk.sort_values("Risk score", ascending=False).head(top_n)

fig6 = px.bar(top.sort_values("Risk score"), x="Risk score", y="Geography",
              orientation="h", color="Share 65+ (%)",
              title=f"Top {top_n} Highest-Risk Communities")
st.plotly_chart(fig6, use_container_width=True)

fig7 = px.scatter(risk, x="Share 65+ (%)", y="Change %", color="Risk score",
                  hover_name="Geography",
                  title="Aging vs Population Change (each dot is a community)")
st.plotly_chart(fig7, use_container_width=True)

st.dataframe(top[["Geography", "Pop 2010", "Pop 2020", "Change %",
                  "Share 65+ (%)", "Risk score"]])