import json
import time
import sqlite3

with open('program_File/Data/build_info.json', "r") as file:
    data = json.load(file)
    build_id = data.get("build_id")
    author = data.get("author")
    Version = data.get("version")
    build_id = data.get("build_id")



print("this software is still currently in Beta.")
print(f"Version:{Version}")
print(f"build id:{build_id}")
print(f"made by:{author}")
print(f"build ID:{build_id}")

print("would you like to create a new meet?")
print("or would you like to resume or start a existing meet?")

x = input("(yes for new meet no for existing meet)")


if(x == "yes"):
    print("Creating meet")