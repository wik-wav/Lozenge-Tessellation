"""festvox_gui.py -- Windows-XP styled desktop GUI for a Festival/Festvox backend.

PyQt5 + PyQtGraph. Features:
  * config.json driven Language + Voicebank pickers, XP toolbar
  * waveform view with draggable red phoneme boundaries
  * duration-aligned, editable phoneme text fields under the waveform
  * dragging a boundary time-stretches that segment (real DSP) and redraws
  * Vocaloid-style Velocity envelope with draggable keyframe nodes
  * Generate (real Festival, demo fallback) / Play / Stop / Save / Export WAV

Run:  python festvox_gui.py
Deps: pip install PyQt5 pyqtgraph numpy   (optional: sounddevice, librosa)
"""
from __future__ import annotations
import os, sys, copy

import numpy as np

try:
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import Qt
    import pyqtgraph as pg
except Exception as e:  # pragma: no cover
    sys.stderr.write("This GUI needs PyQt5 and pyqtgraph:\n"
                     "    pip install PyQt5 pyqtgraph numpy\n\n%s\n" % e)
    raise

import festvox_core as fc

pg.setConfigOptions(antialias=True)

MIN_SEG = 0.010  # s, smallest phoneme duration a boundary can create

# --------------------------------------------------------------- XP Luna theme
XP_QSS = """
* { font-family: Tahoma, 'Segoe UI', sans-serif; font-size: 11px; color: #000; }
QMainWindow, QWidget { background: #ECE9D8; }
QMenuBar { background: #ECE9D8; }
QMenuBar::item:selected { background: #316AC5; color: #fff; }
QMenu { background: #fff; border: 1px solid #808080; }
QMenu::item:selected { background: #316AC5; color: #fff; }
QGroupBox { border: 1px solid #ACA899; margin-top: 8px; }
QGroupBox::title { subcontrol-origin: margin; left: 7px; padding: 0 2px; }
QLabel#hdr { font-weight: bold; }
QPushButton {
    background: qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 #FDFDFD, stop:1 #E3E0D2);
    border: 1px solid #707070; border-radius: 3px; padding: 4px 8px; min-height: 16px;
}
QPushButton:hover { border: 1px solid #E9A700; }
QPushButton:pressed { background: #DEDBCE; }
QPushButton:disabled { color: #A0A0A0; border: 1px solid #B4B0A4; }
QComboBox, QLineEdit, QListWidget, QSpinBox {
    background: #fff; border: 1px solid #7F9DB9; padding: 2px; selection-background-color: #316AC5;
}
QComboBox::drop-down { border-left: 1px solid #7F9DB9; width: 16px; }
QListWidget::item:selected { background: #316AC5; color: #fff; }
QSlider::groove:horizontal { height: 4px; background: #B4B0A4; border: 1px solid #808080; }
QSlider::handle:horizontal { width: 11px; background: #ECE9D8; border: 1px solid #404040;
    margin: -6px 0; border-radius: 2px; }
QStatusBar { background: #ECE9D8; border-top: 1px solid #ACA899; }
QLineEdit#phon { background: #fff; border: 1px solid #7F9DB9; padding: 1px; qproperty-alignment: AlignCenter; }
"""


