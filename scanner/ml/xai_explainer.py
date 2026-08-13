import logging
from functools import lru_cache

import numpy as np

from .feature_extraction import (
    FEATURE_DESCRIPTIONS,
    FEATURE_NAMES,
    extract_features,
    get_feature_descriptions,
    get_feature_names,
)
from .hybrid_engine import load_model

logger = logging.getLogger(__name__)


def _dangerous_class_index(model):
    classes = list(getattr(model, "classes_", []))
    if not classes:
        raise ValueError("Model does not expose classes_.")

    preferred = {1, "1", True, "phishing", "malicious", "scam", "dangerous", "high risk", "high_risk"}
    for index, class_value in enumerate(classes):
        normalized = str(class_value).strip().lower()
        if class_value in preferred or normalized in preferred:
            return index

    if len(classes) == 2:
        return int(np.argmax(classes))

    raise ValueError(f"Unable to identify dangerous class from model.classes_: {classes}")


def _feature_array(content, scan_type):
    features = np.asarray(extract_features(content, scan_type), dtype=float)
    model = load_model()
    expected = getattr(model, "n_features_in_", None)
    if len(features) != len(FEATURE_NAMES):
        raise ValueError(f"Feature extraction returned {len(features)} values, expected {len(FEATURE_NAMES)}.")
    if expected is not None and len(features) != expected:
        raise ValueError(f"Model expects {expected} features, but extractor returned {len(features)}.")
    return model, features.reshape(1, -1)


@lru_cache(maxsize=1)
def _shap_explainer():
    import shap

    return shap.TreeExplainer(load_model())


def _class_shap_values(shap_values, class_index):
    values = np.asarray(shap_values)
    if isinstance(shap_values, list):
        return np.asarray(shap_values[class_index])[0]
    if values.ndim == 3:
        return values[0, :, class_index]
    if values.ndim == 2:
        return values[0]
    return values


def _top_feature_payload(features, contributions, value_key, top_n):
    rows = []
    for name, value, contribution in zip(FEATURE_NAMES, features[0], contributions):
        contribution = float(contribution)
        rows.append({
            "feature": name,
            "value": float(value),
            value_key: contribution,
            "direction": "increases_risk" if contribution >= 0 else "decreases_risk",
            "description": FEATURE_DESCRIPTIONS.get(name, name.replace("_", " ").title()),
        })
    rows.sort(key=lambda item: abs(item[value_key]), reverse=True)
    return _with_display_width(rows[:top_n], value_key)


def _with_display_width(rows, value_key):
    max_abs = max((abs(float(item.get(value_key, 0))) for item in rows), default=0.0)
    for item in rows:
        item["display_width"] = 0 if max_abs == 0 else round((abs(float(item.get(value_key, 0))) / max_abs) * 100)
    return rows


def explain_with_shap(content, scan_type, top_n=10):
    model, features = _feature_array(content, scan_type)
    class_index = _dangerous_class_index(model)
    shap_values = _shap_explainer().shap_values(features)
    contributions = _class_shap_values(shap_values, class_index)
    return {
        "method": "SHAP",
        "class_index": class_index,
        "class_label": str(model.classes_[class_index]),
        "top_features": _top_feature_payload(features, contributions, "shap_value", top_n),
    }


@lru_cache(maxsize=1)
def _lime_background():
    from ml_model.train import load_datasets

    rows = load_datasets()
    matrix = np.asarray([extract_features(content, scan_type) for content, scan_type, _ in rows], dtype=float)
    if matrix.shape[1] != len(FEATURE_NAMES):
        raise ValueError(f"LIME background has {matrix.shape[1]} features, expected {len(FEATURE_NAMES)}.")
    return matrix


@lru_cache(maxsize=1)
def _lime_explainer():
    from lime.lime_tabular import LimeTabularExplainer

    return LimeTabularExplainer(
        _lime_background(),
        feature_names=FEATURE_NAMES,
        class_names=[str(value) for value in load_model().classes_],
        mode="classification",
        discretize_continuous=False,
        random_state=42,
    )


def _lime_feature_name(raw_name):
    for name in FEATURE_NAMES:
        if raw_name == name or raw_name.startswith(f"{name} ") or raw_name.startswith(f"{name} <") or raw_name.startswith(f"{name} >"):
            return name
    return raw_name.split()[0]


def explain_with_lime(content, scan_type, top_n=10):
    model, features = _feature_array(content, scan_type)
    class_index = _dangerous_class_index(model)
    explanation = _lime_explainer().explain_instance(
        features[0],
        model.predict_proba,
        labels=(class_index,),
        num_features=top_n,
    )
    rows = []
    feature_values = dict(zip(FEATURE_NAMES, features[0]))
    for raw_name, weight in explanation.as_list(label=class_index):
        name = _lime_feature_name(raw_name)
        rows.append({
            "feature": name,
            "value": float(feature_values.get(name, 0.0)),
            "weight": float(weight),
            "direction": "increases_risk" if weight >= 0 else "decreases_risk",
            "description": FEATURE_DESCRIPTIONS.get(name, name.replace("_", " ").title()),
        })
    rows = _with_display_width(rows, "weight")
    return {
        "method": "LIME",
        "class_index": class_index,
        "class_label": str(model.classes_[class_index]),
        "top_features": rows,
    }


def _unavailable(method, exc):
    logger.exception("%s explanation failed: %s", method, exc)
    return {
        "method": method,
        "available": False,
        "message": f"{method} explanation unavailable.",
        "top_features": [],
    }


def _comparison(shap_result, lime_result):
    if not shap_result.get("top_features") or not lime_result.get("top_features"):
        return []
    lime_by_feature = {item["feature"]: item for item in lime_result["top_features"]}
    rows = []
    for item in shap_result["top_features"]:
        lime_item = lime_by_feature.get(item["feature"])
        rows.append({
            "feature": item["feature"],
            "description": item["description"],
            "shap": float(item.get("shap_value", 0.0)),
            "lime": float(lime_item.get("weight", 0.0)) if lime_item else None,
        })
    return rows


def get_combined_explanation(content, scan_type, rules=None, external=None, top_n=10):
    model, features = _feature_array(content, scan_type)
    class_index = _dangerous_class_index(model)
    ml_probability = float(model.predict_proba(features)[0][class_index])

    try:
        shap_result = explain_with_shap(content, scan_type, top_n)
        shap_result["available"] = True
    except Exception as exc:
        shap_result = _unavailable("SHAP", exc)

    try:
        lime_result = explain_with_lime(content, scan_type, top_n)
        lime_result["available"] = True
    except Exception as exc:
        lime_result = _unavailable("LIME", exc)

    return {
        "feature_names": get_feature_names(),
        "feature_descriptions": get_feature_descriptions(),
        "ml_prediction": {
            "dangerous_class": str(model.classes_[class_index]),
            "dangerous_class_index": class_index,
            "dangerous_probability": ml_probability,
            "dangerous_probability_percent": round(ml_probability * 100),
        },
        "shap": shap_result,
        "lime": lime_result,
        "comparison": _comparison(shap_result, lime_result),
        "rules": list(rules or []),
        "external": dict(external or {}),
        "statement": (
            "SHAP provides feature contribution explanations based on the Random Forest model. "
            "LIME provides a local approximation of the model around the specific input. "
            "Rule-based explanations provide deterministic reasons based on predefined security signals. "
            "SHAP and LIME explain the machine-learning prediction and do not directly determine the final hybrid risk score."
        ),
    }
