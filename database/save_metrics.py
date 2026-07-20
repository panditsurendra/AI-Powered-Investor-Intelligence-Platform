import warnings
from sqlalchemy import text
from database.postgres_sql import get_engine

# Ignore minor SQLAlchemy deprecation flags for cleaner logs
warnings.filterwarnings("ignore", category=DeprecationWarning)

def ensure_string_block(value) -> str:
    """
    Safely converts incoming data into a clean text block.
    Prevents strings from being accidentally letter-split by string joins.
    """
    if not value:
        return ""
    if isinstance(value, list):
        # Filter out empty items and join with newlines
        return "\n".join(str(item).strip() for item in value if item)
    return str(value).strip()


def save_metrics(
    company: str,
    year: int,
    metrics: dict
) -> None:
    """
    Save extracted financial metrics to your local PostgreSQL database.
    """
    engine = get_engine()

    query = """
    INSERT INTO financial_metrics (
        company,
        year,
        revenue,
        net_income,
        operating_income,
        cash_flow,
        total_assets,
        total_liabilities,
        risk_factors,
        growth_drivers
    )
    VALUES (
        :company,
        :year,
        :revenue,
        :net_income,
        :operating_income,
        :cash_flow,
        :total_assets,
        :total_liabilities,
        :risk_factors,
        :growth_drivers
    )
    """

    # Extract values checking both PascalCase (from Azure) and snake_case (Pydantic model_dump defaults)
    raw_risks = metrics.get("Top Risk Factors") or metrics.get("risk_factors")
    raw_drivers = metrics.get("Top Growth Drivers") or metrics.get("growth_drivers")

    params = {
        "company": company,
        "year": str(year) if year else "",
        "revenue": str(metrics.get("Revenue") or metrics.get("revenue") or ""),
        "net_income": str(metrics.get("Net Income") or metrics.get("net_income") or ""),
        "operating_income": str(metrics.get("Operating Income") or metrics.get("operating_income") or ""),
        "cash_flow": str(metrics.get("Cash Flow from Operating Activities") or metrics.get("cash_flow") or ""),
        "total_assets": str(metrics.get("Total Assets") or metrics.get("total_assets") or ""),
        "total_liabilities": str(metrics.get("Total Liabilities") or metrics.get("total_liabilities") or ""),
        # Safe string translation mapping 
        "risk_factors": ensure_string_block(raw_risks),
        "growth_drivers": ensure_string_block(raw_drivers)
    }

    with engine.begin() as connection:
        connection.execute(text(query), params)

    print(f"✅ Successfully saved metrics for {company} ({year}) to PostgreSQL.")


if __name__ == "__main__":
    # Test dataset mimicking Ollama pipeline outputs
    sample_metrics = {
        "revenue": "$391,035",
        "net_income": "$93,736",
        "operating_income": "$123,216",
        "cash_flow": "$118,254",
        "total_assets": "$364,980",
        "total_liabilities": "$308,030",
        "risk_factors": [
            "Macroeconomic conditions including inflation and currency fluctuations.",
            "High competition with short product life cycles."
        ],
        "growth_drivers": "Increased Services revenue from advertising and cloud services." # Testing raw string safety
    }

    save_metrics(
        company="Apple Test",
        year=2024,
        metrics=sample_metrics
    )