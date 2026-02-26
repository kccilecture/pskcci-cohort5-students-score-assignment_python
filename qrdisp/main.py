from qtpy import QtWidgets, QtGui, QtCore
from PIL import Image
from PIL.ImageQt import ImageQt
import qrcode
from qrcode.constants import ERROR_CORRECT_M
import sys
import argparse

DEFAULT_WIDTH = 800
DEFAULT_HEIGHT = 600


class QRWindow(QtWidgets.QWidget):
    def __init__(self, width=DEFAULT_WIDTH, height=DEFAULT_HEIGHT):
        super().__init__()
        self.setWindowTitle("QR Disp from string")
        self.resize(width, height)

        # --- widgets ---
        self.data_edit = QtWidgets.QLineEdit(self)
        self.data_edit.returnPressed.connect(self.generate)

        self.gen_btn = QtWidgets.QPushButton("Generate", self)
        self.exit_btn = QtWidgets.QPushButton("Exit", self)

        self.preview = QtWidgets.QLabel(self)
        self.preview.setFrameShape(QtWidgets.QFrame.Box)
        self.preview.setAlignment(QtCore.Qt.AlignCenter)

        # --- layout ---
        form = QtWidgets.QGridLayout()
        form.addWidget(QtWidgets.QLabel("Data"), 0, 0)
        form.addWidget(self.data_edit, 0, 1, 1, 3)

        btns = QtWidgets.QHBoxLayout()
        btns.addStretch(1)
        btns.addWidget(self.gen_btn)
        btns.addWidget(self.exit_btn)

        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.addLayout(form)
        root.addLayout(btns)
        root.addWidget(self.preview, 1)

        # --- state ---
        self._pil_image = None  # keep original PIL image for saving

        # --- signals ---
        self.gen_btn.clicked.connect(self.generate)
        self.exit_btn.clicked.connect(self.close)

        # enable drag & drop of URLs/text
        self.setAcceptDrops(True)

    def resizeEvent(self, event):
        """Handle window resize to update QR code scaling"""
        super().resizeEvent(event)
        # Regenerate QR code with new size if we have data
        if hasattr(self, '_pil_image') and self._pil_image is not None:
            self._update_preview_scaling()

    def _update_preview_scaling(self):
        """Update the QR code scaling for current preview size"""
        if self._pil_image is None:
            return

        # Convert PIL -> QImage -> QPixmap
        qimage = ImageQt(self._pil_image)
        pix = QtGui.QPixmap.fromImage(qimage)

        # Scale to maximize for current window size
        preview_size = self.preview.size()
        # Use the full preview area with minimal padding
        target = QtCore.QSize(preview_size.width() - 4,
                              preview_size.height() - 4)

        # Scale to fit the available space, maintaining aspect ratio
        scaled = pix.scaled(
            target,
            QtCore.Qt.KeepAspectRatio,
            QtCore.Qt.SmoothTransformation
        )
        self.preview.setPixmap(scaled)

    # ---- drag & drop ----
    def dragEnterEvent(self, e: QtGui.QDragEnterEvent):
        if e.mimeData().hasText():
            e.acceptProposedAction()

    def dropEvent(self, e: QtGui.QDropEvent):
        text = e.mimeData().text().strip()
        # browsers often drop as "url\n" with schema
        if text.startswith("file://"):
            return  # ignore file drops
        self.data_edit.setText(text)
        self.generate()

    # ---- actions ----
    def generate(self):
        text_data = self.data_edit.text().strip()
        if not text_data:
            QtWidgets.QMessageBox.warning(
                self, "Missing Text", "Please enter some text.")
            return

        try:
            qr = qrcode.QRCode()
            qr.add_data(text_data)
            qr.make(fit=True)
            self._pil_image = qr.make_image(
                fill_color="black", back_color="white").convert("RGB")

            # Update the preview with proper scaling
            self._update_preview_scaling()
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self, "Error", f"Failed to generate QR:\n{e}")


def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='QR Code Generator from String', add_help=False)
    parser.add_argument('text', nargs='?', help='Text to encode in QR code')
    parser.add_argument('-w', '--width', type=int, default=DEFAULT_WIDTH,
                        help=f'Window width (default: {DEFAULT_WIDTH})')
    parser.add_argument('-h', '--height', type=int, default=DEFAULT_HEIGHT,
                        help=f'Window height (default: {DEFAULT_HEIGHT})')
    parser.add_argument('-f', '--fullscreen', action='store_true',
                        help='Display in fullscreen mode')
    parser.add_argument('--help', action='help',
                        help='Show this help message and exit')

    args = parser.parse_args()
    app = QtWidgets.QApplication(sys.argv)
    window = QRWindow(width=args.width, height=args.height)

    # If text was provided via command line, set it and generate QR
    if args.text:
        window.data_edit.setText(args.text)
        window.generate()

    # Show window in fullscreen or normal mode
    if args.fullscreen:
        window.showFullScreen()
    else:
        window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
