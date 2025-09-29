import xarray as xr
import psycopg2
import numpy as np
from datetime import datetime
import pandas as pd
import os
import dotenv

dotenv.load_dotenv()

# --- Database connection ---
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")

# --- Utility functions ---
def decode_nc_value(val):
    """Decode NetCDF scalar/attribute values to str/float/int/None"""
    if isinstance(val, (bytes, bytearray)):
        return val.decode("utf-8", errors="ignore").strip() or None
    if isinstance(val, np.generic):
        val = val.item()
    if isinstance(val, np.ndarray):
        if val.shape == ():
            return decode_nc_value(val.item())
        return None
    if isinstance(val, str):
        return val.strip() or None
    return val

def parse_timestamp(val):
    """Convert numpy.datetime64 or YYYYMMDDHHMMSS string to datetime"""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    if isinstance(val, np.datetime64):
        return pd.to_datetime(str(val)).to_pydatetime()
    if isinstance(val, datetime):
        return val
    if isinstance(val, str):
        if val.isdigit() and len(val) == 14:
            try:
                return datetime.strptime(val, "%Y%m%d%H%M%S")
            except Exception:
                return None
        try:
            return datetime.fromisoformat(val)
        except Exception:
            return None
    return None

def safe_str(val): return None if val is None else str(val)
def safe_int(val): 
    try: return int(val)
    except: return None
def safe_float(val): 
    try: return float(val)
    except: return None

# --- Insert functions ---

def insert_global_metadata(cur, conn, ds):
    cur.execute("""
        INSERT INTO global_metadata (
            data_type, format_version, handbook_version, reference_date_time,
            date_creation, date_update, title, institution, source, history,
            file_references, user_manual_version, conventions, feature_type
        ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
        RETURNING id
    """, (
        decode_nc_value(ds.attrs.get("DATA_TYPE")),
        decode_nc_value(ds.attrs.get("FORMAT_VERSION")),
        decode_nc_value(ds.attrs.get("HANDBOOK_VERSION")),
        parse_timestamp(decode_nc_value(ds.attrs.get("REFERENCE_DATE_TIME"))),
        parse_timestamp(decode_nc_value(ds.attrs.get("DATE_CREATION"))),
        parse_timestamp(decode_nc_value(ds.attrs.get("DATE_UPDATE"))),
        decode_nc_value(ds.attrs.get("title")),
        decode_nc_value(ds.attrs.get("institution")),
        decode_nc_value(ds.attrs.get("source")),
        decode_nc_value(ds.attrs.get("history")),
        decode_nc_value(ds.attrs.get("references")),
        decode_nc_value(ds.attrs.get("USER_MANUAL_VERSION")),
        decode_nc_value(ds.attrs.get("Conventions")),
        decode_nc_value(ds.attrs.get("featureType")),
    ))
    gid = cur.fetchone()[0]
    conn.commit()
    print(f"Inserted global_metadata id={gid}")
    return gid


