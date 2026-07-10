"""festvox_gui.py -- Windows-XP styled desktop GUI for the synth_diphone
concatenative diphone engine (99_Tools/vocab_forge/synth_diphone.py).

PyQt5 + PyQtGraph. What it really does:
  * Languages = the engine's real front ends: Asaxi / English (CMU) / Japanese
  * Voicebanks = the diphone DBs from festvox.json (+ any folder you add)
  * Generate renders with synth_diphone.render() -- no Festival binary,
    pure Python, works on Windows out of the box
  * waveform view with draggable red phoneme boundaries (time-stretch DSP)
  * editable phoneme fields under the waveform; Re-render feeds your edited
    phone list straight back through the engine (e.g. override r -> rr)
  * Vocaloid-style Velocity envelope, applied as a gain curve on play/export
  * Play (sounddevice / winsound / Qt), Save+Open project, Export WAV

Run:  python festvox_gui.py
Deps: pip install PyQt5 pyqtgraph numpy   (optional: sounddevice, librosa,
      cmudict for English)
"""
from __future__ import annotations
import copy
import os
import sys

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
CONFIG_PATH = os.path.join(fc.GUI_DIR, "config.json")

# --------------------------------------------------------------- XP Luna theme
XP_QSS = """
* { font-family: Tahoma, 'Segoe UI', sans-serif; font-size: 11px; color: #000; }
QMainWindow, QWidget { background: #ECE9D8; }
QMenuBar { background: #ECE9D8; }
QMenuBar::item:selected { background: #316AC5; color: #fff; }
QMenu { background: #fff; border: 1px solid #808080; }
QMenu::item:selected { background: #316AC5; color: #fff; }
QMenu::item:disabled { color: #A0A0A0; }
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
QComboBox, QLineEdit, QListWidget, QSpinBox, QDoubleSpinBox {
    background: #fff; border: 1px solid #7F9DB9; padding: 2px; selection-background-color: #316AC5;
}
QComboBox::drop-down { border-left: 1px solid #7F9DB9; width: 16px; }
QListWidget::item:selected { background: #316AC5; color: #fff; }
QSlider::groove:horizontal { height: 4px; background: #B4B0A4; border: 1px solid #808080; }
QSlider::handle:horizontal { width: 11px; background: #ECE9D8; border: 1px solid #404040;
    margin: -6px 0; border-radius: 2px; }
QStatusBar { background: #ECE9D8; border-top: 1px solid #ACA899; }
QLineEdit#phon { background: #fff; border: 1px solid #7F9DB9; padding: 1px; }
QLineEdit#phon[dirty="true"] { background: #FFF3C2; }
QLineEdit#phon:read-only { background: #E4E2D6; color: #707070; }
"""


