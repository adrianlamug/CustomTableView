import sys
import re
import pandas as pd
from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QActionGroup


class FilterHeader(QtWidgets.QHeaderView):
    filterActivated = QtCore.pyqtSignal()

    def __init__(self, parent, mainWindow):
        super().__init__(QtCore.Qt.Horizontal, parent)
        self.mainWindow = mainWindow
        self._editors = []
        self._padding = 4
        self.setStretchLastSection(True)
        self.setSectionResizeMode(QtWidgets.QHeaderView.Stretch)
        self.setDefaultAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        self.setSortIndicatorShown(False)
        self.setSectionsMovable(True)
        self.sectionResized.connect(self.adjustPositions)
        parent.horizontalScrollBar().valueChanged.connect(self.adjustPositions)

        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.headerContextMenu)


    def headerContextMenu(self, pos):
        columnIndex = self.logicalIndexAt(pos)
        menu = QtWidgets.QMenu(self)

        sortGroup = QActionGroup(self)
        actionSortAsc = menu.addAction("Sort Ascending")
        actionSortDesc = menu.addAction("Sort Descending")
        actionResetFilters = menu.addAction("Reset Filters")

        actionSortAsc.setCheckable(True)
        actionSortDesc.setCheckable(True)

        searchAction = QtWidgets.QWidgetAction(menu)
        searchEdit = QtWidgets.QLineEdit(menu)
        searchEdit.setPlaceholderText("Search...")
        searchAction.setDefaultWidget(searchEdit)
        menu.addSeparator()
        menu.addAction(searchAction)

        # Dynamic checkboxes for unique values
        unique_values = sorted(self.mainWindow.getUniqueValuesForColumn(columnIndex))
        currentFilters = self.mainWindow.getCurrentFilters(columnIndex)
        allCheckBoxActions = []

        def rebuildCheckBoxes(filterText=""):
            nonlocal allCheckBoxActions
            for action in allCheckBoxActions:
                menu.removeAction(action)
            allCheckBoxActions.clear()

            # Filter and sort unique values based on search text
            filteredValues = [val for val in unique_values if filterText.lower() in val.lower()]
            for value in filteredValues:
                checkBoxAction = QtWidgets.QWidgetAction(menu)
                checkBox = QtWidgets.QCheckBox(value, menu)
                checkBox.setChecked(value in currentFilters)
                checkBoxAction.setDefaultWidget(checkBox)
                menu.addAction(checkBoxAction)
                allCheckBoxActions.append(checkBoxAction)

        # Initially build checkboxes with all values
        rebuildCheckBoxes()

        searchEdit.textChanged.connect(rebuildCheckBoxes)
        selectedAction = menu.exec_(self.mapToGlobal(pos))


        # Check if one of the standard actions was selected
        if selectedAction:
            if selectedAction == actionSortAsc:
                actionSortAsc.setChecked(True)
                self.model().sort(columnIndex, QtCore.Qt.AscendingOrder)
            elif selectedAction == actionSortDesc:
                actionSortDesc.setChecked(True)
                self.model().sort(columnIndex, QtCore.Qt.DescendingOrder)
            elif selectedAction == actionResetFilters:
                self.mainWindow.resetAllFilters()

        selectedItems = [checkBox.text() for action in allCheckBoxActions for checkBox in [action.defaultWidget()] if checkBox.isChecked()]
        if set(selectedItems) != set(currentFilters):
            self.mainWindow.setFilterCriteria(columnIndex, selectedItems)
            self.filterActivated.emit()

    def resetAllFilters(self):
        self.mainWindow.resetAllFilters()

    def setFilterBoxes(self, count):
        while self._editors:
            editor = self._editors.pop()
            editor.deleteLater()
        for index in range(count):
            editor = QtWidgets.QLineEdit(self.parent())
            editor.setPlaceholderText('Filter')
            editor.setClearButtonEnabled(True)
            editor.returnPressed.connect(self.filterActivated.emit)
            editor.textChanged.connect(lambda text, idx=index: self.onFilterTextChanged(text, idx))
            self._editors.append(editor)
        self.adjustPositions()

    def onFilterTextChanged(self, text, index):
        if text == "":
            self.mainWindow.resetTextFilter(index)
        else:
            self.filterActivated.emit()
    def sizeHint(self):
        size = super().sizeHint()
        if self._editors:
            height = self._editors[0].sizeHint().height()
            size.setHeight(size.height() + height + self._padding)
        return size

    def updateGeometries(self):
        if self._editors:
            height = self._editors[0].sizeHint().height()
            self.setViewportMargins(0, 0, 0, height + self._padding)
        else:
            self.setViewportMargins(0, 0, 0, 0)
        super().updateGeometries()
        self.adjustPositions()

    def adjustPositions(self):
        for index, editor in enumerate(self._editors):
            height = editor.sizeHint().height()
            editor.move(
                self.sectionPosition(index) - self.offset() + 2,
                height + (self._padding // 2))
            editor.resize(self.sectionSize(index), height)

    def filterText(self, index):
        if 0 <= index < len(self._editors):
            return self._editors[index].text()
        return ''

    def setFilterText(self, index, text):
        if 0 <= index < len(self._editors):
            self._editors[index].setText(text)

    def clearFilters(self):
        for editor in self._editors:
            editor.clear()

class HumanProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(HumanProxyModel, self).__init__(parent)
        self.textFilters = {}
        self.advancedFilters = {}

    def setTextFilter(self, columnIndex, text):
        columnName = self.sourceModel().headerData(columnIndex, QtCore.Qt.Horizontal)
        if text == "":
            if columnName in self.textFilters:
                del self.textFilters[columnName]
        else:
            self.textFilters[columnName] = text
        self.invalidateFilter()

    def setAdvancedFilter(self, columnName, criteria):
        if criteria:
            self.advancedFilters[columnName] = criteria
        else:
            # Remove the filter if no criteria are selected
            if columnName in self.advancedFilters:
                del self.advancedFilters[columnName]
        self.invalidateFilter()

    def filterAcceptsRow(self, sourceRow, sourceParent):
        sourceModel = self.sourceModel()
        for columnIndex in range(sourceModel.columnCount()):
            columnName = sourceModel.headerData(columnIndex, QtCore.Qt.Horizontal)
            if columnName in self.textFilters:
                if not self.applyTextFilter(columnIndex, self.textFilters[columnName], sourceRow, sourceParent):
                    return False
            if columnName in self.advancedFilters:
                if not self.applyAdvancedFilter(columnIndex, self.advancedFilters[columnName], sourceRow, sourceParent):
                    return False
        return True

    def applyTextFilter(self, columnIndex, text, sourceRow, sourceParent):
        if not text:
            return True
        index = self.sourceModel().index(sourceRow, columnIndex, sourceParent)
        return text.lower() in str(index.data()).lower()

    def applyAdvancedFilter(self, columnIndex, criteria, sourceRow, sourceParent):
        if not criteria:
            return True
        index = self.sourceModel().index(sourceRow, columnIndex, sourceParent)
        return str(index.data()) in criteria

class winMain(QtWidgets.QMainWindow):
    def __init__(self, df, parent=None):
        super().__init__(parent)
        self.df = df
        self.setupUi()
        self.setGeometry(300,200,700,500)
        self.show()

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
        proxy = HumanProxyModel(self)
        proxy.setSourceModel(model)
        self.tableView.setModel(proxy)

        header.setFilterBoxes(self.df.shape[1])
        header.filterActivated.connect(self.handleFilterActivated)

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
    window = winMain(df)
    sys.exit(app.exec_())
