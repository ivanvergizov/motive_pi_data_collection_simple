from __future__ import annotations

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from motion_app.core.constants import DEFAULT_PREVIEW_AA
from motion_app.rendering.pyvista_scene import PyVistaRigidBodyScene
from motion_app.ui.widgets.render_settings import RenderSettingsWidget
from motion_app.ui.widgets.smoothing_controls import SmoothingControlsWidget


class LivePlaybackTab(QWidget):
    """Live transport is still a placeholder; the PyVista scene is ready for incoming frames."""

    def __init__(self, anti_aliasing: str = DEFAULT_PREVIEW_AA) -> None:
        super().__init__()
        self.status_label = QLabel("Live transport is not implemented yet.")
        self.status_label.setWordWrap(True)
        self.bind_address_lineedit = QLineEdit("0.0.0.0")
        self.data_port_spinbox = QSpinBox()
        self.data_port_spinbox.setRange(1, 65535)
        self.data_port_spinbox.setValue(1511)
        self.start_button = QPushButton("Start live stream")
        self.stop_button = QPushButton("Stop live stream")
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(False)
        self.record_checkbox = QCheckBox("Record incoming data")
        self.record_checkbox.setEnabled(False)
        self.smoothing = SmoothingControlsWidget("Live smoothing", "Apply live smoothing")
        self.render_settings = RenderSettingsWidget(
            "Live preview settings",
            "The preview follows the visible widget size and monitor DPI.",
        )
        self.metrics_label = QLabel()
        self.metrics_label.setWordWrap(True)
        self.scene = PyVistaRigidBodyScene(anti_aliasing)

        self.metrics_timer = QTimer(self)
        self.metrics_timer.setInterval(500)
        self.metrics_timer.timeout.connect(self._update_metrics)
        self.metrics_timer.start()
        self.render_settings.fps_combobox.currentTextChanged.connect(self._update_metrics)

        self._build_layout()
        self._update_metrics()

    def _build_layout(self) -> None:
        settings = QWidget()
        layout = QVBoxLayout(settings)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        layout.addWidget(self._create_connection_group())
        layout.addWidget(self.smoothing)
        layout.addWidget(self.render_settings)
        layout.addWidget(self.metrics_label)
        layout.addStretch()

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFixedWidth(340)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setWidget(settings)

        root = QHBoxLayout(self)
        root.addWidget(scroll)
        root.addWidget(self.scene, stretch=1)

    def _create_connection_group(self) -> QGroupBox:
        group = QGroupBox("Live connection")
        layout = QVBoxLayout(group)
        layout.addWidget(QLabel("Bind address"))
        layout.addWidget(self.bind_address_lineedit)
        layout.addWidget(QLabel("Data port"))
        layout.addWidget(self.data_port_spinbox)
        buttons = QHBoxLayout()
        buttons.addWidget(self.start_button)
        buttons.addWidget(self.stop_button)
        layout.addLayout(buttons)
        layout.addWidget(self.record_checkbox)
        layout.addWidget(self.status_label)
        return group

    def _update_metrics(self, _text: str | None = None) -> None:
        self.metrics_label.setText(self.scene.metrics_text(self.render_settings.fps()))

    def set_global_anti_aliasing(self, anti_aliasing: str) -> None:
        self.scene.set_anti_aliasing(anti_aliasing)
        self.scene.request_render()
        self._update_metrics()

    def shutdown(self) -> None:
        self.metrics_timer.stop()
        self.scene.shutdown()
