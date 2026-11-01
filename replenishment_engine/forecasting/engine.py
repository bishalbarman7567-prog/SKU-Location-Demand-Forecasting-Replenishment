"""Statistical Demand Forecasting Models for SKU-Location Replenishment.

Implements:
1. Holt-Winters Additive (level + trend + weekly seasonality)
2. Croston's Method (for slow and intermittent demand patterns)
3. Uncensored Moving Average (rolling window after stockout adjustment)
4. Censored Baseline (naive sales forecast ignoring stockouts)
"""

import math
from typing import List, Dict, Any, Tuple
import numpy as np
import pandas as pd


class DemandForecaster:
    """Provides modular demand forecasting algorithms with model selection."""

    @staticmethod
    def forecast_holt_winters(
        series: List[float],
        horizon: int = 14,
        season_length: int = 7,
        alpha: float = 0.25,
        beta: float = 0.05,
        gamma: float = 0.20,
    ) -> Tuple[float, float, List[float]]:
        """Fits Holt-Winters additive exponential smoothing with weekly seasonality.

        Returns:
            (mean_daily_forecast, standard_deviation, horizon_point_forecasts)
        """
        n = len(series)
        if n < season_length * 2:
            # Fallback to simple mean if series is too short
            mean_val = float(np.mean(series)) if n > 0 else 1.0
            std_val = float(np.std(series)) if n > 1 else 0.5
            return mean_val, std_val, [mean_val] * horizon

        # Initialize seasonal components
        seasonals = [0.0] * season_length
        season_averages = []
        num_seasons = n // season_length
        for i in range(num_seasons):
            season_averages.append(sum(series[i * season_length : (i + 1) * season_length]) / season_length)

        for i in range(season_length):
            sum_over_seasons = 0.0
            for j in range(num_seasons):
                sum_over_seasons += series[j * season_length + i] - season_averages[j]
            seasonals[i] = sum_over_seasons / num_seasons

        level = season_averages[0]
        trend = (season_averages[-1] - season_averages[0]) / (len(season_averages) * season_length)

        residuals = []
        for i in range(n):
            val = series[i]
            s_idx = i % season_length
            prev_level = level
            pred = level + trend + seasonals[s_idx]
            residuals.append(val - pred)

            # Update level, trend, seasonal
            level = alpha * (val - seasonals[s_idx]) + (1 - alpha) * (level + trend)
            trend = beta * (level - prev_level) + (1 - beta) * trend
            seasonals[s_idx] = gamma * (val - level) + (1 - gamma) * seasonals[s_idx]

        # Forecast forward
        forecasts = []
        for m in range(1, horizon + 1):
            s_idx = (n + m - 1) % season_length
            pred = max(0.0, level + (m * trend) + seasonals[s_idx])
            forecasts.append(round(pred, 2))

        daily_mean = round(float(np.mean(forecasts)), 2)
        daily_std = round(float(np.std(residuals)), 2) if len(residuals) > 1 else 0.5
        if daily_std < 0.1:
            daily_std = 0.5

        return daily_mean, daily_std, forecasts

    @staticmethod
    def forecast_croston(
        series: List[float],
        horizon: int = 14,
        alpha: float = 0.15,
    ) -> Tuple[float, float, List[float]]:
        """Fits Croston's Method for intermittent demand.

        Decomposes series into non-zero demand size (z) and inter-arrival intervals (p).
        Forecast = z / p
        """
        non_zero_demands = []
        intervals = []
        current_interval = 0

        for val in series:
            current_interval += 1
            if val > 0:
                non_zero_demands.append(val)
                intervals.append(current_interval)
                current_interval = 0

        if not non_zero_demands:
            return 0.1, 0.5, [0.1] * horizon

        # Exponential smoothing on demand size and intervals
        z = non_zero_demands[0]
        p = intervals[0]
        for demand, interval in zip(non_zero_demands[1:], intervals[1:]):
            z = alpha * demand + (1 - alpha) * z
            p = alpha * interval + (1 - alpha) * p

        rate = max(0.05, z / max(1.0, p))
        std_est = max(0.3, float(np.std(series))) if len(series) > 1 else 0.5
        forecasts = [round(rate, 2)] * horizon

        return round(rate, 2), round(std_est, 2), forecasts

    @classmethod
    def generate_sku_forecast(
        cls,
        history_df: pd.DataFrame,
        horizon: int = 14,
        use_uncensored: bool = True,
    ) -> Dict[str, Any]:
        """Runs model selection and forecasting for a single SKU-Store series."""
        df = history_df.sort_values("date").reset_index(drop=True)
        target_col = "uncensored_demand" if (use_uncensored and "uncensored_demand" in df.columns) else "units_sold"
        series = df[target_col].astype(float).tolist()

        zero_ratio = float((np.array(series) == 0).mean())

        if zero_ratio > 0.40:
            method = "CROSTON_INTERMITTENT"
            daily_mean, daily_std, horizon_preds = cls.forecast_croston(series, horizon=horizon)
        else:
            method = "HOLT_WINTERS"
            daily_mean, daily_std, horizon_preds = cls.forecast_holt_winters(series, horizon=horizon)

        return {
            "method": method,
            "target_column": target_col,
            "daily_mean": daily_mean,
            "daily_std": daily_std,
            "total_horizon_demand": round(float(sum(horizon_preds)), 2),
            "horizon_predictions": horizon_preds,
            "zero_sales_ratio": round(zero_ratio, 3),
        }

