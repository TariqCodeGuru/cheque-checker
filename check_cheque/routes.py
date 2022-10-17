from tracemalloc import start
from check_cheque import app
from flask import render_template
from scripts.check_cheques_1 import get_cheque_status_df, get_bounced_cheques, get_undeposited_cheques
import plotly.graph_objs as go
import plotly, json
import pandas as pd


end_date=pd.to_datetime('2022-09-30')
start_date=pd.to_datetime('2022-01-01')

full_df = get_cheque_status_df('./data/cheques.csv', './data/bank_statement.csv', start_date, end_date)
bounced_df = get_bounced_cheques(full_df)
undeposit_df = get_undeposited_cheques(full_df)

##Grouping the new, clean df (which includes infor about the cheque status) by month and status
grouped_sum = full_df.groupby([full_df['cheque_date'].dt.month, 'status'],).sum().drop(columns='index')
grouped_count = full_df.groupby([full_df['cheque_date'].dt.month, 'status']).count().drop(columns='index')


### Visualization

#GRAPH 1 - Amounts
x = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct']
 
graph_one = [go.Bar(
    name = 'Cleared',
    x = x,
    #the cleared values retrieved from the groupby object using a cross-section method 
    y = grouped_sum.xs('cleared',level=1)['cheque_amount']/1000,
    ), go.Bar(
    name = 'Bounced',
    x = x,
    #the cleared values retrieved from the groupby object using a cross-section method 
    y = grouped_sum.xs('bounced',level=1)['cheque_amount']/1000,
   ),go.Bar(
    name = 'Not Deposited',
    x = x,
    #the cleared values retrieved from the groupby object using a cross-section method 
    y = grouped_sum.xs('not deposited',level=1)['cheque_amount']/1000,
   )]

layout_one = dict(title='Cheque Amounts by Status',
            yaxis=dict(title='OMR 000'),
             barmode='stack')

#GRAPH 2 - Counts
graph_two = [go.Bar(
    name = 'Cleared',
    x = x,
    #the cleared values retrieved from the groupby object using a cross-section method 
    y = grouped_count.xs('cleared',level=1)['cheque_amount'],
    ), go.Bar(
    name = 'Bounced',
    x = x,
    #the cleared values retrieved from the groupby object using a cross-section method 
    y = grouped_count.xs('bounced',level=1)['cheque_amount'],
   ),go.Bar(
    name = 'Not Deposited',
    x = x,
    #the cleared values retrieved from the groupby object using a cross-section method 
    y = grouped_count.xs('not deposited',level=1)['cheque_amount'],
   )]

layout_two = dict(title='Cheque Counts by Status',
            yaxis=dict(title='# of Cheques'),
             barmode='stack')

#Adding graphs to figures
figures=[]
figures.append(dict(data=graph_one, layout=layout_one))
figures.append(dict(data=graph_two, layout=layout_two))

ids=['figures-{}'.format(i) for i, _ in enumerate(figures)]

figuresJSON = json.dumps(figures,cls=plotly.utils.PlotlyJSONEncoder)





@app.route('/')
@app.route('/index')
def root():
    return render_template('index.html')

@app.route('/cheque_status')
def cheque_status():
    return render_template('cheque_status.html', ids=ids, figuresJSON=figuresJSON)

@app.route('/unpaid_cheques')
def unpaid_cheques():
    return render_template('unpaid_cheques.html', tables=[bounced_df.to_html(classes='data')], titles=bounced_df.columns.values)

@app.route('/undeposited_cheques')
def undeposited_cheques():
    return render_template('undeposited_cheques.html', tables=[undeposit_df.to_html(classes='data')], titles=undeposit_df.columns.values)