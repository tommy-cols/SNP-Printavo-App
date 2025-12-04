from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor
import csv
import os


class DataPreviewGUI(QDialog):
    """GUI for previewing CSV data before creating quote"""

    def __init__(self, csv_path, parent=None):
        super().__init__(parent)
        self.csv_path = csv_path
        self.setWindowTitle("Preview Order Data")
        self.setModal(True)
        self.setMinimumWidth(900)
        self.setMinimumHeight(600)

        self.has_unsaved_changes = False

        self.init_ui()
        self.load_csv_data()

    def init_ui(self):
        """Initialize the user interface"""
        layout = QVBoxLayout()

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("Data Preview")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # File info
        filename = os.path.basename(self.csv_path)
        file_label = QLabel(f"File: {filename}")
        file_label.setStyleSheet("color: #666; font-size: 11px;")
        header_layout.addWidget(file_label)

        layout.addLayout(header_layout)

        # Description
        desc = QLabel(
            "Review and edit the extracted order data below. Double-click any cell to edit. Changes are saved automatically."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(desc)

        # Table
        self.table = QTableWidget()
        self.setup_table()
        layout.addWidget(self.table)

        # Stats bar
        self.stats_label = QLabel("")
        self.stats_label.setStyleSheet("""
            background-color: #f5f5f5;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 12px;
        """)
        layout.addWidget(self.stats_label)

        # Legend
        legend_layout = QHBoxLayout()
        legend_layout.addWidget(QLabel("Legend:"))

        valid_label = QLabel("[OK] Valid")
        valid_label.setStyleSheet("color: #4CAF50; font-weight: bold;")
        legend_layout.addWidget(valid_label)

        error_label = QLabel("[X] Error")
        error_label.setStyleSheet("color: #f44336; font-weight: bold;")
        legend_layout.addWidget(error_label)

        legend_layout.addStretch()
        layout.addLayout(legend_layout)

        layout.addSpacing(10)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Save button
        save_btn = QPushButton("Save Changes")
        save_btn.clicked.connect(self.save_changes)
        save_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
            }
        """)
        self.save_btn = save_btn
        button_layout.addWidget(save_btn)

        # Export button
        export_btn = QPushButton("Export CSV")
        export_btn.clicked.connect(self.export_csv)
        export_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #607D8B;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #546E7A;
            }
        """)
        button_layout.addWidget(export_btn)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.on_close)
        close_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def setup_table(self):
        """Initialize table structure"""
        headers = ["Item Number", "Color", "Size", "Quantity", "Confidence", "Status"]
        self.table.setColumnCount(len(headers))
        self.table.setHorizontalHeaderLabels(headers)

        # Configure table - ENABLE EDITING
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.DoubleClicked | QTableWidget.EditKeyPressed)

        # Connect to item changed signal
        self.table.itemChanged.connect(self.on_item_changed)

        # Style
        self.table.setStyleSheet("""
            QTableWidget {
                gridline-color: #ddd;
                background-color: white;
            }
            QTableWidget::item {
                padding: 8px;
            }
            QTableWidget::item:selected {
                background-color: #e3f2fd;
            }
            QHeaderView::section {
                background-color: #f5f5f5;
                padding: 10px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)

    def get_value_case_insensitive(self, row_data, *possible_keys):
        """Get value from dict trying multiple key variations"""
        # Try exact matches first
        for key in possible_keys:
            if key in row_data:
                return row_data[key].strip()

        # Try case-insensitive match
        row_data_lower = {k.lower(): v for k, v in row_data.items()}
        for key in possible_keys:
            if key.lower() in row_data_lower:
                return row_data_lower[key.lower()].strip()

        return ''

    def load_csv_data(self):
        """Load data from CSV file"""
        if not os.path.exists(self.csv_path):
            QMessageBox.critical(self, "Error", f"CSV file not found: {self.csv_path}")
            return

        try:
            # Temporarily disconnect itemChanged signal during load
            self.table.itemChanged.disconnect(self.on_item_changed)

            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

            if not rows:
                QMessageBox.warning(self, "Warning", "CSV file is empty!")
                return

            # Set row count
            self.table.setRowCount(len(rows))

            # Counters for stats
            valid_count = 0
            error_count = 0
            total_quantity = 0

            # Populate table
            for row_idx, row_data in enumerate(rows):
                # Extract data with case-insensitive fallbacks
                item_num = self.get_value_case_insensitive(
                    row_data, 'item num', 'Item Number', 'item_num', 'item_number', 'ItemNumber'
                )
                color = self.get_value_case_insensitive(
                    row_data, 'color', 'Color', 'COLOR'
                )
                size = self.get_value_case_insensitive(
                    row_data, 'size', 'Size', 'SIZE'
                )
                qty = self.get_value_case_insensitive(
                    row_data, 'qty', 'quantity', 'Quantity', 'QTY', 'QUANTITY'
                )
                confidence = self.get_value_case_insensitive(
                    row_data, 'confidence', 'Confidence', 'CONFIDENCE'
                )

                # Create editable items (columns 0-3)
                item_num_item = QTableWidgetItem(item_num)
                color_item = QTableWidgetItem(color)
                size_item = QTableWidgetItem(size)
                qty_item = QTableWidgetItem(qty)

                self.table.setItem(row_idx, 0, item_num_item)
                self.table.setItem(row_idx, 1, color_item)
                self.table.setItem(row_idx, 2, size_item)
                self.table.setItem(row_idx, 3, qty_item)

                # Confidence column (read-only)
                confidence_item = QTableWidgetItem(confidence if confidence else 'N/A')
                confidence_item.setFlags(confidence_item.flags() & ~Qt.ItemIsEditable)
                if confidence:
                    # Color code confidence
                    try:
                        conf_val = float(confidence.rstrip('%'))
                        if conf_val >= 90:
                            confidence_item.setForeground(QColor(76, 175, 80))  # Green
                        elif conf_val >= 70:
                            confidence_item.setForeground(QColor(255, 152, 0))  # Orange
                        else:
                            confidence_item.setForeground(QColor(244, 67, 54))  # Red
                    except ValueError:
                        pass
                self.table.setItem(row_idx, 4, confidence_item)

                # Determine status (read-only)
                status = self.validate_row(item_num, color, size, qty)
                status_item = QTableWidgetItem(status['symbol'])
                status_item.setFlags(status_item.flags() & ~Qt.ItemIsEditable)

                # Color code status
                if status['level'] == 'valid':
                    status_item.setForeground(QColor(76, 175, 80))  # Green
                    valid_count += 1
                else:  # error
                    status_item.setForeground(QColor(244, 67, 54))  # Red
                    error_count += 1

                status_item.setToolTip(status['message'])
                self.table.setItem(row_idx, 5, status_item)

                # Add to quantity total
                try:
                    qty_clean = qty.rstrip('%')
                    total_quantity += int(qty_clean)
                except (ValueError, AttributeError):
                    pass

            # Update stats
            self.update_stats(len(rows), total_quantity, valid_count, error_count)

            # Reconnect itemChanged signal
            self.table.itemChanged.connect(self.on_item_changed)

            # Reset unsaved changes flag
            self.has_unsaved_changes = False
            self.update_save_button()

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load CSV: {str(e)}")
            import traceback
            print(traceback.format_exc())

    def on_item_changed(self, item):
        """Handle when a cell is edited"""
        row = item.row()
        col = item.column()

        # Only track changes to editable columns (0-3)
        if col < 4:
            self.has_unsaved_changes = True
            self.update_save_button()

            # Re-validate the row and update status
            self.update_row_status(row)

            # Recalculate stats
            self.recalculate_stats()

    def update_row_status(self, row):
        """Update the status column for a specific row"""
        # Get current values
        item_num = self.table.item(row, 0).text() if self.table.item(row, 0) else ''
        color = self.table.item(row, 1).text() if self.table.item(row, 1) else ''
        size = self.table.item(row, 2).text() if self.table.item(row, 2) else ''
        qty = self.table.item(row, 3).text() if self.table.item(row, 3) else ''

        # Validate
        status = self.validate_row(item_num, color, size, qty)

        # Update status column
        status_item = self.table.item(row, 5)
        if status_item:
            status_item.setText(status['symbol'])
            status_item.setToolTip(status['message'])

            # Update color
            if status['level'] == 'valid':
                status_item.setForeground(QColor(76, 175, 80))
            else:
                status_item.setForeground(QColor(244, 67, 54))

    def recalculate_stats(self):
        """Recalculate and update statistics"""
        valid_count = 0
        error_count = 0
        total_quantity = 0

        for row in range(self.table.rowCount()):
            # Check status
            status_item = self.table.item(row, 5)
            if status_item and '[OK]' in status_item.text():
                valid_count += 1
            else:
                error_count += 1

            # Add quantity
            qty_item = self.table.item(row, 3)
            if qty_item:
                try:
                    qty_clean = qty_item.text().rstrip('%')
                    total_quantity += int(qty_clean)
                except (ValueError, AttributeError):
                    pass

        self.update_stats(self.table.rowCount(), total_quantity, valid_count, error_count)

    def update_stats(self, total_items, total_quantity, valid_count, error_count):
        """Update the statistics label"""
        stats_text = (
            f"Total Items: {total_items} | "
            f"Total Pieces: {total_quantity} | "
            f"[OK] {valid_count} Valid  "
            f"[X] {error_count} Errors"
        )
        self.stats_label.setText(stats_text)

    def update_save_button(self):
        """Update save button state based on changes"""
        if self.has_unsaved_changes:
            self.save_btn.setText("Save Changes *")
            self.save_btn.setEnabled(True)
        else:
            self.save_btn.setText("Save Changes")
            self.save_btn.setEnabled(False)

    def validate_row(self, item_num, color, size, qty):
        """Validate a row and return status"""
        issues = []

        # Check required fields
        if not item_num:
            issues.append("Missing item number")
        if not color:
            issues.append("Missing color")
        if not size:
            issues.append("Missing size")
        if not qty:
            issues.append("Missing quantity")
        else:
            try:
                qty_clean = qty.rstrip('%')
                qty_int = int(qty_clean)
                if qty_int <= 0:
                    issues.append("Invalid quantity")
            except ValueError:
                issues.append("Quantity must be a number")

        # Determine status level
        if not issues:
            return {
                'level': 'valid',
                'symbol': '[OK]',
                'message': 'All required fields present'
            }

        return {
            'level': 'error',
            'symbol': '[X]',
            'message': '; '.join(issues)
        }

    def save_changes(self):
        """Save changes back to the CSV file"""
        try:
            # Read all data from table
            rows = []
            for row in range(self.table.rowCount()):
                item_num = self.table.item(row, 0).text() if self.table.item(row, 0) else ''
                color = self.table.item(row, 1).text() if self.table.item(row, 1) else ''
                size = self.table.item(row, 2).text() if self.table.item(row, 2) else ''
                qty = self.table.item(row, 3).text() if self.table.item(row, 3) else ''
                confidence = self.table.item(row, 4).text() if self.table.item(row, 4) else ''

                rows.append({
                    'qty': qty,
                    'size': size,
                    'item num': item_num,
                    'color': color,
                    'confidence': confidence
                })

            # Write back to CSV
            with open(self.csv_path, 'w', newline='', encoding='utf-8') as f:
                fieldnames = ['qty', 'size', 'item num', 'color', 'confidence']
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)

            self.has_unsaved_changes = False
            self.update_save_button()

            QMessageBox.information(self, "Success", "Changes saved successfully!")

        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save changes: {str(e)}")

    def export_csv(self):
        """Export CSV to a user-selected location"""
        from PyQt5.QtWidgets import QFileDialog

        # Save current changes first if there are any
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Save before exporting?",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel
            )
            if reply == QMessageBox.Yes:
                self.save_changes()
            elif reply == QMessageBox.Cancel:
                return

        default_name = f"order_data_{os.path.splitext(os.path.basename(self.csv_path))[0]}.csv"

        save_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export CSV",
            default_name,
            "CSV Files (*.csv);;All Files (*)"
        )

        if save_path:
            try:
                import shutil
                shutil.copy2(self.csv_path, save_path)
                QMessageBox.information(self, "Success", f"CSV exported to:\n{save_path}")
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Export failed: {str(e)}")

    def on_close(self):
        """Handle close button with unsaved changes check"""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                self.save_changes()
                self.accept()
            elif reply == QMessageBox.Discard:
                self.accept()
            # If Cancel, do nothing (stay open)
        else:
            self.accept()

    def closeEvent(self, event):
        """Handle window close event (X button)"""
        if self.has_unsaved_changes:
            reply = QMessageBox.question(
                self,
                "Unsaved Changes",
                "You have unsaved changes. Do you want to save before closing?",
                QMessageBox.Save | QMessageBox.Discard | QMessageBox.Cancel
            )

            if reply == QMessageBox.Save:
                self.save_changes()
                event.accept()
            elif reply == QMessageBox.Discard:
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()


# For testing
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication
    import tempfile

    # Create sample CSV for testing
    test_csv = os.path.join(tempfile.gettempdir(), 'test_preview.csv')
    with open(test_csv, 'w') as f:
        f.write("qty,size,item num,color,confidence\n")
        f.write("5,L,SHIRT001,Navy,95%\n")
        f.write("3,XL,SHIRT001,Navy,90%\n")
        f.write("10,M,POLO123,Red,65%\n")
        f.write("2,OS,HAT456,Black,88%\n")

    app = QApplication(sys.argv)
    window = DataPreviewGUI(test_csv)
    window.show()
    sys.exit(app.exec_())