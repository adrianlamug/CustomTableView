from PyQt5 import QtWidgets, QtGui, QtCore

from filter_header import FilterHeader
from model import SortFilterProxyModel


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df
        self.lastSortActions = {}
        self.setupUi()
        self.setGeometry(300,200,700,500)
        self.show()

    def getLastSortAction(self, columnIndex):
        """Retrieve the last sort action for a given column index."""
        return self.lastSortActions.get(columnIndex, None)

    def setLastSortAction(self, columnIndex, sortAction):
        """Set the last sort action for a given column index."""
        self.lastSortActions[columnIndex] = sortAction

    def getUniqueValuesForColumn(self, columnIndex):
        columnName = self.df.columns[columnIndex]
        unique_values = self.df[columnName].unique().tolist()
        return [str(value) for value in unique_values]

    def getCurrentFilters(self, columnIndex):
        columnName = self.df.columns[columnIndex]
        if columnName in self.tableView.model().advancedFilters:
            return self.tableView.model().advancedFilters[columnName]
        return []

    def setFilterCriteria(self, columnIndex, selectedItems):
        columnName = self.df.columns[columnIndex]
        self.tableView.model().setAdvancedFilter(columnName, selectedItems)

    def createPersonModel(self, parent):
        model = QtGui.QStandardItemModel(0, self.df.shape[1], parent)
        model.setHorizontalHeaderLabels(self.df.columns.tolist())
        for row in self.df.itertuples(index=False):
            items = [QtGui.QStandardItem(str(field)) for field in row]
            model.appendRow(items)
        return model

    def handleFilterActivated(self):
        header = self.tableView.horizontalHeader()
        # filters = []

        for i in range(header.count()):
            text = header.filterText(i)
            if text:
                self.tableView.model().setTextFilter(i, text)

    def resetAllFilters(self):
        proxyModel = self.tableView.model()
        proxyModel.textFilters.clear()
        proxyModel.advancedFilters.clear()
        proxyModel.invalidateFilter()
        # Optionally, clear all QLineEdit widgets in the FilterHeader
        header = self.tableView.horizontalHeader()
        if isinstance(header, FilterHeader):
            for editor in header._editors:
                editor.clear()

    def columnIndex(self, columnName):
        """Find the index of a column in the model by its header name"""
        model = self.tableView.model().sourceModel()
        for column in range(model.columnCount()):
            if model.headerData(column, QtCore.Qt.Horizontal) == columnName:
                return column
        return -1

    def resetTextFilter(self, columnIndex):
        self.tableView.model().setTextFilter(columnIndex, "")
        self.tableView.model().invalidateFilter()

    def setupUi(self):
        self.centralwidget = QtWidgets.QWidget(self)
        self.horizontalLayout = QtWidgets.QHBoxLayout(self.centralwidget)

        self.tableView = QtWidgets.QTableView(self.centralwidget)

        self.tableView.setSortingEnabled(True)
        self.tableView.setAlternatingRowColors(True)
        self.tableView.setSelectionMode(QtWidgets.QAbstractItemView.SingleSelection)
        self.tableView.verticalHeader().setVisible(False)

        self.horizontalLayout.addWidget(self.tableView)
        self.setCentralWidget(self.centralwidget)

        header = FilterHeader(self.tableView, self)
        self.tableView.setHorizontalHeader(header)

        self.statusBar = QtWidgets.QStatusBar()
        self.setStatusBar(self.statusBar)

        model = self.createPersonModel(self)
        proxy = SortFilterProxyModel(self)
        proxy.setSourceModel(model)
        self.tableView.setModel(proxy)

        header.setFilterBoxes(self.df.shape[1])
        header.filterActivated.connect(self.handleFilterActivated)
