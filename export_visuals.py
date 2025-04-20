import pandas as pd
import numpy as np
import plotly.express as px

# --- REBUILD df HERE ---

# 1) Raw bookings per month (Lite / Pro / Ultra)
raw_lite  = np.array([10, 15, 20, 25, 25, 25, 25, 25, 25, 25, 25, 25])
raw_pro   = np.array([ 3,  5,  6,  8,  8,  8,  8,  8,  8,  8,  8, 12])
raw_ultra = np.array([ 0,  0,  0,  1,  0,  1,  0,  0,  1,  0,  0,  1])

# 2) Pipeline-to-close lag (60/30/10 split)
ship_lite = []
ship_pro  = []
for i in range(12):
    # previous two months (or zero if none)
    prev1_l = raw_lite[i-1] if i-1>=0 else 0
    prev2_l = raw_lite[i-2] if i-2>=0 else 0
    prev1_p = raw_pro[i-1]  if i-1>=0 else 0
    prev2_p = raw_pro[i-2]  if i-2>=0 else 0

    ship_lite.append(round(0.6*raw_lite[i] + 0.3*prev1_l + 0.1*prev2_l))
    ship_pro .append(round(0.6*raw_pro[i]  + 0.3*prev1_p + 0.1*prev2_p))

ship_lite  = np.array(ship_lite)
ship_pro   = np.array(ship_pro)
ship_ultra = raw_ultra.copy()

# 3) Cumulative installs & active users
cum_lite  = ship_lite.cumsum()
cum_pro   = ship_pro.cumsum()
cum_ultra = ship_ultra.cumsum()

# per‑device user counts
users_lite, users_pro, users_ultra = 75, 600, 4000
active_users = cum_lite*users_lite + cum_pro*users_pro + cum_ultra*users_ultra

# 4) Revenue calculations
price_lite, price_pro, price_ultra = 5600, 15000, 150000
hardware = ship_lite*price_lite + ship_pro*price_pro + ship_ultra*price_ultra

SW, SUP_L, SUP_P, SUP_U = 8, 100, 300, 2000
software = active_users * SW
support  = cum_lite*SUP_L + cum_pro*SUP_P + cum_ultra*SUP_U

# AIM fees (30% adoption Oct, ramp to 50% by Dec)
aim = np.zeros(12)
for i in range(12):
    if i >= 4:
        rate = [0.30, 0.40, 0.50][min(i-4,2)]
        aim[i] = active_users[i] * 200 * rate * 0.01

# Contributor & Enterprise streams
contrib    = np.array([12500 if m in [0,3,6,9] else 0 for m in range(12)])
enterprise = np.array([100000 if (i>=3 and ship_ultra[i]>0) else 0 for i in range(12)])

# 5) Recurring MRR & ARR
mrr = software + support + aim
arr = mrr * 12

# 6) Final DataFrame
df = pd.DataFrame({
    'Month'            : ['Jun','Jul','Aug','Sep','Oct','Nov','Dec','Jan','Feb','Mar','Apr','May'],
    'Ship Lite'        : ship_lite,
    'Ship Pro'         : ship_pro,
    'Ship Ultra'       : ship_ultra,
    'Cumulative Units' : ship_lite+ship_pro+ship_ultra,  # or (ship_lite+ship_pro+ship_ultra).cumsum() if you prefer
    'Cumulative Lite'  : ship_lite.cumsum(),
    'Cumulative Pro'   : ship_pro.cumsum(),
    'Cumulative Ultra' : ship_ultra.cumsum(),
    'Cumulative Deployed' : (ship_lite+ship_pro+ship_ultra).cumsum(),
    'Active Users'     : active_users,
    'Hardware'         : hardware,
    'Software'         : software,
    'Support'          : support,
    'AIM Fees'         : aim,
    'Contributor'      : contrib,
    'Enterprise'       : enterprise,
    'Total'            : hardware + software + support + aim + contrib + enterprise,
    'MRR'              : mrr,
    'ARR'              : arr,
    'ARPU'             : mrr / active_users,
    'Churn %'          : np.full(12, 0.0043)
})

