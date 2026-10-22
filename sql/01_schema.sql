-- UK Bank Complaints Analysis: star schema
-- Written for SQLite. The same SQL runs on SQL Server or PostgreSQL with minor type changes.
--
-- Staging tables are loaded by etl/load_fca.py: one row per half-year x firm x product,
-- exactly as published by the FCA, before any modelling.

DROP TABLE IF EXISTS stg_complaints;
CREATE TABLE stg_complaints (
    period_label        TEXT    NOT NULL,   -- FCA publication period, e.g. '2026 H1'
    firm_name           TEXT    NOT NULL,   -- as published by the FCA
    fca_group           TEXT,               -- FCA 'Group' column, e.g. 'LLOYDS BANKING GROUP PLC'
    joint_reporting     TEXT,               -- 'yes' if the return includes other firms
    reporting_period    TEXT,               -- the firm's own 6-month window, e.g. '2026-01-01 to 2026-06-30'
    product_group       TEXT    NOT NULL,   -- e.g. 'Banking and credit cards'
    opened              INTEGER,            -- complaints opened
    closed              INTEGER,            -- complaints closed
    pct_closed_3_days   REAL,               -- % of closed complaints closed within 3 days (0-100)
    pct_closed_8_weeks  REAL,               -- % closed after 3 days but within 8 weeks (0-100)
    pct_upheld          REAL,               -- % of closed complaints upheld (0-100)
    complaints_per_1000 REAL,               -- FCA context figure: per 1,000 accounts or policies
    context_basis       TEXT,               -- 'Provision' or 'Intermediation'
    source_file         TEXT    NOT NULL
);

-- Consumer credit complaints are a separate FCA return with fewer measures.
DROP TABLE IF EXISTS stg_consumer_credit;
CREATE TABLE stg_consumer_credit (
    period_label     TEXT NOT NULL,
    firm_name        TEXT NOT NULL,
    fca_group        TEXT,
    reporting_period TEXT,
    received         INTEGER,
    closed           INTEGER,
    pct_upheld       REAL,                  -- 0-100
    source_file      TEXT NOT NULL
);

DROP TABLE IF EXISTS ref_banking_groups;
CREATE TABLE ref_banking_groups (
    match_on      TEXT NOT NULL,            -- 'group' (FCA Group column) or 'firm' (firm name)
    match_value   TEXT NOT NULL,
    banking_group TEXT NOT NULL,            -- display name used in the report
    segment       TEXT NOT NULL
);

-- ---------------------------------------------------------------
-- Dimensions
-- ---------------------------------------------------------------
DROP TABLE IF EXISTS dim_period;
CREATE TABLE dim_period (
    period_id     INTEGER PRIMARY KEY,      -- 1 = earliest half-year, increasing
    period_label  TEXT NOT NULL UNIQUE,
    year          INTEGER NOT NULL,
    half          TEXT NOT NULL,            -- 'H1' or 'H2'
    period_start  TEXT NOT NULL,            -- ISO date of the FCA publication half-year
    period_end    TEXT NOT NULL
);

DROP TABLE IF EXISTS dim_firm;
CREATE TABLE dim_firm (
    firm_id       INTEGER PRIMARY KEY,
    firm_name     TEXT NOT NULL UNIQUE,
    fca_group     TEXT,
    banking_group TEXT NOT NULL,
    segment       TEXT NOT NULL,            -- 'Other' when not in ref_banking_groups
    is_peer_bank  INTEGER NOT NULL          -- 1 for high-street banks, digital banks and building societies
);

DROP TABLE IF EXISTS dim_product;
CREATE TABLE dim_product (
    product_id    INTEGER PRIMARY KEY,
    product_group TEXT NOT NULL UNIQUE
);

-- ---------------------------------------------------------------
-- Fact
-- Percentages are converted back to counts so that any total
-- (by bank, group, product or period) is a ratio of sums, never
-- an average of percentages.
-- ---------------------------------------------------------------
DROP TABLE IF EXISTS fact_complaints;
CREATE TABLE fact_complaints (
    period_id                 INTEGER NOT NULL REFERENCES dim_period(period_id),
    firm_id                   INTEGER NOT NULL REFERENCES dim_firm(firm_id),
    product_id                INTEGER NOT NULL REFERENCES dim_product(product_id),
    reporting_period          TEXT,
    opened                    INTEGER,
    closed                    INTEGER,
    closed_within_3_days      REAL,
    closed_within_8_weeks     REAL,     -- includes those closed within 3 days
    upheld                    REAL,
    opened_with_context       INTEGER,  -- opened, but only where an accounts figure exists
    implied_accounts          REAL,     -- opened / complaints_per_1000 * 1000
    PRIMARY KEY (period_id, firm_id, product_id)
);
