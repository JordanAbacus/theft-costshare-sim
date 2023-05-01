""" PEV Theft Cost-Sharing Program Simulation
    =========================================

"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import random
from millify import millify

INIT_MEMBER_500 = 30
INIT_MEMBER_1000 = 50
INIT_MEMBER_1500 = 10
INIT_MEMBER_2000 = 10
INIT_MEMBER_2500 = 0

INIT_INITIATION_FEE_PCT = 10
INIT_MONTHLY_MEMBERSHIP_FEE_PCT = 1.0
INIT_TAKE_RATE_PCT = 10.0
INIT_ANNUAL_THEFT_RATE_PCT = 5.0

df_members = None
df_cols = ['id', 'coverage_amt', 'paid_in_capital']

def memberCount():
    return (
        st.session_state['members_500'] + 
        st.session_state['members_1000'] +
        st.session_state['members_1500'] +
        st.session_state['members_2000'] +
        st.session_state['members_2500']
    )

def totalCoverage():
    return (
        (st.session_state['members_500'] * 500) + 
        (st.session_state['members_1000'] * 1000) +
        (st.session_state['members_1500'] * 1500) +
        (st.session_state['members_2000'] * 2000) +
        (st.session_state['members_2500'] * 2500)
    )

def targetFundAmount():
    #return totalCoverage() * (st.session_state['annual_theft_rate_pct'] / 100) * 2
    return totalCoverage() * (st.session_state['target_fund_amt_pct'] / 100)

def maxFundAmount():
    return totalCoverage() * (st.session_state['max_fund_amt_pct'] / 100)

def monthlyTheftRate():
    return (st.session_state['annual_theft_rate_pct'] / 1200.0)

def isMemberVehicleStolen():
    """ return true if stolen, false if not """
    if random.random() < monthlyTheftRate():
        return True
    else:
        return False

def stolenVehicleIDs():
    stolen_vehicle_ids = []
    for i in range(memberCount()):
        if isMemberVehicleStolen():
            stolen_vehicle_ids.append(i)
    return stolen_vehicle_ids

def initMemberDataFrame():
    global df_members
    data = []
    count = 0

    for i in range(st.session_state['members_500']):
        row = [count, 500.0, 500.0 * (st.session_state['initiation_fee_pct']/100.0)]
        data.append(row)
        count += 1

    for i in range(st.session_state['members_1000']):
        row = [count, 1000.0, 1000.0 * (st.session_state['initiation_fee_pct']/100.0)]
        data.append(row)
        count += 1

    for i in range(st.session_state['members_1500']):
        row = [count, 1500.0, 1500.0 * (st.session_state['initiation_fee_pct']/100.0)]
        data.append(row)
        count += 1

    for i in range(st.session_state['members_2000']):
        row = [count, 2000.0, 2000.0 * (st.session_state['initiation_fee_pct']/100.0)]
        data.append(row)
        count += 1

    for i in range(st.session_state['members_2500']):
        row = [count, 2500.0, 2500.0 * (st.session_state['initiation_fee_pct']/100.0)]
        data.append(row)
        count += 1

    df_members = pd.DataFrame(data, columns=df_cols)

def executeSimulation():
    # Bjondi's idea: Monthly Fee Adjustment = ((Total Reserve + Deposit) / (Users * Coverage)) * Theft Rate
    global df_members
    initMemberDataFrame()

    sim_num_months = st.session_state["sim_num_months"]
    sim_num_iterations = st.session_state["sim_num_iterations"]

    dyn_rate_adjust = st.session_state["dyn_rate_adjust"]

    cols = []
    data = [[] for i in range(sim_num_months + 1)]
    rates = [[] for i in range(sim_num_months + 1)]

    premiums_500 = [[] for i in range(sim_num_months + 1)]
    premiums_1000 = [[] for i in range(sim_num_months + 1)]
    premiums_1500 = [[] for i in range(sim_num_months + 1)]
    premiums_2000 = [[] for i in range(sim_num_months + 1)]
    premiums_2500 = [[] for i in range(sim_num_months + 1)]

    # add the time axis
    cols.append('month')
    for i in range(sim_num_months + 1):
        data[i].append(i)
        rates[i].append(i)
        premiums_500[i].append(i)
        premiums_1000[i].append(i)
        premiums_1500[i].append(i)
        premiums_2000[i].append(i)
        premiums_2500[i].append(i)

    for j in range(sim_num_iterations):
        cols.append(str(j))
        initial_fund_value = totalCoverage() * (st.session_state['initiation_fee_pct']/100)

        data[0].append(initial_fund_value)

        initial_monthly_rate = st.session_state['monthly_membership_fee_pct'] / 100
        current_monthly_rate = initial_monthly_rate
        rates[0].append(initial_monthly_rate)

        premiums_500[0].append(initial_monthly_rate * 500.0)
        premiums_1000[0].append(initial_monthly_rate * 1000.0)
        premiums_1500[0].append(initial_monthly_rate * 1500.0)
        premiums_2000[0].append(initial_monthly_rate * 2000.0)
        premiums_2500[0].append(initial_monthly_rate * 2500.0)

        for i in range(sim_num_months):
            fund_amount_last_month = data[i][-1]
            fund_income = totalCoverage() * (current_monthly_rate)
            fund_losses = 0

            stolen_vehicle_ids = stolenVehicleIDs()
            for stolen_vehicle_id in stolen_vehicle_ids:
                fund_losses += df_members.loc[stolen_vehicle_id]['coverage_amt']

            fund_amount_this_month = fund_amount_last_month + fund_income - fund_losses
            data[i + 1].append(fund_amount_this_month)

            # optionally calculate new rate
            # target fund amount = theft rate x 2 x total coverage 
            # max fund amount = some multiple of target fund
            if dyn_rate_adjust:
                diff_from_target = fund_amount_this_month - targetFundAmount()
                if diff_from_target >= 0: # at or above target
                    # should lower rate to essentially maintain expected monthly losses
                    #current_monthly_rate = (
                    #    (targetFundAmount() - diff_from_target) / targetFundAmount()
                    #    ) * monthlyTheftRate()
                    current_monthly_rate = (
                            (maxFundAmount() - targetFundAmount() - diff_from_target) / 
                            (maxFundAmount() - targetFundAmount())
                        ) * monthlyTheftRate()
                else: # below target
                    # should raise the rate to reach target fund amount within X months
                    target_total_monthly_fee = (-1 * diff_from_target) / st.session_state['num_months_to_target']
                    current_monthly_rate = (target_total_monthly_fee / totalCoverage()) + monthlyTheftRate()
                rates[i + 1].append(current_monthly_rate)

                premiums_500[i + 1].append(current_monthly_rate * 500.0)
                premiums_1000[i + 1].append(current_monthly_rate * 1000.0)
                premiums_1500[i + 1].append(current_monthly_rate * 1500.0)
                premiums_2000[i + 1].append(current_monthly_rate * 2000.0)
                premiums_2500[i + 1].append(current_monthly_rate * 2500.0)


        #data.append(fund_amount_per_month)

    #st.session_state['funds_per_month'] = pd.DataFrame(data, columns=cols)
    st.session_state['funds_per_month'] = pd.DataFrame(data, columns=cols)
    st.session_state['rates_per_month'] = pd.DataFrame(rates, columns=cols)

    st.session_state['premiums_500'] = pd.DataFrame(premiums_500, columns=cols)
    st.session_state['premiums_1000'] = pd.DataFrame(premiums_1000, columns=cols)
    st.session_state['premiums_1500'] = pd.DataFrame(premiums_1500, columns=cols)
    st.session_state['premiums_2000'] = pd.DataFrame(premiums_2000, columns=cols)
    st.session_state['premiums_2500'] = pd.DataFrame(premiums_2500, columns=cols)


with st.sidebar:
    st.header("Number of Members")

    st.number_input(
        label="with $500 coverage",
        min_value=0,
        max_value=1000,
        value=INIT_MEMBER_500,
        step=1,
        key="members_500"
    )

    st.number_input(
        label="with $1000 coverage",
        min_value=0,
        max_value=1000,
        value=INIT_MEMBER_1000,
        step=1,
        key="members_1000"
    )

    st.number_input(
        label="with $1500 coverage",
        min_value=0,
        max_value=1000,
        value=INIT_MEMBER_1500,
        step=1,
        key="members_1500"
    )

    st.number_input(
        label="with $2000 coverage",
        min_value=0,
        max_value=1000,
        value=INIT_MEMBER_2000,
        step=1,
        key="members_2000"
    )

    st.number_input(
        label="with $2500 coverage",
        min_value=0,
        max_value=1000,
        value=INIT_MEMBER_2500,
        step=1,
        key="members_2500"
    )

    st.header("Payment Details")

    st.number_input(
        label="Initiation fee (%)",
        min_value=0,
        max_value=100,
        value=INIT_INITIATION_FEE_PCT,
        step=1,
        key="initiation_fee_pct"
    )

    st.number_input(
        label="Monthly membership fee (%)",
        min_value=0.0,
        max_value=100.0,
        value=INIT_MONTHLY_MEMBERSHIP_FEE_PCT,
        step=0.1,
        key="monthly_membership_fee_pct"
    )

    st.number_input(
        label="Take rate (%)",
        min_value=0.0,
        max_value=25.0,
        value=INIT_TAKE_RATE_PCT,
        step=0.1,
        key="take_rate_pct"
    )

    st.header("Assumptions")

    st.number_input(
        label="Annual theft rate",
        min_value=0.0,
        max_value=20.0,
        value=INIT_ANNUAL_THEFT_RATE_PCT,
        step=0.1,
        key="annual_theft_rate_pct"
    )

#######
# APP #
#######

st.title("PEV Theft Cost-Sharing Simulation")

st.markdown(
"""
[Skip the explanation](#starting-conditions)

This is a simulation tool to help understand the **StableCare** cost-sharing membership program, including: 
- how it works
- how the fees are calculated 
- how much the membership might cost you

### What is StableCare?

StableCare is a theft insurance **alternative** designed to offer ***affordable theft coverage*** for PEV owners who:
-  are unable to purchase theft insurance (because their vehicle is not covered); or
-  feel the premiums for existing theft insurance are too damn high

#### What makes StableCare different from traditional insurance?

As an *alternative* to traditional theft insurance, StableCare aims to move away from the typical incentive structures of insurance. Because Traditional insurance companies keep the premiums they collect that aren't paid out to claimants, they are incentivized to maximize the premiums collected and minimize the claims paid out. 

In contrast, StableCare shifts the cost of theft from the individual to a group of *members*, who **share** in the cost. Rather than overpaying a fixed preimum (a portion of which is kept by the insurance company), StableCare members pay an algorithmically-adjusted ***membership fee*** that changes to match the true rate of theft.

As a result, your membership fees don't stay artificially high if there are fewer claims than expected. If the group of members takes steps to reduce the chance of theft, everyone benefits with lower monthly fees!

#### How does StableCare work?

The principle behind the StableCare cost-sharing method is fairly simple:

- A common fund is initially capitalized through a refundable deposit from each of the members. 
- Thereafter, monthly fees are collected from each of the members, which builds up money in the common fund. 
- Over time, claims are paid out, which depletes money from the fund.
- The monthly fees are dynamically adjusted to try to maintain a target amount of money in the fund (e.g., 10% of the total coverage amount)

More specifically, the method works as follows:

1. A group of members each pay an **initiation fee**, which functions like a reverse deductible and is a refundable deposit. The initiation fees serve to capitalize a common fund, into which monthly membership fees will also be paid, and from which claims will be paid out. 

> *A conservative initiation fee is set at twice the annual theft rate (e.g., 10%, assuming a 5% annual theft rate).*

2. Thereafter, members pay a monthly **membership fee**, which functions similarly to a premium. This membership fee is determined algorithmically (see algorithm description below), with the goal of maintaining a target amount of money in the fund. Thus, if the fund is fully- or *over*-capitalized, the monthly fees are reduced linearly from a **reference rate** (1/12 the expected annual theft rate) when the fund is at the target amount to 0% when the fund is at a designated maximum amount. Conversely, if the fund is *under*-capitalized, the monthly fees are increased above the reference rate to reach the target amount within a specified period of time (such as within 3 months) so as to reduce the risk of insolvency.
3. Theft claims by members are submitted to Stable, who conducts the initial review of the evidence of the theft and considering the full context of the situation. Stable then issues an opinion and an initial decision of whether to pay out the claim. Once that opinion is issued, StableCare members are invited to review the decision and can either approve, veto, or abstain the decision. If a supermajority of the members veto Stable's decision, the decision is overridden—so a denial of a claim is switched to an approval, or vice versa. This gives the members the ultimate decision-making authority on whether a claim is paid out.
4. If a member decides to leave the StableCare membership program ***and*** they did **not** submit and get paid out for any claims, then that member is entitled to a refund for their initiation fee.
5. If a member submits a claim and it gets paid out, and subsequently wishes to continue their membership, that member will be required to pay another initiation fee.


### How does this simulation work?

StableCare is a theft insurance **alternative** designed to offer ***affordable theft coverage*** for PEV owners who:
-  are unable to purchase theft insurance (because their vehicle is not covered); or
-  feel the premiums for existing theft insurance are too damn high
"""
)

with st.container():
    st.header("Starting Conditions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Total number of customers",
            value=memberCount()
        )

    with col2:
        st.metric(
            label="Total coverage",
            value="$" + millify(totalCoverage(), precision=2)
        )

    with col3:
        st.metric(
            label="Initial funds",
            value="$" + millify(totalCoverage() * (st.session_state['initiation_fee_pct']/100), precision=2)
        )

    with col4:
        st.metric(
            label="Monthly membership fees",
            value="$" + millify(totalCoverage() * (st.session_state['monthly_membership_fee_pct']/100), precision=2)
        )


with st.container():
    st.header("Simulation")
    col5, col6, _ = st.columns(3)

    with col5:
        st.number_input(
            label="Number of months",
            min_value=1,
            max_value=60,
            value=24,
            step=1,
            key="sim_num_months"
        )

    with col6:
        st.number_input(
            label="Number of iterations",
            min_value=1,
            max_value=100,
            value=5,
            step=1,
            key="sim_num_iterations"
        )


with st.container():
    st.subheader("Dynamic Rate Adjustment (DRA)")

    st.checkbox(
        label="Enable DRA",
        value=False,
        key="dyn_rate_adjust"
    )

    col7, col8, col9 = st.columns(3)

    with col7:
        st.number_input(
            label="Target fund amount (% of coverage)",
            min_value=1,
            max_value=100,
            value=10,
            step=1,
            key="target_fund_amt_pct"
        )

        st.number_input(
            label="Max fund amount (% of coverage)",
            min_value=1,
            max_value=100,
            value=20,
            step=1,
            key="max_fund_amt_pct"
        )

        st.number_input(
            label="Number of months to reach target",
            min_value=1,
            max_value=12,
            value=3,
            step=1,
            key="num_months_to_target",
            help="""
            How quickly should the membership fees bring the fund back up to the target, 
            assuming that thefts occur at the expected theft rate? 
            More months = lower rate hikes, but more time to replenish from a deficit."""
        )

    with col8:
        st.metric(
            label="Target fund amount ($)",
            value="$" + millify(targetFundAmount(), precision=2)
        )

        st.metric(
            label="Max fund amount ($)",
            value="$" + millify(maxFundAmount(), precision=2)
        )


    st.button(
        label="Run simulation",
        on_click=executeSimulation
    )


try:
    # get the simulation result column names
    y_cols = list(st.session_state['funds_per_month'].columns.values)
    y_cols.remove('month') # remove the time axis

    st.subheader('Funds per month')
    fig_funds_per_month = px.line(
        st.session_state['funds_per_month'],
        x="month",
        y=y_cols
    )
    fig_funds_per_month.add_hline(
        y=targetFundAmount(),
        line_dash="dot",
        annotation_text="Target Fund Amount"
    )
    fig_funds_per_month.add_hline(
        y=maxFundAmount(),
        line_dash="dot",
        annotation_text="Max Fund Amount"
    )
    st.plotly_chart(fig_funds_per_month)

    st.subheader('Rates per month')
    fig_rates_per_month = px.line(
        st.session_state['rates_per_month'],
        x="month",
        y=y_cols
    )
    st.plotly_chart(fig_rates_per_month)

    tab500, tab1000, tab1500, tab2000, tab2500 = st.tabs(["$500", "$1K", "$1.5K", "$2K", "$2.5K"])

    with tab500:
        st.subheader('To be implemented (check out $1000)')

    with tab1000:
        st.subheader('Premiums per month ($1000 coverage)')
        fig_premiums_1000_per_month = px.line(
            st.session_state['premiums_1000'],
            x="month",
            y=y_cols
        )
        st.plotly_chart(fig_premiums_1000_per_month)

        # calculate some stats
        summary_cols_1000 = ['id', 'avg_fee', 'median_fee', 'min_fee', 'max_fee', 'total_fee']
        #data = [ [] for i in range(len(y_cols)) ]
        data_1000 = []

        for i in range(len(y_cols)):
            data_col = st.session_state['premiums_1000'][y_cols[i]]
            data_1000.append([
                y_cols[i],
                round(data_col.mean(), 2),
                round(data_col.median(), 2),
                round(data_col.min(), 2),
                round(data_col.max(), 2),
                round(data_col.sum(), 2)
            ])

        df_summary_1000 = pd.DataFrame(data_1000, columns=summary_cols_1000)

        col1000_1, col1000_2, col1000_3, col1000_4 = st.columns(4)

        with col1000_1:
            st.metric(
                label="Minimum average fee",
                value=f"${df_summary_1000['avg_fee'].min():.2f}"
            )
            st.metric(
                label="Minimum median fee",
                value=f"${df_summary_1000['median_fee'].min():.2f}"
            )
            st.metric(
                label="Minimum highest fee",
                value=f"${df_summary_1000['max_fee'].min():.2f}"
            )
            st.metric(
                label="Minimum lowest fee",
                value=f"${df_summary_1000['min_fee'].min():.2f}"
            )
            st.metric(
                label="Minimum total fees",
                value=f"${df_summary_1000['total_fee'].min():.2f}"
            )

        with col1000_2:
            st.metric(
                label="Mean average fee",
                value=f"${df_summary_1000['avg_fee'].mean():.2f}"
            )
            st.metric(
                label="Mean median fee",
                value=f"${df_summary_1000['median_fee'].mean():.2f}"
            )
            st.metric(
                label="Mean highest fee",
                value=f"${df_summary_1000['max_fee'].mean():.2f}"
            )
            st.metric(
                label="Mean lowest fee",
                value=f"${df_summary_1000['min_fee'].mean():.2f}"
            )
            st.metric(
                label="Mean total fee",
                value=f"${df_summary_1000['total_fee'].mean():.2f}"
            )

        with col1000_3:
            st.metric(
                label="Median average fee",
                value=f"${df_summary_1000['avg_fee'].median():.2f}"
            )
            st.metric(
                label="Median median fee",
                value=f"${df_summary_1000['median_fee'].median():.2f}"
            )
            st.metric(
                label="Median highest fee",
                value=f"${df_summary_1000['max_fee'].median():.2f}"
            )
            st.metric(
                label="Median lowest fee",
                value=f"${df_summary_1000['min_fee'].median():.2f}"
            )
            st.metric(
                label="Median total fee",
                value=f"${df_summary_1000['total_fee'].median():.2f}"
            )

        with col1000_4:
            st.metric(
                label="Max average fee",
                value=f"${df_summary_1000['avg_fee'].max():.2f}"
            )
            st.metric(
                label="Max median fee",
                value=f"${df_summary_1000['median_fee'].max():.2f}"
            )
            st.metric(
                label="Max highest fee",
                value=f"${df_summary_1000['max_fee'].max():.2f}"
            )
            st.metric(
                label="Max lowest fee",
                value=f"${df_summary_1000['min_fee'].max():.2f}"
            )
            st.metric(
                label="Max total fee",
                value=f"${df_summary_1000['total_fee'].max():.2f}"
            )

        with st.expander("All summary data"):
            st.dataframe(df_summary_1000)

    with tab1500:
        st.subheader('To be implemented (check out $1000)')

    with tab2000:
        st.subheader('To be implemented (check out $1000)')

    with tab2500:
        st.subheader('To be implemented (check out $1000)')


except KeyError:
    pass


#st.dataframe(df_members)

