# UK Banking Complaints Analysis | FCA Power BI Dashboard

**End-to-End Financial Services Data Analytics Portfolio Project**

## Project Overview

This project analyses UK financial services complaints data published by the Financial Conduct Authority (FCA).

It combines **Python, SQL, SQLite and Power BI** to investigate complaint volumes, customer complaint outcomes, banking group performance and complaint resolution efficiency.

The project includes an interactive three-page Power BI dashboard, supporting data-processing scripts, SQL queries and data quality checks.

**Tools:** Python | Pandas | SQL | SQLite | Power BI | DAX | Matplotlib | Excel

**Data source:** [FCA Firm-Level Complaints Data](https://www.fca.org.uk/data/complaints-data/firm-level)

**Reporting period:** 2026 H1, as labelled in the project dataset (pending source verification)

**Power BI file:** [Download Interactive Dashboard](FCA_Banking_Complaints_Dashboard.pbix)

---

## 1. Interactive Power BI Dashboard

The dashboard contains three interactive report pages.

### Page 1 — Overview

![Power BI Overview Dashboard](Screenshot%202026-10-22%20200401.png)

**Features:**
- Total complaints opened and closed
- Complaints closed within 3 days
- Complaints closed within 8 weeks
- Complaints opened by banking group
- Complaint volumes and resolution activity by product group
- Interactive Banking Group selector

**Business purpose:** Provide a high-level overview of complaint activity and operational performance.

### Page 2 — Bank Comparison

![Bank Comparison Dashboard](images/Bank%20Comparison.png)

**Features:**
- Complaint rates per 1,000 accounts
- Percentage of complaints upheld
- Percentage of complaints resolved within 8 weeks
- Banking group comparisons
- Interactive Banking Group filter

**Business purpose:** Compare customer complaint outcomes and identify differences in performance across banking groups.

### Page 3 — Complaint Resolution

![Complaint Resolution Dashboard](images/Complaint%20Resolution.png)

**Features:**
- Percentage of complaints resolved within 3 days
- Percentage of complaints resolved within 8 weeks
- Three-day resolution rates by product category
- Interactive Banking Group selector

**Business purpose:** Analyse resolution efficiency and highlight differences in complaint handling.

---

## 2. Business Questions

The project explores:

1. Which banking groups receive the highest complaint volumes?
2. How do complaint rates vary between banks?
3. Which banking groups uphold the highest percentages of complaints?
4. How quickly are complaints resolved?
5. Which financial product categories have different complaint patterns?
6. How can complaint data help businesses identify operational improvement opportunities?

---

## 3. Key Analytical Findings

The following figures were observed in the project's processed dataset and Power BI dashboard. They should be verified against the original FCA source files before being described as independently confirmed regulatory findings.

### Complaint Rate Analysis

For the selected banking and credit card category, Lloyds Banking Group has a calculated rate of **2.77 complaints per 1,000 accounts**.

### Complaints Upheld

The analysed data shows a **65.2% upheld complaint rate** for Lloyds Banking Group.

An upheld percentage indicates complaint outcomes reported by the firm. It should not be used alone to judge overall service quality.

### Complaint Resolution Performance

| KPI | Lloyds Banking Group |
|---|---:|
| Complaint rate per 1,000 accounts | 2.77 |
| Complaints upheld | 65.2% |
| Resolved within 3 days | 55.96% |
| Resolved within 8 weeks | 86.4% |

### Product Category Differences

The analysis compares financial product groups, including:

- Banking and credit cards
- Insurance and pure protection
- Home finance
- Investments
- Decumulation and pensions

Resolution rates and complaint volumes vary across product groups, suggesting areas for further operational investigation.

---

## 4. Technical Workflow

The project follows an end-to-end analytical workflow:

**FCA Excel Files → Python ETL → SQLite Database → SQL Data Model → Power BI Dashboard**

### Step 1 — Data Collection

Publicly available FCA firm-level complaints data is used as the source.

The dataset includes complaint measures, firm information, reporting periods and financial product categories.

### Step 2 — Data Preparation Using Python

**Script:** `etl/load_fca.py`

The Python workflow supports:

- Loading Excel source files
- Reshaping wide-format data
- Standardising data fields
- Handling missing and inconsistent information
- Preparing complaint measures
- Exporting structured records for SQL analysis

**Libraries:** Pandas and other dependencies listed in `requirements.txt`.

### Step 3 — Data Modelling Using SQL

The project uses SQLite and SQL scripts to organise data for reporting.

The star-schema model includes:

| Table | Purpose |
|---|---|
| `fact_complaints` | Complaint counts and measures |
| `dim_firm` | Firm and banking group information |
| `dim_product` | Financial product categories |
| `dim_period` | Reporting period information |

Supporting scripts include:

- `01_schema.sql` — Defines database structures
- `02_build_model.sql` — Builds the reporting model
- `03_quality_checks.sql` — Contains data validation checks
- `04_analysis.sql` — Contains analytical queries

### Step 4 — Analytical Queries

SQL is used to support analysis of complaint volumes, rates, upheld outcomes and resolution performance.

The project includes techniques such as:

- Joins
- Aggregation
- Common Table Expressions (CTEs)
- Window functions
- Banking group comparisons
- Performance benchmarking

### Step 5 — Power BI Visualisation

Power BI is used to create the interactive report.

DAX measures support calculations including:

- Complaint rate per 1,000 accounts
- Complaints upheld percentage
- Resolved within 3 days percentage
- Resolved within 8 weeks percentage

Banking Group slicers enable users to interact with the report and explore individual banking groups.

---

## 5. Data Quality Checks

The repository includes SQL-based validation checks designed to assess data accuracy and consistency.

| Check | Purpose |
|---|---|
| Duplicate records | Identify duplicate firm-product-period records |
| Missing values | Detect incomplete data |
| Percentage validation | Identify percentages outside valid ranges |
| Negative counts | Detect invalid complaint volumes |
| Total reconciliation | Compare product totals with reported grand totals |
| Reference mapping checks | Identify unmatched firm or banking group references |
| Reporting-period checks | Identify inconsistent reporting windows |

SQL scripts and saved analysis outputs are provided in the repository.

---

## 6. Repository Structure

```text
FCA-Banking-Complaints-PowerBI/
│
├── FCA_Banking_Complaints_Dashboard.pbix
├── README.md
├── requirements.txt
├── create_dashboard.py
├── Screenshot 2026-10-22 200401.png
│
├── data/
│   ├── raw/
│   └── reference/
│       └── banking_groups.csv
│
├── etl/
│   └── load_fca.py
│
├── sql/
│   ├── 01_schema.sql
│   ├── 02_build_model.sql
│   ├── 03_quality_checks.sql
│   └── 04_analysis.sql
│
├── powerbi/
│   ├── data/
│   ├── dax_measures.md
│   ├── report_layout.md
│   └── theme.json
│
├── results/
│
└── images/
    ├── Bank Comparison.png
    ├── Complaint Resolution.png
    ├── consumer_duty.png
    └── overview.png
```

The structure summarises the project folders and supporting files. Some nested files or generated outputs may vary.

---

## 7. How to Run the Project

### Requirements

- Python 3
- SQLite
- Power BI Desktop
- Project dependencies listed in `requirements.txt`

### Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Run Data Preparation

```bash
python etl/load_fca.py
```

### Generate Static Analysis Charts

```bash
python create_dashboard.py
```

The scripts require the corresponding input files and project dependencies.

### Open the Power BI Report

1. Download `FCA_Banking_Complaints_Dashboard.pbix`.
2. Open it using Microsoft Power BI Desktop.
3. Explore the Overview page.
4. Compare banking groups on the Bank Comparison page.
5. Examine resolution performance on the Complaint Resolution page.
6. Use the interactive slicers to filter the visuals.

---

## 8. Additional Consumer Duty Analysis

![Consumer Duty Analysis](images/consumer_duty.png)

The repository contains a supplementary static analysis visualisation related to complaint-handling performance and FCA Consumer Duty considerations.

This visualisation is separate from the three-page Power BI report.

---

## 9. Business Value

This project demonstrates how data analysis can help financial services organisations:

- Monitor customer complaint volumes
- Track complaint outcomes
- Compare banking group performance
- Measure complaint resolution efficiency
- Identify areas requiring further investigation
- Support KPI reporting
- Improve evidence-based business decision-making

The analytical approach is relevant to customer operations, financial services analytics and business performance reporting.

---

## 10. Skills Demonstrated

### Technical Skills

- Python and Pandas
- SQL and SQLite
- Power BI and DAX
- Data cleaning and preparation
- Data modelling
- Data quality validation
- Data visualisation
- Dashboard development

### Business and Analytical Skills

- KPI development
- Financial services analytics
- Customer complaints analysis
- Performance monitoring
- Comparative analysis
- Business reporting
- Insight communication

---

## 11. Limitations

- Complaints information is submitted by financial firms.
- Reporting windows may differ between institutions.
- Complaint volumes can be influenced by institution size.
- Complaint rates should be compared within consistent product categories.
- Upheld percentages do not necessarily include subsequent ombudsman decisions.
- Resolution percentages should not automatically be interpreted as evidence of regulatory non-compliance.
- Reporting periods and analytical results should be checked against original FCA source files before external use.

---

## 12. Data Source and Attribution

**Financial Conduct Authority (FCA)**

[FCA Firm-Level Complaints Data](https://www.fca.org.uk/data/complaints-data/firm-level)

This is an independent data analytics portfolio project and is not an official FCA publication.
