import sys
from PyQt5.QtWidgets import QApplication
from core.logger import AppLogger
from ui.main_window import MainWindow


def main():
    AppLogger.setup()
    log = AppLogger.get("main")
    log.info("=" * 60)
    log.info("NETD Calculator starting")

    app = QApplication(sys.argv)
    app.setApplicationName("NETD Calculator")
    app.setOrganizationName("TIPL")

    window = MainWindow()
    window.show()
    log.info("Main window displayed")

    exit_code = app.exec_()
    log.info("NETD Calculator exiting (code %d)", exit_code)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
