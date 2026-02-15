import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.validators import bassbrechung_validator, interruption_validator


def test_bassbrechung_passes_on_i_v_i():
    model = {"background": {"bassbrechung_pillars": [{"rn": "i", "layer": "background"}, {"rn": "V", "layer": "background"}, {"rn": "i", "layer": "background"}]}}
    assert bassbrechung_validator(model) == []


def test_interruption_flags_missing_return():
    model = {
        "background": {
            "interruption": {"enabled": True, "at_bar": 8, "notation": "2^/V // broken_beam"},
            "urlinie_targets": [{"degree": 2, "bar": 8}],
        }
    }
    issues = interruption_validator(model)
    assert any("return" in i.message for i in issues)
