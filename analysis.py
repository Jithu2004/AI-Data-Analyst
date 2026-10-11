import json
import re

import pandas as pd
import streamlit as st

from google import genai

from config import client, MODEL_NAME

from models import (
    AnalysisPlan,
    FilterCondition
)

from data_utils import (
    clean_json_response,
    create_dataset_context,
    detect_explicit_filters,
    normalize_gemini_plan,
    normalize_text
)


# =========================================================
# 13. TOP N DETECTION
# =========================================================

def detect_top_n(question):

    question_normalized = (
        normalize_text(
            question
        )
    )

    patterns = [
        r"\btop\s+(\d+)\b",
        r"\bfirst\s+(\d+)\b",
        r"\bbest\s+(\d+)\b",
        r"\bhighest\s+(\d+)\b",
        r"\bmost\s+(\d+)\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            question_normalized
        )

        if match:
            return int(
                match.group(1)
            )

    # Natural-language "one" / single-result questions
    single_result_patterns = [
        "most sold",
        "most sales",
        "highest sold",
        "highest sales",
        "best selling",
        "highest selling",
        "most profitable",
        "highest profit",
        "highest revenue",
        "highest sales",
        "highest loss",
        "highest unsold",
        "highest price",
        "maximum revenue",
        "maximum profit",
        "maximum sales",
        "maximum price",
        "best performing",
        "best performing state",
        "best performing brand",
        "best performing product",
        "best performing city"
    ]

    for phrase in single_result_patterns:

        if phrase in question_normalized:
            return 1

    return None


# =========================================================
# 14. BOTTOM N DETECTION
# =========================================================

def detect_bottom_n(question):

    question_normalized = (
        normalize_text(
            question
        )
    )

    patterns = [
        r"\bbottom\s+(\d+)\b",
        r"\blast\s+(\d+)\b",
        r"\bworst\s+(\d+)\b",
        r"\blowest\s+(\d+)\b",
        r"\bleast\s+(\d+)\b"
    ]

    for pattern in patterns:

        match = re.search(
            pattern,
            question_normalized
        )

        if match:
            return int(
                match.group(1)
            )

    single_result_patterns = [
        "least sold",
        "least sales",
        "lowest sold",
        "lowest sales",
        "least selling",
        "lowest selling",
        "least profitable",
        "lowest profit",
        "lowest revenue",
        "lowest sales",
        "lowest loss",
        "lowest unsold",
        "lowest price",
        "minimum revenue",
        "minimum profit",
        "minimum sales",
        "minimum price",
        "worst performing",
        "worst performing state",
        "worst performing brand",
        "worst performing product",
        "worst performing city"
    ]

    for phrase in single_result_patterns:

        if phrase in question_normalized:
            return 1

    return None


# =========================================================
# 15. DETECT GROUP BY
# =========================================================

