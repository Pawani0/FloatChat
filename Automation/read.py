import xarray as xr
import pandas as pd
import os

# 1️⃣ Path to a single NetCDF file
file_path = r"C:\Users\risha\Downloads\20250914_prof.nc"  # <-- replace

# 2️⃣ Open dataset
ds = xr.open_dataset(file_path)
print(ds)

N_PROF = ds.sizes["N_PROF"]
N_LEVELS = ds.sizes["N_LEVELS"]

profiles_list = []
measurements_list = []

# Helper to decode bytes to string
def decode(val):
    if isinstance(val, (bytes, bytearray)):
        return val.decode("utf-8").strip()
    return str(val)

# 3️⃣ Extract profile-level metadata
for i in range(N_PROF):
    profile = {
        "platform_number": decode(ds["PLATFORM_NUMBER"].values[i]),
        "cycle_number": ds["CYCLE_NUMBER"].values[i].item(),
        "juld": pd.to_datetime(ds["JULD"].values[i]),
        "latitude": ds["LATITUDE"].values[i].item(),
        "longitude": ds["LONGITUDE"].values[i].item(),
        "data_center": decode(ds["DATA_CENTRE"].values[i]),
        "project_name": decode(ds["PROJECT_NAME"].values[i]),
        "direction": decode(ds["DIRECTION"].values[i]),
    }
    profiles_list.append(profile)

# 4️⃣ Extract measurements (per profile × depth level)
for i in range(N_PROF):
    pres = ds["PRES"].values[i, :]
    temp = ds["TEMP"].values[i, :]
    psal = ds["PSAL"].values[i, :]

    for level in range(N_LEVELS):
        # Skip missing data
        if pd.isna(pres[level]) and pd.isna(temp[level]) and pd.isna(psal[level]):
            continue

        measurement = {
            "juld": pd.to_datetime(ds["JULD"].values[i]),
            "platform_number": decode(ds["PLATFORM_NUMBER"].values[i]),
            "cycle_number": ds["CYCLE_NUMBER"].values[i].item(),
            "pressure": float(pres[level]),
            "temperature": float(temp[level]),
            "salinity": float(psal[level]),
            "level_index": level
        }
        measurements_list.append(measurement)

ds.close()

# 5️⃣ Convert to Pandas DataFrames
profiles_df = pd.DataFrame(profiles_list)
measurements_df = pd.DataFrame(measurements_list)

# 6️⃣ Print a few rows for verification
print("Profiles Table:")
print(profiles_df.head())

print("\nMeasurements Table:")
print(measurements_df.head())

# 7️⃣ Optional: save to CSV
output_dir = r"C:\Users\risha\OneDrive\Desktop\SIH\processed_test"
os.makedirs(output_dir, exist_ok=True)
profiles_df.to_csv(os.path.join(output_dir, "profiles.csv"), index=False)
measurements_df.to_csv(os.path.join(output_dir, "measurements.csv"), index=False)

print(f"CSVs saved to {output_dir}")
