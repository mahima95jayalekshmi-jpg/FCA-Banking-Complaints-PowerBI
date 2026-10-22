-- Data quality checks. Checks 2-6 should return 0 or no rows.
-- Anything else is investigated and documented in the README.
-- (etl/load_fca.py also checks that product columns add up to the FCA Grand Total.)

-- 1. Coverage: rows and firms per period
SELECT period_label,
       COUNT(*)                  AS rows_loaded,
       COUNT(DISTINCT firm_name) AS firms,
       SUM(opened)               AS total_opened
FROM stg_complaints
GROUP BY period_label
ORDER BY period_label;

-- 2. Duplicate period-firm-product keys
SELECT period_label, firm_name, product_group, COUNT(*) AS records
FROM stg_complaints
GROUP BY period_label, firm_name, product_group
HAVING COUNT(*) > 1;

-- 3. Percentages outside 0-100
SELECT COUNT(*) AS bad_percentages
FROM stg_complaints
WHERE pct_closed_3_days  NOT BETWEEN 0 AND 100
   OR pct_closed_8_weeks NOT BETWEEN 0 AND 100
   OR pct_upheld         NOT BETWEEN 0 AND 100;

-- 4. Closed within 3 days + within 8 weeks cannot exceed 100%
SELECT COUNT(*) AS timeliness_over_100
FROM stg_complaints
WHERE COALESCE(pct_closed_3_days, 0) + COALESCE(pct_closed_8_weeks, 0) > 100.5;  -- 0.5 allows for rounding

-- 5. Negative counts
SELECT COUNT(*) AS negative_counts
FROM stg_complaints
WHERE opened < 0 OR closed < 0;

-- 6. Reference rows that matched nothing (a renamed group would silently drop out)
SELECT r.match_on, r.match_value, r.banking_group
FROM ref_banking_groups r
WHERE NOT EXISTS (
    SELECT 1 FROM dim_firm f
    WHERE (r.match_on = 'group' AND f.fca_group = r.match_value)
       OR (r.match_on = 'firm'  AND f.firm_name = r.match_value)
);

-- 7. Missing measures (expected for some products, e.g. no accounts figure)
SELECT SUM(opened IS NULL)              AS missing_opened,
       SUM(closed IS NULL)              AS missing_closed,
       SUM(pct_upheld IS NULL)          AS missing_upheld,
       SUM(complaints_per_1000 IS NULL) AS missing_context
FROM stg_complaints;

-- 8. Firms whose 6-month window is not the calendar half-year
SELECT period_label, reporting_period, COUNT(DISTINCT firm_name) AS firms
FROM stg_complaints
GROUP BY period_label, reporting_period
ORDER BY period_label, firms DESC;

-- 9. Peer banks and the firms mapped to each (review by eye)
SELECT banking_group, segment, GROUP_CONCAT(firm_name, ' | ') AS firms
FROM dim_firm
WHERE is_peer_bank = 1
GROUP BY banking_group, segment
ORDER BY segment, banking_group;

-- 10. Firms missing from some periods (name changes, mergers, or falling
--     below the FCA's 500-complaint publication threshold)
SELECT firm_name,
       COUNT(DISTINCT period_label) AS periods_present,
       (SELECT COUNT(DISTINCT period_label) FROM stg_complaints) AS periods_total
FROM stg_complaints
GROUP BY firm_name
HAVING COUNT(DISTINCT period_label) < (SELECT COUNT(DISTINCT period_label) FROM stg_complaints)
ORDER BY periods_present;