def detect_group_by(question, df):

    question_normalized = (
        normalize_text(
            question
        )
    )

    # More specific dimensions first.
    # This prevents "product series" from being
    # interpreted as just "product".

    group_patterns = {

        "product_series": [
            "by product series",
            "product series wise",
            "product serieswise",
            "for each product series",
            "per product series",
            "each product series",
            "product series",
            "series wise",
            "serieswise"
        ],

        "brand": [
            "by brand",
            "brand wise",
            "brandwise",
            "for each brand",
            "per brand",
            "each brand",
            "brand"
        ],

        "product": [
            "by product",
            "product wise",
            "productwise",
            "for each product",
            "per product",
            "each product"
        ],

        "state": [
            "by state",
            "state wise",
            "statewise",
            "for each state",
            "per state",
            "each state",
            "state"
        ],

        "city": [
            "by city",
            "city wise",
            "citywise",
            "for each city",
            "per city",
            "each city",
            "city"
        ],

        "year_month": [
            "by month",
            "monthly",
            "month wise",
            "monthwise",
            "for each month",
            "per month",
            "each month",
            "over time",
            "by year month",
            "year month wise"
        ]
    }

    # Explicit phrases first.
    for column, phrases in group_patterns.items():

        for phrase in phrases:

            if phrase in question_normalized:

                if column in df.columns:
                    return column

    # Natural ranking phrases.
    ranking_patterns = {

        "state": [
            "highest state",
            "lowest state",
            "best state",
            "worst state",
            "top state",
            "bottom state",
            "leading state",
            "leading states",
            "performing state",
            "performing states",
            "state with the highest",
            "state with the lowest",
            "state with most",
            "state with least"
        ],

        "brand": [
            "highest brand",
            "lowest brand",
            "best brand",
            "worst brand",
            "top brand",
            "bottom brand",
            "leading brand",
            "most profitable brand",
            "least profitable brand",
            "brand with the highest",
            "brand with the lowest",
            "brand with most",
            "brand with least"
        ],

        "product": [
            "highest product",
            "lowest product",
            "best product",
            "worst product",
            "top product",
            "bottom product",
            "leading product",
            "most profitable product",
            "least profitable product",
            "product with the highest",
            "product with the lowest",
            "product with most",
            "product with least",
            "most sold product",
            "least sold product",
            "best selling product",
            "worst selling product"
        ],

        "city": [
            "highest city",
            "lowest city",
            "best city",
            "worst city",
            "top city",
            "bottom city",
            "city with the highest",
            "city with the lowest",
            "city with most",
            "city with least"
        ],

        "product_series": [
            "highest product series",
            "lowest product series",
            "best product series",
            "worst product series",
            "top product series",
            "bottom product series",
            "most profitable product series",
            "least profitable product series"
        ]
    }

    for column, phrases in ranking_patterns.items():

        for phrase in phrases:

            if phrase in question_normalized:

                if column in df.columns:
                    return column

    return None


# =========================================================
# 15A. DETECT METRIC
# =========================================================

def detect_metric(question):

    question_normalized = (
        normalize_text(
            question
        )
    )

    # Most specific metrics first.
    if (
        "profit margin" in question_normalized
        or "profit percentage" in question_normalized
        or "margin percentage" in question_normalized
        or "margin %" in question_normalized
        or "profit %" in question_normalized
    ):
        return "profit_margin"

    if (
        "revenue per sale" in question_normalized
        or "revenue per unit" in question_normalized
        or "average revenue per sale" in question_normalized
        or "average revenue per unit" in question_normalized
        or "money per sale" in question_normalized
        or "money per unit" in question_normalized
    ):
        return "revenue_per_sale"

    if (
        "profit per sale" in question_normalized
        or "profit per unit" in question_normalized
        or "average profit per sale" in question_normalized
        or "average profit per unit" in question_normalized
        or "profit per item" in question_normalized
    ):
        return "profit_per_sale"

    if (
        "price" in question_normalized
        or "cost per unit" in question_normalized
        or "unit price" in question_normalized
        or "selling price" in question_normalized
        or "average price" in question_normalized
    ):
        return "price"

    if (
        re.search(
            r"\bprofit\b",
            question_normalized
        )
        or "profitability" in question_normalized
        or "profitable" in question_normalized
        or "money made" in question_normalized
        or "earnings" in question_normalized
        or "earning" in question_normalized
    ):
        return "profit"

    if (
        re.search(
            r"\brevenue\b",
            question_normalized
        )
        or "turnover" in question_normalized
        or "income generated" in question_normalized
        or "money generated" in question_normalized
        or "money earned" in question_normalized
    ):
        return "revenue"

    if (
        re.search(
            r"\bsales\b",
            question_normalized
        )
        or "units sold" in question_normalized
        or "quantity sold" in question_normalized
        or "volume sold" in question_normalized
        or "sold quantity" in question_normalized
        or "how many sold" in question_normalized
        or "how much sold" in question_normalized
    ):
        return "sales"

    if (
        re.search(
            r"\bloss\b",
            question_normalized
        )
        or "losses" in question_normalized
    ):
        return "loss"

    if (
        re.search(
            r"\bunsold\b",
            question_normalized
        )
        or "not sold" in question_normalized
        or "left unsold" in question_normalized
        or "remaining stock" in question_normalized
    ):
        return "unsold"

    return None


# =========================================================
# 15B. DETECT OPERATION
# =========================================================

