import streamlit as st
import pandas as pd
from rapidfuzz import process, fuzz
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("Fuzzy Matcher")

uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Preview of Uploaded Data")
    st.dataframe(df.head())

    st.write("### Filter Uploaded Data (Optional)")
    filter_field = st.selectbox("Select a field to filter on (optional)", [None] + df.columns.tolist())
    filter_type = None
    filter_value = None
    filtered_df = df.copy()
    if filter_field:
        filter_type = st.radio(
            "Filter type",
            ("No filter", "Remove Null/Empty values", "Exact match")
        )
        if filter_type == "Remove Null/Empty values":
            # Filter OUT Remove Null/Empty values
            filtered_df = df[~(df[filter_field].isnull() | (df[filter_field].astype(str).str.strip() == ""))]
        elif filter_type == "Exact match":
            unique_values = sorted(df[filter_field].dropna().astype(str).unique())
            filter_value = st.selectbox(f"Select value to exactly match in '{filter_field}'", [None] + unique_values)
            if filter_value:
                filtered_df = df[df[filter_field].astype(str) == filter_value]
    st.write("### Preview of Filtered Data")
    st.dataframe(filtered_df.head())

    st.write("### Enter Master List for Fuzzy Matching")
    user_master_list_input = st.text_area(
        "Enter one item per line to build your master list (e.g., countries, products, etc.)",
        placeholder="United States\nIndia\nGermany\n..."
    )

    master_list = [line.strip() for line in user_master_list_input.splitlines() if line.strip()]
    if not master_list:
        st.warning("Please provide a valid master list before proceeding.")
    else:
        normalized_master = {c.lower(): c for c in master_list}

        selected_fields = st.multiselect("Select fields to search for matches", filtered_df.columns.tolist())
        threshold = st.slider("Matching threshold (0-100)", min_value=60, max_value=100, value=85)

        if st.button("Run Fuzzy Matching"):
            match_results = [None] * len(filtered_df)
            field_stats = defaultdict(lambda: {"matched": 0, "unmatched": 0})

            progress_bar = st.progress(0)
            total_rows = len(filtered_df)

            def match_row(index, row):
                matched_value = None
                evidence = None
                local_stats = defaultdict(lambda: {"matched": 0, "unmatched": 0})

                for field in selected_fields:
                    value = str(row[field]).strip().lower()
                    # Substring match first
                    substring_match = None
                    for master_key in normalized_master.keys():
                        if master_key in value:
                            substring_match = master_key
                            break
                    if substring_match:
                        matched_value = normalized_master[substring_match]
                        evidence = f"Field: {field} | Value: {value} | Substring Match: {matched_value}"
                        local_stats[field]["matched"] += 1
                        break
                    # Fuzzy match fallback
                    best_match, score, _ = process.extractOne(
                        value,
                        normalized_master.keys(),
                        scorer=fuzz.token_sort_ratio
                    )
                    if score >= threshold:
                        matched_value = normalized_master[best_match]
                        evidence = f"Field: {field} | Value: {value} | Fuzzy Match: {matched_value} | Score: {score}"
                        local_stats[field]["matched"] += 1
                        break
                    else:
                        local_stats[field]["unmatched"] += 1

                return index, matched_value, evidence, local_stats

            with ThreadPoolExecutor() as executor:
                futures = [executor.submit(match_row, idx, row) for idx, row in filtered_df.iterrows()]
                for i, future in enumerate(as_completed(futures)):
                    index, matched_value, evidence, local_stats = future.result()
                    match_results[index] = {
                        "Matched Value": matched_value or "Not Found",
                        "Evidence": evidence if matched_value else ""
                    }
                    for field in local_stats:
                        field_stats[field]["matched"] += local_stats[field]["matched"]
                        field_stats[field]["unmatched"] += local_stats[field]["unmatched"]
                    progress_bar.progress((i + 1) / total_rows)

            result_df = pd.concat([filtered_df, pd.DataFrame(match_results)], axis=1)

            # Show only matched cases in Results
            matched_only_df = result_df[result_df["Matched Value"] != "Not Found"]

            st.write("### Results with Fuzzy Matching")
            st.dataframe(matched_only_df)

            st.download_button("Download Results", data=result_df.to_csv(index=False), file_name="fuzzy_matched_results.csv")

            st.write("### Matching Stats per Field")
            st.json(field_stats)
else:
    st.info("Please upload a CSV file to begin.")