from typing import List, Dict, Any
import numpy as np
from dataclasses import dataclass


@dataclass
class AnomalyResult:
    is_anomaly: bool
    z_score: float
    method: str
    details: Dict[str, Any]


class AnomalyDetector:
    """
    Simple local anomaly detection using statistical methods.
    Bonus feature for the assignment.
    """

    @staticmethod
    def z_score_detection(
            values: List[float],
            threshold: float = 3.0
    ) -> AnomalyResult:
        """
        Detect anomalies using Z-score method.

        Z-score = (value - mean) / std_dev
        Values beyond threshold standard deviations are anomalies.

        Args:
            values: Time series data
            threshold: Z-score threshold (default: 3.0)

        Returns:
            AnomalyResult with detection details
        """
        if len(values) < 3:
            return AnomalyResult(
                is_anomaly=False,
                z_score=0.0,
                method="z_score",
                details={"error": "Insufficient data for z-score"}
            )

        # Calculate statistics
        arr = np.array(values)
        mean = np.mean(arr)
        std = np.std(arr)

        # Handle zero standard deviation
        if std == 0:
            return AnomalyResult(
                is_anomaly=False,
                z_score=0.0,
                method="z_score",
                details={
                    "mean": float(mean),
                    "std": 0.0,
                    "note": "No variance in data"
                }
            )

        # Z-score of the last value
        current_value = values[-1]
        z_score = (current_value - mean) / std

        is_anomaly = abs(z_score) > threshold

        return AnomalyResult(
            is_anomaly=is_anomaly,
            z_score=float(z_score),
            method="z_score",
            details={
                "mean": float(mean),
                "std": float(std),
                "current_value": current_value,
                "threshold": threshold,
                "interpretation": (
                    f"Value is {abs(z_score):.2f} standard deviations "
                    f"from mean {'(ANOMALY)' if is_anomaly else '(NORMAL)'}"
                )
            }
        )

    @staticmethod
    def rolling_std_detection(
            values: List[float],
            window: int = 5,
            threshold: float = 2.0
    ) -> AnomalyResult:
        """
        Detect anomalies using rolling standard deviation.

        Compares recent values to rolling window statistics.

        Args:
            values: Time series data
            window: Rolling window size
            threshold: Multiplier for rolling std

        Returns:
            AnomalyResult with detection details
        """
        if len(values) < window + 1:
            return AnomalyResult(
                is_anomaly=False,
                z_score=0.0,
                method="rolling_std",
                details={"error": f"Need at least {window + 1} values"}
            )

        arr = np.array(values)

        # Calculate rolling statistics (excluding last value)
        rolling_window = arr[-(window + 1):-1]
        rolling_mean = np.mean(rolling_window)
        rolling_std = np.std(rolling_window)

        if rolling_std == 0:
            return AnomalyResult(
                is_anomaly=False,
                z_score=0.0,
                method="rolling_std",
                details={
                    "rolling_mean": float(rolling_mean),
                    "rolling_std": 0.0,
                    "note": "No variance in rolling window"
                }
            )

        # Check if current value deviates from rolling stats
        current_value = values[-1]
        deviation = abs(current_value - rolling_mean)
        threshold_value = threshold * rolling_std

        is_anomaly = deviation > threshold_value

        return AnomalyResult(
            is_anomaly=is_anomaly,
            z_score=deviation / rolling_std,
            method="rolling_std",
            details={
                "rolling_mean": float(rolling_mean),
                "rolling_std": float(rolling_std),
                "current_value": current_value,
                "deviation": float(deviation),
                "threshold_value": float(threshold_value),
                "window_size": window,
                "interpretation": (
                    f"Value deviates by {deviation:.2f} "
                    f"(threshold: {threshold_value:.2f}) "
                    f"{'(ANOMALY)' if is_anomaly else '(NORMAL)'}"
                )
            }
        )

    @staticmethod
    def iqr_detection(values: List[float], multiplier: float = 1.5) -> AnomalyResult:
        """
        Detect anomalies using Interquartile Range (IQR) method.

        IQR = Q3 - Q1
        Outliers are values < Q1 - multiplier*IQR or > Q3 + multiplier*IQR

        Args:
            values: Time series data
            multiplier: IQR multiplier (default: 1.5 for outliers, 3.0 for extreme)

        Returns:
            AnomalyResult with detection details
        """
        if len(values) < 4:
            return AnomalyResult(
                is_anomaly=False,
                z_score=0.0,
                method="iqr",
                details={"error": "Need at least 4 values for IQR"}
            )

        arr = np.array(values)
        q1 = np.percentile(arr, 25)
        q3 = np.percentile(arr, 75)
        iqr = q3 - q1

        lower_bound = q1 - (multiplier * iqr)
        upper_bound = q3 + (multiplier * iqr)

        current_value = values[-1]
        is_anomaly = current_value < lower_bound or current_value > upper_bound

        # Calculate "z-score equivalent" for consistency
        median = np.median(arr)
        z_equiv = abs(current_value - median) / (iqr / 1.35) if iqr > 0 else 0

        return AnomalyResult(
            is_anomaly=is_anomaly,
            z_score=float(z_equiv),
            method="iqr",
            details={
                "q1": float(q1),
                "q3": float(q3),
                "iqr": float(iqr),
                "lower_bound": float(lower_bound),
                "upper_bound": float(upper_bound),
                "current_value": current_value,
                "interpretation": (
                    f"Value is {'OUTSIDE' if is_anomaly else 'WITHIN'} "
                    f"normal range [{lower_bound:.2f}, {upper_bound:.2f}]"
                )
            }
        )