def detect_operation(question):

    question_normalized = (
        normalize_text(
            question
        )
    )

    if (
        "average" in question_normalized
        or "mean" in question_normalized
        or "avg" in question_normalized
    ):
        return "mean"

    if (
        "count" in question_normalized
        or "number of records" in question_normalized
        or "how many records" in question_normalized
    ):
        return "count"

    if (
        "maximum" in question_normalized
        or "max" in question_normalized
        or "highest value" in question_normalized
    ):
        return "max"

    if (
        "minimum" in question_normalized
        or "min" in question_normalized
        or "lowest value" in question_normalized
    ):
        return "min"

    return "sum"


# =========================================================
# 15C. DETECT RANKING DIRECTION
# =========================================================

def detect_ranking_direction(question):

    question_normalized = (
        normalize_text(
            question
        )
    )

    highest_words = [
        "highest",
        "high",
        "maximum",
        "max",
        "most",
        "best",
        "top",
        "largest",
        "greatest",
        "leading"
    ]

    lowest_words = [
        "lowest",
        "low",
        "minimum",
        "min",
        "least",
        "worst",
        "bottom",
        "smallest"
    ]

    for word in highest_words:

        if re.search(
            rf"\b{re.escape(word)}\b",
            question_normalized
        ):
            return "desc"

    for word in lowest_words:

        if re.search(
            rf"\b{re.escape(word)}\b",
            question_normalized
        ):
            return "asc"

    return None


# =========================================================
# 15D. DETECT RANKING INTENT
# =========================================================

def detect_ranking_intent(question):

    question_normalized = (
        normalize_text(
            question
        )
    )

    ranking_words = [
        "highest",
        "lowest",
        "maximum",
        "minimum",
        "most",
        "least",
        "best",
        "worst",
        "top",
        "bottom",
        "largest",
        "smallest",
        "greatest",
        "leading"
    ]

    for word in ranking_words:

        if re.search(
            rf"\b{re.escape(word)}\b",
            question_normalized
        ):
            return True

    ranking_phrases = [
        "doing best",
        "doing worst",
        "performing best",
        "performing worst",
        "makes the most",
        "makes the least",
        "sells the most",
        "sells the least",
        "generates the most",
        "generates the least"
    ]

    for phrase in ranking_phrases:

        if phrase in question_normalized:
            return True

    return False


# =========================================================
# 15E. IMPROVE ANALYSIS PLAN
# =========================================================

