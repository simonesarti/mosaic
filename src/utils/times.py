from datetime import datetime

"""
Split a temporal interval in a set of sub interval having similar size.
"""
def split_interval(
    start_date:datetime,
    end_date:datetime,
    num_periods:int,
):
    if(num_periods>1):
        tdelta = (end_date - start_date) / num_periods
        edges = [(start_date + i * tdelta).date().isoformat() for i in range(num_periods+1)]
        slots = [(edges[i], edges[i + 1]) for i in range(len(edges)-1)]
    else:
        slots = [(start_date.date().isoformat(), end_date.date().isoformat())]
   
    return(slots)