from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTextEdit, QFileDialog, QMessageBox, QFrame, QGroupBox,
    QCheckBox, QScrollArea, QWidget
)
from PyQt5.QtCore import Qt, pyqtSignal, QThread
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent
import os
import tempfile
from datetime import datetime


class PromptSettingsDialog(QDialog):
    """Dialog for customizing the Claude AI prompt"""

    def __init__(self, current_prompt="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Prompt Settings")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)

        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "Customize the prompt sent to Claude for processing your order data.\n"
            "The default prompt is optimized for extracting order information."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 10px;")
        layout.addWidget(instructions)

        # Use default checkbox
        self.use_default_checkbox = QCheckBox("Use Default Prompt (Recommended)")
        self.use_default_checkbox.setChecked(not current_prompt)
        self.use_default_checkbox.toggled.connect(self.toggle_custom_prompt)
        layout.addWidget(self.use_default_checkbox)

        layout.addSpacing(10)

        # Prompt text area
        prompt_label = QLabel("Custom Prompt:")
        prompt_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(prompt_label)

        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText(
            "Enter your custom prompt here...\n\n"
            "Example: Extract all order items with their sizes, colors, and quantities. "
            "Format the output as a CSV with columns: Item Number, Color, Size, Quantity."
        )
        if current_prompt:
            self.prompt_input.setText(current_prompt)
        self.prompt_input.setEnabled(bool(current_prompt))
        layout.addWidget(self.prompt_input)

        # Info note
        note = QLabel(
            "Tip: The prompt should instruct Claude to return data in CSV format "
            "with columns: Item Number, Color, Size, Quantity, Description (optional)"
        )
        note.setWordWrap(True)
        note.setStyleSheet("background-color: #e3f2fd; padding: 10px; border-radius: 4px; font-size: 11px;")
        layout.addWidget(note)

        # Buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.accept)
        save_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 8px 16px;
                border: none;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def toggle_custom_prompt(self, checked):
        """Enable/disable custom prompt input"""
        self.prompt_input.setEnabled(not checked)

    def get_prompt(self):
        """Return the prompt to use (empty string means use default)"""
        if self.use_default_checkbox.isChecked():
            return ""
        return self.prompt_input.toPlainText().strip()


class ClaudeProcessingThread(QThread):
    """Thread for processing files with Claude API"""

    status_update = pyqtSignal(str)
    finished_signal = pyqtSignal(bool, str, str)  # success, message, csv_path

    def __init__(self, files, text_content, custom_prompt):
        super().__init__()
        self.files = files
        self.text_content = text_content
        self.custom_prompt = custom_prompt

    def run(self):
        """Process files with Claude"""
        try:
            # Import here to avoid circular dependencies
            from claude_processor import process_files_with_claude
            import config

            # Check if API key is configured
            if not config.CLAUDE_API_KEY:
                self.status_update.emit("[ERROR] Claude API key not configured")
                self.finished_signal.emit(
                    False,
                    "Claude API key not configured. Please add it in Settings.",
                    ""
                )
                return

            # Call Claude processor with status callback
            def status_callback(message):
                self.status_update.emit(message)

            success, csv_path, metadata = process_files_with_claude(
                self.files,
                self.text_content,
                self.custom_prompt,
                config.CLAUDE_API_KEY,
                status_callback=status_callback
            )

            if success:
                item_count = metadata.get('item_count', 0)
                message = f"Successfully extracted {item_count} items!"
                if metadata.get('extraction_notes'):
                    message += f"\n\nNote: {metadata['extraction_notes']}"

                self.finished_signal.emit(True, message, csv_path)
            else:
                error_msg = metadata.get('error', 'Unknown error occurred')
                self.status_update.emit(f"[ERROR] {error_msg}")
                self.finished_signal.emit(False, error_msg, "")

        except Exception as e:
            error_msg = f"Processing error: {str(e)}"
            self.status_update.emit(f"[ERROR] {error_msg}")
            self.finished_signal.emit(False, error_msg, "")


