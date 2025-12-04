"""
PyQt5 GUI for Printavo Quote Creator
UPDATED: Added AI preprocessing widget with drag-and-drop support
"""
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QLineEdit, QTextEdit,
    QFileDialog, QMessageBox, QGroupBox,
    QApplication, QDialog, QDialogButtonBox, QTabWidget, QCheckBox,
    QFrame, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent, QPalette, QColor

import os
import config
from worker import WorkerThread

class SettingsDialog(QDialog):
    """Dialog for entering Printavo, SSActivewear, Sanmar, and Claude AI credentials"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("API Credentials")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.setMinimumHeight(500)

        layout = QVBoxLayout()

        # Tab widget for organizing credentials
        tabs = QTabWidget()

        # Printavo tab
        printavo_tab = self.create_printavo_tab()
        tabs.addTab(printavo_tab, "Printavo")

        # SSActivewear tab
        ssactivewear_tab = self.create_ssactivewear_tab()
        tabs.addTab(ssactivewear_tab, "SSActivewear")

        # Sanmar tab
        sanmar_tab = self.create_sanmar_tab()
        tabs.addTab(sanmar_tab, "Sanmar")

        # Claude AI tab
        claude_tab = self.create_claude_tab()
        tabs.addTab(claude_tab, "Claude AI")

        layout.addWidget(tabs)

        # Buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Save | QDialogButtonBox.Cancel
        )
        button_box.accepted.connect(self.save_credentials)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def create_printavo_tab(self):
        """Create the Printavo credentials tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "Enter your Printavo API credentials.\n"
            "These will be saved securely on your computer."
        )
        instructions.setWordWrap(True)
        layout.addWidget(instructions)

        layout.addSpacing(10)

        # Email input
        email_layout = QHBoxLayout()
        email_layout.addWidget(QLabel("Email:"))
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("your-email@example.com")
        if config.PRINTAVO_EMAIL:
            self.email_input.setText(config.PRINTAVO_EMAIL)
        email_layout.addWidget(self.email_input)
        layout.addLayout(email_layout)

        # Token input
        token_layout = QHBoxLayout()
        token_layout.addWidget(QLabel("Token:"))
        self.token_input = QLineEdit()
        self.token_input.setPlaceholderText("your-api-token")
        self.token_input.setEchoMode(QLineEdit.Password)
        if config.PRINTAVO_TOKEN:
            self.token_input.setText(config.PRINTAVO_TOKEN)
        token_layout.addWidget(self.token_input)
        layout.addLayout(token_layout)

        # Show/hide token checkbox
        self.show_token_btn = QPushButton("Show Token")
        self.show_token_btn.setCheckable(True)
        self.show_token_btn.toggled.connect(self.toggle_token_visibility)
        layout.addWidget(self.show_token_btn)

        layout.addSpacing(10)

        # Help text
        help_text = QLabel(
            "To get your API credentials:\n"
            "1. Log in to Printavo\n"
            "2. Go to Settings → API\n"
            "3. Generate an API token if needed\n"
            "4. Copy your email and token here"
        )
        help_text.setStyleSheet("color: #666; font-size: 11px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def create_ssactivewear_tab(self):
        """Create the SSActivewear credentials tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "SSActivewear credentials are optional but recommended.\n"
            "They enable automatic product description lookup."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-weight: bold;")
        layout.addWidget(instructions)

        layout.addSpacing(10)

        # Account Number input
        account_layout = QHBoxLayout()
        account_layout.addWidget(QLabel("Account Number:"))
        self.ss_account_input = QLineEdit()
        self.ss_account_input.setPlaceholderText("Your SSActivewear account number")
        if config.SSACTIVEWEAR_ACCOUNT:
            self.ss_account_input.setText(config.SSACTIVEWEAR_ACCOUNT)
        account_layout.addWidget(self.ss_account_input)
        layout.addLayout(account_layout)

        # API Key input
        apikey_layout = QHBoxLayout()
        apikey_layout.addWidget(QLabel("API Key:"))
        self.ss_apikey_input = QLineEdit()
        self.ss_apikey_input.setPlaceholderText("Your API key")
        self.ss_apikey_input.setEchoMode(QLineEdit.Password)
        if config.SSACTIVEWEAR_API_KEY:
            self.ss_apikey_input.setText(config.SSACTIVEWEAR_API_KEY)
        apikey_layout.addWidget(self.ss_apikey_input)
        layout.addLayout(apikey_layout)

        # Show/hide API key checkbox
        self.show_ss_key_btn = QPushButton("Show API Key")
        self.show_ss_key_btn.setCheckable(True)
        self.show_ss_key_btn.toggled.connect(self.toggle_ss_key_visibility)
        layout.addWidget(self.show_ss_key_btn)

        layout.addSpacing(10)

        # Help text
        help_text = QLabel(
            "How to get SSActivewear API credentials:\n\n"
            "1. You need an active SSActivewear wholesale account\n"
            "2. Your Account Number is your customer/account ID\n"
            "3. To get an API Key, email: api@ssactivewear.com\n"
            "4. Request API access for product catalog integration\n\n"
            "Note: Without these credentials, you'll need to manually\n"
            "enter product descriptions in Printavo after quote creation."
        )
        help_text.setStyleSheet("color: #666; font-size: 11px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def create_sanmar_tab(self):
        """Create the Sanmar credentials tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "Sanmar credentials are optional but recommended.\n"
            "They enable automatic product description lookup from Sanmar's catalog."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-weight: bold;")
        layout.addWidget(instructions)

        layout.addSpacing(10)

        # Customer Number input
        customer_layout = QHBoxLayout()
        customer_layout.addWidget(QLabel("Customer Number:"))
        self.sanmar_customer_input = QLineEdit()
        self.sanmar_customer_input.setPlaceholderText("Your Sanmar account number")
        if config.SANMAR_CUSTOMER_NUMBER:
            self.sanmar_customer_input.setText(config.SANMAR_CUSTOMER_NUMBER)
        customer_layout.addWidget(self.sanmar_customer_input)
        layout.addLayout(customer_layout)

        # Username input
        username_layout = QHBoxLayout()
        username_layout.addWidget(QLabel("Username:"))
        self.sanmar_username_input = QLineEdit()
        self.sanmar_username_input.setPlaceholderText("Your Sanmar.com username")
        if config.SANMAR_USERNAME:
            self.sanmar_username_input.setText(config.SANMAR_USERNAME)
        username_layout.addWidget(self.sanmar_username_input)
        layout.addLayout(username_layout)

        # Password input
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Password:"))
        self.sanmar_password_input = QLineEdit()
        self.sanmar_password_input.setPlaceholderText("Your Sanmar.com password")
        self.sanmar_password_input.setEchoMode(QLineEdit.Password)
        if config.SANMAR_PASSWORD:
            self.sanmar_password_input.setText(config.SANMAR_PASSWORD)
        password_layout.addWidget(self.sanmar_password_input)
        layout.addLayout(password_layout)

        # Show/hide password button
        self.show_sanmar_pass_btn = QPushButton("Show Password")
        self.show_sanmar_pass_btn.setCheckable(True)
        self.show_sanmar_pass_btn.toggled.connect(self.toggle_sanmar_password_visibility)
        layout.addWidget(self.show_sanmar_pass_btn)

        layout.addSpacing(10)

        # Environment selection
        self.sanmar_production_checkbox = QCheckBox("Use Production Environment")
        self.sanmar_production_checkbox.setChecked(config.SANMAR_USE_PRODUCTION)
        self.sanmar_production_checkbox.setStyleSheet("color: #d32f2f; font-weight: bold;")
        layout.addWidget(self.sanmar_production_checkbox)

        env_note = QLabel("⚠ Leave unchecked to use staging environment (recommended for testing)")
        env_note.setStyleSheet("color: #ff9800; font-size: 11px; margin-left: 20px;")
        env_note.setWordWrap(True)
        layout.addWidget(env_note)

        layout.addSpacing(10)

        # Help text
        help_text = QLabel(
            "How to get Sanmar API credentials:\n\n"
            "1. You received an email with a one-time URL for SFTP credentials\n"
            "   (Even though you're using the API, retrieve these now!)\n\n"
            "2. Your credentials should already be set up for API access\n"
            "   - Customer Number: Your Sanmar account number\n"
            "   - Username: Your Sanmar.com login username\n"
            "   - Password: Your Sanmar.com login password\n\n"
            "3. If you have issues, contact:\n"
            "   Email: sanmarintegrations@sanmar.com\n"
            "   Phone: 206-727-6458\n\n"
            "Note: Both SSActivewear and Sanmar can be configured.\n"
            "The system will try both vendors when looking up products."
        )
        help_text.setStyleSheet("color: #666; font-size: 11px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def create_claude_tab(self):
        """Create the Claude AI credentials tab"""
        tab = QWidget()
        layout = QVBoxLayout()

        # Instructions
        instructions = QLabel(
            "Claude AI powers the automatic order data extraction.\n"
            "Required for AI Processing features."
        )
        instructions.setWordWrap(True)
        instructions.setStyleSheet("font-weight: bold;")
        layout.addWidget(instructions)

        layout.addSpacing(10)

        # API Key input
        apikey_layout = QHBoxLayout()
        apikey_layout.addWidget(QLabel("API Key:"))
        self.claude_apikey_input = QLineEdit()
        self.claude_apikey_input.setPlaceholderText("sk-ant-...")
        self.claude_apikey_input.setEchoMode(QLineEdit.Password)
        if config.CLAUDE_API_KEY:
            self.claude_apikey_input.setText(config.CLAUDE_API_KEY)
        apikey_layout.addWidget(self.claude_apikey_input)
        layout.addLayout(apikey_layout)

        # Show/hide API key button
        self.show_claude_key_btn = QPushButton("Show API Key")
        self.show_claude_key_btn.setCheckable(True)
        self.show_claude_key_btn.toggled.connect(self.toggle_claude_key_visibility)
        layout.addWidget(self.show_claude_key_btn)

        layout.addSpacing(10)

        # Help text
        help_text = QLabel(
            "How to get your Claude API key:\n\n"
            "1. Go to https://console.anthropic.com/\n"
            "2. Sign up or log in to your account\n"
            "3. Navigate to API Keys section\n"
            "4. Create a new API key\n"
            "5. Copy the key (starts with 'sk-ant-')\n\n"
            "Note: Keep your API key secure. It will be stored locally\n"
            "in an encrypted format on your computer.\n\n"
            "Pricing: Claude API usage is billed separately by Anthropic.\n"
            "Visit https://www.anthropic.com/pricing for current rates."
        )
        help_text.setStyleSheet("color: #666; font-size: 11px;")
        help_text.setWordWrap(True)
        layout.addWidget(help_text)

        layout.addStretch()
        tab.setLayout(layout)
        return tab

    def toggle_token_visibility(self, checked):
        """Toggle Printavo token visibility"""
        if checked:
            self.token_input.setEchoMode(QLineEdit.Normal)
            self.show_token_btn.setText("Hide Token")
        else:
            self.token_input.setEchoMode(QLineEdit.Password)
            self.show_token_btn.setText("Show Token")

    def toggle_ss_key_visibility(self, checked):
        """Toggle SSActivewear API key visibility"""
        if checked:
            self.ss_apikey_input.setEchoMode(QLineEdit.Normal)
            self.show_ss_key_btn.setText("Hide API Key")
        else:
            self.ss_apikey_input.setEchoMode(QLineEdit.Password)
            self.show_ss_key_btn.setText("Show API Key")

    def toggle_sanmar_password_visibility(self, checked):
        """Toggle Sanmar password visibility"""
        if checked:
            self.sanmar_password_input.setEchoMode(QLineEdit.Normal)
            self.show_sanmar_pass_btn.setText("Hide Password")
        else:
            self.sanmar_password_input.setEchoMode(QLineEdit.Password)
            self.show_sanmar_pass_btn.setText("Show Password")

    def toggle_claude_key_visibility(self, checked):
        """Toggle Claude API key visibility"""
        if checked:
            self.claude_apikey_input.setEchoMode(QLineEdit.Normal)
            self.show_claude_key_btn.setText("Hide API Key")
        else:
            self.claude_apikey_input.setEchoMode(QLineEdit.Password)
            self.show_claude_key_btn.setText("Show API Key")

    def save_credentials(self):
        """Validate and save credentials"""
        # Printavo credentials (required)
        email = self.email_input.text().strip()
        token = self.token_input.text().strip()

        if not email or not token:
            QMessageBox.warning(self, "Error", "Please enter both Printavo email and token.")
            return

        # SSActivewear credentials (optional)
        ss_account = self.ss_account_input.text().strip() or None
        ss_apikey = self.ss_apikey_input.text().strip() or None

        # Sanmar credentials (optional)
        sanmar_customer = self.sanmar_customer_input.text().strip() or None
        sanmar_username = self.sanmar_username_input.text().strip() or None
        sanmar_password = self.sanmar_password_input.text().strip() or None
        sanmar_production = self.sanmar_production_checkbox.isChecked()

        # Claude AI credentials (optional) - FIXED: Now collecting the value
        claude_apikey = self.claude_apikey_input.text().strip() or None

        # Validate that if one SSActivewear field is filled, both should be
        if (ss_account and not ss_apikey) or (ss_apikey and not ss_account):
            reply = QMessageBox.question(
                self,
                "Incomplete SSActivewear Credentials",
                "You've only filled in one SSActivewear field.\n"
                "Both Account Number and API Key are needed for product lookup.\n\n"
                "Do you want to continue without SSActivewear integration?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            # Clear partial credentials
            ss_account = None
            ss_apikey = None

        # Validate Sanmar credentials
        sanmar_fields = [sanmar_customer, sanmar_username, sanmar_password]
        sanmar_filled = sum(1 for f in sanmar_fields if f)

        if 0 < sanmar_filled < 3:  # Some but not all fields filled
            reply = QMessageBox.question(
                self,
                "Incomplete Sanmar Credentials",
                "You've only filled in some Sanmar fields.\n"
                "All three fields (Customer Number, Username, Password) are needed.\n\n"
                "Do you want to continue without Sanmar integration?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply == QMessageBox.No:
                return
            # Clear partial credentials
            sanmar_customer = None
            sanmar_username = None
            sanmar_password = None

        try:
            # FIXED: Now passing claude_apikey parameter
            config.save_credentials(
                email,
                token,
                ss_account,
                ss_apikey,
                sanmar_customer,
                sanmar_username,
                sanmar_password,
                sanmar_production,
                claude_apikey  # FIXED: Added this parameter
            )

            # Show appropriate success message
            vendors = []
            if ss_account and ss_apikey:
                vendors.append("SSActivewear")
            if sanmar_customer and sanmar_username and sanmar_password:
                vendors.append("Sanmar")

            msg = "Printavo credentials saved successfully!\n\n"

            if vendors:
                vendor_str = " and ".join(vendors)
                msg += f"Product descriptions will be automatically looked up from {vendor_str}.\n\n"
            else:
                msg += "No vendor credentials configured.\nProduct descriptions won't be auto-filled.\n\n"

            # FIXED: Added Claude status to success message
            if claude_apikey:
                msg += "✓ Claude AI configured - AI processing enabled!"
            else:
                msg += "⚠ Claude AI not configured - AI processing will be disabled."

            QMessageBox.information(self, "Success", msg)
            self.accept()
        except Exception as e:
            QMessageBox.critical(
                self,
                "Error",
                f"Failed to save credentials:\n{str(e)}"
            )


class PrintavoGUI(QMainWindow):
    """Main GUI window for Printavo quote creation"""

    def __init__(self):
        super().__init__()
        self.csv_path = None
        self.worker = None
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface"""
        self.setWindowTitle("Printavo Quote Creator")
        self.setGeometry(100, 100, 1000, 800)

        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout()
        main_widget.setLayout(main_layout)

        # ===== LEFT SIDE: Main content =====
        left_panel = QWidget()
        left_layout = QVBoxLayout()
        left_panel.setLayout(left_layout)

        # Title and settings button
        title_layout = QHBoxLayout()
        title = QLabel("Printavo Quote Creator")
        title_font = QFont()
        title_font.setPointSize(16)
        title_font.setBold(True)
        title.setFont(title_font)
        title_layout.addWidget(title)
        title_layout.addStretch()

        self.settings_btn = QPushButton("Settings")
        self.settings_btn.clicked.connect(self.show_settings)
        title_layout.addWidget(self.settings_btn)

        left_layout.addLayout(title_layout)

        # Credentials status
        self.creds_status = QLabel()
        self.ss_creds_status = QLabel()
        self.sanmar_creds_status = QLabel()
        self.claude_creds_status = QLabel()
        self.update_credentials_status()
        left_layout.addWidget(self.creds_status)
        left_layout.addWidget(self.ss_creds_status)
        left_layout.addWidget(self.sanmar_creds_status)
        left_layout.addWidget(self.claude_creds_status)

        left_layout.addSpacing(15)

        # ===== FILE INPUT SECTION (SIMPLIFIED) =====
        input_group = QGroupBox("Order Data Input")
        input_layout = QVBoxLayout()

        # Two-column layout for input options
        options_layout = QHBoxLayout()

        # LEFT: Traditional file upload (simplified)
        trad_layout = QVBoxLayout()

        trad_title = QLabel("Upload File")
        trad_title_font = QFont()
        trad_title_font.setPointSize(11)
        trad_title_font.setBold(True)
        trad_title.setFont(trad_title_font)
        trad_layout.addWidget(trad_title)

        trad_desc = QLabel("Pre-formatted CSV or Excel")
        trad_desc.setStyleSheet("color: #666; font-size: 10px;")
        trad_layout.addWidget(trad_desc)

        trad_layout.addSpacing(5)

        # File selection - single line
        self.file_label = QLabel("No file selected")
        self.file_label.setWordWrap(True)
        self.file_label.setStyleSheet(
            "padding: 6px; border: 1px solid #ccc; border-radius: 3px; "
            "background-color: white; font-size: 10px;"
        )
        trad_layout.addWidget(self.file_label)

        self.select_btn = QPushButton("Browse Files")
        self.select_btn.clicked.connect(self.select_file)
        self.select_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #1976D2;
            }
        """)
        trad_layout.addWidget(self.select_btn)

        options_layout.addLayout(trad_layout)

        # Vertical divider
        divider = QFrame()
        divider.setFrameShape(QFrame.VLine)
        divider.setFrameShadow(QFrame.Sunken)
        divider.setStyleSheet("background-color: #ddd;")
        options_layout.addWidget(divider)

        # RIGHT: AI Processing (simplified)
        ai_layout = QVBoxLayout()

        ai_title = QLabel("AI Processing")
        ai_title_font = QFont()
        ai_title_font.setPointSize(11)
        ai_title_font.setBold(True)
        ai_title.setFont(ai_title_font)
        ai_layout.addWidget(ai_title)

        ai_desc = QLabel("Extract data from any format")
        ai_desc.setStyleSheet("color: #666; font-size: 10px;")
        ai_layout.addWidget(ai_desc)

        ai_layout.addSpacing(5)

        # AI result label
        self.ai_result_label = QLabel("No AI-processed data")
        self.ai_result_label.setWordWrap(True)
        self.ai_result_label.setStyleSheet(
            "padding: 6px; border: 1px solid #ccc; border-radius: 3px; "
            "background-color: white; font-size: 10px;"
        )
        ai_layout.addWidget(self.ai_result_label)

        self.ai_process_btn = QPushButton("Use AI Processing")
        self.ai_process_btn.clicked.connect(self.open_ai_processing)
        self.ai_process_btn.setStyleSheet("""
            QPushButton {
                padding: 8px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 3px;
                font-weight: bold;
                font-size: 11px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """)
        ai_layout.addWidget(self.ai_process_btn)

        options_layout.addLayout(ai_layout)

        input_layout.addLayout(options_layout)
        input_group.setLayout(input_layout)
        left_layout.addWidget(input_group)

        left_layout.addSpacing(15)

        # ===== QUOTE DETAILS SECTION =====
        # Contact ID input group
        contact_group = QGroupBox("Customer Contact ID")
        contact_layout = QVBoxLayout()

        help_text = QLabel(
            "Enter the Printavo Contact ID (found in the URL when viewing a contact).\n"
            "Example: https://example.printavo.com/contacts/12345 -> Contact ID is 12345"
        )
        help_text.setWordWrap(True)
        help_text.setStyleSheet("color: #666; font-size: 10px; margin-bottom: 8px;")
        contact_layout.addWidget(help_text)

        id_layout = QHBoxLayout()
        id_layout.addWidget(QLabel("Contact ID:"))
        self.contact_input = QLineEdit()
        self.contact_input.setText("6989038")  # Default value
        self.contact_input.setPlaceholderText("Enter Printavo contact ID")
        self.contact_input.textChanged.connect(self.update_create_button)
        id_layout.addWidget(self.contact_input, stretch=1)
        contact_layout.addLayout(id_layout)

        contact_group.setLayout(contact_layout)
        left_layout.addWidget(contact_group)

        # Note input
        note_group = QGroupBox("Quote Note (Optional)")
        note_layout = QVBoxLayout()
        self.note_input = QLineEdit()
        self.note_input.setPlaceholderText("Quote note/description")
        self.note_input.setText("Automated quote created via Printavo API v2")
        note_layout.addWidget(self.note_input)
        note_group.setLayout(note_layout)
        left_layout.addWidget(note_group)

        left_layout.addSpacing(15)

        # Create button (centered)
        self.create_btn = QPushButton("Create Quote in Printavo")
        self.create_btn.clicked.connect(self.create_quote)
        self.create_btn.setEnabled(False)
        self.create_btn.setStyleSheet("""
            QPushButton {
                padding: 15px;
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
        left_layout.addWidget(self.create_btn)

        left_layout.addStretch()

        # Add left panel to main layout
        main_layout.addWidget(left_panel, stretch=2)

        # Vertical divider
        main_divider = QFrame()
        main_divider.setFrameShape(QFrame.VLine)
        main_divider.setFrameShadow(QFrame.Sunken)
        main_divider.setStyleSheet("background-color: #ccc;")
        main_layout.addWidget(main_divider)

        # ===== RIGHT SIDE: Processing Log =====
        right_panel = QWidget()
        right_layout = QVBoxLayout()
        right_panel.setLayout(right_layout)

        log_title = QLabel("Processing Log")
        log_title_font = QFont()
        log_title_font.setPointSize(11)
        log_title_font.setBold(True)
        log_title.setFont(log_title_font)
        right_layout.addWidget(log_title)

        self.log_output = QTextEdit()
        self.log_output.setReadOnly(True)

        # Use platform-appropriate monospace font
        if os.name == 'nt':  # Windows
            log_font = QFont("Consolas", 9)
        else:  # macOS/Linux
            log_font = QFont("Courier", 9)

        self.log_output.setFont(log_font)
        self.log_output.setStyleSheet(
            "background-color: #f5f5f5; border: 1px solid #ddd; "
            "padding: 5px;"
        )
        right_layout.addWidget(self.log_output)

        # Add right panel to main layout
        main_layout.addWidget(right_panel, stretch=1)

    def open_ai_processing(self):
        """Open AI processing dialog"""
        import config

        # Check if Claude API key is configured
        if not config.CLAUDE_API_KEY:
            QMessageBox.warning(
                self,
                "Claude API Not Configured",
                "Claude API key is required for AI processing.\n\n"
                "Please go to Settings and add your Claude API key in the 'Claude AI' tab."
            )
            return

        from ai_processing_gui import AIProcessingGUI

        ai_dialog = AIProcessingGUI(self)
        ai_dialog.csv_generated.connect(self.on_ai_csv_generated)
        ai_dialog.exec_()

    def on_ai_csv_generated(self, csv_path):
        """Handle CSV generated from AI processing"""
        self.csv_path = csv_path
        filename = os.path.basename(csv_path)
        self.ai_result_label.setText(f"[SUCCESS] AI Generated: {filename}")
        self.ai_result_label.setStyleSheet(
            "padding: 6px; border: 2px solid #4CAF50; border-radius: 3px; "
            "background-color: #e8f5e9; font-weight: bold; font-size: 10px;"
        )

        # Also update the file label
        self.file_label.setText(f"[AI] {filename}")
        self.file_label.setStyleSheet(
            "padding: 6px; border: 1px solid #4CAF50; border-radius: 3px; "
            "background-color: #e8f5e9; font-size: 10px;"
        )

        self.update_create_button()
        self.log_output.append(f"[SUCCESS] AI-processed data loaded: {csv_path}\n")

        QMessageBox.information(
            self,
            "Success",
            "AI-processed data is ready! You can now create the quote."
        )

    def show_settings(self):
        """Show settings dialog for entering credentials"""
        dialog = SettingsDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            self.update_credentials_status()
            self.update_create_button()

    def update_credentials_status(self):
        """Update the credentials status labels"""
        # Printavo status
        creds_valid, creds_message = config.validate_credentials()
        self.creds_status.setText(creds_message)
        if creds_valid:
            self.creds_status.setStyleSheet("color: green;")
        else:
            self.creds_status.setStyleSheet("color: orange;")

        # SSActivewear status
        ss_valid, ss_message = config.validate_ssactivewear_credentials()
        self.ss_creds_status.setText(ss_message)
        if ss_valid:
            self.ss_creds_status.setStyleSheet("color: green;")
        else:
            self.ss_creds_status.setStyleSheet("color: #ff9800;")

        # Sanmar status
        sanmar_valid, sanmar_message = config.validate_sanmar_credentials()
        self.sanmar_creds_status.setText(sanmar_message)
        if sanmar_valid:
            self.sanmar_creds_status.setStyleSheet("color: green;")
        else:
            self.sanmar_creds_status.setStyleSheet("color: #ff9800;")

        # Claude status (NEW)
        claude_valid, claude_message = config.validate_claude_credentials()
        self.claude_creds_status.setText(claude_message)
        if claude_valid:
            self.claude_creds_status.setStyleSheet("color: green;")
        else:
            self.claude_creds_status.setStyleSheet("color: #ff9800;")

    def select_file(self):
        """Open file dialog to select CSV file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select CSV or Excel File",
            "",
            "Supported Files (*.csv *.xlsx *.xls);;CSV Files (*.csv);;Excel Files (*.xlsx *.xls);;All Files (*)"
        )
        if file_path:
            self.csv_path = file_path
            filename = os.path.basename(file_path)
            self.file_label.setText(filename)
            self.file_label.setStyleSheet(
                "padding: 6px; border: 1px solid #2196F3; border-radius: 3px; "
                "background-color: #e3f2fd; font-size: 10px;"
            )

            # Clear AI result label when manual file is selected
            self.ai_result_label.setText("No AI-processed data")
            self.ai_result_label.setStyleSheet(
                "padding: 6px; border: 1px solid #ccc; border-radius: 3px; "
                "background-color: white; font-size: 10px;"
            )

            self.update_create_button()
            self.log_output.append(f"[INFO] File selected: {filename}\n")

    def update_create_button(self):
        """Enable/disable create button based on input validity"""
        enabled = (
                self.csv_path is not None and
                len(self.contact_input.text().strip()) > 0 and
                bool(config.PRINTAVO_EMAIL) and bool(config.PRINTAVO_TOKEN)
        )
        self.create_btn.setEnabled(bool(enabled))

    def create_quote(self):
        """Start the quote creation process"""
        if not self.csv_path:
            QMessageBox.warning(self, "Error", "Please select a CSV file or use AI processing first.")
            return

        contact_id = self.contact_input.text().strip()
        if not contact_id:
            QMessageBox.warning(self, "Error", "Please enter a contact ID.")
            return

        # Disable buttons during processing
        self.create_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.ai_process_btn.setEnabled(False)
        self.contact_input.setEnabled(False)
        self.note_input.setEnabled(False)

        # Clear log
        self.log_output.clear()
        self.log_output.append("[INFO] Starting quote creation process...\n")

        # Start worker thread
        note = self.note_input.text().strip()
        self.worker = WorkerThread(self.csv_path, contact_id, note)
        self.worker.log_signal.connect(self.append_log)
        self.worker.finished_signal.connect(self.on_finished)
        self.worker.start()

    def append_log(self, text):
        """Append text to the log output"""
        self.log_output.append(text)
        self.log_output.verticalScrollBar().setValue(
            self.log_output.verticalScrollBar().maximum()
        )

    def on_finished(self, success, message):
        """Handle completion of quote creation"""
        # Re-enable buttons
        self.select_btn.setEnabled(True)
        self.ai_process_btn.setEnabled(True)
        self.contact_input.setEnabled(True)
        self.note_input.setEnabled(True)
        self.update_create_button()

        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)