import numpy as np
import pandas as pd
from sklearn.neighbors import KNeighborsRegressor
X = [[0], [1], [2], [3]]
y = [0, 1, 2, 3]

X = pd.DataFrame(X)
y = pd.DataFrame(y)

def get_ws(ds):
    ws = ds ** 0.5
    return ws

neigh = KNeighborsRegressor(n_neighbors=2, weights=lambda x: x**0.5)
neigh.fit(X, y) 
print(neigh.predict([[1.5], [2.8]]))
yjh = neigh.predict([[1.5], [2.8]])
yjh = pd.DataFrame(yjh)