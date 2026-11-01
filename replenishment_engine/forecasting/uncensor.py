"""Demand Uncensoring and Stockout Adjustment Module.

Addresses demand censoring where recorded historical sales drop to zero
due to inventory stockouts rather than genuine lack of customer demand.
"""

from typing import Tuple, Dict, Any
import numpy as np
import pandas as pd


class DemandUncensorer:
    """Detects inventory stockout periods and imputes true unconstrained customer demand."""

    @staticmethod
    def uncensor_sales_series(
        series_df: pd.DataFrame,
        window: int = 14,
        min_demand_floor: float = 0.5,
    ) -> pd.DataFrame:
        """Takes a single SKU-Store time series and returns an uncensored demand series.

        Columns expected in series_df:
        - date
        - units_sold
        - stockout_flag
        - promotion_flag
        """
        df = series_df.copy().sort_values("date").reset_index(drop=True)
        df["dow"] = pd.to_datetime(df["date"]).dt.dayofweek

        # 1. Compute baseline non-stockout velocity by day of week
        non_stockout = df[df["stockout_flag"] == False]
        dow_avg = non_stockout.groupby("dow")["units_sold"].mean().to_dict()
        overall_mean = non_stockout["units_sold"].mean() if len(non_stockout) > 0 else 1.0
        if np.isnan(overall_mean) or overall_mean <= 0:
            overall_mean = 1.0

        # Fill any missing day-of-week averages
        for dow in range(7):
            if dow not in dow_avg or np.isnan(dow_avg[dow]) or dow_avg[dow] < min_demand_floor:
                dow_avg[dow] = overall_mean

        # 2. Impute unconstrained demand
        uncensored_demand = []
        is_imputed = []

        for _, row in df.iterrows():
            units = row["units_sold"]
            stockout = bool(row["stockout_flag"])
            dow = row["dow"]
            is_promo = bool(row.get("promotion_flag", False))

            if stockout:
                # Stockout occurred: sales were censored by available inventory
                base_est = dow_avg[dow]
                if is_promo:
                    base_est *= 1.5  # Promotional boost imputation
                imputed_val = max(float(units), float(base_est))
                uncensored_demand.append(round(imputed_val, 2))
                is_imputed.append(True)
            else:
                uncensored_demand.append(float(units))
                is_imputed.append(False)

        df["uncensored_demand"] = uncensored_demand
        df["was_demand_imputed"] = is_imputed
        return df

    @staticmethod
    def calculate_censoring_impact(sales_df: pd.DataFrame) -> Dict[str, Any]:
        """Quantifies the degree of demand distortion caused by stockouts."""
        total_records = len(sales_df)
        stockout_records = int((sales_df["stockout_flag"] == True).sum())
        stockout_rate = round(stockout_records / max(1, total_records), 4)

        censored_total_sales = float(sales_df["units_sold"].sum())
        uncensored_total_demand = float(sales_df["unconstrained_demand_est"].sum())
        total_lost_sales = uncensored_total_demand - censored_total_sales
        underestimation_pct = round(
            (total_lost_sales / max(1.0, uncensored_total_demand)) * 100.0, 2
        )

        return {
            "total_observations": total_records,
            "stockout_events": stockout_records,
            "stockout_percentage": round(stockout_rate * 100.0, 2),
            "recorded_sales_units": round(censored_total_sales, 1),
            "true_unconstrained_demand_units": round(uncensored_total_demand, 1),
            "total_lost_sales_units": round(total_lost_sales, 1),
            "demand_underestimation_pct": underestimation_pct,
        }