# ------------------------------------------------------------------- audio play
class Player:
    """Prefers sounddevice; falls back to Qt Multimedia; else no-op with error."""
    def __init__(self):
        self.mode = None
        self._sd = None
        self._qmp = None
        self._tmp = None
        try:
            import sounddevice as sd
            self._sd = sd
            self.mode = "sd"
        except Exception:
            try:
                from PyQt5.QtMultimedia import QMediaPlayer
                self._qmp = QMediaPlayer()
                self.mode = "qt"
            except Exception:
                self.mode = None

    def play(self, samples, sr):
        samples = np.asarray(samples, dtype=np.float32)
        if samples.size == 0:
            raise RuntimeError("Nothing to play -- generate audio first.")
        if self.mode == "sd":
            self._sd.stop()
            self._sd.play(samples, int(sr))
        elif self.mode == "qt":
            from PyQt5.QtMultimedia import QMediaContent
            import tempfile
            self._tmp = tempfile.mktemp(suffix=".wav")
            fc.write_wav(self._tmp, samples, sr)
            self._qmp.setMedia(QMediaContent(QtCore.QUrl.fromLocalFile(self._tmp)))
            self._qmp.play()
        else:
            raise RuntimeError("No audio backend. Install sounddevice: pip install sounddevice")

    def stop(self):
        if self.mode == "sd":
            self._sd.stop()
        elif self.mode == "qt" and self._qmp is not None:
            self._qmp.stop()


# --------------------------------------------------------------- velocity nodes
class EnvelopeGraph(pg.GraphItem):
    """Draggable keyframe nodes joined by a line (Vocaloid-style envelope)."""
    def __init__(self, changed_cb=None):
        self.dragPoint = None
        self.dragOffset = None
        self.changed_cb = changed_cb
        self.tmax = 1.0
        self.data = {}
        pg.GraphItem.__init__(self)

    def set_nodes(self, ts, vs, tmax=None):
        if tmax:
            self.tmax = float(tmax)
        pos = np.column_stack([np.asarray(ts, float), np.asarray(vs, float)])
        n = len(pos)
        adj = (np.column_stack([np.arange(n - 1), np.arange(1, n)]).astype(int)
               if n > 1 else np.empty((0, 2), int))
        meta = np.empty(n, dtype=[('index', int)])
        meta['index'] = np.arange(n)
        self.data = dict(pos=pos, adj=adj, size=11, symbol='o', pxMode=True,
                         pen=pg.mkPen('#C05000', width=2),
                         symbolBrush=pg.mkBrush('#FFCC33'),
                         symbolPen=pg.mkPen('#7F3300', width=1.5), data=meta)
        pg.GraphItem.setData(self, **self.data)

    def nodes(self):
        p = self.data.get('pos')
        return [] if p is None else [(float(p[i, 0]), float(p[i, 1])) for i in range(len(p))]

    def add_node(self, t, v):
        p = self.data['pos']
        ts = list(p[:, 0]) + [float(t)]
        vs = list(p[:, 1]) + [float(v)]
        order = np.argsort(ts)
        self.set_nodes(np.array(ts)[order], np.array(vs)[order])
        if self.changed_cb:
            self.changed_cb()

    def mouseDragEvent(self, ev):
        if ev.button() != Qt.LeftButton:
            ev.ignore(); return
        if ev.isStart():
            pts = self.scatter.pointsAt(ev.buttonDownPos())
            if len(pts) == 0:
                self.dragPoint = None; ev.ignore(); return
            self.dragPoint = pts[0]
            ind = int(pts[0].data()[0])
            self.dragOffset = self.data['pos'][ind] - ev.buttonDownPos()
        elif ev.isFinish():
            self.dragPoint = None; return
        elif self.dragPoint is None:
            ev.ignore(); return
        ind = int(self.dragPoint.data()[0])
        pos = self.data['pos']
        newpos = ev.pos() + self.dragOffset
        y = float(min(1.0, max(0.0, newpos[1])))
        n = len(pos)
        if ind == 0:
            x = 0.0
        elif ind == n - 1:
            x = self.tmax
        else:
            lo = pos[ind - 1, 0] + 1e-4
            hi = pos[ind + 1, 0] - 1e-4
            x = float(min(hi, max(lo, newpos[0])))
        pos[ind] = [x, y]
        pg.GraphItem.setData(self, **self.data)
        ev.accept()
        if self.changed_cb:
            self.changed_cb()


