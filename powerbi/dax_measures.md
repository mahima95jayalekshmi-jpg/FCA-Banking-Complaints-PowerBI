# DAX measures

Create a blank table called `_Measures` (Home → Enter data → OK) and add every measure below to it, so they sit together in the Fields pane.

The measures rebuild every rate from summed counts, so the figures stay correct whether a visual shows one bank, a whole group or all of the UK.

## Core volumes

```dax
Complaints Opened = SUM ( fact_complaints[opened] )

Complaints Closed = SUM ( fact_complaints[closed] )

Complaints Upheld = SUM ( fact_complaints[upheld] )
```

## Rates

```dax
Complaints per 1,000 =
DIVIDE (
    SUM ( fact_complaints[opened_with_context] ),
    SUM ( fact_complaints[implied_accounts] )
) * 1000

% Upheld =
DIVIDE ( [Complaints Upheld], [Complaints Closed] )

% Closed Within 3 Days =
DIVIDE ( SUM ( fact_complaints[closed_within_3_days] ), [Complaints Closed] )

% Closed Within 8 Weeks =
DIVIDE ( SUM ( fact_complaints[closed_within_8_weeks] ), [Complaints Closed] )
```

`opened_with_context` only counts complaints where the FCA published an accounts figure, so the top and bottom of the rate always cover the same firms.

Format `% Upheld` and both timeliness measures as **Percentage, 1 decimal place**. Format `Complaints per 1,000` as **Decimal, 2 places**.

## Change from the previous half-year

`dim_period[period_id]` increases by 1 each half-year, so the previous period is always `period_id - 1`.

```dax
Complaints per 1,000 (Prev) =
VAR CurrentPeriod = MAX ( dim_period[period_id] )
RETURN
    CALCULATE (
        [Complaints per 1,000],
        REMOVEFILTERS ( dim_period ),
        dim_period[period_id] = CurrentPeriod - 1
    )

Change per 1,000 =
IF (
    NOT ISBLANK ( [Complaints per 1,000 (Prev)] ),
    [Complaints per 1,000] - [Complaints per 1,000 (Prev)]
)

% Upheld (Prev) =
VAR CurrentPeriod = MAX ( dim_period[period_id] )
RETURN
    CALCULATE (
        [% Upheld],
        REMOVEFILTERS ( dim_period ),
        dim_period[period_id] = CurrentPeriod - 1
    )

Change % Upheld (pts) =
IF (
    NOT ISBLANK ( [% Upheld (Prev)] ),
    ( [% Upheld] - [% Upheld (Prev)] ) * 100
)
```

## Peer comparison

The peer group is every high-street bank, digital bank and building society (`dim_firm[is_peer_bank] = 1`).

```dax
Peer Avg per 1,000 =
CALCULATE (
    [Complaints per 1,000],
    REMOVEFILTERS ( dim_firm ),
    dim_firm[is_peer_bank] = 1
)

Peer Avg % Upheld =
CALCULATE (
    [% Upheld],
    REMOVEFILTERS ( dim_firm ),
    dim_firm[is_peer_bank] = 1
)

vs Peer per 1,000 = [Complaints per 1,000] - [Peer Avg per 1,000]

vs Peer % Upheld (pts) = ( [% Upheld] - [Peer Avg % Upheld] ) * 100
```

## Ranking

```dax
Rank by Complaint Rate =
IF (
    HASONEVALUE ( dim_firm[banking_group] ),
    RANKX (
        ALLSELECTED ( dim_firm[banking_group] ),
        [Complaints per 1,000],
        ,
        DESC,
        DENSE
    )
)
```

## Labels and formatting helpers

```dax
Latest Period Label =
VAR LatestPeriod = MAX ( dim_period[period_id] )
RETURN
    CALCULATE (
        MAX ( dim_period[period_label] ),
        REMOVEFILTERS ( dim_period ),
        dim_period[period_id] = LatestPeriod
    )

Selected Bank =
SELECTEDVALUE ( dim_firm[banking_group], "All peer banks" )

Page Title Bank =
"Complaints profile: " & [Selected Bank] & ", " & [Latest Period Label]

Change Colour =
SWITCH (
    TRUE (),
    ISBLANK ( [Change per 1,000] ), "#8A8A8A",
    [Change per 1,000] > 0, "#B3261E",   -- more complaints: red
    "#1E7B4A"                             -- fewer complaints: green
)
```

To use `Change Colour`, select a visual → Format → the value's colour → **fx** → Format style: *Field value* → `Change Colour`.

To use `Page Title Bank`, add a text box or card → Title → **fx** → Field value → `Page Title Bank`.
