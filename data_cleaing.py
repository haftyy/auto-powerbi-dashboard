import pandas as pd
import numpy as np
import re
import json
import openai

# ---------- RULE-BASED CLEANING ----------
def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    # same rule-based cleaning we built earlier
    # ...
    return df


# ---------- AI-POWERED CLEANING ----------
def ai_clean_dataframe(df: pd.DataFrame, api_key: str) -> pd.DataFrame:
    """
    Use OpenAI GPT to suggest and apply data cleaning steps.
    """
    openai.api_key = api_key

    # Take a sample of data for GPT
    sample = df.head(20).to_dict(orient="records")

    prompt = f"""
    You are a data cleaning assistant.
    The user uploaded a dataset. Suggest clean column names,
    handle missing values, standardize categories, and detect data types.

    Dataset sample:
    {json.dumps(sample, indent=2)}

    Output JSON should include:
    - "renamed_columns": mapping of old → new names
    - "cleaning_steps": list of transformations (drop duplicates, fill nulls, etc.)
    """

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        cleaning_plan = response.choices[0].message["content"]
        plan = json.loads(cleaning_plan)
    except Exception as e:
        print("AI Cleaning Error:", e)
        return df

    # Apply renaming
    if "renamed_columns" in plan:
        df = df.rename(columns=plan["renamed_columns"])

    # Apply simple steps (extendable)
    if "cleaning_steps" in plan:
        for step in plan["cleaning_steps"]:
            if "drop duplicates" in step.lower():
                df = df.drop_duplicates()
            if "fill nulls" in step.lower() or "missing" in step.lower():
                df = df.fillna("Unknown")

    return df
