import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from my_package import analysis
import os

@st.cache_data
def load_data():
    directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    csv_path = os.path.join(directory, 'data', 'processed', 'economic_election_data.csv')
    return pd.read_csv(csv_path)

df = load_data()

st.title("Economic & Election Analysis Dashboard")
st.write("Analyze economic trends and voting patterns across U.S. presidencies")

st.sidebar.header("Navigation")
page = st.sidebar.radio("Choose Analysis", [
    "Economic Trends by President",
    "Exploratory Data Analysis",
    "Presidency Analysis"
])

if page == "Economic Trends by President":
    st.header("Economic Trends by President")

    presidents = sorted(df['President Elect'].unique())
    
    president = st.selectbox("Select President", presidents)
    term = st.radio("Term", ['both', 'first', 'second'])
    indicators = st.multiselect(
        "Select Economic Indicators",
        ['GDP', 'CPI', 'UNRATE'],
        default=['GDP', 'CPI', 'UNRATE']
    )
     
    if st.button("Analyze"):
        results = analysis.economic_trends_for_president(df, president, indicators, term)
        
        st.subheader(f"Results for {president}")
        st.dataframe(results)
        
        for indicator in indicators:
            fig, ax = plt.subplots(figsize=(12, 5))

            results['Date'] = pd.to_datetime(results['Year'].astype(str) + '-' + results['Month'], format = '%Y-%B')
            sorted_res = results.sort_values('Date')

            ax.plot(results['Date'], results[indicator], marker='o')
            if indicator == 'UNRATE':
                ax.set_title(f"Unemployment Rate during {president}'s Presidency")
            else:
                ax.set_title(f"{indicator} during {president}'s Presidency")
            ax.set_xlabel('Year')
            ax.set_ylabel(indicator)
            ax.grid(True)
            st.pyplot(fig)
       
elif page == "Exploratory Data Analysis":
    st.header("Exploratory Data Analysis")
    eda_data = analysis.simple_eda(df)
    
    st.subheader("Correlation Heatmap")
    cols = ['GDP', 'CPI', 'UNRATE', 'Republican Percentage', 'Democratic Percentage']
    cols = [col for col in cols if col in eda_data['correlation_matrix'].columns]

    fig, ax = plt.subplots(figsize=(10, 8))
    sns.heatmap(eda_data['correlation_matrix'].loc[cols, cols], annot=True, cmap="coolwarm", fmt=".2f",ax=ax,vmin=-1, vmax=1)
    st.pyplot(fig)
    
    st.subheader("Economic Indicators vs Vote Share")
    
    for indicator in eda_data['econ_cols']:
        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['red', 'blue']
        
        for i, vote_col in enumerate(eda_data['vote_cols']):
            sns.regplot(
                x=indicator,
                y=vote_col,
                data=eda_data['regression_data'],
                ax=ax,
                scatter=True,
                color=colors[i % len(colors)],
                label=vote_col.replace(' Percentage', ''),
                x_jitter=0.5
            )
        
        ax.set_title(f"{indicator} vs Vote Share")
        ax.set_xlabel(indicator)
        ax.set_ylabel("Vote Percentage (%)")
        ax.legend()
        ax.grid(True)
        st.pyplot(fig)

elif page == "Presidency Analysis":
    st.header("Presidency Analysis")
    
    presidents = sorted(df['President Elect'].unique())
    president = st.selectbox("Select President", presidents)
    
    if st.button("Run Analysis"):
        results = analysis.president_party_and_economic_analyis(df, president)
        
        if results is None:
            st.error("No data found for this president")
        else:
            st.subheader("Overall Economic Changes")
            overall = results['overall_economic_changes']
            st.write(f"{overall['years_in_office']} years in office.")
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("GDP Change", f"{overall['GDP_change']:.2f}")
            with col2:
                st.metric("CPI Change", f"{overall['CPI_change']:.2f}")
            with col3:
                st.metric("Unemployment Change", f"{overall['UNRATE_change']:.2f}")
            
            if results['last_year_changes']:
                st.subheader("Last Year Changes")
                last = results['last_year_changes']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("GDP Change", f"{last['GDP_change']:.2f}")
                with col2:
                    st.metric("CPI Change", f"{last['CPI_change']:.2f}")
                with col3:
                    st.metric("Unemployment Change", f"{last['UNRATE_change']:.2f}")
            
            st.subheader("Party Transition")
            transition = results['party_transition']
            if transition['party_switched'] is None:
                st.info("President still in office")
            elif transition['party_switched'] == True:
                st.success(f"Party switched from {transition['current_party']} to {transition['next_party']}. Succesor: {transition['following_president']}")
            else:
                st.info(f"Party remained {transition['current_party']}. Succesor: {transition['following_president']}")
            
            if results['state_vote_swings']:
                st.subheader("State Vote Swings (in percentage)")
                swings_df = pd.DataFrame(results['state_vote_swings'])
                st.dataframe(swings_df)