# --- CHART 1: Monthly Revenue Streams (stacked bar) ---
fig1 = px.bar(
    df, x='Month',
    y=['Hardware','Software','Support','AIM Fees','Contributor','Enterprise'],
    title='Monthly Revenue Streams',
    labels={'value':'USD','variable':'Stream'}
)
fig1.update_layout(hovermode='x unified')
fig1.write_html('monthly_revenue_streams.html', include_plotlyjs='cdn')

# --- CHART 2: Cumulative Units Installed (line) ---
fig2 = px.line(
    df, x='Month', y='Cumulative Units',
    title='Cumulative Units Installed',
    markers=True
)
fig2.update_layout(hovermode='x')
fig2.write_html('cumulative_units.html', include_plotlyjs='cdn')

# --- CHART 3: MRR & ARR Ramp (dual-line) ---
fig3 = px.line(
    df, x='Month', y=['MRR','ARR'],
    title='MRR & ARR Ramp', markers=True
)
fig3.write_html('mrr_arr_ramp.html', include_plotlyjs='cdn')

# --- CHART 4: Unit Shipments by Tier (grouped bar) ---
fig4 = px.bar(
    df, x='Month',
    y=['Ship Lite','Ship Pro','Ship Ultra'],
    title='Shipments by Tier', barmode='group',
    labels={'value':'Units','variable':'Tier'}
)
fig4.write_html('unit_shipments.html', include_plotlyjs='cdn')

# --- CHART 5: ARPU & Churn (dual-line) ---
fig5 = px.line(
    df, x='Month', y=['ARPU','Churn %'],
    title='ARPU vs Monthly Churn',
    markers=True
)
fig5.write_html('arpu_churn.html', include_plotlyjs='cdn')

# --- CHART 6: Month-to-Month Δ Revenue (waterfall style) ---
df['Delta'] = df['Total'].diff().fillna(df['Total'])
fig6 = px.bar(
    df, x='Month', y='Delta',
    title='Month‑to‑Month Δ Revenue',
    color='Delta', color_continuous_scale=['red','green']
)
fig6.write_html('delta_revenue.html', include_plotlyjs='cdn')

# --- CHART 7: Sensitivity Analysis (waterfall) ---
base = df['Total'].sum()
sens = {
    'Rev -25%': base*0.75 - base,
    'Rev +25%': base*1.25 - base,
    'Churn -2%': base*0.98 - base,
    'Churn +2%': base*1.02 - base,
    'ARPU -10%': base*0.90 - base,
    'ARPU +10%': base*1.10 - base,
    'AIM Delay -1m': base*0.95 - base,
    'AIM Delay +1m': base*1.05 - base
}
labels, vals = zip(*sens.items())
fig7 = px.bar(
    x=vals, y=labels, orientation='h',
    title='Sensitivity Analysis Δ from Base',
    labels={'x':'Δ Total Revenue','y':''}
)
fig7.write_html('sensitivity_waterfall.html', include_plotlyjs='cdn')

# --- CHART 8: Annual Revenue Mix (pie) ---
mix = df[['Hardware','Software','Support','AIM Fees','Contributor','Enterprise']].sum().reset_index()
mix.columns = ['Stream','Value']
fig8 = px.pie(
    mix, names='Stream', values='Value',
    title='Annual Revenue Mix', hole=0.4
)
fig8.write_html('annual_mix.html', include_plotlyjs='cdn')

# --- CHART 9: Cumulative Deployments by Tier ---
fig9 = px.line(
    df,
    x='Month',
    y=['Cumulative Lite','Cumulative Pro','Cumulative Ultra','Cumulative Deployed'],
    title='Cumulative Deployments by Device Class',
    markers=True,
    labels={'value':'Units Deployed','variable':'Device Class'}
)
fig9.update_layout(
    yaxis=dict(title='Units Deployed', tickformat=','),
    hovermode='x unified'
)
for trace in fig9.data:
    trace.update(hovertemplate='%{x}<br>%{variable}: %{y:,.0f} units')
fig9.write_html('cumulative_by_tier.html', include_plotlyjs='cdn') 