def improve_analysis_plan(
    plan,
    question,
    df
):

    valid_metrics = {
        "sales",
        "revenue",
        "profit",
        "loss",
        "unsold",
        "price",
        "profit_margin",
        "revenue_per_sale",
        "profit_per_sale"
    }

    metric = (
        normalize_text(
            plan.metric
        )
        if plan.metric
        else None
    )

    # First use explicit human-language metric detection.
    detected_metric = detect_metric(
        question
    )

    if detected_metric in valid_metrics:
        metric = detected_metric

    if metric not in valid_metrics:
        metric = "profit"

    valid_operations = {
        "sum",
        "mean",
        "count",
        "max",
        "min"
    }

    operation = normalize_text(
        plan.operation
    )

    detected_operation = detect_operation(
        question
    )

    if detected_operation in valid_operations:
        operation = detected_operation

    if operation not in valid_operations:
        operation = "sum"

    sort_direction = (
        normalize_text(
            plan.sort_direction
        )
        if plan.sort_direction
        else None
    )

    if sort_direction not in {
        "asc",
        "desc"
    }:

        sort_direction = None

    final_filters = []

    for condition in plan.filters:

        if condition.column not in df.columns:
            continue

        final_filters.append(
            FilterCondition(
                column=condition.column,
                value=str(
                    condition.value
                )
            )
        )

    detected_filters = (
        detect_explicit_filters(
            question,
            df
        )
    )

    for detected in detected_filters:

        replaced = False

        for index, existing in enumerate(
            final_filters
        ):

            if (
                existing.column
                == detected.column
            ):

                final_filters[index] = (
                    detected
                )

                replaced = True
                break

        if not replaced:

            final_filters.append(
                detected
            )

    # Detect grouping from natural language.
    group_by = plan.group_by

    detected_group = detect_group_by(
        question,
        df
    )

    if detected_group is not None:
        group_by = detected_group

    if group_by:

        group_by = group_by.strip()

        if group_by not in df.columns:
            group_by = None

    top_n = plan.top_n

    detected_top_n = (
        detect_top_n(
            question
        )
    )

    if detected_top_n is not None:

        top_n = detected_top_n
        sort_direction = "desc"

    detected_bottom_n = (
        detect_bottom_n(
            question
        )
    )

    if detected_bottom_n is not None:

        top_n = detected_bottom_n
        sort_direction = "asc"

    # -----------------------------------------------------
    # Natural ranking questions
    # -----------------------------------------------------

    ranking_intent = detect_ranking_intent(
        question
    )

    ranking_direction = detect_ranking_direction(
        question
    )

    if ranking_intent:

        if ranking_direction is not None:

            sort_direction = ranking_direction

        if top_n is None:

            top_n = 1

    # -----------------------------------------------------
    # Explicit "highest/lowest X by Y" handling
    # -----------------------------------------------------

    question_normalized = (
        normalize_text(
            question
        )
    )

    # Example:
    # lowest state by revenue
    # highest brand by profit
    # worst product by sales

    ranking_dimension_patterns = {

        "state": [
            "highest state",
            "lowest state",
            "best state",
            "worst state",
            "top state",
            "bottom state",
            "state with the highest",
            "state with the lowest",
            "state with most",
            "state with least"
        ],

        "brand": [
            "highest brand",
            "lowest brand",
            "best brand",
            "worst brand",
            "top brand",
            "bottom brand",
            "brand with the highest",
            "brand with the lowest",
            "brand with most",
            "brand with least"
        ],

        "product": [
            "highest product",
            "lowest product",
            "best product",
            "worst product",
            "top product",
            "bottom product",
            "product with the highest",
            "product with the lowest",
            "product with most",
            "product with least"
        ],

        "city": [
            "highest city",
            "lowest city",
            "best city",
            "worst city",
            "top city",
            "bottom city",
            "city with the highest",
            "city with the lowest",
            "city with most",
            "city with least"
        ],

        "product_series": [
            "highest product series",
            "lowest product series",
            "best product series",
            "worst product series",
            "top product series",
            "bottom product series"
        ]
    }

    for dimension, phrases in (
        ranking_dimension_patterns.items()
    ):

        matched_dimension = False

        for phrase in phrases:

            if phrase in question_normalized:

                if dimension in df.columns:

                    group_by = dimension
                    matched_dimension = True

                break

        if matched_dimension:
            break

    # -----------------------------------------------------
    # Very natural "which X..." questions
    # -----------------------------------------------------

    which_patterns = {

        "state": [
            "which state",
            "what state"
        ],

        "brand": [
            "which brand",
            "what brand"
        ],

        "product": [
            "which product",
            "what product"
        ],

        "city": [
            "which city",
            "what city"
        ],

        "product_series": [
            "which product series",
            "what product series"
        ]
    }

    if ranking_intent:

        for dimension, phrases in (
            which_patterns.items()
        ):

            for phrase in phrases:

                if phrase in question_normalized:

                    if dimension in df.columns:

                        group_by = dimension

                    break

    # -----------------------------------------------------
    # Specific product-selling questions
    # -----------------------------------------------------

    if (
        "most sold product"
        in question_normalized
        or
        "most selling product"
        in question_normalized
        or
        "best selling product"
        in question_normalized
        or
        "highest selling product"
        in question_normalized
        or
        "product sold the most"
        in question_normalized
        or
        "product sells the most"
        in question_normalized
    ):

        metric = "sales"
        group_by = "product"
        top_n = 1
        sort_direction = "desc"

    elif (
        "least sold product"
        in question_normalized
        or
        "least selling product"
        in question_normalized
        or
        "lowest selling product"
        in question_normalized
        or
        "lowest sales product"
        in question_normalized
        or
        "product sold the least"
        in question_normalized
        or
        "product sells the least"
        in question_normalized
    ):

        metric = "sales"
        group_by = "product"
        top_n = 1
        sort_direction = "asc"

    # -----------------------------------------------------
    # Specific price questions
    # -----------------------------------------------------

    if "highest price" in question_normalized:
        metric = "price"
        top_n = 1
        sort_direction = "desc"

    elif "lowest price" in question_normalized:
        metric = "price"
        top_n = 1
        sort_direction = "asc"

    # -----------------------------------------------------
    # Normalize top_n
    # -----------------------------------------------------

    if top_n is not None:

        try:

            top_n = int(
                top_n
            )

            if top_n <= 0:
                top_n = None

        except Exception:

            top_n = None

    return AnalysisPlan(
        operation=operation,
        metric=metric,
        filters=final_filters,
        group_by=group_by,
        sort_direction=sort_direction,
        top_n=top_n
    )


