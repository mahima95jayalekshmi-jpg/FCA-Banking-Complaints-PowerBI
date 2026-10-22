-- Builds the star schema from the staging tables.
-- Run after etl/load_fca.py has filled stg_complaints and ref_banking_groups.

-- Periods: '2026 H1' -> 1 Jan - 30 Jun 2026
INSERT INTO dim_period (period_id, period_label, year, half, period_start, period_end)
SELECT ROW_NUMBER() OVER (ORDER BY period_label) AS period_id,
       period_label,
       CAST(SUBSTR(period_label, 1, 4) AS INTEGER),
       SUBSTR(period_label, 6, 2),
       SUBSTR(period_label, 1, 4) || CASE SUBSTR(period_label, 6, 2) WHEN 'H1' THEN '-01-01' ELSE '-07-01' END,
       SUBSTR(period_label, 1, 4) || CASE SUBSTR(period_label, 6, 2) WHEN 'H1' THEN '-06-30' ELSE '-12-31' END
FROM (SELECT DISTINCT period_label FROM stg_complaints);

-- Firms: a firm-name match takes priority over an FCA-group match.
-- Firms not in the reference table keep their FCA group as the banking group
-- (or their own name when the FCA lists them as 'NO GROUP').
-- Each firm takes its group from the most recent period, so history is shown
-- under current ownership (e.g. Co-operative Bank under Coventry Building Society).
WITH firms AS (
    SELECT firm_name, fca_group
    FROM (
        SELECT firm_name, fca_group,
               ROW_NUMBER() OVER (PARTITION BY firm_name ORDER BY period_label DESC) AS rn
        FROM (SELECT DISTINCT firm_name, fca_group, period_label FROM stg_complaints)
    )
    WHERE rn = 1
),
matched AS (
    SELECT f.firm_name,
           f.fca_group,
           COALESCE(rf.banking_group, rg.banking_group) AS banking_group,
           COALESCE(rf.segment,       rg.segment)       AS segment
    FROM firms f
    LEFT JOIN ref_banking_groups rf ON rf.match_on = 'firm'  AND rf.match_value = f.firm_name
    LEFT JOIN ref_banking_groups rg ON rg.match_on = 'group' AND rg.match_value = f.fca_group
)
INSERT INTO dim_firm (firm_id, firm_name, fca_group, banking_group, segment, is_peer_bank)
SELECT ROW_NUMBER() OVER (ORDER BY firm_name),
       firm_name,
       fca_group,
       COALESCE(banking_group,
                CASE WHEN fca_group IS NULL OR fca_group = 'NO GROUP' THEN firm_name ELSE fca_group END),
       COALESCE(segment, 'Other'),
       CASE WHEN segment IN ('High-street bank', 'Digital bank', 'Building society') THEN 1 ELSE 0 END
FROM matched;

INSERT INTO dim_product (product_id, product_group)
SELECT ROW_NUMBER() OVER (ORDER BY product_group), product_group
FROM (SELECT DISTINCT product_group FROM stg_complaints);

INSERT INTO fact_complaints
SELECT p.period_id,
       f.firm_id,
       d.product_id,
       s.reporting_period,
       s.opened,
       s.closed,
       s.closed * s.pct_closed_3_days / 100.0,
       s.closed * (COALESCE(s.pct_closed_3_days, 0) + COALESCE(s.pct_closed_8_weeks, 0)) / 100.0,
       s.closed * s.pct_upheld / 100.0,
       CASE WHEN s.complaints_per_1000 > 0 THEN s.opened END,
       CASE WHEN s.complaints_per_1000 > 0 THEN s.opened * 1000.0 / s.complaints_per_1000 END
FROM stg_complaints s
JOIN dim_period  p ON p.period_label  = s.period_label
JOIN dim_firm    f ON f.firm_name     = s.firm_name
JOIN dim_product d ON d.product_group = s.product_group;
