import pandas as pd

def economic_trends_for_president(df, president, indicators, term = 'both'):
    if indicators is None:
        indicators = ['GDP', 'CPI', 'UNRATE']

    president_data = df[df['President Elect'] == president].copy()
    president_data = president_data.drop_duplicates(subset=['Year', 'Month'])

    if term != 'both':
        years = sorted(president_data['Year'].unique())

        if term == 'first':
            first_term_years = years[:4]
            president_data = president_data[president_data['Year'].isin(first_term_years)]
        elif term == 'second':
            second_term_years = years[4:8]
            president_data = president_data[president_data['Year'].isin(second_term_years)]

    columns = ['Year', 'Month'] + indicators
    return columns


def simple_eda(df):
    df_clean = df.copy()
    
    vote_cols = [col for col in df_clean.columns if "Percentage" in col]
    for col in vote_cols:
        df_clean[col] = df_clean[col].astype(str).str.rstrip("%").astype(float)
    
    econ_cols = ["CPI", "UNRATE", "GDP"]
    econ_cols = [col for col in econ_cols if col in df_clean.columns]
    
    numeric_cols = df_clean.select_dtypes(include='number').columns.tolist()
    correlation_matrix = df_clean[numeric_cols].corr()
    
    return {
        'regression_data': df_clean[econ_cols + vote_cols],
        'correlation_matrix': correlation_matrix,
        'vote_cols': vote_cols,
        'econ_cols': econ_cols
    }

def president_party_and_economic_analyis(df, president):
    president_data = df[df['President Elect'] == president].copy()

    if len(president_data) == 0:
        return None
    
    econ_data = president_data.drop_duplicates(subset=['Year', 'Month']).sort_values(['Year', 'Month'])
    first = econ_data.iloc[0]
    last = econ_data.iloc[-1]

    all_changes = {
        'start_year': first['Year'],
        'end_year': last['Year'],
        'GDP_change': last['GDP'] - first['GDP'],
        'CPI_change': last['CPI'] - first['CPI'],
        'UNRATE_change': last['UNRATE'] - first['UNRATE']
    }

    year_change = econ_data['Year'].max()
    year_change_data = econ_data[econ_data['Year'] == year_change].sort_values('Month')

    if len(year_change_data) >= 2:
        last_year_start = year_change_data.iloc[0]
        last_year_end = year_change_data.iloc[-1]
    
        last_year_changes = {
            'year': year_change,
            'GDP_change': last_year_end['GDP'] - last_year_start['GDP'],
            'CPI_change': last_year_end['CPI'] - last_year_start['CPI'],
            'UNRATE_change': last_year_end['UNRATE'] - last_year_start['UNRATE']
        }
    else:
        last_year_changes = None

    election_cycle = president_data['Election Cycle'].iloc[0]
    previous_cycle = election_cycle - 4
    current_election = president_data[president_data['Election Cycle'] == election_cycle][
        ['State', 'Republican Percentage', 'Democratic Percentage']
    ].drop_duplicates()
    previous_election = df[df['Election Cycle'] == previous_cycle][
        ['State', 'Republican Percentage', 'Democratic Percentage']
    ].drop_duplicates()
    
    if len(previous_election) > 0:
        vote_swings = current_election.merge(
            previous_election, 
            on='State', 
            suffixes=('_current', '_previous')
        )
        vote_swings['Republican_swing'] = vote_swings['Republican Percentage_current'] - vote_swings['Republican Percentage_previous']
        vote_swings['Democratic_swing'] = vote_swings['Democratic Percentage_current'] - vote_swings['Democratic Percentage_previous']
        
        state_swings = vote_swings[['State', 'Republican_swing', 'Democratic_swing']].to_dict('records')
    else:
        state_swings = None

    current_party = president_data['Winning Party'].iloc[0]
    previous_pres_data = df[df['Election Cycle'] == previous_cycle]


    if len(previous_pres_data) > 0:
        previous_party = previous_pres_data['Winning Party'].iloc[0]
        party_switched = (current_party != previous_party)
    else:
        previous_party = None
        party_switched = None
    
    party_transition = {
        'current_party': current_party,
        'previous_party': previous_party,
        'party_switched': party_switched
    }
    
    return {
        'president': president,
        'overall_economic_changes': all_changes,
        'last_year_changes': last_year_changes,
        'state_vote_swings': state_swings,
        'party_transition': party_transition
    }