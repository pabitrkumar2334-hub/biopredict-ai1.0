import pickle
from pathlib import Path

import pandas as pd
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "training" / "datasets" / "heart.csv"
MODEL_PATH = ROOT / "saved_models" / "heart_model.pkl"
REPORT_PATH = ROOT / "training" / "reports" / "heart_report.txt"


def normalize_columns(df):
    rename_map = {
        "target": "target",
        "Target": "target",
        "HeartDisease": "target",
        "condition": "target",
        "age": "age",
        "sex": "sex",
        "cp": "cp",
        "trestbps": "trestbps",
        "chol": "chol",
        "fbs": "fbs",
        "restecg": "restecg",
        "thalach": "thalach",
        "exang": "exang",
        "oldpeak": "oldpeak",
        "slope": "slope",
        "ca": "ca",
        "thal": "thal",
    }
    df = df.rename(columns={col: rename_map.get(col, col) for col in df.columns})
    return df


def load_data():
    df = pd.read_csv(DATA_PATH)
    df = normalize_columns(df)

    print("Dataset shape:", df.shape)
    print("Columns:", list(df.columns))
    print(df.head())

    target_col = "target"
    if target_col not in df.columns:
        raise ValueError("Could not find target column. Expected one of: target, Target, HeartDisease, condition")

    feature_cols = [
        "age", "sex", "cp", "trestbps", "chol", "fbs", "restecg",
        "thalach", "exang", "oldpeak", "slope", "ca", "thal"
    ]

    missing = [col for col in feature_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required feature columns: {missing}")

    df = df[feature_cols + [target_col]].dropna()

    X = df[feature_cols]
    y = df[target_col]

    return X, y, feature_cols


def train_models(X_train, X_test, y_train, y_test):
    candidates = {
        "Logistic Regression": Pipeline([
            ("scaler", StandardScaler()),
            ("model", LogisticRegression(max_iter=1000))
        ]),
        "Random Forest": RandomForestClassifier(
            n_estimators=300,
            random_state=42,
            class_weight="balanced"
        ),
        "Gradient Boosting": GradientBoostingClassifier(
            random_state=42
        ),
    }

    results = {}

    for name, model in candidates.items():
        model.fit(X_train, y_train)
        preds = model.predict(X_test)
        probs = model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, preds)
        auc = roc_auc_score(y_test, probs)

        results[name] = {
            "model": model,
            "accuracy": acc,
            "roc_auc": auc,
            "classification_report": classification_report(y_test, preds)
        }

    best_name = max(results, key=lambda name: results[name]["roc_auc"])
    return best_name, results


def main():
    X, y, feature_cols = load_data()

    X_train, X_test, y_train, y_test = train_test_split(
        X,
        y,
        test_size=0.2,
        random_state=42,
        stratify=y
    )

    best_name, results = train_models(X_train, X_test, y_train, y_test)
    best = results[best_name]

    model_package = {
        "model": best["model"],
        "features": feature_cols,
        "target": "Heart",
        "metrics": {
            "best_model": best_name,
            "accuracy": round(best["accuracy"], 4),
            "roc_auc": round(best["roc_auc"], 4),
        }
    }

    MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(MODEL_PATH, "wb") as f:
        pickle.dump(model_package, f)

    with open(REPORT_PATH, "w", encoding="utf-8") as f:
        f.write("Heart Model Training Report\n")
        f.write("===========================\n\n")
        f.write(f"Best model: {best_name}\n")
        f.write(f"Accuracy: {best['accuracy']:.4f}\n")
        f.write(f"ROC-AUC: {best['roc_auc']:.4f}\n\n")

        for name, result in results.items():
            f.write(f"\n{name}\n")
            f.write("-" * len(name) + "\n")
            f.write(f"Accuracy: {result['accuracy']:.4f}\n")
            f.write(f"ROC-AUC: {result['roc_auc']:.4f}\n")
            f.write(result["classification_report"])
            f.write("\n")

    print("Training complete.")
    print(f"Best model: {best_name}")
    print(f"Accuracy: {best['accuracy']:.4f}")
    print(f"ROC-AUC: {best['roc_auc']:.4f}")
    print(f"Saved model to: {MODEL_PATH}")
    print(f"Saved report to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