# --------------------------------------------------------------- waveform editor
class WaveformEditor(QtWidgets.QWidget):
    """Waveform + draggable boundaries + duration-aligned editable phoneme fields."""
    audioChanged = QtCore.pyqtSignal()

    def __init__(self, stretch_hook=None, parent=None):
        super().__init__(parent)
        self.sr = 16000
        self.base_audio = []     # per-segment ORIGINAL audio (stretch from these)
        self.base_durs = []      # per-segment ORIGINAL durations
        self.segments = []       # current fc.Segment list (targets)
        self.audio = np.zeros(1, np.float32)
        self.boundaries = []     # pg.InfiniteLine (internal)
        self.fields = []         # QLineEdit per segment
        self.stretch_hook = stretch_hook

        lay = QtWidgets.QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0)
        self.plot = pg.PlotWidget(background='#B8B8B8')
        self.plot.hideAxis('left'); self.plot.hideAxis('bottom')
        self.plot.setMenuEnabled(False)
        self.plot.setMouseEnabled(x=False, y=False)
        self.plot.getPlotItem().setContentsMargins(0, 0, 0, 0)
        self.plot.setMinimumHeight(230)
        self.curve = self.plot.plot([], [], pen=pg.mkPen('#1010C0', width=1))
        lay.addWidget(self.plot, 1)

        self.fields_host = QtWidgets.QWidget()
        self.fields_lay = QtWidgets.QHBoxLayout(self.fields_host)
        self.fields_lay.setContentsMargins(0, 3, 0, 0); self.fields_lay.setSpacing(2)
        self.fields_host.setFixedHeight(30)
        lay.addWidget(self.fields_host)

    # -- data in -------------------------------------------------------------
    def set_synthesis(self, syn: fc.Synthesis):
        self.sr = syn.sr
        self.segments = copy.deepcopy(syn.segments)
        self.audio = np.asarray(syn.samples, np.float32)
        self.base_audio, self.base_durs = [], []
        for s in self.segments:
            a = int(round(s.start * self.sr)); b = int(round(s.end * self.sr))
            a = max(0, min(a, len(self.audio))); b = max(a, min(b, len(self.audio)))
            self.base_audio.append(self.audio[a:b].copy())
            self.base_durs.append(max(s.dur, 1e-4))
        self._rebuild_boundaries()
        self._rebuild_fields()
        self._redraw()

    def duration(self):
        return len(self.audio) / float(self.sr) if self.sr else 0.0

    # -- boundaries ----------------------------------------------------------
    def _rebuild_boundaries(self):
        for ln in self.boundaries:
            self.plot.removeItem(ln)
        self.boundaries = []
        pen = pg.mkPen('#D00000', width=1, style=Qt.DashLine)
        hoverpen = pg.mkPen('#FF3030', width=2, style=Qt.DashLine)
        for i in range(len(self.segments) - 1):
            x = self.segments[i].end
            ln = pg.InfiniteLine(pos=x, angle=90, movable=True, pen=pen, hoverPen=hoverpen)
            ln.seg_index = i
            ln.sigDragged.connect(self._on_drag)
            ln.sigPositionChangeFinished.connect(self._on_drag_finish)
            self.plot.addItem(ln)
            self.boundaries.append(ln)

    def _on_drag(self, line):
        i = line.seg_index
        left = self.segments[i].start
        right = self.segments[i + 1].end
        x = float(min(right - MIN_SEG, max(left + MIN_SEG, line.value())))
        if x != line.value():
            line.setValue(x)
        self.segments[i].end = x
        self.segments[i + 1].start = x

    def _on_drag_finish(self, line):
        self._on_drag(line)
        self._rebuild_audio()
        self._redraw()
        self.audioChanged.emit()

    # -- audio rebuild via time-stretch -------------------------------------
    def _rebuild_audio(self):
        chunks = []
        t = 0.0
        for i, seg in enumerate(self.segments):
            factor = max(seg.dur, 1e-4) / max(self.base_durs[i], 1e-4)
            y = fc.time_stretch(self.base_audio[i], self.sr, factor, hook=self.stretch_hook)
            n = max(1, int(round(seg.dur * self.sr)))
            if len(y) < n:
                y = np.pad(y, (0, n - len(y)))
            else:
                y = y[:n]
            chunks.append(y.astype(np.float32))
            seg.start = t; seg.end = t + len(y) / self.sr; t = seg.end
        self.audio = np.concatenate(chunks) if chunks else np.zeros(1, np.float32)

    # -- phoneme fields (duration-proportional => aligned with the waveform) -
    def _rebuild_fields(self):
        while self.fields_lay.count():
            w = self.fields_lay.takeAt(0).widget()
            if w:
                w.deleteLater()
        self.fields = []
        for i, seg in enumerate(self.segments):
            e = QtWidgets.QLineEdit(seg.phone)
            e.setObjectName("phon")
            e.setAlignment(Qt.AlignCenter)
            e.seg_index = i
            e.textEdited.connect(lambda txt, idx=i: self._on_phone_edit(idx, txt))
            self.fields_lay.addWidget(e, max(1, int(seg.dur * 1000)))
            self.fields.append(e)

    def _relayout_fields(self):
        for i, seg in enumerate(self.segments):
            if i < len(self.fields):
                self.fields_lay.setStretch(i, max(1, int(seg.dur * 1000)))

    def _on_phone_edit(self, idx, txt):
        if 0 <= idx < len(self.segments):
            self.segments[idx].phone = txt

    # -- draw ---------------------------------------------------------------
    def _redraw(self):
        n = len(self.audio)
        x = np.arange(n) / float(self.sr) if self.sr else np.arange(n)
        self.curve.setData(x, self.audio)
        dur = self.duration() or 1.0
        self.plot.setXRange(0, dur, padding=0)
        self.plot.setYRange(-1.05, 1.05, padding=0)
        for i, ln in enumerate(self.boundaries):
            ln.setValue(self.segments[i].end)
        self._relayout_fields()

    def get_audio(self):
        return self.audio, self.sr