# =========================================================
# 16. FOLLOW-UP CONTEXT
# =========================================================

def resolve_follow_up(
    question,
    previous_plan,
    previous_question,
    df
):

    if previous_plan is None:
        return None

    plan = AnalysisPlan(
        **previous_plan
    )

    top_n = detect_top_n(
        question
    )

    if top_n is not None:

        plan.top_n = top_n
        plan.sort_direction = "desc"

        if previous_question:

            previous_filters = (
                detect_explicit_filters(
                    previous_question,
                    df
                )
            )

            cleaned_filters = []

            for condition in plan.filters:

                was_previous_specific = any(
                    condition.column
                    == previous.column
                    and
                    normalize_text(
                        condition.value
                    )
                    ==
                    normalize_text(
                        previous.value
                    )
                    for previous
                    in previous_filters
                )

                if not was_previous_specific:

                    cleaned_filters.append(
                        condition
                    )

            plan.filters = cleaned_filters

        return plan

    bottom_n = detect_bottom_n(
        question
    )

    if bottom_n is not None:

        plan.top_n = bottom_n
        plan.sort_direction = "asc"

    question_normalized = (
        normalize_text(
            question
        )
    )

    # Update metric if the follow-up explicitly
    # requests another metric.
    detected_metric = detect_metric(
        question
    )

    if detected_metric is not None:
        plan.metric = detected_metric

    detected_group = detect_group_by(
        question,
        df
    )

    if detected_group is not None:
        plan.group_by = detected_group

    detected_filters = (
        detect_explicit_filters(
            question,
            df
        )
    )

    for detected in detected_filters:

        replaced = False

        for index, existing in enumerate(
            plan.filters
        ):

            if (
                existing.column
                == detected.column
            ):

                plan.filters[index] = (
                    detected
                )

                replaced = True
                break

        if not replaced:

            plan.filters.append(
                detected
            )

    # Ranking follow-ups.
    ranking_intent = detect_ranking_intent(
        question
    )

    if ranking_intent:

        ranking_direction = (
            detect_ranking_direction(
                question
            )
        )

        if ranking_direction is not None:

            plan.sort_direction = (
                ranking_direction
            )

        if plan.top_n is None:
            plan.top_n = 1

    # Specific selling questions.
    if (
        "most sold product"
        in question_normalized
        or
        "most selling product"
        in question_normalized
        or
        "best selling product"
        in question_normalized
        or
        "highest selling product"
        in question_normalized
        or
        "product sold the most"
        in question_normalized
        or
        "product sells the most"
        in question_normalized
    ):

        plan.metric = "sales"
        plan.group_by = "product"
        plan.top_n = 1
        plan.sort_direction = "desc"

    elif (
        "least sold product"
        in question_normalized
        or
        "least selling product"
        in question_normalized
        or
        "lowest selling product"
        in question_normalized
        or
        "lowest sales product"
        in question_normalized
        or
        "product sold the least"
        in question_normalized
        or
        "product sells the least"
        in question_normalized
    ):

        plan.metric = "sales"
        plan.group_by = "product"
        plan.top_n = 1
        plan.sort_direction = "asc"

    # Natural "lowest state by revenue", etc.
    detected_group = detect_group_by(
        question,
        df
    )

    if detected_group is not None:
        plan.group_by = detected_group

    return plan


# =========================================================
# CLARIFICATION OPTIONS FOR METRIC-ONLY QUESTIONS
# =========================================================

