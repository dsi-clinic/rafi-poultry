import pandas as pd
import numpy as np
from pathlib import Path

here = Path(__file__).resolve().parent

ABI_dict = dict({np.nan: 'None', 7537913.0: 'Tyson Foods Inc', 0.0: 'None', 987289857.0: 'JBS USA',
                7516065.0: 'Hormel Foods Corp',  453614844.0: 'Cargil Inc', 9564816.0: 'Foster Farms',
                441416815.0: 'Sanderson Farms Inc', 517549762.0: 'Koch Foods Inc', 835874538.0: 'Mountaire Corp', 
                7529217.0: 'Perdue Farms Inc', 433353331.0: 'Continental Grain Co', 513523.0: 'House of Raeford Farms Inc', 
                436136139.0: "Pilgrim's Pride Corp", 512392.0: "George's Inc", 431481290.0: 'Cal-main Foods Inc', 
                7509045.0: "Conagra Brands Inc", 7534076.0: "Simmons Foods Inc", 531052413.0: "Peco Foods Inc",  
                1941509.0: "UNKNOWN"})


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

    df_large_chickens.to_csv(here.parent / "data/clean/cleaned_fsis_processors.csv")

    return



def clean_infogroup(filepath):
    """Cleans the infogroup files, combines them into one large master df.

    Args:
        filepath: absolute path to folder that contains all infogroup files 

    Returns:
        n/a, puts cleaned df into the data/clean folder

    """

    all_years_df = pd.DataFrame()
    dfs = []

    for name in filepath.iterdir():
        df = pd.read_csv(name)
        df.columns = map(str.upper, df.columns)
        dfs.append(df)

    all_years_df = pd.concat(dfs, ignore_index=True)
    all_years_df = all_years_df.sort_values(by='ARCHIVE VERSION YEAR').reset_index(drop=True)

    cols = ['YEAR ESTABLISHED', 'YEAR 1ST APPEARED', 'PARENT NUMBER']
    
    for x in cols:
        all_years_df[x] = all_years_df[x].fillna(0)
        all_years_df[x] = all_years_df[x].apply(np.int64)

    all_years_df['PARENT NAME'] = all_years_df['PARENT NUMBER'].map(ABI_dict)
    all_years_df['PARENT NAME'] = all_years_df['PARENT NAME'].fillna('Small Biz')

    master = all_years_df[['COMPANY', 'ADDRESS LINE 1', 'CITY', 'STATE', 'ZIPCODE', 'PRIMARY SIC CODE', 
                    'ARCHIVE VERSION YEAR', 'YEAR ESTABLISHED', 'ABI', 'COMPANY HOLDING STATUS', 'PARENT NUMBER', 
                    'PARENT NAME', 'LATITUDE', 'LONGITUDE', 'YEAR 1ST APPEARED']]


    master = master.dropna(subset = ['COMPANY', 'LATITUDE', 'LONGITUDE'])

    master.to_csv(here.parent / "data/clean/cleaned_infogroup_plants_all_time.csv")

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

    df.to_csv(here.parent / "data/clean/cleaned_counterglow_facility_list.csv")

    return



def clean_cafo(filepath):
    """Example function with PEP 484 type annotations.

    Args:
        param1: The first parameter.
        param2: The second parameter.

    Returns:
        The return value. True for success, False otherwise.

    """

    5

    return


if __name__ == "__main__":
    clean_infogroup(here.parent / "data/raw/infogroup")
    clean_FSIS(here.parent / "data/raw/fsis-processors-with-location.csv")