# ------------------------------------------------------------------- audio play
class Player:
    """sounddevice if installed; else winsound (Windows stdlib -- always
    available on the target machine); else Qt Multimedia; else clear error."""
    def __init__(self):
        self.mode = None
        self._sd = None
        self._qmp = None
        self._tmp = None
        try:
            import sounddevice as sd
            self._sd = sd
            self.mode = "sd"
            return
        except Exception:
            pass
        if sys.platform == "win32":
            try:
                import winsound  # noqa: F401
                self.mode = "winsound"
                return
            except Exception:
                pass
        try:
            from PyQt5.QtMultimedia import QMediaPlayer
            self._qmp = QMediaPlayer()
            self.mode = "qt"
        except Exception:
            self.mode = None

    def play(self, samples, sr):
        samples = np.asarray(samples, dtype=np.float32)
        if samples.size <= 1:
            raise RuntimeError("Nothing to play -- generate audio first.")
        if self.mode == "sd":
            self._sd.stop()
            self._sd.play(samples, int(sr))
        elif self.mode == "winsound":
            import tempfile, winsound
            self._tmp = os.path.join(tempfile.gettempdir(), "festvox_gui_play.wav")
            fc.write_wav(self._tmp, samples, sr)
            winsound.PlaySound(self._tmp,
                               winsound.SND_FILENAME | winsound.SND_ASYNC)
        elif self.mode == "qt":
            from PyQt5.QtMultimedia import QMediaContent
            import tempfile
            self._tmp = tempfile.mktemp(suffix=".wav")
            fc.write_wav(self._tmp, samples, sr)
            self._qmp.setMedia(QMediaContent(QtCore.QUrl.fromLocalFile(self._tmp)))
            self._qmp.play()
        else:
            raise RuntimeError("No audio backend. Install sounddevice:  "
                               "pip install sounddevice")

    def stop(self):
        if self.mode == "sd":
            self._sd.stop()
        elif self.mode == "winsound":
            import winsound
            winsound.PlaySound(None, winsound.SND_PURGE)
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
        return [] if p is None else [(float(p[i, 0]), float(p[i, 1]))
                                     for i in range(len(p))]

    def set_tmax(self, tmax):
        """Rescale node times proportionally onto a new total duration."""
        old = self.tmax or 1.0
        tmax = max(1e-6, float(tmax))
        pts = self.nodes()
        if pts and abs(old - tmax) > 1e-9:
            self.set_nodes([t / old * tmax for t, _ in pts],
                           [v for _, v in pts], tmax=tmax)
        else:
            self.tmax = tmax

    def add_node(self, t, v):
        p = self.data['pos']
        ts = list(p[:, 0]) + [float(t)]
        vs = list(p[:, 1]) + [float(v)]
        order = np.argsort(ts)
        self.set_nodes(np.array(ts)[order], np.array(vs)[order])
        if self.changed_cb:
            self.changed_cb()

    def remove_node_near(self, t, v):
        pts = self.nodes()
        if len(pts) <= 2:
            return False
        d = [abs(p[0] - t) / (self.tmax or 1.0) + abs(p[1] - v) for p in pts]
        i = int(np.argmin(d))
        if i in (0, len(pts) - 1) or d[i] > 0.08:
            return False
        del pts[i]
        self.set_nodes([p[0] for p in pts], [p[1] for p in pts])
        if self.changed_cb:
            self.changed_cb()
        return True

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
    """Waveform + draggable boundaries + duration-aligned editable phoneme
    fields. Boundary drags time-stretch that segment (post-DSP); phoneme text
    edits are collected by the main window's Re-render action."""
    audioChanged = QtCore.pyqtSignal()
    phonesEdited = QtCore.pyqtSignal()
    rerenderRequested = QtCore.pyqtSignal()

    def __init__(self, stretch_hook=None, parent=None):
        super().__init__(parent)
        self.sr = 16000
        self.base_audio = []     # per-segment ORIGINAL audio (stretch source)
        self.base_durs = []      # per-segment ORIGINAL durations
        self.segments = []       # current fc.Segment list
        self.audio = np.zeros(1, np.float32)
        self.boundaries = []     # pg.InfiniteLine
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

    def phone_list(self):
        """Current phoneme labels, in order, as typed (fields may hold several
        space-separated phones, or be emptied to delete a phone)."""
        out = []
        for seg in self.segments:
            out.extend(p for p in seg.phone.replace(",", " ").split() if p)
        return out

    # -- boundaries ----------------------------------------------------------
    def _rebuild_boundaries(self):
        for ln in self.boundaries:
            self.plot.removeItem(ln)
        self.boundaries = []
        pen = pg.mkPen('#D00000', width=1, style=Qt.DashLine)
        hoverpen = pg.mkPen('#FF3030', width=2, style=Qt.DashLine)
        for i in range(len(self.segments) - 1):
            x = self.segments[i].end
            ln = pg.InfiniteLine(pos=x, angle=90, movable=True, pen=pen,
                                 hoverPen=hoverpen)
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

    # -- audio rebuild via time-stretch --------------------------------------
    def _rebuild_audio(self):
        chunks = []
        t = 0.0
        for i, seg in enumerate(self.segments):
            factor = max(seg.dur, 1e-4) / max(self.base_durs[i], 1e-4)
            y = fc.time_stretch(self.base_audio[i], self.sr, factor,
                                hook=self.stretch_hook)
            n = max(1, int(round(seg.dur * self.sr)))
            if len(y) < n:
                y = np.pad(y, (0, n - len(y)))
            else:
                y = y[:n]
            chunks.append(y.astype(np.float32))
            seg.start = t; seg.end = t + len(y) / self.sr; t = seg.end
        self.audio = np.concatenate(chunks) if chunks else np.zeros(1, np.float32)

    # -- phoneme fields (duration-proportional => aligned with the waveform) --
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
            if seg.phone == "pau":
                e.setReadOnly(True)
                e.setToolTip("edge silence (added by the engine)")
            else:
                e.setToolTip("type a phone from the bank (e.g. r -> rr), "
                             "space-separate to insert, clear to delete;\n"
                             "Enter or the Re-render button applies it")
                e.textEdited.connect(lambda txt, idx=i: self._on_phone_edit(idx, txt))
                e.returnPressed.connect(self.rerenderRequested.emit)
            self.fields_lay.addWidget(e, max(1, int(seg.dur * 1000)))
            self.fields.append(e)

    def _relayout_fields(self):
        for i, seg in enumerate(self.segments):
            if i < len(self.fields):
                self.fields_lay.setStretch(i, max(1, int(seg.dur * 1000)))

    def _on_phone_edit(self, idx, txt):
        if 0 <= idx < len(self.segments):
            self.segments[idx].phone = txt
            w = self.fields[idx]
            w.setProperty("dirty", True)
            w.style().unpolish(w); w.style().polish(w)
            self.phonesEdited.emit()

    # -- draw -----------------------------------------------------------------
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
        self.player = Player()
        self.current = None            # fc.Synthesis of the last render
        self.backend = None
        self.backend_err = None
        self.setWindowTitle("Festvox Speech Synthesis GUI v2.0 -- synth_diphone")
        self.resize(1024, 660)
        self._init_backend()
        self._build_menu()
        self._build_body()
        self._populate_from_backend()
        self.statusBar().showMessage("Status: " + (
            "Ready" if self.backend else
            "backend not loaded -- " + str(self.backend_err)))

    # -- backend ---------------------------------------------------------------
    def _init_backend(self):
        try:
            self.backend = fc.DiphoneBackend(self.cfg)
            self.backend_err = None
        except fc.BackendError as e:
            self.backend = None
            self.backend_err = e

    def _need_backend(self) -> bool:
        if self.backend:
            return True
        QtWidgets.QMessageBox.critical(
            self, "Engine not loaded",
            str(self.backend_err or "synth_diphone.py is not loaded.") +
            "\n\nUse Options > Locate synth_diphone.py...")
        return False

    # -- menu -------------------------------------------------------------------
    def _build_menu(self):
        mb = self.menuBar()
        m_file = mb.addMenu("&File")
        m_file.addAction("Open Project...", self.on_open_project)
        m_file.addAction("Save Project...", self.on_save_project)
        m_file.addAction("Export Audio (WAV)...", self.on_export)
        m_file.addSeparator()
        m_file.addAction("Exit", self.close)

        m_gen = mb.addMenu("&Generate")
        m_gen.addAction("Generate Audio", self.on_generate)
        m_gen.addAction("Re-render edited phonemes", self.on_rerender)
        m_gen.addSeparator()
        m_gen.addAction("Last render details...", self.on_render_details)

        m_vb = mb.addMenu("&Voicebank")
        m_vb.addAction("Add voicebank folder...", self.on_add_voice_folder)
        m_vb.addAction("Set festvox.json...", self.on_set_festvox_config)
        m_vb.addAction("Reload voicebanks", self.on_reload_voicebanks)

        m_opt = mb.addMenu("&Options")
        m_opt.addAction("Locate synth_diphone.py...", self.on_locate_engine)
        m_opt.addAction("Advanced synthesis settings...", self.on_advanced)
        self.act_velocity = m_opt.addAction("Apply velocity on play/export")
        self.act_velocity.setCheckable(True)
        self.act_velocity.setChecked(bool(self.cfg.get("apply_velocity", True)))
        self.act_velocity.toggled.connect(self._on_velocity_toggled)

        m_help = mb.addMenu("&Help")
        m_help.addAction("About", lambda: QtWidgets.QMessageBox.information(
            self, "About",
            "Festvox Speech Synthesis GUI v2.0\n\n"
            "PyQt5 + PyQtGraph front-end for synth_diphone.py --\n"
            "pure-Python concatenative diphone synthesis over the\n"
            "FestVox-style DBs built by utau2festvox.py.\n"
            "No Festival runtime required."))

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
        self.lang = QtWidgets.QComboBox()
        left.addWidget(self.lang)

        vlbl = QtWidgets.QLabel("Voicebank Database:"); vlbl.setObjectName("hdr")
        left.addWidget(vlbl)
        self.voicebank = QtWidgets.QListWidget()
        self.voicebank.setFixedHeight(76)
        left.addWidget(self.voicebank)

        slbl = QtWidgets.QLabel("Output Speed:"); slbl.setObjectName("hdr")
        left.addWidget(slbl)
        self.speed = QtWidgets.QSlider(Qt.Horizontal)
        # 2**(v/100): -200 -> x0.25 (engine minimum), +200 -> x4 (maximum)
        self.speed.setMinimum(-200); self.speed.setMaximum(200); self.speed.setValue(0)
        self.speed.valueChanged.connect(self._speed_label)
        left.addWidget(self.speed)
        row = QtWidgets.QHBoxLayout()
        for t in ("x0.25", "x1", "x4"):
            q = QtWidgets.QLabel(t); q.setStyleSheet("color:#555")
            row.addWidget(q)
            if t != "x4":
                row.addStretch(1)
        left.addLayout(row)
        self.speed_val = QtWidgets.QLabel("speed x1.00")
        self.speed_val.setStyleSheet("color:#555")
        left.addWidget(self.speed_val)

        left.addSpacing(8)
        self.btn_gen = self._toolbtn("Generate Audio", "SP_MediaVolume", self.on_generate)
        self.btn_play = self._toolbtn("Play", "SP_MediaPlay", self.on_play)
        self.btn_stop = self._toolbtn("Stop", "SP_MediaStop", self.on_stop)
        self.btn_rerender = self._toolbtn("Re-render Phonemes", "SP_BrowserReload", self.on_rerender)
        self.btn_rerender.setEnabled(False)
        self.btn_save = self._toolbtn("Save Project", "SP_DialogSaveButton", self.on_save_project)
        self.btn_export = self._toolbtn("Export Audio (WAV)", "SP_DriveHDIcon", self.on_export)
        for b in (self.btn_gen, self.btn_play, self.btn_stop, self.btn_rerender,
                  self.btn_save, self.btn_export):
            left.addWidget(b)
        left.addStretch(1)

        leftw = QtWidgets.QWidget(); leftw.setLayout(left); leftw.setFixedWidth(190)
        root.addWidget(leftw)

        # ---- right side
        right = QtWidgets.QVBoxLayout(); right.setSpacing(6)
        trow = QtWidgets.QHBoxLayout()
        trow.addWidget(QtWidgets.QLabel("Text:"))
        self.text = QtWidgets.QLineEdit(self.cfg.get("default_text", ""))
        self.text.returnPressed.connect(self.on_generate)
        trow.addWidget(self.text, 1)
        right.addLayout(trow)

        wf_group = QtWidgets.QGroupBox("Waveform  /  Phonemes")
        wf_lay = QtWidgets.QVBoxLayout(wf_group); wf_lay.setContentsMargins(6, 4, 6, 6)
        self.waveform = WaveformEditor()
        self.waveform.audioChanged.connect(self._on_audio_changed)
        self.waveform.phonesEdited.connect(
            lambda: self.btn_rerender.setEnabled(True))
        self.waveform.rerenderRequested.connect(self.on_rerender)
        wf_lay.addWidget(self.waveform)
        right.addWidget(wf_group, 3)

        env_group = QtWidgets.QGroupBox(
            "Phoneme Velocity -- gain envelope  (double-click: add node, "
            "right-click: remove;  0.5 = unity)")
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

    # -- populate from config/backend -----------------------------------------
    def _populate_from_backend(self):
        langs = self.cfg.get("languages") or {"Asaxi": "asaxi"}
        self.lang.clear()
        for label in langs:
            self.lang.addItem(label)
        want = self.cfg.get("default_language")
        if self.backend and not want:
            code = self.backend.default_lang_code()
            want = next((L for L, c in langs.items() if c == code), None)
        if want and self.lang.findText(want) >= 0:
            self.lang.setCurrentText(want)

        self._refresh_voicebanks()

        spd = self.backend.default_speed() if self.backend else \
            float(self.cfg.get("synth_speed", 1.0) or 1.0)
        try:
            self.speed.setValue(int(round(100 * np.log2(max(0.25, min(4.0, spd))))))
        except Exception:
            self.speed.setValue(0)
        self._speed_label()

    def _refresh_voicebanks(self, keep=None):
        keep = keep or self._current_voicebank()
        self.voicebank.clear()
        vbs = self.backend.voicebanks() if self.backend else []
        if not vbs:
            it = QtWidgets.QListWidgetItem("(no voicebanks)")
            it.setFlags(Qt.NoItemFlags)
            it.setToolTip("No voices in festvox.json and none added.\n"
                          "Voicebank > Add voicebank folder...")
            self.voicebank.addItem(it)
            return
        default = self.backend.default_voicebank()
        for v in vbs:
            it = QtWidgets.QListWidgetItem(
                ("%s" if v["ok"] else "%s  (missing)") % v["name"])
            it.setData(Qt.UserRole, v["name"])
            tip = "%s\nfrom %s" % (v["dir"] or "(no path)", v["source"])
            if not v["ok"]:
                it.setForeground(QtGui.QBrush(QtGui.QColor("#A00000")))
                tip += "\nNOT FOUND: needs dic/diphone_index.json"
            it.setToolTip(tip)
            self.voicebank.addItem(it)
            if v["name"] == (keep or default):
                self.voicebank.setCurrentItem(it)
        if self.voicebank.currentRow() < 0:
            self.voicebank.setCurrentRow(0)

    def _current_voicebank(self):
        it = self.voicebank.currentItem() if hasattr(self, "voicebank") else None
        return it.data(Qt.UserRole) if it and it.data(Qt.UserRole) else None

    def _current_lang_code(self):
        langs = self.cfg.get("languages") or {}
        return langs.get(self.lang.currentText(), "asaxi")

    # -- helpers ------------------------------------------------------------
    def _speed_factor(self):
        return float(2.0 ** (self.speed.value() / 100.0))

    def _speed_label(self):
        self.speed_val.setText("speed x%.2f" % self._speed_factor())

    def _persist_config(self):
        self.cfg["default_language"] = self.lang.currentText()
        self.cfg["default_text"] = self.text.text()
        self.cfg["synth_speed"] = round(self._speed_factor(), 3)
        self.cfg["apply_velocity"] = bool(self.act_velocity.isChecked())
        try:
            fc.save_config(self.cfg, CONFIG_PATH)
        except Exception as e:
            self.statusBar().showMessage(
                "Status: could not save config.json (%s)" % e)

    def closeEvent(self, ev):
        self._persist_config()
        super().closeEvent(ev)

    def _env_click(self, ev):
        vb = self.env_plot.getPlotItem().getViewBox()
        p = vb.mapSceneToView(ev.scenePos())
        dur = self.waveform.duration() or 1.0
        t = float(min(dur, max(0.0, p.x())))
        v = float(min(1.0, max(0.0, p.y())))
        if ev.double():
            self.env.add_node(t, v)
        elif ev.button() == Qt.RightButton:
            self.env.remove_node_near(t, v)

    def _output_audio(self):
        """Editor audio with the velocity envelope applied (if enabled)."""
        samples, sr = self.waveform.get_audio()
        if self.act_velocity.isChecked() and samples.size > 1:
            samples = fc.apply_velocity(
                samples, sr, self.env.nodes(),
                depth=float(self.cfg.get("velocity_depth", 1.0)))
        return samples, sr

    def _show_synthesis(self, syn: fc.Synthesis):
        self.current = syn
        self.waveform.set_synthesis(syn)
        dur = self.waveform.duration() or 1.0
        self.env.set_tmax(dur)
        self.env_plot.setXRange(0, dur, padding=0)
        self.btn_rerender.setEnabled(False)
        n_ph = len(syn.phones)
        msg = ("Ready -- %d phones, %d diphones, %.2fs [%s @ x%.2f]"
               % (n_ph, len(syn.diphones), dur, syn.voicebank,
                  self._speed_factor()))
        if syn.skipped:
            msg += "  |  %d MISSING: %s" % (len(syn.skipped),
                                            ", ".join(syn.skipped[:6]))
            if len(syn.skipped) > 6:
                msg += ", ..."
        self.statusBar().showMessage("Status: " + msg)

    # -- actions ------------------------------------------------------------
    def on_generate(self):
        if not self._need_backend():
            return
        text = self.text.text().strip()
        if not text:
            self.statusBar().showMessage("Status: enter some text to synthesize.")
            return
        vb = self._current_voicebank()
        if not vb:
            QtWidgets.QMessageBox.information(
                self, "Voicebank", "No voicebank selected.\n"
                "Voicebank > Add voicebank folder... to register one.")
            return
        self.statusBar().showMessage("Status: synthesizing...")
        QtWidgets.QApplication.processEvents()
        try:
            syn = self.backend.synth(text, self._current_lang_code(), vb,
                                     self._speed_factor())
        except fc.BackendError as e:
            QtWidgets.QMessageBox.critical(self, "Synthesis error", str(e))
            self.statusBar().showMessage("Status: Ready")
            return
        # fresh utterance: reset the velocity envelope to unity
        self.env.set_nodes([0.0, max(syn.duration, 1e-3)], [0.5, 0.5],
                           tmax=max(syn.duration, 1e-3))
        self._show_synthesis(syn)

    def on_rerender(self):
        """Feed the (edited) phoneme fields back through the engine."""
        if not self._need_backend():
            return
        if self.current is None:
            self.statusBar().showMessage("Status: generate audio first.")
            return
        phones = self.waveform.phone_list()
        vb = self._current_voicebank()
        self.statusBar().showMessage("Status: re-rendering edited phonemes...")
        QtWidgets.QApplication.processEvents()
        try:
            syn = self.backend.synth_phones(
                phones, vb, self._speed_factor(),
                text=self.text.text().strip(),
                lang=self._current_lang_code())
        except fc.BackendError as e:
            QtWidgets.QMessageBox.critical(self, "Re-render error", str(e))
            return
        self._show_synthesis(syn)

    def on_render_details(self):
        if self.current is None:
            QtWidgets.QMessageBox.information(self, "Render details",
                                              "Nothing rendered yet.")
            return
        s = self.current
        QtWidgets.QMessageBox.information(
            self, "Render details",
            "text: %s\nlanguage: %s   voicebank: %s\n\nphones (%d):\n%s\n\n"
            "diphones used (%d):\n%s\n\nmissing/skipped (%d):\n%s"
            % (s.text, s.lang, s.voicebank, len(s.phones), " ".join(s.phones),
               len(s.diphones), " ".join(s.diphones), len(s.skipped),
               " ".join(s.skipped) or "(none)"))

    def _on_audio_changed(self):
        dur = self.waveform.duration() or 1.0
        self.env.set_tmax(dur)
        self.env_plot.setXRange(0, dur, padding=0)
        self.statusBar().showMessage(
            "Status: segment re-timed -- %.2fs total" % dur)

    def on_play(self):
        try:
            self.player.play(*self._output_audio())
            self.statusBar().showMessage("Status: playing... (%s)" % self.player.mode)
        except Exception as e:
            QtWidgets.QMessageBox.warning(self, "Playback", str(e))

    def on_stop(self):
        try:
            self.player.stop()
        except Exception:
            pass
        self.statusBar().showMessage("Status: stopped")

    def on_export(self):
        samples, sr = self._output_audio()
        if samples.size <= 1:
            QtWidgets.QMessageBox.information(self, "Export", "Generate audio first.")
            return
        start_dir = self.backend.synth_output_dir() if self.backend else ""
        name = "output"
        if self.backend and self.current and self.current.text:
            name = "%s_%s" % (self.current.lang or "out",
                              self.backend.sd.safe_name(self.current.text))
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Export WAV", os.path.join(start_dir, name + ".wav"),
            "WAV (*.wav)")
        if not path:
            return
        try:
            fc.write_wav(path, samples, sr)
            self.statusBar().showMessage("Status: exported " + os.path.basename(path))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Export error", str(e))

    def on_save_project(self):
        path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self, "Save Project", "project.json", "JSON (*.json)")
        if not path:
            return
        try:
            fc.save_project(
                path, text=self.text.text(), language=self.lang.currentText(),
                lang_code=self._current_lang_code(),
                voicebank=self._current_voicebank() or "",
                speed=self._speed_factor(),
                segments=self.waveform.segments,
                phones=(self.current.phones if self.current else []),
                velocity=self.env.nodes())
            self.statusBar().showMessage("Status: saved " + os.path.basename(path))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Save error", str(e))

    def on_open_project(self):
        if not self._need_backend():
            return
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Open Project", "", "JSON (*.json)")
        if not path:
            return
        try:
            d = fc.load_project(path)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Open error", str(e))
            return
        self.text.setText(d.get("text", ""))
        if self.lang.findText(d.get("language", "")) >= 0:
            self.lang.setCurrentText(d["language"])
        self._refresh_voicebanks(keep=d.get("voicebank"))
        try:
            self.speed.setValue(int(round(100 * np.log2(
                max(0.25, min(4.0, d.get("speed", 1.0)))))))
        except Exception:
            pass
        try:
            phones = d.get("phones") or []
            vb = self._current_voicebank()
            if phones and vb:   # re-render the saved (possibly edited) phones
                syn = self.backend.synth_phones(
                    phones, vb, self._speed_factor(),
                    text=d.get("text", ""), lang=d.get("lang_code", ""))
                self._show_synthesis(syn)
            else:
                self.on_generate()
        except fc.BackendError as e:
            QtWidgets.QMessageBox.critical(self, "Open project", str(e))
            return
        vel = d.get("velocity")
        if vel:
            self.env.set_nodes([p[0] for p in vel], [p[1] for p in vel],
                               tmax=self.waveform.duration() or 1.0)
        self.statusBar().showMessage("Status: opened " + os.path.basename(path))

    # -- voicebank / engine management ----------------------------------------
    def on_add_voice_folder(self):
        if not self._need_backend():
            return
        d = QtWidgets.QFileDialog.getExistingDirectory(
            self, "Select a diphone DB folder (contains dic/diphone_index.json)")
        if not d:
            return
        try:
            name = self.backend.add_voicebank_dir(d)
        except fc.BackendError as e:
            QtWidgets.QMessageBox.critical(self, "Voicebank", str(e))
            return
        self._persist_config()
        self._refresh_voicebanks(keep=name)
        self.statusBar().showMessage(
            "Status: added '%s' (%d diphones) -- saved to config.json"
            % (name, self.backend.db_size(name)))

    def on_set_festvox_config(self):
        if not self._need_backend():
            return
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Locate festvox.json", self.backend.fcfg_path or "",
            "JSON (*.json)")
        if not path:
            return
        self.cfg["festvox_config"] = path
        try:
            self.backend.reload_festvox_config()
        except fc.BackendError as e:
            QtWidgets.QMessageBox.critical(self, "festvox.json", str(e))
            return
        self._persist_config()
        self._refresh_voicebanks()
        self.statusBar().showMessage("Status: festvox.json = " + path)

    def on_reload_voicebanks(self):
        if not self._need_backend():
            return
        try:
            self.backend.reload_festvox_config()
        except fc.BackendError as e:
            QtWidgets.QMessageBox.critical(self, "festvox.json", str(e))
            return
        self._refresh_voicebanks()
        self.statusBar().showMessage(
            "Status: voicebanks reloaded (%s)" % (self.backend.fcfg_path or
                                                  "no festvox.json found"))

    def on_locate_engine(self):
        path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self, "Locate synth_diphone.py", "", "Python (*.py)")
        if not path:
            return
        self.cfg["synth_diphone_dir"] = os.path.dirname(path)
        self._init_backend()
        if self.backend:
            self._persist_config()
            self._populate_from_backend()
            self.statusBar().showMessage("Status: engine loaded from " + path)
        else:
            QtWidgets.QMessageBox.critical(self, "Engine", str(self.backend_err))

    def _on_velocity_toggled(self, on):
        self.cfg["apply_velocity"] = bool(on)
        self._persist_config()
        self.statusBar().showMessage(
            "Status: velocity envelope %s on play/export"
            % ("applied" if on else "ignored"))

    def on_advanced(self):
        adv = dict(self.cfg.get("advanced") or {})
        dlg = QtWidgets.QDialog(self)
        dlg.setWindowTitle("Advanced synthesis settings")
        form = QtWidgets.QFormLayout(dlg)

        def dspin(val, lo, hi, step=1.0):
            s = QtWidgets.QDoubleSpinBox()
            s.setRange(lo, hi); s.setSingleStep(step); s.setDecimals(1)
            s.setValue(float(val))
            return s

        cross = dspin(adv.get("crossfade_ms", 15.0), 0, 100)
        edge = dspin(adv.get("edge_fade_ms", 8.0), 0, 50)
        half = dspin(adv.get("half_ms", 150.0), 30, 500, 10)
        depth = dspin(self.cfg.get("velocity_depth", 1.0), 0.0, 1.0, 0.1)
        depth.setDecimals(2)
        form.addRow("Diphone crossfade (ms):", cross)
        form.addRow("Utterance edge fade (ms):", edge)
        form.addRow("Phone window (ms/side):", half)
        form.addRow("Velocity depth (0-1):", depth)
        note = QtWidgets.QLabel(
            "Phone window caps audio kept per side of each diphone boundary;\n"
            "the speed slider divides it. These map to the engine's\n"
            "CROSSFADE_MS / EDGE_FADE_MS / HALF_MS constants.")
        note.setStyleSheet("color:#555")
        form.addRow(note)
        bb = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject)
        form.addRow(bb)
        if dlg.exec_() != QtWidgets.QDialog.Accepted:
            return
        self.cfg["advanced"] = {"crossfade_ms": cross.value(),
                                "edge_fade_ms": edge.value(),
                                "half_ms": half.value()}
        self.cfg["velocity_depth"] = depth.value()
        self._persist_config()
        self.statusBar().showMessage(
            "Status: synthesis settings saved -- regenerate to hear them")


def main():
    try:
        cfg = fc.load_config(CONFIG_PATH)
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
# end of festvox_gui
