from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from langchain_groq import ChatGroq
import re

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0,
    groq_api_key="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",
)

engine = create_engine("postgresql+psycopg2://pawani:pawani09@20.244.12.11:5432/indian_ocean")

DATABASE_SCHEMA = """Database Schema (Full)

1. global_metadata

General metadata about the dataset.
Columns:

id [INTEGER] NOT NULL

conventions [TEXT]

data_type [TEXT]

date_creation [TIMESTAMP]

date_update [TIMESTAMP]

feature_type [TEXT]

file_references [TEXT]

format_version [TEXT]

handbook_version [TEXT]

history [TEXT]

institution [TEXT]

reference_date_time [TIMESTAMP]

source [TEXT]

title [TEXT]

user_manual_version [TEXT]


Relations:

One global_metadata record can be linked to many profiles.



---

2. profiles

Main table storing each profile (measurement event).
Columns:

id [INTEGER] NOT NULL

config_mission_number [INTEGER]

cycle_number [INTEGER]

data_centre [TEXT]

data_mode [CHAR(1)]

data_state_indicator [TEXT]

dc_reference [TEXT]

direction [CHAR(1)]

firmware_version [TEXT]

float_serial_no [TEXT]

global_id [INTEGER] → FK to global_metadata.id

juld [TIMESTAMP]

juld_location [TIMESTAMP]

juld_qc [TEXT]

latitude [DOUBLE PRECISION]

longitude [DOUBLE PRECISION]

pi_name [TEXT]

platform_number [TEXT]

platform_type [TEXT]

position_qc [TEXT]

positioning_system [TEXT]

profile_pres_qc [TEXT]

profile_psal_qc [TEXT]

profile_temp_qc [TEXT]

project_name [TEXT]

vertical_sampling_scheme [TEXT]

wmo_inst_type [TEXT]


Relations:

One profile can have many profile_levels.

One profile can have many calibration records.

One profile can have many history records.

Many profiles can belong to one global_metadata.



---

3. profile_levels

Stores measurements at each depth level for a given profile.
Columns:

id [INTEGER] NOT NULL

level [INTEGER]

pres [DOUBLE PRECISION]

pres_adjusted [DOUBLE PRECISION]

pres_adjusted_error [DOUBLE PRECISION]

pres_adjusted_qc [TEXT]

pres_qc [TEXT]

profile_id [INTEGER] → FK to profiles.id

psal [DOUBLE PRECISION]

psal_adjusted [DOUBLE PRECISION]

psal_adjusted_error [DOUBLE PRECISION]

psal_adjusted_qc [TEXT]

psal_qc [TEXT]

temp [DOUBLE PRECISION]

temp_adjusted [DOUBLE PRECISION]

temp_adjusted_error [DOUBLE PRECISION]

temp_adjusted_qc [TEXT]

temp_qc [TEXT]


Relations:

Many profile_levels belong to one profile.



---

4. calibration

Stores calibration data for instruments used in profiles.
Columns:

id [INTEGER] NOT NULL

calib_coefficient [TEXT]

calib_comment [TEXT]

calib_date [TIMESTAMP]

calib_equation [TEXT]

param_name [TEXT]

profile_id [INTEGER] → FK to profiles.id


Relations:

Many calibration records belong to one profile.



---

5. history

Logs changes made to profile data.
Columns:

id [INTEGER] NOT NULL

action [TEXT]

history_date [TIMESTAMP]

institution [TEXT]

parameter [TEXT]

previous_value [TEXT]

profile_id [INTEGER] → FK to profiles.id

qctest [TEXT]

reference [TEXT]

software [TEXT]

software_release [TEXT]

start_pres [DOUBLE PRECISION]

step [TEXT]

stop_pres [DOUBLE PRECISION]


Relations:

Many history records belong to one profile.



---

Relations Summary

global_metadata (1) → (N) profiles

profiles (1) → (N) profile_levels

profiles (1) → (N) calibration

profiles (1) → (N) history"""

def generate_postgresql_query(__arg1: str) -> str:
    prompt = f"""
You are an expert PostgreSQL query generator for oceanographic data.
Convert the following natural language request into a safe SELECT query ONLY.
Use proper JOINs and WHERE clauses. Default LIMIT 100 if not specified.
Do not include any INSERT, UPDATE, DELETE, DROP, or ALTER commands.
If the user query is irrelevant to the database, respond with "SELECT 'No relevant data found' AS message;".
The data can contain nan values; handle them appropriately.
- It has "NaN" values so also add a filter like temp != 'NaN' to get accurate answer.

Database Schema:
{DATABASE_SCHEMA}

User Query: "{__arg1}"

Return ONLY the SQL query without comments or explanation.
"""
    try:
        response = llm.invoke(prompt)
        sql_query = re.sub(r'```sql\n?', '', response.content)
        sql_query = re.sub(r'```\n?', '', sql_query).strip()
        return sql_query
    except Exception as e:
        print(f"Error generating SQL query: {e}")
        return ""

def fire_sql(sql_query: str) -> str:
    try:
        with engine.connect() as conn:
            result = conn.execute(text(sql_query))
            # fetch all rows
            rows = result.fetchall()
            # get column names
            colnames = result.keys()
            # convert to list of dicts
            return [dict(zip(colnames, row)) for row in rows]
    except SQLAlchemyError as e:
        print(f"Error executing SQL query: {e}")
        return []
    finally:
        engine.dispose()