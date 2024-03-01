"""
Split a temporal interval in a set of sub interval having similar size.
"""
def split_interval(start, end, n):
    if(n>1):
        tdelta = (end - start) / n
        edges = [(start + i * tdelta).date().isoformat() for i in range(n+1)]
        slots = [(edges[i], edges[i + 1]) for i in range(len(edges)-1)]
    else:
        slots = [(start.date().isoformat(), end.date().isoformat())]
    return(slots)