def show_clarification_options(metric):

    metric_name = {
        "sales": "Sales",
        "revenue": "Revenue",
        "profit": "Profit",
        "loss": "Loss",
        "unsold": "Unsold",
        "price": "Price",
        "profit_margin": "Profit Margin",
        "revenue_per_sale": "Revenue Per Sale",
        "profit_per_sale": "Profit Per Sale"
    }.get(
        metric,
        str(metric).replace(
            "_",
            " "
        ).title()
    )

    st.warning(
        f"What would you like to know about "
        f"{metric_name.lower()}?"
    )

    st.write("Choose an option:")

    col1, col2 = st.columns(2)

    with col1:

        total_clicked = st.button(
            f"Total {metric_name}",
            key=f"clarification_total_{metric}",
            use_container_width=True
        )

        by_product_clicked = st.button(
            f"{metric_name} by product",
            key=f"clarification_product_{metric}",
            use_container_width=True
        )

    with col2:

        by_brand_clicked = st.button(
            f"{metric_name} by brand",
            key=f"clarification_brand_{metric}",
            use_container_width=True
        )

        highest_clicked = st.button(
            f"Highest {metric_name} product",
            key=f"clarification_highest_{metric}",
            use_container_width=True
        )

    if total_clicked:

        return AnalysisPlan(
            operation="sum",
            metric=metric,
            filters=[],
            group_by=None,
            sort_direction=None,
            top_n=None
        )

    if by_product_clicked:

        return AnalysisPlan(
            operation="sum",
            metric=metric,
            filters=[],
            group_by="product",
            sort_direction="desc",
            top_n=None
        )

    if by_brand_clicked:

        return AnalysisPlan(
            operation="sum",
            metric=metric,
            filters=[],
            group_by="brand",
            sort_direction="desc",
            top_n=None
        )

    if highest_clicked:

        return AnalysisPlan(
            operation="sum",
            metric=metric,
            filters=[],
            group_by="product",
            sort_direction="desc",
            top_n=1
        )

    return None


# =========================================================
# EXPLICIT CURRENT QUESTION OVERRIDE
# =========================================================

def apply_current_question_override(
    plan,
    question,
    df
):

    question_normalized = normalize_text(
        question
    )

    detected_group = detect_group_by(
        question,
        df
    )

    if detected_group is not None:
        plan.group_by = detected_group

    detected_metric = detect_metric(
        question
    )

    if detected_metric is not None:
        plan.metric = detected_metric

    detected_top_n = detect_top_n(
        question
    )

    if detected_top_n is not None:

        plan.top_n = detected_top_n
        plan.sort_direction = "desc"

    detected_bottom_n = detect_bottom_n(
        question
    )

    if detected_bottom_n is not None:

        plan.top_n = detected_bottom_n
        plan.sort_direction = "asc"

    ranking_intent = detect_ranking_intent(
        question
    )

    if ranking_intent:

        ranking_direction = (
            detect_ranking_direction(
                question
            )
        )

        if ranking_direction is not None:

            plan.sort_direction = (
                ranking_direction
            )

        if plan.top_n is None:
            plan.top_n = 1

    # Specific selling questions.
    if (
        "most sold product"
        in question_normalized
        or
        "most selling product"
        in question_normalized
        or
        "best selling product"
        in question_normalized
        or
        "highest selling product"
        in question_normalized
        or
        "product sold the most"
        in question_normalized
        or
        "product sells the most"
        in question_normalized
    ):

        plan.metric = "sales"
        plan.group_by = "product"
        plan.top_n = 1
        plan.sort_direction = "desc"

    elif (
        "least sold product"
        in question_normalized
        or
        "least selling product"
        in question_normalized
        or
        "lowest selling product"
        in question_normalized
        or
        "lowest sales product"
        in question_normalized
        or
        "product sold the least"
        in question_normalized
        or
        "product sells the least"
        in question_normalized
    ):

        plan.metric = "sales"
        plan.group_by = "product"
        plan.top_n = 1
        plan.sort_direction = "asc"

    return plan


# =========================================================
# 17. APPLY FILTERS
# =========================================================

def apply_filters(
    df,
    filters
):

    filtered_df = df.copy()

    for condition in filters:

        column = condition.column

        value = normalize_text(
            condition.value
        )

        if column not in filtered_df.columns:
            continue

        mask = (
            filtered_df[column]
            .astype(str)
            .str.strip()
            .str.lower()
            == value
        )

        filtered_df = filtered_df[
            mask
        ]

    return filtered_df


# =========================================================
# 18. CALCULATE METRIC
# =========================================================

