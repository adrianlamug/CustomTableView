from PyQt5 import QtCore


class SortFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(SortFilterProxyModel, self).__init__(parent)
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