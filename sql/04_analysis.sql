-- Analysis queries on the star schema. Each answers one question in the README.
-- Rates are ratios of summed counts, so they are correct at any level of grouping.


-- Q1. Which banks have the highest complaint rates for banking and credit cards
--     in the latest half-year, and how did each move since the previous one?
WITH bank_period AS (
    SELECT f.banking_group,
           p.period_id,
           p.period_label,
           SUM(c.opened)                                       AS opened,
           1000.0 * SUM(c.opened_with_context) / SUM(c.implied_accounts)    AS per_1000,
           100.0  * SUM(c.upheld) / SUM(c.closed)              AS pct_upheld
    FROM fact_complaints c
    JOIN dim_firm    f ON f.firm_id    = c.firm_id
    JOIN dim_period  p ON p.period_id  = c.period_id
    JOIN dim_product d ON d.product_id = c.product_id
    WHERE f.is_peer_bank = 1
      AND d.product_group LIKE 'Banking%'
    GROUP BY f.banking_group, p.period_id, p.period_label
),
with_change AS (
    SELECT *,
           LAG(per_1000)   OVER (PARTITION BY banking_group ORDER BY period_id) AS prev_per_1000,
           LAG(pct_upheld) OVER (PARTITION BY banking_group ORDER BY period_id) AS prev_pct_upheld
    FROM bank_period
)
SELECT RANK() OVER (ORDER BY per_1000 DESC)       AS rank_highest_first,
       banking_group,
       opened,
       ROUND(per_1000, 2)                          AS complaints_per_1000,
       ROUND(per_1000 - prev_per_1000, 2)          AS change_per_1000,
       ROUND(pct_upheld, 1)                        AS pct_upheld,
       ROUND(pct_upheld - prev_pct_upheld, 1)      AS change_upheld_pts
FROM with_change
WHERE period_id = (SELECT MAX(period_id) FROM dim_period)
ORDER BY rank_highest_first;


-- Q2. Trend: complaint rate for each of the big five banking groups by half-year
SELECT p.period_label,
       f.banking_group,
       ROUND(1000.0 * SUM(c.opened_with_context) / SUM(c.implied_accounts), 2) AS complaints_per_1000,
       ROUND(100.0 * SUM(c.upheld) / SUM(c.closed), 1)            AS pct_upheld
FROM fact_complaints c
JOIN dim_firm    f ON f.firm_id    = c.firm_id
JOIN dim_period  p ON p.period_id  = c.period_id
JOIN dim_product d ON d.product_id = c.product_id
WHERE f.banking_group IN ('HSBC', 'Barclays', 'Lloyds Banking Group', 'NatWest Group', 'Santander UK')
  AND d.product_group LIKE 'Banking%'
GROUP BY p.period_id, p.period_label, f.banking_group
ORDER BY f.banking_group, p.period_id;


-- Q3. Digital banks vs high-street banks: complaint rate, % upheld, timeliness
SELECT p.period_label,
       f.segment,
       COUNT(DISTINCT f.banking_group)                                   AS groups,
       ROUND(1000.0 * SUM(c.opened_with_context) / SUM(c.implied_accounts), 2)         AS complaints_per_1000,
       ROUND(100.0 * SUM(c.upheld) / SUM(c.closed), 1)                    AS pct_upheld,
       ROUND(100.0 * SUM(c.closed_within_8_weeks) / SUM(c.closed), 1)     AS pct_closed_8_weeks
FROM fact_complaints c
JOIN dim_firm    f ON f.firm_id    = c.firm_id
JOIN dim_period  p ON p.period_id  = c.period_id
JOIN dim_product d ON d.product_id = c.product_id
WHERE f.segment IN ('High-street bank', 'Digital bank')
  AND d.product_group LIKE 'Banking%'
GROUP BY p.period_id, p.period_label, f.segment
ORDER BY p.period_id, f.segment;


-- Q4. Outliers: banks above the peer average on BOTH complaint rate and % upheld
--     in the latest period (the top-right quadrant of the Power BI scatter)
WITH latest AS (
    SELECT f.banking_group,
           SUM(c.opened_with_context) AS opened, SUM(c.implied_accounts) AS accounts,
           SUM(c.upheld) AS upheld, SUM(c.closed) AS closed
    FROM fact_complaints c
    JOIN dim_firm    f ON f.firm_id    = c.firm_id
    JOIN dim_product d ON d.product_id = c.product_id
    WHERE f.is_peer_bank = 1
      AND d.product_group LIKE 'Banking%'
      AND c.period_id = (SELECT MAX(period_id) FROM dim_period)
    GROUP BY f.banking_group
),
peer AS (
    SELECT 1000.0 * SUM(opened) / SUM(accounts) AS peer_per_1000,
           100.0  * SUM(upheld) / SUM(closed)   AS peer_pct_upheld
    FROM latest
)
SELECT l.banking_group,
       ROUND(1000.0 * l.opened / l.accounts, 2) AS complaints_per_1000,
       ROUND(peer.peer_per_1000, 2)             AS peer_per_1000,
       ROUND(100.0 * l.upheld / l.closed, 1)    AS pct_upheld,
       ROUND(peer.peer_pct_upheld, 1)           AS peer_pct_upheld
FROM latest l CROSS JOIN peer
WHERE 1000.0 * l.opened / l.accounts > peer.peer_per_1000
  AND 100.0  * l.upheld / l.closed   > peer.peer_pct_upheld
ORDER BY complaints_per_1000 DESC;


-- Q5. Which product groups drive complaints across all peer banks?
SELECT d.product_group,
       SUM(c.opened)                                                       AS opened,
       ROUND(100.0 * SUM(c.opened) / SUM(SUM(c.opened)) OVER (), 1)        AS share_of_all_pct,
       ROUND(100.0 * SUM(c.upheld) / SUM(c.closed), 1)                     AS pct_upheld
FROM fact_complaints c
JOIN dim_firm    f ON f.firm_id    = c.firm_id
JOIN dim_product d ON d.product_id = c.product_id
WHERE f.is_peer_bank = 1
  AND c.period_id = (SELECT MAX(period_id) FROM dim_period)
GROUP BY d.product_group
ORDER BY opened DESC;


-- Q6. Timeliness: share of complaints resolved within the 8-week regulatory deadline
--     (after 8 weeks the customer can go to the Financial Ombudsman)
SELECT f.banking_group,
       f.segment,
       SUM(c.closed)                                                    AS closed,
       ROUND(100.0 * SUM(c.closed_within_3_days)  / SUM(c.closed), 1)   AS pct_within_3_days,
       ROUND(100.0 * SUM(c.closed_within_8_weeks) / SUM(c.closed), 1)   AS pct_within_8_weeks,
       ROUND(SUM(c.closed) - SUM(c.closed_within_8_weeks))              AS closed_after_8_weeks
FROM fact_complaints c
JOIN dim_firm    f ON f.firm_id    = c.firm_id
JOIN dim_product d ON d.product_id = c.product_id
WHERE f.is_peer_bank = 1
  AND d.product_group LIKE 'Banking%'
  AND c.period_id = (SELECT MAX(period_id) FROM dim_period)
GROUP BY f.banking_group, f.segment
ORDER BY pct_within_8_weeks;
