
import pandas as pd

# Load real research data
environment = pd.read_csv(
    "data/real/grainguard_usda_daily_environment.csv"
)

outcomes = pd.read_csv(
    "data/real/grainguard_usda_sample_outcomes.csv"
)

print("\nENVIRONMENT DATA")
print(environment.head())
print("Shape:", environment.shape)
print("Columns:", environment.columns.tolist())

print("\nEXPERIMENTAL OUTCOMES")
print(outcomes.head())
print("Shape:", outcomes.shape)
print("Columns:", outcomes.columns.tolist())

print("\nMISSING VALUES")
print(outcomes.isnull().sum())
