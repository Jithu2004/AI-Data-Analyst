# AI Data Analyst

An AI-powered data analysis application built with Python, Streamlit, Pandas, and Google Gemini.

## Project Structure

```text
AI_Data_Analyst/
│
├── README.md
├── app.py
├── config.py
├── models.py
├── data_utils.py
├── analysis.py
├── reports.py
├── .env
└── requirements.txt
```

## Features

- Upload CSV and Excel datasets
- Ask questions about data using natural language
- Use Google Gemini for natural-language understanding
- Convert questions into structured analysis plans
- Perform calculations using Pandas
- Generate charts
- Generate business insights
- Support filtering, grouping, ranking, and top/bottom analysis
- Support follow-up questions
- Maintain conversation history
- Generate Word reports

## Core Principle

> **AI understands the question. Python calculates the answer.**

Gemini understands the user's question and creates structured analysis instructions. Python/Pandas performs the actual numerical calculations on the dataset.

## Architecture

```text
User Question
      ↓
Streamlit
      ↓
Gemini AI
      ↓
Structured Analysis Plan
      ↓
Python / Pandas
      ↓
Actual Calculation
      ↓
Result + Chart
      ↓
Business Insights
      ↓
Word Report
```

## File Description

### `app.py`
Main Streamlit application and entry point. Handles the UI, file upload, questions, results, charts, insights, conversation history, and connects all modules.

### `config.py`
Handles environment variables, Gemini API configuration, Gemini client creation, and model configuration.

### `models.py`
Contains structured Pydantic models such as `FilterCondition` and `AnalysisPlan`.

### `data_utils.py`
Contains dataset utilities including file reading, text normalization, DataFrame normalization, schema validation, dataset context creation, and filter detection.

### `analysis.py`
Contains the core analysis logic including intent detection, metrics, operations, grouping, filtering, ranking, calculations, charts, business insights, and Gemini analysis planning.

### `reports.py`
Handles Word report generation, including analysis results, charts, insights, and previous Q&A.

### `.env`
Stores the Gemini API key. Do not upload `.env` to GitHub.

Example:

```text
GEMINI_API_KEY=your_api_key_here
```

### `requirements.txt`
Contains the Python dependencies required by the project.

## Example Questions

```text
What is the total profit?
What is profit by brand?
What is revenue by state?
Which state has the highest revenue?
Which state has the lowest profit?
What is the total sales for ASUS?
Show profit by product.
Which product generated the highest revenue?
Show the top 5 brands by profit.
Show the bottom 5 products by revenue.
```

# Example Results & Charts

The application converts natural-language questions into structured analysis plans, performs the actual calculation with Python/Pandas, and then displays the result with visualizations and AI-generated business insights.

## Example 1 — Profit by Brand

### User Question

```text
What is profit by brand?
```

### Analysis Plan

```text
🔎 Analysis Plan

Metric: profit
Operation: sum
Grouped by: brand

Filters applied:
None
```

### Example Result

```text
Profit by Brand

ASUS       ₹62,455,173.64
Lenovo     ₹60,231,845.20
HP         ₹58,917,432.15
Dell       ₹57,823,901.44
Acer       ₹54,672,318.73
```

### Example Chart

The application can display the result as a bar chart comparing profit across brands.

> **Note:** The values above are illustrative README examples and should not be treated as actual dataset results unless they are produced by the application from the dataset.

## Example 2 — Monthly Revenue

### User Question

```text
Show monthly revenue.
```

### Example Result

```text
Monthly Revenue

Apr 2025    ₹XXX,XXX,XXX
May 2025    ₹XXX,XXX,XXX
Jun 2025    ₹XXX,XXX,XXX
Jul 2025    ₹XXX,XXX,XXX
...
```

### Example Chart

The application can generate a line chart showing how revenue changes over time.

```text
Revenue
  │
  │             ●
  │       ●    / \
  │   ●  / \  /   ●
  │  / \/
  │ ●
  └────────────────────
    Apr  May  Jun  Jul
```

## Example 3 — Highest Revenue State

### User Question

```text
Which state has the highest revenue?
```

### Example Result

```text
Top State by Revenue
--------------------
State: Telangana
Revenue: ₹XXX,XXX,XXX
```

The application can also display a ranked bar chart showing revenue by state.

## Example 4 — Top 5 Brands by Profit

### User Question

```text
Show the top 5 brands by profit.
```

### Example Result

```text
Top 5 Brands by Profit

1. ASUS
2. Lenovo
3. HP
4. Dell
5. Acer
```

A ranked bar chart can be generated automatically from the calculated Pandas result.

## Example 5 — Business Insights

After calculating the result, the application can generate AI-assisted business insights such as:

```text
💡 Business Insights

• ASUS generated the highest total profit among the displayed brands.
• The difference between the top-performing and lowest-performing brands
  indicates variation in profitability across brands.
• Further investigation can focus on product and state-level performance.
```

These insights are generated after the numerical result has been calculated by Python/Pandas.

## Complete Example Flow

```text
User Question
      │
      ▼
"What is profit by brand?"
      │
      ▼
Gemini understands the question
      │
      ▼
Analysis Plan
      │
      ├── Metric: profit
      ├── Operation: sum
      └── Group By: brand
      │
      ▼
Python / Pandas
      │
      ▼
Actual Calculation
      │
      ▼
Result
      │
      ├── Table / Values
      ├── Chart
      └── AI Business Insights
      │
      ▼
Optional Word Report
```

## Technologies

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| Streamlit | Web application UI |
| Pandas | Data processing and calculations |
| Google Gemini | Natural-language understanding and business insights |
| Pydantic | Structured analysis plans |
| Matplotlib | Data visualization |
| OpenPyXL | Excel file support |
| python-docx | Word report generation |
| python-dotenv | Environment variable management |

## Installation

### Create a virtual environment

```bash
python -m venv venv
```

### Windows activation

```powershell
venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Configure Gemini API

Create `.env`:

```text
GEMINI_API_KEY=your_api_key_here
```

### Run the application

```bash
streamlit run app.py
```

## Data Flow

```text
1. Upload Dataset
        ↓
2. Read Dataset
        ↓
3. Validate Dataset
        ↓
4. User Asks Question
        ↓
5. Understand User Intent
        ↓
6. Create Analysis Plan
        ↓
7. Validate / Improve Plan
        ↓
8. Apply Filters
        ↓
9. Calculate Using Pandas
        ↓
10. Display Result
        ↓
11. Generate Chart
        ↓
12. Generate Business Insights
        ↓
13. Generate Report
```

## Project Goal

This project demonstrates how Generative AI can be combined with traditional data-analysis tools while keeping numerical calculations deterministic.

## Future Improvements

- Support for multiple datasets
- Automatic dataset relationship detection
- More advanced visualizations
- SQL-based analysis
- Advanced anomaly detection
- Automated dashboard generation
- More complex business questions
- User authentication
- Database connectivity
- Cloud deployment
