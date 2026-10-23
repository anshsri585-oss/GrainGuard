
import pandas as pd

stacks = []

for i in range(1, 17):
    stack = {
        "stack_id": f"S{i:02d}",
        "grain_type": "Wheat",
        "number_of_bags": 100,
        "probe_count": 3,
        "status": "Not Monitored"
    }

    stacks.append(stack)

df = pd.DataFrame(stacks)

print(df)

df.to_csv("stacks.csv", index=False)

print("16 grain stacks created successfully!")
