import sys

import pandas as pd
from PySide6.QtCore import Qt, QSortFilterProxyModel
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QHBoxLayout,
    QVBoxLayout,
    QWidget,
    QLineEdit,
    QSplitter,
    QTableView,
    QPushButton,
    QAbstractItemView,
)

from utils.sql_controller import read_sql, SQLController
from config.sql_config import ITEMS_SQL_CONFIG
from config.sql_paths import SELECT_ITEMS_SQL_PATH


class MultiColumnFilterProxyModel(QSortFilterProxyModel):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.clear_filters()

    def set_filter(self, column, value):
        if not value:
            if column in self.filter_conditions:
                del self.filter_conditions[column]
        else:
            self.filter_conditions[column] = str(value).lower()

        self.invalidateFilter()

    def clear_filters(self):
        self.filter_conditions = {}
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row, source_parent):
        if not self.filter_conditions:
            return False

        model = self.sourceModel()
        for col, search_text in self.filter_conditions.items():
            index = model.index(source_row, col, source_parent)
            item_text = str(model.data(index)).lower()
            if item_text != search_text:
                return False

        return True


class DataManager:

    def __init__(self):
        self.sql_controller = SQLController(ITEMS_SQL_CONFIG)

    def read_parents(self):
        select_items_sql = read_sql(SELECT_ITEMS_SQL_PATH)
        parents_df = (
            self.sql_controller.execute_sql_to_df(select_items_sql)[["parent_name"]]
            .drop_duplicates()
            .reset_index(drop=True)
        )
        return parents_df

    def read_items(self):
        select_items_sql = read_sql(SELECT_ITEMS_SQL_PATH)
        items_df = self.sql_controller.execute_sql_to_df(select_items_sql)
        return items_df


class ParentWidget(QWidget):

    def __init__(self, source_model, on_clicked):
        super().__init__()
        layout = QVBoxLayout()
        self.search_bar = QLineEdit()
        self.search_bar.setPlaceholderText("キーワードで検索...")
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.proxy_model = QSortFilterProxyModel()
        self.proxy_model.setSourceModel(source_model)
        self.proxy_model.setFilterKeyColumn(0)
        self.table_view.setModel(self.proxy_model)
        self.search_bar.textChanged.connect(self.proxy_model.setFilterFixedString)
        layout.addWidget(self.search_bar)
        layout.addWidget(self.table_view)
        self.setLayout(layout)
        self.table_view.clicked.connect(on_clicked)


class ChildWidget(QWidget):

    def __init__(self, source_model):
        super().__init__()
        layout = QVBoxLayout()
        self.table_view = QTableView()
        self.table_view.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.proxy_model = MultiColumnFilterProxyModel()
        self.proxy_model.setSourceModel(source_model)
        self.proxy_model.setFilterKeyColumn(1)
        self.table_view.setModel(self.proxy_model)
        self.table_view.setColumnHidden(0, True)
        layout.addWidget(self.table_view)
        self.setLayout(layout)

    def filtered_by_parent(self, parent):
        self.proxy_model.set_filter(0, parent)


class MainWindow(QMainWindow):

    SCREEN_WIDTH = 800
    SCREEN_HEIGHT = 800

    def __init__(self):

        super().__init__()
        self.item_data_manager = DataManager()
        self.resize(self.SCREEN_WIDTH, self.SCREEN_HEIGHT)
        self.setWindowTitle("list_test")
        main_widget = QWidget(self)
        main_layout = QHBoxLayout(main_widget)
        splitter = QSplitter(Qt.Horizontal)

        parents_model = self.read_parents_model()

        self.parent_widget = ParentWidget(parents_model, self.on_clicked)

        items_model = self.read_items_model()

        self.child_widget = ChildWidget(items_model)

        splitter.addWidget(self.parent_widget)
        splitter.addWidget(self.child_widget)

        main_layout.addWidget(splitter)
        self.setCentralWidget(main_widget)

    def read_parents_model(self):
        parents_model = QStandardItemModel(0, 1)
        parents_model.setHorizontalHeaderLabels(["parent"])

        parents_df = self.item_data_manager.read_parents()
        for item in parents_df.itertuples(index=False):
            row_item = [QStandardItem(field) for field in item]
            parents_model.appendRow(row_item)
        return parents_model

    def read_items_model(self):
        items_model = QStandardItemModel(0, 3)
        items_model.setHorizontalHeaderLabels(["parent", "item", "status"])

        items_df = self.item_data_manager.read_items()
        for item in items_df.itertuples(index=False):
            row_item = [QStandardItem(field) for field in item[1:]]
            items_model.appendRow(row_item)
        return items_model

    def on_clicked(self, index):
        row = index.row()
        parent = index.sibling(row, 0).data()
        self.child_widget.filtered_by_parent(parent)


def main():
    app = QApplication()
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
