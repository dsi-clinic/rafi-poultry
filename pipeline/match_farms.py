import pandas as pd
import numpy as np
from fuzzywuzzy import fuzz
from distances import haversine


def name_match(counterglow: pd.DataFrame,  cafomaps: pd.DataFrame):
    """Matches plants in Counterglow dataset with permit data from various state websites by name. 

    Args:
        counterglow: DataFrame containing Counterglow CAFO data.
        cafomaps: DataFrame containing CAFO permit data. 

    Returns:
        A new DataFrame, match_df, that duplicates the cafomaps DataFrame but adds columns that note whether a name match
        (either exact or fuzzy) was found.
    """
    name, perfect_match, fuzzy_name, no_match = ([] for i in range(4))
    match_df = cafomaps.copy()
    for i, srow in match_df.iterrows():
        cafo_name = str(srow["name"])
    
        name.append(cafo_name)
        perfect_match.append(None)
        fuzzy_name.append(None)
        no_match.append(True)

        cafo_state = srow['state']
        counterglow_subset = counterglow[counterglow['State']==cafo_state]

        for j, crow in counterglow_subset.iterrows():
            cg_name = crow["Name"]
            if type(cg_name)==str:
                cg_name = crow["Name"].upper()
            if cafo_name == cg_name:
                perfect_match[i] = cg_name
            elif fuzz.token_sort_ratio(cafo_name, cg_name) > 90:
                fuzzy_name[i] = cg_name
            else: 
                pass

    match_df["Exact Name Match"] = perfect_match
    match_df["Fuzzy Name"] = fuzzy_name
    match_df["No Match"] = no_match

    for i, drow in match_df.iterrows():
        if drow[["Exact Name Match", "Fuzzy Name"]].notnull().any():
            match_df.loc[i, "No Match"] = False

    return match_df


def name_loc_match(counterglow: pd.DataFrame, cafomaps: pd.DataFrame, thresh = 0.3048):
    """Matches plants in Counterglow dataset with permit data from various state websites by name and location.

    Args:
        counterglow: DataFrame containing Counterglow CAFO data.
        cafomaps: DataFrame containing CAFO permit data. 

    Returns:
        A new DataFrame, match_df, that duplicates the cafomaps DataFrame but adds columns that indicate whether a name and/or 
        location match was found. The relevant column is filled in with the name of the matching farm in the Counterglow dataset.
    """
    name, latitude, longitude, name_location, fuzzyname_location, name_match, fuzzyname_match, \
        location_match, no_match = ([] for i in range(9))
    match_df = cafomaps.copy()
    for i, srow in cafomaps.iterrows():
        cafo_loc = (srow["lat"], srow["long"])
        cafo_name = str(srow["name"])

        name.append(cafo_name)
        latitude.append(cafo_loc[0])
        longitude.append(cafo_loc[1])
        name_location.append(None)
        fuzzyname_location.append(None)
        name_match.append(None)
        fuzzyname_match.append(None)
        location_match.append(None)
        no_match.append(True)

        cafo_state = srow['state']
        counterglow_subset = counterglow[counterglow['State']==cafo_state]

        for j, crow in counterglow_subset.iterrows():
            # check name match
            cg_name = crow["Name"]
            if type(cg_name)==str:
                cg_name = crow["Name"].upper()
            cg_loc = (crow["Lat"], crow["Lat.1"])
            if cafo_name == cg_name:
                nmatch = 1
            elif fuzz.token_sort_ratio(cafo_name, cg_name) > 90:
                nmatch = 2
            else:
                nmatch = 0
            
            # check location match - within 1000 feet
            dist = haversine(cafo_loc[1], cafo_loc[0], cg_loc[1], cg_loc[0])
            if dist <= thresh:
                if nmatch == 1:
                    name_location[i] = cg_name
                elif nmatch == 2:
                    fuzzyname_location[i] = cg_name
                else: 
                    location_match[i] = cg_name
            else: # dist > thresh
                if nmatch == 1:
                    name_match[i] = cg_name
                elif nmatch == 2:
                    fuzzyname_match[i] = cg_name
            
    dictionary = {
        'Exact Name/Location': name_location,
        'Fuzzy Name/Exact Location': fuzzyname_location,
        'Exact Name Match': name_match,
        'Fuzzy Name': fuzzyname_match,
        'Location Match': location_match,
        'No Match': no_match
    }
    
    for key, value in dictionary.items():
        match_df[key] = value

    for i, drow in match_df.iterrows():
        if drow[["Exact Name/Location", "Fuzzy Name/Exact Location", \
            "Exact Name Match", "Fuzzy Name", "Location Match"]].notnull().any():
            match_df.loc[i, "No Match"] = False

    return match_df


