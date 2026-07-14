import sys

# pyrefly: ignore [missing-import]
from PySide6.QtWidgets import QApplication
# pyrefly: ignore [missing-import]
from ui.mainwindow import MainWindow


def main():
    app = QApplication(sys.argv)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()