def calculate_metric_series(
    df,
    metric
):

    if metric in {
        "sales",
        "revenue",
        "profit",
        "loss",
        "unsold",
        "price"
    }:

        return pd.to_numeric(
            df[metric],
            errors="coerce"
        ).fillna(0)

    if metric == "profit_margin":

        revenue = pd.to_numeric(
            df["revenue"],
            errors="coerce"
        ).fillna(0)

        profit = pd.to_numeric(
            df["profit"],
            errors="coerce"
        ).fillna(0)

        return (
            profit
            .div(
                revenue.replace(
                    0,
                    pd.NA
                )
            )
            .fillna(0)
            * 100
        )

    if metric == "revenue_per_sale":

        revenue = pd.to_numeric(
            df["revenue"],
            errors="coerce"
        ).fillna(0)

        sales = pd.to_numeric(
            df["sales"],
            errors="coerce"
        ).fillna(0)

        return (
            revenue
            .div(
                sales.replace(
                    0,
                    pd.NA
                )
            )
            .fillna(0)
        )

    if metric == "profit_per_sale":

        profit = pd.to_numeric(
            df["profit"],
            errors="coerce"
        ).fillna(0)

        sales = pd.to_numeric(
            df["sales"],
            errors="coerce"
        ).fillna(0)

        return (
            profit
            .div(
                sales.replace(
                    0,
                    pd.NA
                )
            )
            .fillna(0)
        )

    return pd.Series(
        [0] * len(df),
        index=df.index
    )


# =========================================================
# 19. RUN ANALYSIS
# =========================================================

def run_analysis_plan(
    plan,
    df
):

    filtered_df = apply_filters(
        df,
        plan.filters
    )

    matched_rows = len(
        filtered_df
    )

    metric = (
        plan.metric
        or "profit"
    )

    # Safety fallback for datasets that do not
    # actually contain a requested metric.
    if metric not in df.columns and metric not in {
        "profit_margin",
        "revenue_per_sale",
        "profit_per_sale"
    }:

        metric = "profit"

    metric_values = (
        calculate_metric_series(
            filtered_df,
            metric
        )
    )

    if plan.group_by:

        working_df = (
            filtered_df.copy()
        )

        working_df[
            "_metric_value"
        ] = metric_values

        grouped = (
            working_df
            .groupby(
                plan.group_by
            )["_metric_value"]
        )

        if plan.operation == "sum":
            result = grouped.sum()

        elif plan.operation == "mean":
            result = grouped.mean()

        elif plan.operation == "count":
            result = grouped.count()

        elif plan.operation == "max":
            result = grouped.max()

        elif plan.operation == "min":
            result = grouped.min()

        else:
            result = grouped.sum()

        result = result.reset_index()

        result.columns = [
            plan.group_by,
            metric
        ]

        if plan.sort_direction == "asc":

            result = result.sort_values(
                by=metric,
                ascending=True
            )

        else:

            result = result.sort_values(
                by=metric,
                ascending=False
            )

        if plan.top_n:

            result = result.head(
                plan.top_n
            )

        result = result.reset_index(
            drop=True
        )

        return result, matched_rows

    if plan.operation == "sum":
        value = metric_values.sum()

    elif plan.operation == "mean":
        value = metric_values.mean()

    elif plan.operation == "count":
        value = metric_values.count()

    elif plan.operation == "max":
        value = metric_values.max()

    elif plan.operation == "min":
        value = metric_values.min()

    else:
        value = metric_values.sum()

    result = pd.DataFrame(
        {
            metric: [value]
        }
    )

    return result, matched_rows


# =========================================================
# 20. CREATE CHART
# =========================================================

def create_chart(result):

    if len(result.columns) < 2:
        return

    if len(result) == 0:
        return

    x_column = result.columns[0]
    y_column = result.columns[1]

    chart_data = result.copy()

    chart_data = chart_data.sort_values(
        by=y_column,
        ascending=False
    )

    if len(chart_data) > 20:
        chart_data = chart_data.head(20)

    chart_data = chart_data.set_index(
        x_column
    )[[y_column]]

    st.bar_chart(
        chart_data,
        horizontal=True
    )


# =========================================================
# 21. BUSINESS INSIGHTS
# =========================================================

