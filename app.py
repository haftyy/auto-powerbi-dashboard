# app.py
import streamlit as st
import pandas as pd
import json
import numpy as np
from io import BytesIO

st.set_page_config(page_title="Auto Power BI Schema Generator", layout="wide")
st.title("Auto Power BI → Schema & Rows for Power BI Push Dataset")

# --- Upload ---
uploaded = st.file_uploader("Upload CSV or Excel", type=["csv", "xlsx"])
if not uploaded:
    st.info("Upload a CSV or XLSX to start. (I'll generate a push-dataset schema + sample rows.)")
    st.stop()

# --- Read file ---
try:
    if uploaded.name.endswith(".csv"):
        df = pd.read_csv(uploaded)
    else:
        df = pd.read_excel(uploaded)
except Exception as e:
    st.error("Error reading file: " + str(e))
    st.stop()

st.markdown("### Preview (first 10 rows)")
st.dataframe(df.head(10))

# --- Column selection & cleaning ---
st.sidebar.header("Column options")
all_cols = list(df.columns)
selected = st.sidebar.multiselect("Columns to include in Power BI table", all_cols, default=all_cols)

# Optionally fill nulls
fill_na = st.sidebar.text_input("Fill missing values (leave empty to keep NaN)", value="")
if fill_na != "":
    df[selected] = df[selected].fillna(fill_na)

# --- Infer datatypes and map to Power BI types ---
def map_dtype_to_powerbi(series: pd.Series):
    """Return a Power BI-compatible dataType string."""
    if pd.api.types.is_datetime64_any_dtype(series):
        return "DateTime"
    if pd.api.types.is_float_dtype(series) or pd.api.types.is_integer_dtype(series):
        # Decide between Int64 and Double
        if pd.api.types.is_integer_dtype(series.dropna()):
            return "Int64"
        return "Double"
    if pd.api.types.is_bool_dtype(series):
        return "Boolean"
    # fallback to string
    return "String"

st.markdown("### Inferred schema")
schema = []
for c in selected:
    dtype = map_dtype_to_powerbi(df[c])
    schema.append({"name": c, "dataType": dtype})
st.json(schema)

# --- Build dataset JSON for Power BI create dataset API ---
dataset_name = st.text_input("Dataset name (Power BI)", value=f"MyDataset_{uploaded.name.split('.')[0]}")
table_name = st.text_input("Table name", value="Table1")

dataset_json = {
    "name": dataset_name,
    "defaultMode": "Push",
    "tables": [
        {
            "name": table_name,
            "columns": schema
        }
    ]
}

st.markdown("### Power BI create-dataset JSON (push dataset)")
st.code(json.dumps(dataset_json, indent=2), language="json")

# --- Prepare rows payload ---
def df_to_rows_payload(df_, cols):
    # convert numpy types to native python types, replace NaN with None
    df2 = df_[cols].replace({np.nan: None}).copy()
    # Convert datetimes to ISO strings
    for col in df2.columns:
        if pd.api.types.is_datetime64_any_dtype(df2[col]):
            df2[col] = df2[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
    rows = df2.to_dict(orient="records")
    return {"rows": rows}

if st.button("Preview rows payload (first 50 rows)"):
    payload = df_to_rows_payload(df, selected)
    preview = {"rows": payload["rows"][:50]}
    st.write(f"Total rows: {len(payload['rows'])}")
    st.json(preview)

# --- Download JSON files ---
if st.button("Download create-dataset JSON"):
    b = BytesIO()
    b.write(json.dumps(dataset_json, indent=2).encode("utf-8"))
    b.seek(0)
    st.download_button("Download dataset schema JSON", b, file_name="powerbi_dataset_schema.json")

if st.button("Download rows payload (full)"):
    payload = df_to_rows_payload(df, selected)
    b = BytesIO()
    b.write(json.dumps(payload, indent=2, default=str).encode("utf-8"))
    b.seek(0)
    st.download_button("Download rows JSON", b, file_name="powerbi_rows_payload.json")

st.success("Step 1 ready — schema/generated. Next: authenticate & push this to Power BI (Step 2).")
