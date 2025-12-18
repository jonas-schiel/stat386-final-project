import requests
from bs4 import BeautifulSoup
import pandas as pd

def wrangle_data(filepath, value_col, drop_rows=None, rename_from=None):
    df = pd.read_csv(filepath)

    if drop_rows is not None:
        df = df.drop(drop_rows)

    df['Year'] = df['observation_date'].str.extract(r'(\d{4})')
    df['Month'] = df['observation_date'].str.extract(r'((?<=\d{4}-)\d{2})')

    if rename_from is not None:
        df[value_col] = df[rename_from]
        df = df.drop(rename_from, axis=1)

    df = df.drop('observation_date', axis=1)

    df['Month'] = df['Month'].astype(int)
    df['Month'] = pd.to_datetime(df['Month'], format='%m').dt.month_name()
    df['Year'] = df['Year'].astype(int)

    column_order = ['Month', 'Year', value_col]
    df = df[column_order]

    return df


def merge_and_sort_data(df1, df2, df3):
    combined = pd.merge(df1, df2, on=['Month', 'Year'], how='outer')

    data = pd.merge(combined, df3, on=['Year', 'Month'], how='outer')

    month_order = [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December"]
        
    data["Month"] = pd.Categorical(data["Month"], categories=month_order, ordered=True)

    data = data.sort_values(["Year", "Month"]).reset_index(drop=True)

    return data



def add_presidents_to_data(data, html_text, min_year=1948):

    tables = pd.read_html(html_text)
    df = tables[0]

    df["No."] = df["No.[a]"]
    df["President"] = df["Name (birth–death)"].str.extract(
    r"([A-Z][a-z]+\W[A-Z][a-z]+)")

    df["Party"] = df["Party[b][17].1"]

    df[["Start", "End"]] = df["Term[16]"].str.split("–", expand=True)   
    df["Start_Month"] = df["Start"].str.extract(r"([A-Z][a-z]+)")
    df["Start_Year"] = df["Start"].str.extract(r"(\d{4})")
    df["End_Month"] = df["End"].str.extract(r"([A-Z][a-z]+)")
    df["End_Year"] = df["End"].str.extract(r"(\d{4})")

    df["End_Year"] = df["End_Year"].fillna(2025)
    df.loc[df["End_Month"] == "Incumbent", "End_Month"] = "November"

    df["Start_Date"] = pd.to_datetime(
    df["Start_Month"] + " " + df["Start_Year"].astype(str))

    df["End_Date"] = pd.to_datetime(
        df["End_Month"] + " " + df["End_Year"].astype(str))

    rows = []
    for _, row in df.iterrows():
        dates = pd.date_range(row["Start_Date"], row["End_Date"], freq="MS")
        for d in dates:
            rows.append({
            "Year": d.year,
            "Month": d.month_name(),
            "President": row["President"],
            "Party": row["Party"],})

    Presidents = pd.DataFrame(rows)
    Presidents = Presidents[Presidents["Year"] >= min_year]

    Final = pd.merge(data, Presidents, on=["Year", "Month"], how="outer")

    Final["Month"] = Final["Month"].str.strip()
    Final["President"] = Final["President"].str.strip()

    month_map = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12}

    terms = [
    ("Harry S Truman", (1945, "April"), (1953, "January")),
    ("Dwight D Eisenhower", (1953, "January"), (1961, "January")),
    ("John F Kennedy", (1961, "January"), (1963, "November")),
    ("Lyndon B Johnson", (1963, "November"), (1969, "January")),]

    for i, row in Final.iterrows():
        if pd.isna(row["President"]):
            current = (row["Year"], month_map[row["Month"]])

            for pres, (sy, sm), (ey, em) in terms:
                start = (sy, month_map[sm])
                end = (ey, month_map[em])

                if start <= current < end:
                    Final.loc[i, "President"] = pres
                    break

    month_order = list(month_map.keys())
    Final["Month"] = pd.Categorical(
        Final["Month"], categories=month_order, ordered=True)

    Final = Final.sort_values(["Year", "Month"]).reset_index(drop=True)
    Final = Final.drop_duplicates()
    Final["GDP"] = Final["GDP"].interpolate(method="linear") \
                    .ffill()
    Final = Final.iloc[:-2]

    return Final


def get_presidents_html(ua, email, url="https://en.wikipedia.org/wiki/List_of_presidents_of_the_United_States"):
    r = requests.get(url, headers={"User-Agent": ua, "From": email}, timeout=15)
    r.raise_for_status()
    return r.text