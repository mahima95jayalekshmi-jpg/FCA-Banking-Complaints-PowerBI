# Building the Power BI report

Follow this step by step in Power BI Desktop. It should take about 2–3 hours the first time.

## 1. Load the data

1. **Home → Get data → Text/CSV**, and load each file in `powerbi/data/`:
   `fact_complaints.csv`, `dim_firm.csv`, `dim_period.csv`, `dim_product.csv`.
2. In **Model view**, create these relationships (all *Many-to-one*, single direction, from fact to dimension):

   | From | To |
   |---|---|
   | `fact_complaints[period_id]` | `dim_period[period_id]` |
   | `fact_complaints[firm_id]` | `dim_firm[firm_id]` |
   | `fact_complaints[product_id]` | `dim_product[product_id]` |

3. In `dim_period`, select `period_label` → **Column tools → Sort by column → `period_id`**, so half-years sort in date order rather than alphabetically.
4. Hide the ID columns and the raw columns of `fact_complaints` from report view (right-click → Hide in report view). Users should only see measures and dimension fields.
5. **View → Themes → Browse for themes** → `powerbi/theme.json`.
6. Add every measure from `dax_measures.md`.

## 2. Page 1: Overview

*Purpose: the headline story in five seconds.*

- **Title text box:** "UK Bank Complaints, Banking and Credit Cards".
- **Slicers (top right):** `dim_period[period_label]` (dropdown, single select, default to the latest) and `dim_product[product_group]` (dropdown, default to Banking and credit cards).
- **Four KPI cards** across the top:
  - `Complaints Opened`
  - `Complaints per 1,000`, with `Change per 1,000` as the reference label
  - `% Upheld`, with `Change % Upheld (pts)` as the reference label
  - `% Closed Within 8 Weeks`
- **Bar chart (left, half width):** "Complaints per 1,000 accounts by banking group". Y-axis `dim_firm[banking_group]`, X-axis `Complaints per 1,000`, sorted descending. Add a constant line at `Peer Avg per 1,000` (Analytics pane → Constant line → fx). Filter the visual to `is_peer_bank = 1`.
- **Line chart (right, half width):** "Complaint rate over time, big five banks". X-axis `period_label`, Y-axis `Complaints per 1,000`, Legend `banking_group`. Filter to HSBC, Barclays, Lloyds Banking Group, NatWest Group and Santander UK.
- **Text box (bottom):** two or three sentences with the key findings. Write these once the numbers are final.

## 3. Page 2: Bank comparison

*Purpose: pick a bank and see how it compares with its peers.*

- **Slicer (left panel):** `dim_firm[banking_group]` as a vertical list, single select, filtered to `is_peer_bank = 1`.
- **Dynamic title:** a card showing `Page Title Bank`.
- **Cards:** `Complaints per 1,000`, `vs Peer per 1,000`, `% Upheld` and `vs Peer % Upheld (pts)`. Apply `Change Colour`-style conditional formatting so a worse-than-peer figure shows red.
- **Clustered bar chart:** "Complaint rate by product". Y-axis `product_group`, X-axis `Complaints per 1,000` and `Peer Avg per 1,000`, so the selected bank and the peer average sit side by side.
- **Line chart:** "% upheld over time". X-axis `period_label`, Y-axis `% Upheld` and `Peer Avg % Upheld`.
- **Table:** `period_label`, `Complaints Opened`, `Complaints per 1,000`, `% Upheld` and `% Closed Within 8 Weeks`, with data bars on `Complaints per 1,000`.

## 4. Page 3: Consumer Duty view

*Purpose: find where customers are getting poor outcomes.*

Consumer Duty is the FCA's rule (in force since July 2023) that firms must deliver good outcomes for retail customers. Complaints, and especially upheld complaints, are one of the main signals the FCA uses to check it.

- **Scatter chart (main visual):** "Complaint rate vs % upheld". X-axis `Complaints per 1,000`, Y-axis `% Upheld`, Values `banking_group`, Size `Complaints Opened`. Add an X constant line at `Peer Avg per 1,000` and a Y constant line at `Peer Avg % Upheld`. Banks in the **top-right quadrant** have more complaints than their peers *and* are more often found to be in the wrong.
- **Matrix:** rows `banking_group`, columns `product_group`, values `Complaints per 1,000`. Add a background-colour scale (white → red) so problem areas stand out.
- **Bar chart:** "Resolved within the 8-week deadline". Y-axis `banking_group`, X-axis `% Closed Within 8 Weeks`, sorted ascending so the worst banks are at the top. Set the X-axis to start at 75% so the gaps are visible, and add a constant line at 95%.
- **Bar chart:** "Biggest increases since last half-year". Y-axis `banking_group`, X-axis `Change per 1,000`, sorted descending, with the visual filtered to Top 5 by `Change per 1,000`.
- **Drill-through:** on Page 2, add `dim_firm[banking_group]` to the Drill-through well. Users can then right-click any bank on this page → Drill through → Bank comparison.

## 5. Finishing touches

- Use the same position for slicers and titles on every page.
- Add a footer text box on each page: "Source: FCA firm-level complaints data. Firms with 500+ complaints in a half-year."
- **Export screenshots** of each page to `images/` (File → Export → PDF, or a screenshot) for the README.
- **Optional:** File → Publish → Publish to web gives a public link recruiters can click without Power BI. Check your organisation's or account's settings first, and only use this because the data is already public.