def generate_business_insights(
    question,
    result
):

    result_text = result.to_string(
        index=False
    )

    prompt = (
        "You are a business analyst.\n\n"

        "User question:\n"
        + str(question)

        + "\n\n"

        "Actual calculated result:\n"
        + result_text

        + "\n\n"

        "Generate 3 to 5 concise business insights.\n\n"

        "Rules:\n"
        "- Use only the provided result.\n"
        "- Do not invent numbers.\n"
        "- Do not perform new calculations.\n"
        "- Do not claim facts that are not visible.\n"
        "- Keep the language simple.\n"
        "- Return bullet points only."
    )

    try:

        response = (
            client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
        )

        return response.text.strip()

    except Exception as e:

        return (
            "Could not generate insights: "
            + str(e)
        )


# =========================================================
# 24. GEMINI PLANNER
# =========================================================

def ask_gemini(
    question,
    df,
    previous_question="",
    previous_plan=None,
    previous_result=None
):

    dataset_context = (
        create_dataset_context(
            df
        )
    )

    previous_context = (
        "No previous analysis."
    )

    if previous_question:

        previous_context = (
            "Previous question:\n"
            + str(previous_question)

            + "\n\n"

            "Previous plan:\n"
            + json.dumps(
                previous_plan,
                indent=2
            )

            + "\n\n"

            "Previous result:\n"
            + str(previous_result)
        )

    prompt = (
        "You are the planning component "
        "of an AI Data Analyst.\n\n"

        "Convert the user's question into "
        "a structured analysis plan.\n\n"

        "Do NOT calculate numbers.\n\n"

        "Python performs the actual calculation.\n\n"

        "Dataset:\n"
        + json.dumps(
            dataset_context,
            indent=2
        )

        + "\n\n"

        "Previous conversation:\n"
        + previous_context

        + "\n\n"

        "Current question:\n"
        + str(question)

        + "\n\n"

        "Rules:\n"
        "1. Return ONLY valid JSON.\n"
        "2. No markdown.\n"
        "3. Do not calculate numerical answers.\n"
        "4. Use previous context for follow-up questions.\n"
        "5. Preserve previous metric unless a new metric is requested.\n"
        "6. Preserve previous group_by for top/bottom questions.\n"
        "7. top N = descending + top_n=N.\n"
        "8. bottom N = ascending + top_n=N.\n"
        "9. Most sold product = sales grouped by product, descending, top_n=1.\n"
        "10. Least sold product = sales grouped by product, ascending, top_n=1.\n"
        "11. Highest/lowest/best/worst questions should use the appropriate group_by and ranking direction.\n"
        "12. Questions like 'lowest state by revenue' mean revenue grouped by state, ascending, top_n=1.\n"
        "13. Questions like 'highest brand by profit' mean profit grouped by brand, descending, top_n=1.\n"
        "14. Questions like 'top 5 products by sales' mean sales grouped by product, descending, top_n=5.\n"
        "15. Questions like 'bottom 3 states by revenue' mean revenue grouped by state, ascending, top_n=3.\n"
        "16. Questions like 'what about ASUS' = brand filter ASUS while preserving analysis.\n"
        "17. group_by MUST be a string or null.\n"
        "18. filters MUST be an array.\n"
        "19. top_n MUST be a number or null.\n"
        "20. Use only actual dataset columns.\n\n"

        "Allowed operations:\n"
        "sum\n"
        "mean\n"
        "count\n"
        "max\n"
        "min\n\n"

        "Allowed metrics:\n"
        "sales\n"
        "revenue\n"
        "profit\n"
        "loss\n"
        "unsold\n"
        "price\n"
        "profit_margin\n"
        "revenue_per_sale\n"
        "profit_per_sale\n\n"

        "Return JSON in this format:\n"

        "{\n"
        '  "operation": "sum",\n'
        '  "metric": "profit",\n'
        '  "filters": [],\n'
        '  "group_by": "brand",\n'
        '  "sort_direction": "desc",\n'
        '  "top_n": 3\n'
        "}"
    )

    try:

        response = (
            client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
        )

        cleaned = clean_json_response(
            response.text
        )

        raw_data = json.loads(
            cleaned
        )

        data = normalize_gemini_plan(
            raw_data
        )

        return AnalysisPlan(
            **data
        )

    except Exception as e:

        st.error(
            "Gemini planning error: "
            + str(e)
        )

        return None