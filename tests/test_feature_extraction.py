import pytest
from app.services.feature_extractor import FeatureExtractor
from app.config import Settings


@pytest.fixture
def feature_extractor():
    settings = Settings()
    return FeatureExtractor(settings)


def test_basic_increase(feature_extractor):
    """Test detection of basic increase"""
    values = [100, 150]
    features = feature_extractor.extract_from_metrics(values)

    assert features.previous_value == 100
    assert features.current_value == 150
    assert features.change_absolute == 50
    assert features.change_percent == 50.0
    assert features.severity == "critical"  # 50% = critical threshold


def test_basic_decrease(feature_extractor):
    """Test detection of basic decrease"""
    values = [100, 80]
    features = feature_extractor.extract_from_metrics(values)

    assert features.change_percent == -20.0
    assert features.severity == "medium"  # 20% = medium


def test_zero_division_handling(feature_extractor):
    """Test handling of division by zero"""
    values = [0, 100]
    features = feature_extractor.extract_from_metrics(values)

    # Should cap at 1000%
    assert features.change_percent == 1000.0
    assert features.severity == "critical"


def test_no_change(feature_extractor):
    """Test handling of no change"""
    values = [100, 100]
    features = feature_extractor.extract_from_metrics(values)

    assert features.change_percent == 0.0
    assert features.severity == "low"


def test_custom_thresholds(feature_extractor):
    """Test custom severity thresholds"""
    values = [100, 130]  # 30% increase

    # Default thresholds: 30% should be "high"
    features = feature_extractor.extract_from_metrics(values)
    assert features.severity == "high"

    # Custom thresholds
    context = {
        'thresholds': {
            'critical': 100,
            'high': 50,
            'medium': 20
        }
    }
    features = feature_extractor.extract_from_metrics(values, context)
    assert features.severity == "medium"


def test_insufficient_data(feature_extractor):
    """Test error on insufficient data"""
    with pytest.raises(ValueError, match="at least 2 values"):
        feature_extractor.extract_from_metrics([100])
