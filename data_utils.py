import pandas as pd
import streamlit as st

from models import FilterCondition


# =========================================================
# 5. TEXT HELPERS
# =========================================================

def normalize_text(value):

    return str(
        value
    ).strip().lower()


def clean_json_response(text):

    text = text.strip()

    if text.startswith("```"):

        lines = text.splitlines()

        if lines:
            lines = lines[1:]

        if (
            lines
            and
            lines[-1].strip() == "```"
        ):

            lines = lines[:-1]

        text = "\n".join(
            lines
        )

    return text.strip()


# =========================================================
# 6. NORMALIZE GEMINI PLAN
# =========================================================

def normalize_gemini_plan(data):

    if not isinstance(
        data,
        dict
    ):

        data = {}

    operation = data.get(
        "operation",
        "sum"
    )

    if isinstance(
        operation,
        list
    ):

        operation = (
            operation[0]
            if operation
            else "sum"
        )

    operation = str(
        operation
    ).strip().lower()

    metric = data.get(
        "metric",
        "profit"
    )

    if isinstance(
        metric,
        list
    ):

        metric = (
            metric[0]
            if metric
            else "profit"
        )

    if metric is not None:

        metric = str(
            metric
        ).strip().lower()

    group_by = data.get(
        "group_by"
    )

    if isinstance(
        group_by,
        list
    ):

        group_by = (
            group_by[0]
            if group_by
            else None
        )

    if group_by is not None:

        group_by = str(
            group_by
        ).strip()

    sort_direction = data.get(
        "sort_direction"
    )

    if isinstance(
        sort_direction,
        list
    ):

        sort_direction = (
            sort_direction[0]
            if sort_direction
            else None
        )

    if sort_direction is not None:

        sort_direction = str(
            sort_direction
        ).strip().lower()

    top_n = data.get(
        "top_n"
    )

    if isinstance(
        top_n,
        list
    ):

        top_n = (
            top_n[0]
            if top_n
            else None
        )

    if top_n is not None:

        try:

            top_n = int(
                top_n
            )

        except Exception:

            top_n = None

    raw_filters = data.get(
        "filters",
        []
    )

    if not isinstance(
        raw_filters,
        list
    ):

        raw_filters = []

    cleaned_filters = []

    for item in raw_filters:

        if not isinstance(
            item,
            dict
        ):

            continue

        column = item.get(
            "column"
        )

        value = item.get(
            "value"
        )

        if isinstance(
            column,
            list
        ):

            column = (
                column[0]
                if column
                else None
            )

        if isinstance(
            value,
            list
        ):

            value = (
                value[0]
                if value
                else None
            )

        if column is None:
            continue

        if value is None:
            continue

        cleaned_filters.append(
            {
                "column": str(
                    column
                ).strip(),

                "value": str(
                    value
                ).strip()
            }
        )

    return {
        "operation": operation,
        "metric": metric,
        "filters": cleaned_filters,
        "group_by": group_by,
        "sort_direction": sort_direction,
        "top_n": top_n
    }


# =========================================================
# 7. READ UPLOADED FILE
# =========================================================

def read_uploaded_file(
    uploaded_file
):

    filename = (
        uploaded_file.name.lower()
    )

    try:

        if filename.endswith(
            ".csv"
        ):

            return pd.read_csv(
                uploaded_file
            )

        if filename.endswith(
            ".xlsx"
        ):

            return pd.read_excel(
                uploaded_file
            )

        return None

    except Exception as e:

        st.error(
            f"Could not read "
            f"{uploaded_file.name}: {e}"
        )

        return None


# =========================================================
# 8. NORMALIZE DATAFRAME
# =========================================================

def normalize_dataframe(df):

    df = df.copy()

    df = df.dropna(
        axis=1,
        how="all"
    )

    df.columns = [
        str(column).strip()
        for column in df.columns
    ]

    numeric_columns = [
        "sales",
        "revenue",
        "profit",
        "loss",
        "unsold",

        # Added because the dataset now
        # contains the derived price column.
        "price"
    ]

    for column in numeric_columns:

        if column in df.columns:

            df[column] = pd.to_numeric(
                df[column],
                errors="coerce"
            ).fillna(0)

    return df


# =========================================================
# 9. CHECK SCHEMA
# =========================================================

def check_schema_compatibility(
    dataframes
):

    if not dataframes:

        return True, ""

    reference_columns = list(
        dataframes[0].columns
    )

    reference_set = set(
        reference_columns
    )

    for index, df in enumerate(
        dataframes[1:],
        start=2
    ):

        current_set = set(
            df.columns
        )

        missing = (
            reference_set
            - current_set
        )

        extra = (
            current_set
            - reference_set
        )

        if missing or extra:

            message = (
                f"File {index} has "
                f"an incompatible schema.\n\n"
            )

            if missing:

                message += (
                    "Missing columns: "
                    + ", ".join(
                        sorted(missing)
                    )
                    + "\n"
                )

            if extra:

                message += (
                    "Additional columns: "
                    + ", ".join(
                        sorted(extra)
                    )
                )

            return False, message

    return True, ""


# =========================================================
# 10. DATASET CONTEXT
# =========================================================

def create_dataset_context(df):

    context = {
        "columns": list(
            df.columns
        ),

        "dtypes": {
            column: str(dtype)
            for column, dtype
            in df.dtypes.items()
        },

        "categorical_values": {}
    }

    categorical_columns = [
        "year_month",
        "state",
        "city",
        "product",
        "brand",
        "product_series"
    ]

    for column in categorical_columns:

        if column in df.columns:

            values = (
                df[column]
                .dropna()
                .astype(str)
                .unique()
                .tolist()
            )

            context[
                "categorical_values"
            ][column] = values

    return context


# =========================================================
# 11. FIND DATASET VALUE
# =========================================================

def find_dataset_value(
    question,
    df,
    column
):

    if column not in df.columns:

        return None

    question_normalized = (
        normalize_text(
            question
        )
    )

    values = (
        df[column]
        .dropna()
        .astype(str)
        .unique()
        .tolist()
    )

    values.sort(
        key=lambda value:
        len(
            normalize_text(
                value
            )
        ),
        reverse=True
    )

    for value in values:

        normalized_value = (
            normalize_text(
                value
            )
        )

        if (
            normalized_value
            in question_normalized
        ):

            return value

    return None


# =========================================================
# 12. DETECT EXPLICIT FILTERS
# =========================================================

def detect_explicit_filters(
    question,
    df
):

    filters = []

    columns = [
        "year_month",
        "state",
        "city",
        "product",
        "brand",
        "product_series"
    ]

    for column in columns:

        value = find_dataset_value(
            question,
            df,
            column
        )

        if value is not None:

            filters.append(
                FilterCondition(
                    column=column,
                    value=value
                )
            )

    return filters