from PyQt5.QtWidgets import (
    QFrame, QVBoxLayout, QLabel, QPushButton, QFileDialog
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent


class DragDropFileZone(QFrame):
    """Drag-and-drop zone for file uploads"""

    files_dropped = pyqtSignal(list)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAcceptDrops(True)
        self.setup_ui()
        self.set_default_style()

    def setup_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignCenter)

        # Icon
        icon = QLabel("[FILE]")
        icon.setAlignment(Qt.AlignCenter)
        icon_font = QFont()
        icon_font.setPointSize(24)
        icon_font.setBold(True)
        icon.setFont(icon_font)
        icon.setStyleSheet("color: #2196F3;")
        layout.addWidget(icon)

        # Main text
        main_text = QLabel("Drag & Drop Files Here")
        main_text.setAlignment(Qt.AlignCenter)
        main_font = QFont()
        main_font.setPointSize(14)
        main_font.setBold(True)
        main_text.setFont(main_font)
        layout.addWidget(main_text)

        # Supported files
        supported = QLabel("PDF | CSV | XLSX | TXT | EML")
        supported.setAlignment(Qt.AlignCenter)
        supported.setStyleSheet("color: #666; font-size: 11px;")
        layout.addWidget(supported)

        layout.addSpacing(10)

        # Browse button
        browse_btn = QPushButton("Browse Files")
        browse_btn.setStyleSheet("""
            QPushButton {
                padding: 8px 16px;
                font-size: 12px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        browse_btn.clicked.connect(self.browse_files)
        layout.addWidget(browse_btn, alignment=Qt.AlignCenter)

        self.setLayout(layout)
        self.setMinimumHeight(180)
        self.setMaximumHeight(180)

    def set_default_style(self):
        """Default style"""
        self.setStyleSheet("""
            DragDropFileZone {
                border: 2px dashed #bbb;
                border-radius: 8px;
                background-color: #f9f9f9;
            }
        """)

    def set_hover_style(self):
        """Style when hovering with files"""
        self.setStyleSheet("""
            DragDropFileZone {
                border: 2px dashed #2196F3;
                border-radius: 8px;
                background-color: #e3f2fd;
            }
        """)

    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter"""
        print("DEBUG: dragEnterEvent triggered")  # Debug line
        if event.mimeData().hasUrls():
            print(f"DEBUG: Has URLs: {event.mimeData().urls()}")  # Debug line
            event.acceptProposedAction()
            self.set_hover_style()
        else:
            print("DEBUG: No URLs in mime data")  # Debug line
            event.ignore()

    def dragMoveEvent(self, event):
        """Handle drag move - IMPORTANT: This needs to be implemented"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragLeaveEvent(self, event):
        """Handle drag leave"""
        print("DEBUG: dragLeaveEvent triggered")  # Debug line
        self.set_default_style()

    def dropEvent(self, event: QDropEvent):
        """Handle file drop"""
        print("DEBUG: dropEvent triggered")  # Debug line
        self.set_default_style()

        if event.mimeData().hasUrls():
            files = [url.toLocalFile() for url in event.mimeData().urls()]
            print(f"DEBUG: Files dropped: {files}")  # Debug line

            if files:
                self.files_dropped.emit(files)
                event.acceptProposedAction()
            else:
                event.ignore()
        else:
            event.ignore()

    def browse_files(self):
        """Open file browser"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Files",
            "",
            "All Supported (*.pdf *.csv *.xlsx *.xls *.txt *.eml);;PDF Files (*.pdf);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;Text Files (*.txt);;Email Files (*.eml);;All Files (*)"
        )
        if files:
            self.files_dropped.emit(files)


# Test code
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QTextEdit


    class TestWindow(QMainWindow):
        def __init__(self):
            super().__init__()
            self.setWindowTitle("Drag-Drop Test")
            self.setGeometry(100, 100, 600, 400)

            central = QWidget()
            layout = QVBoxLayout()

            # Drag-drop zone
            self.drop_zone = DragDropFileZone()
            self.drop_zone.files_dropped.connect(self.handle_files)
            layout.addWidget(self.drop_zone)

            # Output area
            self.output = QTextEdit()
            self.output.setReadOnly(True)
            layout.addWidget(self.output)

            central.setLayout(layout)
            self.setCentralWidget(central)

        def handle_files(self, files):
            self.output.append(f"Files received: {files}\n")


    app = QApplication(sys.argv)
    window = TestWindow()
    window.show()
    sys.exit(app.exec_())

