import pandas as pd
import numpy as np
import glob



def demo_print():
    print("HEY TESTER")



def clean_FSIS(filepath):
    """Example function with PEP 484 type annotations.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        The return value. True for success, False otherwise.

    """
    df = pd.read_csv(filepath)
    df_chickens = df[df['Animals Processed'].str.contains('Chicken')]
    df_large_chickens = df_chickens.loc[df_chickens.Size == "Large"]

    df_large_chickens.to_csv("../data/clean/cleaned_fsis_processors.csv")



def clean_infogroup(filepath):
    """Cleans the infogroup files, combines them into one large master df.

    Args:
        filepath: path to folder that contains all infogroup files 

    Returns:
        n/a, puts cleaned df into the data/clean folder

    """

    all_years_df = pd.DataFrame()
    dfs = []
    files = glob.glob(filepath)

    for name in files:
        df = pd.read_csv(name)
        df.columns = map(str.upper, df.columns)
        dfs.append(df)

    all_years_df = pd.concat(dfs, ignore_index=True)
    all_years_df = all_years_df.sort_values(by='ARCHIVE VERSION YEAR')

    cols = ['YEAR ESTABLISHED', 'YEAR 1ST APPEARED', 'COMPANY HOLDING STATUS', 'PARENT NUMBER']
    
    for x in cols:
        all_years_df[x] = all_years_df[x].fillna(0)
        all_years_df[x] = all_years_df[x].apply(np.int64)

    all_years_df.to_csv("../data/clean/cleaned_infogroup_plants_all_time.csv")

    return



def clean_counterglow(filepath):
    """Example function with PEP 484 type annotations.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        The return value. True for success, False otherwise.

    """

    df = pd.read_csv(filepath)
    df["Name"] = df["Name"].astype(str, copy=False).apply(lambda x : x.upper())

    df.to_csv("../data/clean/cleaned_counterglow_facility_list.csv")



def clean_cafo(filepath):
    """Example function with PEP 484 type annotations.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        The return value. True for success, False otherwise.

    """
