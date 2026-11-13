STYLE = """
QWidget { font-family: 'Segoe UI'; font-size: 13px; color: #243a35; }
QMainWindow, QWidget#workspace { background: #f4f6f3; }
QFrame#sidebar { background: #173d38; }
QLabel#brand { color: white; font-size: 26px; font-weight: 700; }
QLabel#sidebarHint { color: #b3ccbc; font-size: 12px; }
QPushButton#nav { text-align: left; background: transparent; color: #c3d8c8;
  border: 0; padding: 13px 16px; border-radius: 7px; }
QPushButton#nav:checked { background: #d9eacb; color: #264b3b; font-weight: 600; }
QPushButton#nav:hover { background: #31594c; color: white; }
QLabel#heading { font-size: 27px; font-weight: 650; }
QLabel#subheading { font-size: 18px; font-weight: 600; }
QLabel#muted { color: #687b6c; font-size: 12px; }
QLabel#status { background: #e7efdf; color: #496a39; padding: 12px; border-radius: 7px; }
QFrame#panel { background: white; border: 1px solid #e0e7dc; border-radius: 10px; }
QPushButton { background: #2c654d; color: white; border: 1px solid #2c654d;
  padding: 10px 17px; border-radius: 6px; font-weight: 600; }
QPushButton:hover { background: #204f3c; }
QPushButton:disabled { background: #dce3d7; color: #8b9a83; border-color: #dce3d7; }
QPushButton#secondary { background: white; color: #46693a; border-color: #cbd9c3; }
QPushButton#secondary:hover { background: #edf3e7; }
QComboBox, QLineEdit, QSpinBox { border: 1px solid #cdd9c7; border-radius: 5px;
  padding: 8px; background: white; selection-background-color: #dceccf; }
QComboBox QAbstractItemView { background: white; selection-background-color: #dceccf; color: #243a35; }
QCheckBox { padding: 5px 0; spacing: 9px; }
QCheckBox::indicator { width: 17px; height: 17px; }
QTableWidget { background: white; alternate-background-color: #f7faf4; gridline-color: #e8eee2;
  border: 1px solid #e1e9db; selection-background-color: #ddebd1; selection-color: #243a35; }
QHeaderView::section { background: #edf3e7; color: #617b51; padding: 10px;
  border: 0; border-bottom: 1px solid #dfe8d6; font-size: 12px; font-weight: 600; }
QScrollArea { border: 0; background: transparent; }
QStatusBar { background: #edf2e8; color: #7b8d6e; }
"""
