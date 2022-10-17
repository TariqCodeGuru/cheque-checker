
import pandas as pd
import numpy as np
import plotly.graph_objects as px
from datetime import datetime
import calendar

def get_cheque_status_df(cheque_register, bank_statement, start_date, end_date):
    #Reading the cheque register
    cheques = pd.read_csv(cheque_register, parse_dates=True)
    cheques.drop(columns=['KEY','Unnamed: 17','Month','Year'], inplace=True)

    cheques.columns = ['_'.join(cheque.lower().split()) for cheque in cheques.columns]

    #Cleaning and converting the amount values and delivered switch
    cheques['cheque_amount']=cheques['cheque_amount'].apply(lambda s: 0.0 if s==' -   ' else float(s.replace(","," ").replace(" ","")))
    cheques['deposit_amount']=cheques['deposit_amount'].fillna('0')
    cheques['deposit_amount']=cheques['deposit_amount'].apply(lambda s: float(s.replace(","," ").replace(" ","")))
    cheques['delivered?'] = cheques['delivered?'].apply(lambda s: 1 if (s=='y' or s=='Y') else 0)
    cheques['cashed?']=cheques['cashed?'].fillna(0).apply(lambda s: 1 if s>0 else 0)

    #Dealing with dates
    cheques['cheque_payment_start']=pd.to_datetime(cheques['cheque_payment_start'])
    cheques['cheque_date']=pd.to_datetime(cheques['cheque_date'])
    cheques['end_date']=pd.to_datetime(cheques['end_date'])

    #Dealing with numbers
    cheques['cheque_amount']=pd.to_numeric(cheques['cheque_amount'])
    cheques['deposit_amount']=pd.to_numeric(cheques['deposit_amount'])

    #Reading bank statement
    statement = pd.read_csv(bank_statement)
    statement['Value Date']=pd.to_datetime(statement['Value Date'],format="%d/%m/%Y")
    statement = statement[['Value Date', 'Narration',' Debit ', ' Credit ', ' Running Balance ']]
    statement=statement.dropna(axis=1, how='all')

    #Extracting cheque numbers
    statement['cheque_no']=statement['Narration'].apply(get_cheque_number)

    statement[' Debit ']=pd.to_numeric(statement[' Debit '])
    statement[' Credit ']=pd.to_numeric(statement[' Credit '])

    #Merging debit and credit columns
    statement[' Debit ']=statement[' Debit '].fillna(0)
    statement[' Debit ']=statement[' Debit ']*-1
    statement[' Credit ']=statement[' Credit '].fillna(0)
    statement['Amount']=statement[' Debit ']+statement[' Credit ']
    statement=statement.drop(columns=[' Debit ', ' Credit '])

    #Getting the list of cheques that were deposited based on a number present in cheque_no col
    deposited_cheques = statement[statement['cheque_no']!=0]

    #-ve means debited, and if it has a cheque_no it means it bounced.
    bounced_cheques = deposited_cheques[deposited_cheques['Amount']<0]

    # #### Reporting on the cheques status. Still open vs. bounced

    #Getting cheques based on the requested dates:
    cheques_ytd = cheques[(cheques['cheque_date']>=start_date) & (cheques['cheque_date']<=end_date)].drop(columns=['pays_for_(inclusive_of_start_date)','delivered?','cashed?'])

    #Removing records that aren't cheques in the cheque register
    cheques_ytd=cheques_ytd.drop(cheques_ytd[
        (cheques_ytd['cheque_number']=='Free') | 
        (cheques_ytd['cheque_number']=='Cash')].index)

    #Dropping a row that weirdly showed nan for cheque number
    cheques_ytd = cheques_ytd.drop(cheques_ytd[cheques_ytd['cheque_number'].isna()].index)
    cheques_ytd.reset_index(inplace=True)

    #Getting the cheques from the register
    cheques_in_register = list(set(cheques_ytd['cheque_number']))

    #Checking if the cheques have gone to the bank or not, if they have, have they bounced or not

    status_list = []
    for c in cheques_ytd.iterrows():
        if c[1]['cheque_number'] in list(set(statement['cheque_no'])):
            if c[1]['cheque_number'] in list(set(bounced_cheques['cheque_no'])):
                status_list.append('bounced')
            else:
                status_list.append('cleared')
        else:
            status_list.append('not deposited')
            
    cheques_ytd['status']=status_list
    
    return cheques_ytd
# ## This will give me a list of bounced cheques in the register format

#Getting a df of bounced cheques
def get_bounced_cheques(df):
    return df[df['status']=='bounced'].sort_values('cheque_date')

def get_undeposited_cheques(df):
    return df[df['status']=='not deposited'].sort_values('cheque_date')
# # ## Here we're going to read and extract the cheques that were deposited to the bank

# # ### This is how the algorithm works.
# # 1. Read the bank statement and clean it
# # 2. Create a new column that extracts the cheques numbers from the narration
# #     - There are two primary types of narrations as follows:
# #         - This is used for bank muscat cheques: ***Transfer 03544290 LEADING CAPITAL SPECTRUM LLC***
# #         - This is used for non bank muscat cheques: ***:-Clearing Cheque Deposit 91718620 Chq No/PO 00000023,,MTHAQ***
# #         - 
# # 

def get_cheque_number(narration):

    narration_list = narration.lower().split()

    if narration_list[0]=='transfer' and narration_list[1].isnumeric():        
        
        for x in narration_list:
            if x.isnumeric() and len(x)==8:
                return x
        return 0
    
    elif narration_list[0]==':-clearing':
        return narration_list[-1].replace(',',' ').split()[0]
    
    elif narration_list[0]==':-outward':
        return narration_list[-2]
    
    else:
        return 0
        
#         for x in narration_list:
#             if x.isnumeric() and len(x)==8:
#                 return x
#         return 0
    
#     elif narration_list[0]==':-clearing':
#         return narration_list[-1].replace(',',' ').split()[0]
    
#     elif narration_list[0]==':-outward':
#         return narration_list[-2]
    
#     else:
#         return 0