def insert_profiles(cur, conn, ds, global_id):
    num_profiles = ds.dims["N_PROF"]
    profile_ids = []

    for i in range(num_profiles):
        cur.execute("""
            INSERT INTO profiles (
                global_id, platform_number, project_name, pi_name, cycle_number,
                direction, data_centre, dc_reference, data_state_indicator, data_mode,
                platform_type, float_serial_no, firmware_version, wmo_inst_type,
                juld, juld_qc, juld_location, latitude, longitude,
                position_qc, positioning_system, profile_pres_qc, profile_temp_qc,
                profile_psal_qc, vertical_sampling_scheme, config_mission_number
            ) VALUES (%s,%s,%s,%s,%s,
                      %s,%s,%s,%s,%s,
                      %s,%s,%s,%s,
                      %s,%s,%s,%s,%s,
                      %s,%s,%s,%s,
                      %s,%s,%s)
            RETURNING id
        """, (
            global_id,
            safe_str(ds["PLATFORM_NUMBER"].values[i]),
            safe_str(ds["PROJECT_NAME"].values[i]),
            safe_str(ds["PI_NAME"].values[i]),
            safe_int(ds["CYCLE_NUMBER"].values[i]),
            safe_str(ds["DIRECTION"].values[i]),
            safe_str(ds["DATA_CENTRE"].values[i]),
            safe_str(ds["DC_REFERENCE"].values[i]),
            safe_str(ds["DATA_STATE_INDICATOR"].values[i]),
            safe_str(ds["DATA_MODE"].values[i]),
            safe_str(ds["PLATFORM_TYPE"].values[i]),
            safe_str(ds["FLOAT_SERIAL_NO"].values[i]),
            safe_str(ds["FIRMWARE_VERSION"].values[i]),
            safe_str(ds["WMO_INST_TYPE"].values[i]),
            parse_timestamp(ds["JULD"].values[i]),
            safe_str(ds["JULD_QC"].values[i]),
            parse_timestamp(ds["JULD_LOCATION"].values[i]),
            safe_float(ds["LATITUDE"].values[i]),
            safe_float(ds["LONGITUDE"].values[i]),
            safe_str(ds["POSITION_QC"].values[i]),
            safe_str(ds["POSITIONING_SYSTEM"].values[i]),
            safe_str(ds["PROFILE_PRES_QC"].values[i]),
            safe_str(ds["PROFILE_TEMP_QC"].values[i]),
            safe_str(ds["PROFILE_PSAL_QC"].values[i]),
            safe_str(ds["VERTICAL_SAMPLING_SCHEME"].values[i]),
            safe_int(ds["CONFIG_MISSION_NUMBER"].values[i]),
        ))
        pid = cur.fetchone()[0]
        conn.commit()
        profile_ids.append(pid)
        print(f"Inserted profile id={pid}")
    return profile_ids


