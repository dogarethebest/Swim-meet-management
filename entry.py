print("beginning start up")


import json
import time

with open('program_File/Data/build_info.json', "r") as file:
    data = json.load(file)
    build_id = data.get("build_id")
    Version = data.get("version")


print("this software is still currently in Beta.")

time.sleep(0.5)

print(f"Version:{Version}")
print(f"build id:{build_id}")