# --------------------------------------------------------------------- main win
class MainWindow(QtWidgets.QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.backend = fc.FestivalBackend(cfg)
        self.player = Player()
        self.current = None
        self.setWindowTitle("Festvox Speech Synthesis GUI v1.0")
        self.resize(1024, 640)
        self._build_menu()
        self._build_body()
        self.statusBar().showMessage("Status: Ready")

    # -- menu ---------------------------------------------------------------
    def _build_menu(self):
        mb = self.menuBar()
        m_file = mb.addMenu("&File")
        m_file.addAction("Open Project...", self.on_open_project)
        m_file.addAction("Save Project...", self.on_save_project)
        m_file.addAction("Export Audio (WAV)...", self.on_export)
        m_file.addSeparator()
        m_file.addAction("Exit", self.close)
        mb.addMenu("&Edit")
        m_gen = mb.addMenu("&Generate")
        m_gen.addAction("Generate Audio", self.on_generate)
        m_vb = mb.addMenu("&Voicebank")
        m_vb.addAction("Scan installed voices (Festival)", self.on_scan_voices)
        m_vb.addAction("Add voice folder...", self.on_add_voice_folder)
        m_vb.addAction("Set Festival binary...", self.on_set_festival_bin)
        mb.addMenu("&Options")
        m_help = mb.addMenu("&Help")
        m_help.addAction("About", lambda: QtWidgets.QMessageBox.information(
            self, "About", "Festvox Speech Synthesis GUI v1.0\nPyQt5 + PyQtGraph front-end "
            "for a Festival/Festvox backend."))

    # -- body ---------------------------------------------------------------
    def _build_body(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        root = QtWidgets.QHBoxLayout(central)
        root.setContentsMargins(8, 8, 8, 8); root.setSpacing(10)

        # ---- left panel
        left = QtWidgets.QVBoxLayout(); left.setSpacing(6)
        lbl = QtWidgets.QLabel("Language:"); lbl.setObjectName("hdr")
        left.addWidget(lbl)
        self.lang = QtWidgets.QComboBox(); self.lang.addItems(self.cfg["languages"])
        left.addWidget(self.lang)

        vlbl = QtWidgets.QLabel("Voicebank Database:"); vlbl.setObjectName("hdr")
        left.addWidget(vlbl)
        self.voicebank = QtWidgets.QListWidget()
        self.voicebank.addItems(self.cfg["voicebanks"])
        self.voicebank.setCurrentRow(0)
        self.voicebank.setFixedHeight(76)
        left.addWidget(self.voicebank)

        slbl = QtWidgets.QLabel("Output Speed:"); slbl.setObjectName("hdr")
        left.addWidget(slbl)
        self.speed = QtWidgets.QSlider(Qt.Horizontal)
        self.speed.setMinimum(-150); self.speed.setMaximum(100); self.speed.setValue(0)
        self.speed.valueChanged.connect(self._speed_label)
        left.addWidget(self.speed)
        row = QtWidgets.QHBoxLayout()
        for t in ("-1.5", "0", "1.0"):
            q = QtWidgets.QLabel(t); q.setStyleSheet("color:#555")
            row.addWidget(q)
            if t != "1.0":
                row.addStretch(1)
        left.addLayout(row)
        self.speed_val = QtWidgets.QLabel("speed x1.00"); self.speed_val.setStyleSheet("color:#555")
        left.addWidget(self.speed_val)

        left.addSpacing(8)
        self.btn_gen = self._toolbtn("Generate Audio", "SP_MediaVolume", self.on_generate)
        self.btn_play = self._toolbtn("Play", "SP_MediaPlay", self.on_play)
        self.btn_stop = self._toolbtn("Stop", "SP_MediaStop", self.on_stop)
        self.btn_copy = self._toolbtn("Copy", "SP_FileDialogDetailedView", None); self.btn_copy.setEnabled(False)
        self.btn_save = self._toolbtn("Save Project", "SP_DialogSaveButton", self.on_save_project)
        self.btn_export = self._toolbtn("Export Audio (WAV)", "SP_DriveHDIcon", self.on_export)
        for b in (self.btn_gen, self.btn_play, self.btn_stop, self.btn_copy, self.btn_save, self.btn_export):
            left.addWidget(b)
        left.addStretch(1)

        leftw = QtWidgets.QWidget(); leftw.setLayout(left); leftw.setFixedWidth(190)
        root.addWidget(leftw)

        # ---- right side
        right = QtWidgets.QVBoxLayout(); right.setSpacing(6)
        trow = QtWidgets.QHBoxLayout()
        trow.addWidget(QtWidgets.QLabel("Text:"))
        self.text = QtWidgets.QLineEdit(self.cfg.get("default_text", "Hello, world."))
        self.text.returnPressed.connect(self.on_generate)
        trow.addWidget(self.text, 1)
        right.addLayout(trow)

        wf_group = QtWidgets.QGroupBox("Waveform  /  Phonemes")
        wf_lay = QtWidgets.QVBoxLayout(wf_group); wf_lay.setContentsMargins(6, 4, 6, 6)
        self.waveform = WaveformEditor()
        self.waveform.audioChanged.connect(self._on_audio_changed)
        wf_lay.addWidget(self.waveform)
        right.addWidget(wf_group, 3)

        env_group = QtWidgets.QGroupBox("Phoneme Velocity  (double-click track to add a node)")
        env_lay = QtWidgets.QVBoxLayout(env_group); env_lay.setContentsMargins(6, 4, 6, 6)
        self.env_plot = pg.PlotWidget(background='#DCDCDC')
        self.env_plot.setMenuEnabled(False)
        self.env_plot.hideAxis('bottom')
        self.env_plot.getAxis('left').setWidth(24)
        self.env_plot.setMouseEnabled(x=False, y=False)
        self.env_plot.setYRange(0, 1, padding=0.02)
        self.env_plot.setMinimumHeight(120)
        self.env = EnvelopeGraph(changed_cb=None)
        self.env_plot.addItem(self.env)
        self.env.set_nodes([0.0, 1.0], [0.5, 0.5], tmax=1.0)
        self.env_plot.scene().sigMouseClicked.connect(self._env_click)
        env_lay.addWidget(self.env_plot)
        right.addWidget(env_group, 1)

        root.addLayout(right, 1)

    def _toolbtn(self, text, icon_name, slot):
        b = QtWidgets.QPushButton("  " + text)
        try:
            b.setIcon(self.style().standardIcon(getattr(QtWidgets.QStyle, icon_name)))
        except Exception:
            pass
        b.setStyleSheet("text-align:left;")
        if slot:
            b.clicked.connect(slot)
        return b

    # -- helpers ------------------------------------------------------------
    def _speed_factor(self):
        return float(2.0 ** (self.speed.value() / 100.0))

    def _speed_label(self):
        self.speed_val.setText("speed x%.2f" % self._speed_factor())

    def _select_voicebank(self, v):
        items = self.cfg["voicebanks"]
        if v in items:
            self.voicebank.setCurrentRow(items.index(v))

    def _refresh_voicebanks(self):
        cur = self._current_voicebank()
        self.voicebank.clear()
        self.voicebank.addItems(self.cfg["voicebanks"])
        self._select_voicebank(cur if cur in self.cfg["voicebanks"] else self.cfg["voicebanks"][0])

    def _persist_config(self):
        try:
            fc.save_config(self.cfg, os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json"))
        except Exception as e:
            self.statusBar().showMessage("Status: could not save config.json (%s)" % e)

    def on_scan_voices(self):
        if not self.backend.available():
            QtWidgets.QMessageBox.information(
                self, "Festival not found",
                "The 'festival' binary is not on PATH.\n"
                "Use Voicebank -> Set Festival binary... first.")
            return
        self.statusBar().showMessage("Status: querying Festival for voices...")
        QtWidgets.QApplication.processEvents()
        voices = self.backend.list_installed_voices()
        if not voices:
            QtWidgets.QMessageBox.information(self, "Voicebank", "Festival reported no voices.")
            return
        added = 0
        for v in voices:
            if v not in self.cfg["voicebanks"]:
                self.cfg["voicebanks"].append(v)
                self.cfg["festival"]["voice_map"][v] = self.backend._guess_voice_fn(v)
                added += 1
        self._refresh_voicebanks()
        self._persist_config()
        self.statusBar().showMessage(
            "Status: %d installed voices (%d new) -- saved to config.json" % (len(voices), added))

    def on_add_voice_folder(self):
        d = QtWidgets.QFileDialog.getExistingDirectory(self, "Select a festvox / Multisyn voice folder")
        if not d:
            return
        info = self.backend.scan_voice_dir(d)
        name = info["name"]
        self.cfg["festival"]["voice_map"][name] = {
            "dir": info["dir"], "voice": info["voice"], "scm": info["scm"]}
        if name not in self.cfg["voicebanks"]:
            self.cfg["voicebanks"].append(name)
        self._refresh_voicebanks()
        self._select_voicebank(name)
        self._persist_config()
        note = "" if info["scm"] else "  (no .scm auto-detected -- edit config.json if it will not load)"
        self.statusBar().showMessage("Status: added '%s' -> %s%s" % (name, info["voice"], note))

    def on_set_festival_bin(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Locate the festival binary")
        if not path:
            return
        self.cfg["festival"]["bin"] = path
        self.backend.bin = path
        self._persist_config()
        ok = self.backend.available()
        self.statusBar().showMessage(
            "Status: festival = %s  (%s)" % (path, "found" if ok else "NOT executable"))

    def _current_voicebank(self):
        it = self.voicebank.currentItem()
        return it.text() if it else self.cfg["voicebanks"][0]

    def _env_click(self, ev):
        if ev.double():
            vb = self.env_plot.getPlotItem().getViewBox()
            p = vb.mapSceneToView(ev.scenePos())
            dur = self.waveform.duration() or 1.0
            t = float(min(dur, max(0.0, p.x())))
            v = float(min(1.0, max(0.0, p.y())))
            self.env.add_node(t, v)

    # -- actions ------------------------------------------------------------
    def on_generate(self):
        text = self.text.text().strip()
        if not text:
            self.statusBar().showMessage("Status: enter some text to synthesize.")
            return
        self.statusBar().showMessage("Status: synthesizing...")
        QtWidgets.QApplication.processEvents()
        try:
            syn = self.backend.synth(text, self._current_voicebank(), self._speed_factor())
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Synthesis error", str(e))
            self.statusBar().showMessage("Status: Ready")
            return
        self.current = syn
        self.waveform.set_synthesis(syn)
        dur = self.waveform.duration() or 1.0
        self.env.set_nodes([0.0, dur], [0.6, 0.6], tmax=dur)
        self.env_plot.setXRange(0, dur, padding=0)
        msg = syn.warning or ("Status: Ready -- %d phonemes, %.2fs" % (len(syn.segments), dur))
        self.statusBar().showMessage("Status: " + msg if not msg.startswith("Status") else msg)

    def _on_audio_changed(self):
        dur = self.waveform.duration() or 1.0
        self.env.tmax = dur
        self.env_plot.setXRange(0, dur, padding=0)
        self.statusBar().showMessage("Status: segment re-timed -- %.2fs total" % dur)

    def on_play(self):
        samples, sr = self.waveform.get_audio()
        try:
            self.player.play(samples, sr)
            self.statusBar().showMessage("Status: playing...")
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Playback", str(e))

    def on_stop(self):
        try:
            self.player.stop()
        except Exception:
            pass
        self.statusBar().showMessage("Status: stopped")

    def on_export(self):
        if self.waveform.get_audio()[0].size <= 1:
            QtWidgets.QMessageBox.information(self, "Export", "Generate audio first.")
            return
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Export WAV", "output.wav", "WAV (*.wav)")
        if not path:
            return
        try:
            s, sr = self.waveform.get_audio()
            fc.write_wav(path, s, sr)
            self.statusBar().showMessage("Status: exported " + os.path.basename(path))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export error", str(e))

    def on_save_project(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save Project", "project.json", "JSON (*.json)")
        if not path:
            return
        try:
            fc.save_project(path, text=self.text.text(), language=self.lang.currentText(),
                            voicebank=self._current_voicebank(), speed=self._speed_factor(),
                            segments=self.waveform.segments, velocity=self.env.nodes())
            self.statusBar().showMessage("Status: saved " + os.path.basename(path))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Save error", str(e))

    def on_open_project(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open Project", "", "JSON (*.json)")
        if not path:
            return
        try:
            d = fc.load_project(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Open error", str(e))
            return
        self.text.setText(d.get("text", ""))
        if d.get("language") in self.cfg["languages"]:
            self.lang.setCurrentText(d["language"])
        self._select_voicebank(d.get("voicebank", ""))
        try:
            self.speed.setValue(int(round(100 * np.log2(max(1e-3, d.get("speed", 1.0))))))
        except Exception:
            pass
        self.on_generate()
        vel = d.get("velocity")
        if vel:
            ts = [p[0] for p in vel]; vs = [p[1] for p in vel]
            self.env.set_nodes(ts, vs, tmax=self.waveform.duration() or 1.0)
        self.statusBar().showMessage("Status: opened " + os.path.basename(path))


def main():
    cfg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
    try:
        cfg = fc.load_config(cfg_path)
    except Exception as e:
        cfg = fc.load_config("nonexistent")  # defaults
        sys.stderr.write("config.json problem, using defaults: %s\n" % e)
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(XP_QSS)
    win = MainWindow(cfg)
    win.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
