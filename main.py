#!/usr/bin/env python3
"""
Printavo v2 CSV -> Quote script with PyQt5 GUI

Usage:
  - Run: python main.py
  - Click Settings to enter credentials (saved to ~/.printavo_quote_creator/config.json)
  - Select CSV file and enter contact ID via GUI
"""

import sys
from PyQt5.QtWidgets import QApplication

import config
from gui import PrintavoGUI


def main():
    """Main entry point for the application"""
    app = QApplication(sys.argv)
    window = PrintavoGUI()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()