def match_all_farms(counterglow_path, cafomaps_path, animal_exp):
    """Executes the helper matching functions and saves the results for matched farms and unmatched farms
    to the cleaned data folder.

    Args:
        counterglow: DataFrame containing Counterglow CAFO data.
        cafomaps: DataFrame containing CAFO permit data. 
        animal_exp: String with substrings to filter permit types for (ie. "Poultry|Chicken|Broiler")

    Returns:
        N/A, saves two CSVs to the cleaned data folder. 
    """
    counterglow = pd.read_csv(counterglow_path)
    cafomaps = pd.read_csv(cafomaps_path).drop(columns='Unnamed: 0')
    cafomaps['name'] = cafomaps['name'].str.upper()

    # Filters for specific animal (ie. poultry) and drops rows with no data
    cafomaps = cafomaps[cafomaps["permit"].str.contains(animal_exp, regex=True)]
    counterglow = counterglow[counterglow['Farm Type'].notna()]
    counterglow = counterglow[counterglow["Farm Type"].str.contains(animal_exp, regex=True)]

    # Splitting cafomaps into facilities with/without locations
    cm_nameonly = cafomaps[cafomaps["lat"].isnull()].reset_index(drop=True)
    cm_nameloc = cafomaps[cafomaps["lat"].notnull()].reset_index(drop=True)

    # Calls different matching functions on each subset of cafomaps
    cm_nameonly_match = name_match(counterglow, cm_nameonly)
    cm_nameloc_match = name_loc_match(counterglow, cm_nameloc)

    # Combining the results of the match
    combined_df = pd.concat([cm_nameonly_match, cm_nameloc_match], ignore_index=True)

    # Creating full matched dataframe
    matched_df = combined_df[~combined_df["No Match"]].drop(columns=["No Match"])

    # Pulling out names of the farms matched in Counterglow
    counterglow["Name"] = counterglow["Name"].str.upper()
    subset = ['Exact Name/Location', 'Fuzzy Name/Exact Location','Exact Name Match', 'Fuzzy Name', 'Location Match']
    cg_matches = matched_df[subset].stack().dropna().tolist()
    cg_unmatched = counterglow[~counterglow.Name.isin(cg_matches)]

    # Appending unmatched cafomaps farms with unmatched Counterglow farms
    cg_unmatched = cg_unmatched.rename(columns={"Name": "name", "Address": "address", "Lat": "lat", "Lat.1": "long", "State": "state"})
    cg_unmatched["source"] = ["Counterglow"] * len(cg_unmatched)

    unmatched_df = pd.concat([combined_df[combined_df['No Match']], cg_unmatched], ignore_index=True).drop(columns=["No Match"])

    matched_df.to_csv("../data/clean/matched_farms.csv")
    unmatched_df.to_csv("../data/clean/unmatched_farms.csv")


if __name__ == "__main__":
    match_all_farms("../data/raw/Counterglow+Facility+List+Complete.csv", "../data/clean/cleaned_matched_farms.csv", "Poultry|Chicken|Broiler")