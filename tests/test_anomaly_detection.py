import pytest
import numpy as np
from app.services.anomaly_detector import AnomalyDetector


@pytest.fixture
def detector():
    return AnomalyDetector()


def test_z_score_normal_value(detector):
    """Test z-score with normal value"""
    values = [100, 105, 98, 102, 110]  # Normal variation
    result = detector.z_score_detection(values, threshold=3.0)

    assert result.is_anomaly == False
    assert result.method == "z_score"
    assert result.z_score < 3.0


def test_z_score_anomaly(detector):
    """Test z-score with actual anomaly"""
    values = [100, 105, 98, 102, 500]  # 500 is an outlier
    result = detector.z_score_detection(values, threshold=3.0)

    assert result.is_anomaly == True
    assert result.method == "z_score"
    assert result.z_score > 3.0


def test_z_score_insufficient_data(detector):
    """Test z-score with too little data"""
    values = [100, 105]  # Only 2 values
    result = detector.z_score_detection(values)

    assert result.is_anomaly == False
    assert "error" in result.details


def test_rolling_std_normal(detector):
    """Test rolling std with normal values"""
    values = [100, 105, 110, 108, 112, 115]
    result = detector.rolling_std_detection(values, window=5, threshold=2.0)

    assert result.is_anomaly == False
    assert result.method == "rolling_std"


def test_rolling_std_anomaly(detector):
    """Test rolling std with anomaly"""
    values = [100, 105, 110, 108, 112, 300]  # 300 is anomaly
    result = detector.rolling_std_detection(values, window=5, threshold=2.0)

    assert result.is_anomaly == True
    assert result.method == "rolling_std"


def test_iqr_detection_normal(detector):
    """Test IQR with normal distribution"""
    values = [100, 105, 110, 108, 112, 115, 120, 118]
    result = detector.iqr_detection(values, multiplier=1.5)

    assert result.is_anomaly == False
    assert result.method == "iqr"


def test_iqr_detection_outlier(detector):
    """Test IQR with outlier"""
    values = [100, 105, 110, 108, 112, 115, 120, 500]  # 500 is outlier
    result = detector.iqr_detection(values, multiplier=1.5)

    assert result.is_anomaly == True
    assert result.method == "iqr"
    assert result.details["current_value"] == 500


def test_z_score_zero_std(detector):
    """Test z-score with no variation (all same values)"""
    values = [100, 100, 100, 100]
    result = detector.z_score_detection(values)

    assert result.is_anomaly == False
    assert result.z_score == 0.0
    assert "No variance" in result.details["note"]