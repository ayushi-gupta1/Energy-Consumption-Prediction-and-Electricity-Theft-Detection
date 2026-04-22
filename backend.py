import pandas as pd

def load_data():
    data = pd.read_csv("Final_Model_Output.csv")
    
    # Clean column names (remove spaces, lowercase)
    data.columns = data.columns.str.strip().str.lower()
    
    # Try to detect columns automatically
    # datetime column
    datetime_col = [col for col in data.columns if 'date' in col or 'time' in col][0]
    
    # actual consumption
    actual_col = [col for col in data.columns if 'actual' in col][0]
    
    # predicted consumption
    pred_col = [col for col in data.columns if 'pred' in col][0]
    
    # theft flag column (last column fallback)
    theft_col = [col for col in data.columns if 'theft' in col or 'flag' in col]
    if theft_col:
        theft_col = theft_col[0]
    else:
        theft_col = data.columns[-1]  # fallback
    
    # Rename columns to standard names
    data = data.rename(columns={
        datetime_col: 'datetime',
        actual_col: 'actual',
        pred_col: 'predicted',
        theft_col: 'theft_flag'
    })
    
    # Convert datetime
    data['datetime'] = pd.to_datetime(data['datetime'])
    
    return data


def get_theft_cases(data):
    return data[data['theft_flag'] == 1]


def get_summary(data):
    total = len(data)
    theft = len(data[data['theft_flag'] == 1])
    normal = total - theft
    
    return total, theft, normal