import numpy as np
from typing import List

def write_data_to_tecplot_format(filename: str, title: str, data: np.ndarray,
                                 variables: List[str], zone: str):
    """
    Writes line data to tecplot format
    """
    vars = ''
    for var in variables:
        vars += f' "{var}"'
    columns = data.shape[0]
    header = (f'TITLE     = "{title}"\n' +
              f'VARIABLES ={vars}\n' +
              f'ZONE T="{zone}"  I={columns}, ZONETYPE=Ordered DATAPACKING=POINT')
    np.savetxt(filename, data, header=header, comments='')
