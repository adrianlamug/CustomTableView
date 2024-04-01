from PyQt5 import QtWidgets, QtCore


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
        sortGroup.setExclusive(True)

        actionSortAsc = QtWidgets.QAction("Sort Ascending", menu, checkable=True)
        actionSortDesc = QtWidgets.QAction("Sort Descending", menu, checkable=True)
        sortGroup.addAction(actionSortAsc)
        sortGroup.addAction(actionSortDesc)
        menu.addAction(actionSortAsc)
        menu.addAction(actionSortDesc)

        lastSortAction = self.mainWindow.getLastSortAction(columnIndex)
        if lastSortAction == "asc":
            actionSortAsc.setChecked(True)
        elif lastSortAction == "desc":
            actionSortDesc.setChecked(True)

        menu.addSeparator()
        actionResetFilters = menu.addAction("Reset Filters")


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
                self.model().sort(columnIndex, QtCore.Qt.AscendingOrder)
                self.mainWindow.setLastSortAction(columnIndex, "asc")
            elif selectedAction == actionSortDesc:
                actionSortDesc.setChecked(True)
                self.mainWindow.setLastSortAction(columnIndex, "desc")
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
