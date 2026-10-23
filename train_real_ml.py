from pathlib import Path
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.metrics import confusion_matrix, classification_report
from sklearn.metrics import accuracy_score, recall_score, precision_score, f1_score

BASE_DIR = Path(__file__).resolve().parent

data_path = BASE_DIR / "data" / "processed" / "real_ml_data.csv"
df = pd.read_csv(data_path)

# Environmental features only.
# Grain moisture is an experimental outcome here,
# so don't use it to predict that same experiment's result.
features = [
    "avg_temperature",
    "max_temperature",
    "avg_humidity",
    "max_humidity"
]

X = df[features]
y = df["insect_progeny_detected"]

# Group by replicate number as an exploratory split.
# Important caveat: This evaluates across replicates, but treatment confounding exists
# because environmental conditions were determined by treatment assignment.
groups = df["replicate"]

logo = LeaveOneGroupOut()
predictions = []
actual = []

for train_idx, test_idx in logo.split(X, y, groups):
    model = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight="balanced"
    )

    model.fit(X.iloc[train_idx], y.iloc[train_idx])

    pred = model.predict(X.iloc[test_idx])

    predictions.extend(pred)
    actual.extend(y.iloc[test_idx])

print("Confusion Matrix:")
print(confusion_matrix(actual, predictions, labels=[0, 1]))

print("\nClassification Report:")
print(classification_report(
    actual, predictions,
    labels=[0, 1],
    zero_division=0
))

results_dir = BASE_DIR / "results"
results_dir.mkdir(parents=True, exist_ok=True)

eval_file = results_dir / "real_ml_evaluation.txt"
with open(eval_file, "w", encoding="utf-8") as f:
    f.write("GrainGuard - USDA Insect Progeny Experiment\n")
    f.write("Exploratory evaluation only\n\n")

    f.write(f"Samples: {len(actual)}\n")
    f.write(f"Accuracy: {accuracy_score(actual, predictions):.3f}\n")
    f.write(f"Precision: {precision_score(actual, predictions, zero_division=0):.3f}\n")
    f.write(f"Recall: {recall_score(actual, predictions, zero_division=0):.3f}\n")
    f.write(f"F1: {f1_score(actual, predictions, zero_division=0):.3f}\n")

    f.write("\nNote on Scientific Interpretation:\n")
    f.write("- N = 20 experimental samples.\n")
    f.write("- Accuracy matches naive majority class baseline (13/20 = 0.650).\n")
    f.write("- Evaluates across replicates; not validated for real-time grain spoilage prediction.\n")

print(f"Results saved to {eval_file}")
