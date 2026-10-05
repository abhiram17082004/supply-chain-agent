import duckdb

DB_PATH = "data/processed/supply_chain.duckdb"

ALLOWED_DIMENSIONS = {
    "category_name", "market", "shipping_mode",
    "department_name", "order_region", "customer_segment"
}

ALLOWED_MARKETS = {"LATAM", "Europe", "Pacific Asia", "USCA", "Africa"}


def get_delivery_risk_report(
    group_by: str,
    market: str = None,
    limit: int = 10
) -> dict:
    """Ranked delivery risk report grouped by a supply chain dimension.
    Best tool when asked: which X has worst delays / best performance.

    group_by options:
      category_name, market, shipping_mode,
      department_name, order_region, customer_segment

    market optional filter:
      LATAM, Europe, Pacific Asia, USCA, Africa
    """
    if group_by not in ALLOWED_DIMENSIONS:
        return {"error": f"group_by must be one of: {sorted(ALLOWED_DIMENSIONS)}"}

    if market and market not in ALLOWED_MARKETS:
        return {"error": f"market must be one of: {sorted(ALLOWED_MARKETS)}"}

    where_clause = f"AND market = '{market}'" if market else ""

    safe_limit = min(int(limit or 10), 20)

    query = f"""
        SELECT
            {group_by}                                                       AS dimension,
            COUNT(*)                                                         AS total_orders,
            ROUND(AVG(CASE WHEN delivery_status = 'Late delivery'
                           THEN 1.0 ELSE 0.0 END) * 100, 1)                 AS late_rate_pct,
            ROUND(AVG(days_for_shipping_real
                      - days_for_shipment_scheduled), 1)                     AS avg_delay_days,
            ROUND(AVG(order_profit_per_order), 2)                            AS avg_profit_usd,
            ROUND(SUM(sales), 0)                                             AS total_revenue_usd
        FROM orders
        WHERE {group_by} IS NOT NULL
        {where_clause}
        GROUP BY {group_by}
        ORDER BY late_rate_pct DESC
        LIMIT {safe_limit}
    """

    conn = duckdb.connect(DB_PATH, read_only=True)
    try:
        df = conn.execute(query).fetchdf()
        return {
            "grouped_by": group_by,
            "market_filter": market or "all markets",
            "results": df.to_dict(orient="records")
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
