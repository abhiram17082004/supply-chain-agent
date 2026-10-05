import re
import duckdb

DB_PATH = "data/processed/supply_chain.duckdb"

BLOCKED_KEYWORDS = [
    "drop", "delete", "insert", "update", "create",
    "alter", "truncate", "exec", "execute", "--", ";"
]


def run_sql_query(query: str) -> dict:
    """Run a SQL SELECT query against the supply chain orders table.
    Use for precise numbers, aggregations, filters, rankings, counts.

    Table: orders  (45 columns, 180,519 rows)

    DELIVERY & SHIPPING:
      delivery_status           Late delivery / Advance shipping / Shipping on time / Shipping canceled
      days_for_shipping_real    actual days taken to ship
      days_for_shipment_scheduled  planned days
      late_delivery_risk        0 or 1
      shipping_mode             First Class / Second Class / Standard Class / Same Day
      shipping_date_dateorders  date shipped

    GEOGRAPHY:
      market                    LATAM / Europe / Pacific Asia / USCA / Africa
      order_region              sub-region within market
      order_country             destination country
      order_city                destination city
      order_state               destination state

    CUSTOMER:
      customer_segment          Consumer / Corporate / Home Office
      customer_city             customer city
      customer_country          customer country
      customer_state            customer state
      customer_zipcode          customer zip code

    PRODUCT:
      category_name             product category
      department_name           product department
      product_name              product name
      product_price             unit price

    FINANCIALS:
      sales                     order line revenue
      order_item_total          order item total
      order_profit_per_order    profit per order
      order_item_profit_ratio   profit margin ratio
      order_item_discount       discount amount
      order_item_discount_rate  discount rate
      order_item_quantity       quantity ordered
      benefit_per_order         benefit per order
      sales_per_customer        sales per customer

    ORDER:
      order_id                  unique order ID
      order_status              COMPLETE / PENDING / PENDING_PAYMENT / PROCESSING /
                                CLOSED / ON_HOLD / SUSPECTED_FRAUD / CANCELED / PAYMENT_REVIEW
      order_date_dateorders     order date
      type                      payment type
    """
    if not re.match(r"^\s*SELECT\b", query, re.IGNORECASE):
        return {"error": "Only SELECT statements are permitted"}

    query_lower = query.lower()
    for kw in BLOCKED_KEYWORDS:
        if kw in query_lower:
            return {"error": f"Blocked keyword in query: '{kw}'"}

    conn = duckdb.connect(DB_PATH, read_only=True)
    try:
        result = conn.execute(query).fetchdf()
        truncated = len(result) > 50
        if truncated:
            result = result.head(50)
        return {
            "columns": result.columns.tolist(),
            "rows": result.values.tolist(),
            "row_count": len(result),
            "truncated_to_50": truncated
        }
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()