class AIProcessingGUI(QDialog):
    """GUI for AI-powered order data processing"""

    csv_generated = pyqtSignal(str)  # Emits CSV path when ready

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("AI Order Processing")
        self.setModal(True)
        self.setMinimumWidth(700)
        self.setMinimumHeight(650)

        self.uploaded_files = []
        self.generated_csv_path = None
        self.custom_prompt = ""
        self.processing_thread = None

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        main_layout = QVBoxLayout()
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setSpacing(10)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header
        header_layout = QHBoxLayout()

        title = QLabel("AI Order Processing")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Settings button
        self.settings_btn = QPushButton("Prompt Settings")
        self.settings_btn.clicked.connect(self.show_prompt_settings)
        header_layout.addWidget(self.settings_btn)

        layout.addLayout(header_layout)

        # Description
        desc = QLabel(
            "Upload files or paste text, and Claude will extract order data automatically. "
            "Supported: PDFs, spreadsheets, text files, emails, and pasted content."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #666; font-size: 11px; margin-bottom: 15px;")
        layout.addWidget(desc)

        # Drag-drop zone (fixed height to prevent overlap)
        self.drop_zone = DragDropFileZone()
        self.drop_zone.files_dropped.connect(self.on_files_added)
        layout.addWidget(self.drop_zone)

        layout.addSpacing(10)

        # OR divider
        divider_layout = QHBoxLayout()
        divider_layout.addWidget(self.create_line())
        or_label = QLabel(" OR ")
        or_label.setStyleSheet("color: #999; font-weight: bold;")
        divider_layout.addWidget(or_label)
        divider_layout.addWidget(self.create_line())
        layout.addLayout(divider_layout)

        layout.addSpacing(10)

        # Text paste area
        paste_group = QGroupBox("Paste Email or Text Content")
        paste_layout = QVBoxLayout()

        self.text_input = QTextEdit()
        self.text_input.setPlaceholderText(
            "Paste email content, order details, or any text containing order information here...\n\n"
            "Example:\n"
            "Order for John Doe:\n"
            "- 5x Navy T-Shirts (Large)\n"
            "- 10x Red Polos (Medium)\n"
            "..."
        )
        self.text_input.setMinimumHeight(100)
        self.text_input.setMaximumHeight(120)
        paste_layout.addWidget(self.text_input)

        paste_group.setLayout(paste_layout)
        layout.addWidget(paste_group)

        # Files list container
        self.files_container = QWidget()
        files_container_layout = QVBoxLayout(self.files_container)
        files_container_layout.setContentsMargins(0, 0, 0, 0)

        self.files_list_label = QLabel("Uploaded Files:")
        files_container_layout.addWidget(self.files_list_label)

        self.files_list = QTextEdit()
        self.files_list.setReadOnly(True)
        self.files_list.setMaximumHeight(60)
        self.files_list.setStyleSheet("background-color: #f5f5f5; border: 1px solid #ddd; padding: 5px;")
        files_container_layout.addWidget(self.files_list)

        self.clear_files_btn = QPushButton("Clear Files")
        self.clear_files_btn.clicked.connect(self.clear_files)
        files_container_layout.addWidget(self.clear_files_btn)

        self.files_container.setVisible(False)
        layout.addWidget(self.files_container)

        layout.addSpacing(15)

        # Process button
        self.process_btn = QPushButton("Process with Claude")
        self.process_btn.setEnabled(False)
        self.process_btn.clicked.connect(self.start_processing)
        self.process_btn.setStyleSheet("""
            QPushButton {
                padding: 12px;
                font-size: 14px;
                font-weight: bold;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:disabled {
                background-color: #cccccc;
                color: #666666;
            }
        """)
        layout.addWidget(self.process_btn)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #666; font-size: 11px; margin-top: 5px;")
        self.status_label.setVisible(False)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addSpacing(10)

        # Result actions (hidden until processing complete)
        self.result_group = QGroupBox("Processing Complete")
        self.result_group.setVisible(False)
        result_layout = QHBoxLayout()

        self.preview_btn = QPushButton("Preview Data")
        self.preview_btn.clicked.connect(self.preview_data)
        result_layout.addWidget(self.preview_btn)

        self.delete_btn = QPushButton("Delete && Retry")
        self.delete_btn.clicked.connect(self.delete_and_retry)
        result_layout.addWidget(self.delete_btn)

        result_layout.addStretch()

        self.use_btn = QPushButton("Save && Use This Data")
        self.use_btn.clicked.connect(self.save_and_use)
        self.use_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-weight: bold;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        result_layout.addWidget(self.use_btn)

        self.result_group.setLayout(result_layout)
        layout.addWidget(self.result_group)

        layout.addStretch()

        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)

        # Close button at bottom (outside scroll area)
        button_container = QWidget()
        button_container.setStyleSheet("background-color: #f5f5f5; border-top: 1px solid #ddd;")
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 10, 20, 10)

        close_btn = QPushButton("Cancel")
        close_btn.clicked.connect(self.reject)
        button_layout.addStretch()
        button_layout.addWidget(close_btn)

        main_layout.addWidget(button_container)

        self.setLayout(main_layout)

        # Connect text input to enable process button
        self.text_input.textChanged.connect(self.update_process_button)

    def create_line(self):
        """Create horizontal line"""
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        line.setStyleSheet("background-color: #ddd;")
        return line

    def show_prompt_settings(self):
        """Show prompt settings dialog"""
        dialog = PromptSettingsDialog(self.custom_prompt, self)
        if dialog.exec_() == QDialog.Accepted:
            self.custom_prompt = dialog.get_prompt()
            if self.custom_prompt:
                self.settings_btn.setText("Prompt Settings (Custom)")
                self.settings_btn.setStyleSheet("color: #FF9800; font-weight: bold;")
            else:
                self.settings_btn.setText("Prompt Settings")
                self.settings_btn.setStyleSheet("")

    def on_files_added(self, files):
        """Handle files being added"""
        self.uploaded_files.extend(files)
        self.update_files_list()
        self.update_process_button()
        self.files_container.setVisible(True)

    def update_files_list(self):
        """Update files list display"""
        files_text = ""
        for i, filepath in enumerate(self.uploaded_files, 1):
            filename = os.path.basename(filepath)
            files_text += f"{i}. {filename}\n"
        self.files_list.setText(files_text.strip())

    def clear_files(self):
        """Clear uploaded files"""
        self.uploaded_files = []
        self.files_list.clear()
        self.files_container.setVisible(False)
        self.update_process_button()

    def update_process_button(self):
        """Enable/disable process button based on input"""
        has_files = len(self.uploaded_files) > 0
        has_text = len(self.text_input.toPlainText().strip()) > 0
        self.process_btn.setEnabled(has_files or has_text)

    def start_processing(self):
        """Start Claude processing"""
        # Disable inputs during processing
        self.process_btn.setEnabled(False)
        self.drop_zone.setEnabled(False)
        self.text_input.setEnabled(False)
        self.settings_btn.setEnabled(False)
        self.clear_files_btn.setEnabled(False)

        # Show status
        self.status_label.setVisible(True)
        self.status_label.setText("Processing with Claude AI...")

        # Start processing thread
        text_content = self.text_input.toPlainText().strip()
        self.processing_thread = ClaudeProcessingThread(
            self.uploaded_files,
            text_content,
            self.custom_prompt
        )
        self.processing_thread.status_update.connect(self.on_status_update)
        self.processing_thread.finished_signal.connect(self.on_processing_finished)
        self.processing_thread.start()

    def on_status_update(self, message):
        """Update status label"""
        self.status_label.setText(message)

    def on_processing_finished(self, success, message, csv_path):
        """Handle processing completion"""
        # Re-enable inputs
        self.drop_zone.setEnabled(True)
        self.text_input.setEnabled(True)
        self.settings_btn.setEnabled(True)
        self.clear_files_btn.setEnabled(True)
        self.update_process_button()

        if success:
            self.generated_csv_path = csv_path
            self.result_group.setVisible(True)
            self.status_label.setVisible(False)
            QMessageBox.information(self, "Success", message)
        else:
            self.status_label.setText(f"Error: {message}")
            QMessageBox.critical(self, "Error", message)

    def preview_data(self):
        """Open preview window"""
        if not self.generated_csv_path:
            return

        # Import here to avoid circular dependency
        from data_preview_gui import DataPreviewGUI

        preview = DataPreviewGUI(self.generated_csv_path, self)
        preview.exec_()

    def delete_and_retry(self):
        """Delete generated CSV and reset"""
        if self.generated_csv_path and os.path.exists(self.generated_csv_path):
            try:
                os.remove(self.generated_csv_path)
            except Exception as e:
                QMessageBox.warning(self, "Warning", f"Could not delete file: {e}")

        self.generated_csv_path = None
        self.result_group.setVisible(False)
        self.status_label.setText("")
        self.status_label.setVisible(False)
        QMessageBox.information(self, "Reset", "Ready to process again!")

    def save_and_use(self):
        """Save and return CSV path to main GUI"""
        if self.generated_csv_path:
            self.csv_generated.emit(self.generated_csv_path)
            self.accept()
        else:
            QMessageBox.warning(self, "Error", "No CSV file generated!")


# For testing
if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)
    window = AIProcessingGUI()
    window.show()
    sys.exit(app.exec_())