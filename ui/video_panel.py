"""
ui/video_panel.py - Synchronized Video Playback Panel
CAN log-lar bilen wideo faýllaryny birwagtda (sync) görkezýär.
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QSlider, QStyle, QFileDialog,
    QFrame, QSpinBox
)
from PyQt5.QtMultimedia import QMediaPlayer, QMediaContent
from PyQt5.QtMultimediaWidgets import QVideoWidget
from PyQt5.QtCore import Qt, QUrl, pyqtSignal
from core.i18n import I18N


class VideoPlaybackPanel(QWidget):
    """
    Video pleýer we sync dolandyryş paneli.
    """
    # Signal: current_time_ms, total_time_ms
    position_changed = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.offset_ms = 0
        self._setup_ui()
        self._setup_player()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        # 1. Video Display Area
        self.video_widget = QVideoWidget()
        self.video_widget.setMinimumHeight(240)
        self.video_widget.setStyleSheet("background-color: black; border-radius: 8px;")
        layout.addWidget(self.video_widget)

        # 2. Controls Area
        controls_frame = QFrame()
        controls_frame.setObjectName("CardHeader") # Reuse theme styling
        c_layout = QVBoxLayout(controls_frame)
        
        # Seeker Slider
        self.position_slider = QSlider(Qt.Horizontal)
        self.position_slider.setRange(0, 0)
        self.position_slider.sliderMoved.connect(self._set_position)
        c_layout.addWidget(self.position_slider)

        # Buttons and Offset
        btn_layout = QHBoxLayout()
        
        self.play_btn = QPushButton()
        self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))
        self.play_btn.setFixedSize(40, 30)
        self.play_btn.clicked.connect(self._toggle_playback)
        btn_layout.addWidget(self.play_btn)

        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setProperty("caption", True)
        btn_layout.addWidget(self.time_label)

        btn_layout.addStretch()

        # Offset Control
        self.offset_label = QLabel(I18N.t("video_offset"))
        btn_layout.addWidget(self.offset_label)
        
        self.offset_spin = QSpinBox()
        self.offset_spin.setRange(-600000, 600000) # +/- 10 mins
        self.offset_spin.setSingleStep(100)
        self.offset_spin.setFixedWidth(80)
        self.offset_spin.valueChanged.connect(self._on_offset_changed)
        btn_layout.addWidget(self.offset_spin)

        self.btn_load = QPushButton(I18N.t("video_load"))
        self.btn_load.clicked.connect(self._on_load_clicked)
        btn_layout.addWidget(self.btn_load)

        c_layout.addLayout(btn_layout)
        layout.addWidget(controls_frame)

    def retranslate_ui(self):
        """Update strings dynamically."""
        self.offset_label.setText(I18N.t("video_offset"))
        self.btn_load.setText(I18N.t("video_load"))

    def _setup_player(self):
        self.media_player = QMediaPlayer(None, QMediaPlayer.VideoSurface)
        self.media_player.setVideoOutput(self.video_widget)
        
        # Signals
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.stateChanged.connect(self._on_state_changed)
        self.media_player.error.connect(self._handle_errors)

    def load_video(self, file_path):
        """Video faýlyny ýükleýär."""
        if file_path:
            self.media_player.setMedia(QMediaContent(QUrl.fromLocalFile(file_path)))
            self.play_btn.setEnabled(True)

    def _on_load_clicked(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, I18N.t("video_open_title"), "", f"{I18N.t('video_files')} (*.mp4 *.avi *.mkv *.mov)"
        )
        if file_path:
            self.load_video(file_path)

    def _toggle_playback(self):
        if self.media_player.state() == QMediaPlayer.PlayingState:
            self.media_player.pause()
        else:
            self.media_player.play()

    def _on_state_changed(self, state):
        if state == QMediaPlayer.PlayingState:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPause))
        else:
            self.play_btn.setIcon(self.style().standardIcon(QStyle.SP_MediaPlay))

    def _on_position_changed(self, position):
        self.position_slider.setValue(position)
        self._update_time_label(position, self.media_player.duration())
        # Emit signal for global synchronization
        self.position_changed.emit(position)

    def _on_duration_changed(self, duration):
        self.position_slider.setRange(0, duration)
        self._update_time_label(self.media_player.position(), duration)

    def _set_position(self, position):
        self.media_player.setPosition(position)

    def _on_offset_changed(self, value):
        self.offset_ms = value
        # Trigger an update to re-sync with the new offset
        self.position_changed.emit(self.media_player.position())

    def _update_time_label(self, current, total):
        curr_s = current // 1000
        tot_s = total // 1000
        self.time_label.setText(
            f"{curr_s // 60:02d}:{curr_s % 60:02d} / {tot_s // 60:02d}:{tot_s % 60:02d}"
        )

    def _handle_errors(self):
        self.play_btn.setEnabled(False)
        err_msg = self.media_player.errorString()
        print(f"Video Player Error: {err_msg}")

    def get_sync_timestamp(self, video_pos_ms):
        """
        Videonyň häzirki wagtyny (ms) CAN logynyň timestamp-yna (s) öwürýär.
        Formula: log_ts = video_ts + offset
        """
        return (video_pos_ms + self.offset_ms) / 1000.0
