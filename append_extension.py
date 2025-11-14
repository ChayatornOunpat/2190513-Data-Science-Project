import os

folder = r"C:\Users\ASUS\Downloads\ScopusData2018-2023\ScopusData2018-2023\2019"

for fname in os.listdir(folder):
    full = os.path.join(folder, fname)


    if os.path.isdir(full):
        continue


    if "." in fname:
        continue

    new_name = fname + ".json"
    new_full = os.path.join(folder, new_name)

    os.rename(full, new_full)
    print(f"Renamed: {fname} → {new_name}")
