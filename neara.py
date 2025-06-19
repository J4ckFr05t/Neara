import streamlit as st
st.set_page_config(page_title="Neara - Fuzzy Matcher")
import pandas as pd
from rapidfuzz import process, fuzz
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import re

# ---------------------------
# Streamlit UI
# ---------------------------
st.title("Fuzzy Matcher")

uploaded_file = st.file_uploader("Upload a CSV file", type="csv")

if uploaded_file:
    df = pd.read_csv(uploaded_file)
    st.write("### Uploaded Data Stats")
    num_records = len(df)
    st.write(f"Number of records: {num_records}")
    coverage = (df.notnull().sum() / num_records * 100).round(2)
    coverage_df = pd.DataFrame({
        'Field': coverage.index,
        'Coverage (%)': coverage.values
    })
    st.dataframe(coverage_df)

    st.write("### Filter Uploaded Data (Optional)")
    filter_field = st.selectbox("Select a field to filter on (optional)", [None] + df.columns.tolist())
    filter_type = None
    filter_value = None
    filtered_df = df.copy()
    if filter_field:
        filter_type = st.radio(
            "Filter type",
            ("No filter", "Null/Empty values", "Exact match")
        )
        include_exclude = None
        if filter_type != "No filter":
            include_exclude = st.radio(
                "Include or Exclude?",
                ("Include", "Exclude"),
                horizontal=True
            )
        if filter_type == "Null/Empty values" and include_exclude:
            if include_exclude == "Include":
                # Keep only Null/Empty values
                filtered_df = df[df[filter_field].isnull() | (df[filter_field].astype(str).str.strip() == "")]
            else:
                # Exclude Null/Empty values (current behavior)
                filtered_df = df[~(df[filter_field].isnull() | (df[filter_field].astype(str).str.strip() == ""))]
        elif filter_type == "Exact match":
            unique_values = sorted(df[filter_field].dropna().astype(str).unique())
            filter_value = st.selectbox(f"Select value to exactly match in '{filter_field}'", [None] + unique_values)
            if filter_value and include_exclude:
                if include_exclude == "Include":
                    filtered_df = df[df[filter_field].astype(str) == filter_value]
                else:
                    filtered_df = df[df[filter_field].astype(str) != filter_value]
    st.write("### Preview of Filtered Data")
    st.write(f"Number of records after filter: {len(filtered_df)}")
    st.dataframe(filtered_df.head())

    st.write("### Enter Master List for Fuzzy Matching")
    user_master_list_input = st.text_area(
        "Enter one item per line to build your master list (e.g., countries, products, etc.)",
        placeholder="United States\nIndia\nGermany\n..."
    )

    master_list = [item.strip() for item in re.split(r'[\n,]', user_master_list_input) if item.strip()]
    if not master_list:
        st.warning("Please provide a valid master list before proceeding.")
    else:
        normalized_master = {c.lower(): c for c in master_list}

        selected_fields = st.multiselect("Select fields to search for matches", filtered_df.columns.tolist())
        threshold = st.slider("Matching threshold (0-100)", min_value=60, max_value=100, value=85)

        if st.button("Run Fuzzy Matching"):
            with st.spinner("Running fuzzy matching..."):
                match_results = {}
                field_stats = defaultdict(lambda: {"matched": 0, "unmatched": 0})

                progress_bar = st.progress(0)
                total_rows = len(filtered_df)

                def match_row(index, row):
                    matched_values = []
                    evidences = []
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
                            matched = normalized_master[substring_match]
                            matched_values.append(matched)
                            evidences.append(f"Field: {field} | Value: {value} | Substring Match: {matched}")
                            local_stats[field]["matched"] += 1
                            continue
                        # Fuzzy match fallback
                        best_match, score, _ = process.extractOne(
                            value,
                            normalized_master.keys(),
                            scorer=fuzz.token_sort_ratio
                        )
                        if score >= threshold:
                            matched = normalized_master[best_match]
                            matched_values.append(matched)
                            evidences.append(f"Field: {field} | Value: {value} | Fuzzy Match: {matched} | Score: {score}")
                            local_stats[field]["matched"] += 1
                        else:
                            local_stats[field]["unmatched"] += 1

                    if matched_values:
                        matched_value = "; ".join(matched_values)
                        evidence = "\n".join(evidences)
                    else:
                        matched_value = None
                        evidence = ""
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

                result_df = pd.concat([filtered_df, pd.DataFrame.from_dict(match_results, orient='index')], axis=1)

                # Show only matched cases in Results
                matched_only_df = result_df[result_df["Matched Value"] != "Not Found"]

                st.write("### Results with Fuzzy Matching")
                st.dataframe(matched_only_df)

                # Show stats: how many records matched (count and percentage)
                total_records = len(result_df)
                matched_records = len(matched_only_df)
                percent_matched = (matched_records / total_records * 100) if total_records > 0 else 0
                st.write(f"**Matched Records:** {matched_records} / {total_records} ({percent_matched:.2f}%)")

                st.download_button("Download Results", data=result_df.to_csv(index=False), file_name="fuzzy_matched_results.csv")

                st.write("### Matching Stats per Field")
                st.json(field_stats)
else:
    st.info("Please upload a CSV file to begin.")