def insert_profile_levels(cur, conn, ds, profile_ids):
    num_profiles = ds.dims["N_PROF"]
    num_levels = ds.dims["N_LEVELS"]

    for i, pid in enumerate(profile_ids):
        for lvl in range(num_levels):
            cur.execute("""
                INSERT INTO profile_levels (
                    profile_id, level,
                    pres, pres_qc, pres_adjusted, pres_adjusted_qc, pres_adjusted_error,
                    temp, temp_qc, temp_adjusted, temp_adjusted_qc, temp_adjusted_error,
                    psal, psal_qc, psal_adjusted, psal_adjusted_qc, psal_adjusted_error
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                pid, lvl,
                safe_float(ds["PRES"].values[i, lvl]),
                safe_str(ds["PRES_QC"].values[i, lvl]),
                safe_float(ds["PRES_ADJUSTED"].values[i, lvl]),
                safe_str(ds["PRES_ADJUSTED_QC"].values[i, lvl]),
                safe_float(ds["PRES_ADJUSTED_ERROR"].values[i, lvl]),
                safe_float(ds["TEMP"].values[i, lvl]),
                safe_str(ds["TEMP_QC"].values[i, lvl]),
                safe_float(ds["TEMP_ADJUSTED"].values[i, lvl]),
                safe_str(ds["TEMP_ADJUSTED_QC"].values[i, lvl]),
                safe_float(ds["TEMP_ADJUSTED_ERROR"].values[i, lvl]),
                safe_float(ds["PSAL"].values[i, lvl]),
                safe_str(ds["PSAL_QC"].values[i, lvl]),
                safe_float(ds["PSAL_ADJUSTED"].values[i, lvl]),
                safe_str(ds["PSAL_ADJUSTED_QC"].values[i, lvl]),
                safe_float(ds["PSAL_ADJUSTED_ERROR"].values[i, lvl]),
            ))
        conn.commit()
    print("Inserted profile_levels")


def insert_calibration(cur, conn, ds, profile_ids):
    if not all(dim in ds.dims for dim in ["N_PROF", "N_CALIB", "N_PARAM"]):
        return
    for i, pid in enumerate(profile_ids):
        n_calib = ds.dims["N_CALIB"]
        for j in range(n_calib):
            cur.execute("""
                INSERT INTO calibration (
                    profile_id, param_name, calib_equation,
                    calib_coefficient, calib_comment, calib_date
                ) VALUES (%s,%s,%s,%s,%s,%s)
            """, (
                pid,
                safe_str(ds["PARAMETER"].values[i, j, 0]),
                safe_str(ds["SCIENTIFIC_CALIB_EQUATION"].values[i, j, 0]),
                safe_str(ds["SCIENTIFIC_CALIB_COEFFICIENT"].values[i, j, 0]),
                safe_str(ds["SCIENTIFIC_CALIB_COMMENT"].values[i, j, 0]),
                parse_timestamp(decode_nc_value(ds["SCIENTIFIC_CALIB_DATE"].values[i, j, 0]))
            ))
        conn.commit()
    print("Inserted calibration")


def insert_history(cur, conn, ds, profile_ids):
    if "N_HISTORY" not in ds.dims:
        return
    for i, pid in enumerate(profile_ids):
        n_hist = ds.dims["N_HISTORY"]
        for h in range(n_hist):
            cur.execute("""
                INSERT INTO history (
                    profile_id, institution, step, software, software_release,
                    reference, history_date, action, parameter,
                    start_pres, stop_pres, previous_value, qctest
                ) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """, (
                pid,
                safe_str(ds["HISTORY_INSTITUTION"].values[i, h]),
                safe_str(ds["HISTORY_STEP"].values[i, h]),
                safe_str(ds["HISTORY_SOFTWARE"].values[i, h]),
                safe_str(ds["HISTORY_SOFTWARE_RELEASE"].values[i, h]),
                safe_str(ds["HISTORY_REFERENCE"].values[i, h]),
                parse_timestamp(decode_nc_value(ds["HISTORY_DATE"].values[i, h])),
                safe_str(ds["HISTORY_ACTION"].values[i, h]),
                safe_str(ds["HISTORY_PARAMETER"].values[i, h]),
                safe_float(ds["HISTORY_START_PRES"].values[i, h]),
                safe_float(ds["HISTORY_STOP_PRES"].values[i, h]),
                safe_str(ds["HISTORY_PREVIOUS_VALUE"].values[i, h]),
                safe_str(ds["HISTORY_QCTEST"].values[i, h]),
            ))
        conn.commit()
    print("Inserted history")


# --- Main Ingestion ---
def ingest_nc_to_postgres(file_path):
    conn = psycopg2.connect(
        dbname=DB_NAME, user=DB_USER, password=DB_PASS, host=DB_HOST, port=DB_PORT
    )
    cur = conn.cursor()

    ds = xr.open_dataset(file_path)

    gid = insert_global_metadata(cur, conn, ds)
    pids = insert_profiles(cur, conn, ds, gid)
    insert_profile_levels(cur, conn, ds, pids)
    insert_calibration(cur, conn, ds, pids)
    insert_history(cur, conn, ds, pids)

    cur.close()
    conn.close()
    print("Ingestion completed")

root_dir = "/path/to/netcdf/files"
def ingest_batch_1(root_dir):
    for month in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12"]:
        month_path = os.path.join(root_dir, month)
        if os.path.isdir(month_path):
            print(f"Processing month: {month}")
            for file in sorted(os.listdir(month_path)):
                if file.endswith("_prof.nc"):
                    file_path = os.path.join(month_path, file)
                    print(f"Ingesting {file}")
                    try:
                        ingest_nc_to_postgres(file_path)
                    except Exception as e:
                        print(f"Failed {file}: {e}")
    print(f"Completed ingestion for {root_dir}")