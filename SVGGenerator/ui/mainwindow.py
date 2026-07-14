import os
# pyrefly: ignore [missing-import]
from PySide6.QtGui import QPixmap
# pyrefly: ignore [missing-import]
from PySide6.QtWidgets import QMessageBox

from core.svg_export import create_svg
# pyrefly: ignore [missing-import]
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QLabel, QPushButton, QLineEdit,
    QSpinBox, QCheckBox, QFileDialog, QVBoxLayout,
    QHBoxLayout, QGridLayout, QFrame,
)

# pyrefly: ignore [missing-import]
from PySide6.QtCore import Qt
# pyrefly: ignore [missing-import]
from PySide6.QtSvgWidgets import QSvgWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SVG Generator")
        self.resize(1100, 850)
        self.build_ui()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        # プレビューエリア
        preview_layout = QHBoxLayout()
        self.inputPreview = QLabel("入力画像")
        self.inputPreview.setAlignment(Qt.AlignCenter)
        self.inputPreview.setFrameShape(QFrame.Box)
        self.inputPreview.setMinimumSize(420, 420)
        preview_layout.addWidget(self.inputPreview)

        svgFrame = QFrame()
        svgFrame.setFrameShape(QFrame.Box)
        svgFrame.setMinimumSize(420, 420)
        svgLayout = QVBoxLayout(svgFrame)
        self.svgPreview = QSvgWidget()
        svgLayout.addWidget(self.svgPreview)
        preview_layout.addWidget(svgFrame)
        main_layout.addLayout(preview_layout)

        # ファイル設定
        grid = QGridLayout()
        grid.addWidget(QLabel("入力画像"), 0, 0)
        self.inputPath = QLineEdit()
        grid.addWidget(self.inputPath, 0, 1)
        self.inputButton = QPushButton("参照")
        grid.addWidget(self.inputButton, 0, 2)
        
        grid.addWidget(QLabel("保存先"), 1, 0)
        self.outputPath = QLineEdit()
        grid.addWidget(self.outputPath, 1, 1)
        self.outputButton = QPushButton("参照")
        grid.addWidget(self.outputButton, 1, 2)
        main_layout.addLayout(grid)

        # 設定エリア
        option = QGridLayout()
        option.addWidget(QLabel("輪郭太さ"), 0, 0)
        self.strokeSpin = QSpinBox()
        self.strokeSpin.setRange(1, 50); self.strokeSpin.setValue(5)
        option.addWidget(self.strokeSpin, 0, 1)

        option.addWidget(QLabel("オフセット"), 1, 0)
        self.offsetSpin = QSpinBox()
        self.offsetSpin.setRange(0, 100); self.offsetSpin.setValue(15)
        option.addWidget(self.offsetSpin, 1, 1)

        # スタンド用パラメータ
        option.addWidget(QLabel("差し込み幅"), 0, 2)
        self.tabWidthSpin = QSpinBox()
        self.tabWidthSpin.setRange(10, 200); self.tabWidthSpin.setValue(60)
        option.addWidget(self.tabWidthSpin, 0, 3)

        option.addWidget(QLabel("差し込み高さ"), 1, 2)
        self.tabHeightSpin = QSpinBox()
        self.tabHeightSpin.setRange(5, 50); self.tabHeightSpin.setValue(20)
        option.addWidget(self.tabHeightSpin, 1, 3)

        option.addWidget(QLabel("土台サイズ(横)"), 2, 0)
        self.baseXSpin = QSpinBox()
        self.baseXSpin.setRange(50, 500); self.baseXSpin.setValue(100)
        option.addWidget(self.baseXSpin, 2, 1)

        option.addWidget(QLabel("土台サイズ(縦)"), 2, 2)
        self.baseYSpin = QSpinBox()
        self.baseYSpin.setRange(50, 500); self.baseYSpin.setValue(60)
        option.addWidget(self.baseYSpin, 2, 3)

        # 【変更】本体の下部を広げる「横幅」を設定するスピンボックス
        option.addWidget(QLabel("本体底面幅(px)"), 3, 0)
        self.bottomWidthSpin = QSpinBox()
        self.bottomWidthSpin.setRange(20, 1000); self.bottomWidthSpin.setValue(200)
        option.addWidget(self.bottomWidthSpin, 3, 1)

        main_layout.addLayout(option)

        # ボタン
        button_layout = QHBoxLayout()
        self.previewButton = QPushButton("プレビュー")
        self.exportButton = QPushButton("SVG作成")
        button_layout.addStretch()
        button_layout.addWidget(self.previewButton)
        button_layout.addWidget(self.exportButton)
        main_layout.addLayout(button_layout)

        # イベント接続
        self.inputButton.clicked.connect(self.select_input)
        self.outputButton.clicked.connect(self.select_output)
        self.previewButton.clicked.connect(self.preview_svg)
        self.exportButton.clicked.connect(self.export_svg)

    def select_input(self):
        filename, _ = QFileDialog.getOpenFileName(self, "入力画像", "", "PNG (*.png)")
        if filename:
            self.inputPath.setText(filename)
            self.show_input_image(filename)

    def select_output(self):
        filename, _ = QFileDialog.getSaveFileName(self, "保存先", "", "SVG (*.svg)")
        if filename: self.outputPath.setText(filename)

    def show_input_image(self, filename):
        pixmap = QPixmap(filename).scaled(self.inputPreview.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.inputPreview.setPixmap(pixmap)

    def preview_svg(self):
        input_png = self.inputPath.text().strip()
        if not input_png:
            QMessageBox.warning(self, "エラー", "入力画像を選択してください。")
            return

        preview_svg = os.path.join("output", "temp_preview.svg")
        os.makedirs("output", exist_ok=True)

        try:
            create_svg(
                input_png=input_png,
                output_svg=preview_svg,
                simplify_ratio=0.0005,
                offset_px=self.offsetSpin.value(),
                base_offset_px=self.strokeSpin.value(),
                tab_width=self.tabWidthSpin.value(),
                tab_height=self.tabHeightSpin.value(),
                base_rx=self.baseXSpin.value(),
                base_ry=self.baseYSpin.value(),
                bottom_width=self.bottomWidthSpin.value() # 変更
            )
            self.svgPreview.load(preview_svg)
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))

    def export_svg(self):
        input_png = self.inputPath.text().strip()
        output_svg = self.outputPath.text().strip()
        
        if not input_png or not output_svg:
            QMessageBox.warning(self, "エラー", "入力画像と保存先を指定してください。")
            return
            
        try:
            create_svg(
                input_png=input_png,
                output_svg=output_svg,
                simplify_ratio=0.0005,
                offset_px=self.offsetSpin.value(),
                base_offset_px=self.strokeSpin.value(),
                tab_width=self.tabWidthSpin.value(),
                tab_height=self.tabHeightSpin.value(),
                base_rx=self.baseXSpin.value(),
                base_ry=self.baseYSpin.value(),
                bottom_width=self.bottomWidthSpin.value() # 変更
            )
            QMessageBox.information(self, "完了", "SVGを保存しました。")
        except Exception as e:
            QMessageBox.critical(self, "エラー", str(e))