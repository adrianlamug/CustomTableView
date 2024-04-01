import sys
import pandas as pd
from PyQt5 import QtWidgets

from controller import MainWindow


def create_sample_data():
    data = {
        'id': [1, 2, 3],
        'persId': ['1001', '1002', '1003'],
        'lastName': ['Martin', 'Smith', 'Smith'],
        'firstName': ['Robert', 'Brad', 'Angelina'],
        'country_id': [1, 2, 3]
    }
    df = pd.DataFrame(data)
    return df

if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    df = create_sample_data()
    window = MainWindow(df)
    sys.exit(app.exec_())
