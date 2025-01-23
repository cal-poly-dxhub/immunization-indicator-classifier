import polars as pl
import datetime as dt
import re



# 1.  Find xlsx file with RSV CDSi codes and export a cvs with all columns
CSV_DATA = "CDSi ScheduleSupportingData- Coded Observations-508_v4.60_withRSV.csv"
df_csv = pl.scan_csv(CSV_DATA).filter((pl.col("Observation Title").is_not_null()) & (pl.col("PHIN VS (Code)").is_not_null()))

# 2. Combine and de-duplicate Observation Title and SNOMED (Code) columns into meaningful words that will be used to send to LLM
obs_and_snomed = df_csv.select("Observation Title", "SNOMED (Code)").collect()
for index, obs in enumerate(obs_and_snomed.rows(named=True)):
    # basic filter: remove a new line and a word from SNOMED Code if it is already in the Observation Title
    

    obs["SNOMED (Code)"] = obs["SNOMED (Code)"].replace(obs["Observation Title"], "").replace("\n", "")
    # obs["SNOMED (Code)"]re.sub("^\d+\s|\s\d+\s|\s\d+$", " ", obs["SNOMED (Code)"])
    text = f"{obs["Observation Title"]}: {obs["SNOMED (Code)"]}"
    # print(obs["SNOMED (Code)"])
    print(text)

    # if index  2:
    #     break




