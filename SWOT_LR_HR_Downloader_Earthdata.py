import os
import sys
import threading
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# ─── Ensure Anaconda site-packages are on the path ───────────────────────────
_conda_roots = [
    os.path.expanduser(r'~\AppData\Local\anaconda3\Lib\site-packages'),
    os.path.expanduser(r'~\anaconda3\Lib\site-packages'),
    os.path.expanduser(r'~\AppData\Local\miniconda3\Lib\site-packages'),
    os.path.expanduser(r'~\miniconda3\Lib\site-packages'),
]
for _p in _conda_roots:
    if os.path.isdir(_p) and _p not in sys.path:
        sys.path.insert(0, _p)

# ─── Earthaccess Logic ────────────────────────────────────────────────────────

def run_download(username, password, short_name, granule_pattern,
                 local_dir, log_func):
    try:
        import earthaccess
    except ImportError:
        log_func(f'✘ earthaccess not found. Python used: {sys.executable}')
        log_func('   Run this script from Anaconda Prompt or Spyder terminal:')
        log_func('     python swot_earthaccess_downloader.py')
        return

    log_func('Logging in to NASA Earthdata…')
    # Pass credentials via environment variables (works with all earthaccess versions)
    import os as _os
    _os.environ['EARTHDATA_USERNAME'] = username
    _os.environ['EARTHDATA_PASSWORD'] = password
    auth = earthaccess.login(strategy='environment')
    log_func('✔ Logged in.\n')

    log_func(f'Searching for:  {short_name}')
    log_func(f'Granule pattern: {granule_pattern}\n')

    results = earthaccess.search_data(
        short_name=short_name,
        granule_name=granule_pattern
    )
    granule_list = list(results)
    log_func(f'✔ Found {len(granule_list)} granule(s).\n')

    if not granule_list:
        log_func('⚠ No granules matched. Check your pattern and try again.')
        return

    os.makedirs(local_dir, exist_ok=True)
    log_func(f'Downloading to: {local_dir}\n')
    earthaccess.download(granule_list, local_dir)
    log_func('\n✔ All downloads complete.')


# ─── GUI ──────────────────────────────────────────────────────────────────────

class EarthAccessApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('SWOT Earthdata Downloader')
        self.resizable(False, False)
        self.configure(bg='#f0f4ff')
        self._build_ui()

    def _build_ui(self):
        FONT_TITLE = ('Calibri', 17, 'bold')
        FONT_LABEL = ('Calibri', 10)
        FONT_ENTRY = ('Calibri', 10)
        FONT_BTN   = ('Calibri', 10, 'bold')
        FONT_LOG   = ('Courier New', 9)
        FONT_SMALL = ('Calibri', 9)

        BG       = '#f0f4ff'
        CARD     = '#ffffff'
        ACCENT   = '#1a6fcc'
        TEXT     = '#1a2a4a'
        MUTED    = '#7a9ac0'
        ENTRY_BG = '#eaf1fb'
        BTN_BG   = '#1a6fcc'
        BTN_FG   = '#ffffff'
        BTN_ACT  = '#145aa8'

        # ── Title ─────────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG)
        header.pack(fill='x', padx=20, pady=(18, 4))
        tk.Label(header, text='◈  SWOT Earthdata Downloader',
                 font=FONT_TITLE, bg=BG, fg=ACCENT).pack(side='left')
        tk.Label(header, text='NASA Earthaccess Client',
                 font=FONT_SMALL, bg=BG, fg=MUTED).pack(side='right', anchor='s', pady=4)
        tk.Frame(self, bg=ACCENT, height=1).pack(fill='x', padx=20, pady=(0, 10))

        # ── Body ──────────────────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(padx=20, fill='both')

        left  = tk.Frame(body, bg=BG)
        right = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky='n', padx=(0, 16))
        right.grid(row=0, column=1, sticky='n')

        # ── Widget helpers ────────────────────────────────────────────────────
        def card(parent, title):
            f = tk.LabelFrame(parent, text=f'  {title}  ',
                              font=('Courier New', 9, 'bold'),
                              bg=CARD, fg=ACCENT, bd=1, relief='flat',
                              labelanchor='nw', padx=12, pady=8)
            f.pack(fill='x', pady=(0, 12))
            return f

        def lbl(parent, text):
            tk.Label(parent, text=text, font=FONT_LABEL,
                     bg=CARD, fg=TEXT, anchor='w').pack(fill='x', pady=(6, 1))

        def hint(parent, text):
            tk.Label(parent, text=text, font=FONT_SMALL,
                     bg=CARD, fg=MUTED, anchor='w', wraplength=340,
                     justify='left').pack(fill='x', pady=(1, 2))

        def entry(parent, width=28, default=''):
            e = tk.Entry(parent, font=FONT_ENTRY, bg=ENTRY_BG, fg=TEXT,
                         insertbackground=ACCENT, relief='flat', bd=0,
                         highlightthickness=1, highlightcolor=ACCENT,
                         highlightbackground=MUTED, width=width)
            if default:
                e.insert(0, default)
            e.pack(fill='x', ipady=4)
            return e

        def combobox(parent, values, default=0, width=26):
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('W.TCombobox',
                            fieldbackground='#ffffff', background='#ffffff',
                            foreground='#1a2a4a', arrowcolor='#1a6fcc',
                            bordercolor='#7a9ac0', selectbackground='#d0e8ff',
                            selectforeground='#1a2a4a', font=FONT_ENTRY)
            style.map('W.TCombobox',
                      fieldbackground=[('readonly', '#ffffff')],
                      foreground=[('readonly', '#1a2a4a')],
                      selectbackground=[('readonly', '#d0e8ff')],
                      selectforeground=[('readonly', '#1a2a4a')])
            cb = ttk.Combobox(parent, values=values, state='readonly',
                              style='W.TCombobox', font=FONT_ENTRY, width=width)
            cb.current(default)
            cb.pack(fill='x', ipady=4, pady=(0, 2))
            return cb

        # ── LEFT: credentials + output dir ───────────────────────────────────
        c_cred = card(left, '🔐  NASA Earthdata Credentials')
        lbl(c_cred, 'Username')
        self.e_user = entry(c_cred)
        hint(c_cred, 'ℹ  Register free at urs.earthdata.nasa.gov')
        lbl(c_cred, 'Password')
        self.e_pass = tk.Entry(c_cred, font=FONT_ENTRY, bg=ENTRY_BG, fg=TEXT,
                               insertbackground=ACCENT, relief='flat', bd=0,
                               highlightthickness=1, highlightcolor=ACCENT,
                               highlightbackground=MUTED, show='●', width=28)
        self.e_pass.pack(fill='x', ipady=4)

        c_local = card(left, '📁  Local Output Directory')
        dir_row = tk.Frame(c_local, bg=CARD)
        dir_row.pack(fill='x')
        self.e_local = tk.Entry(dir_row, font=FONT_ENTRY, bg=ENTRY_BG, fg=TEXT,
                                insertbackground=ACCENT, relief='flat', bd=0,
                                highlightthickness=1, highlightcolor=ACCENT,
                                highlightbackground=MUTED, width=20)
        self.e_local.pack(side='left', fill='x', expand=True, ipady=4)
        tk.Button(dir_row, text='Browse', font=FONT_BTN,
                  bg=BTN_BG, fg=BTN_FG, activebackground=BTN_ACT,
                  relief='flat', bd=0, padx=8,
                  command=self._browse_dir).pack(side='left', padx=(6, 0), ipady=4)

        # ── RIGHT: granule pattern builder ───────────────────────────────────
        c_pattern = card(right, '🛰  Granule Pattern Builder')

        lbl(c_pattern, 'Short Name  (dataset)')
        self.cb_shortname = combobox(c_pattern, [
            'SWOT_L2_LR_SSH_D',
            'SWOT_L2_HR_PIXC_D',
            'SWOT_L2_HR_Raster_D',
            'SWOT_L2_HR_RiverSP_D',
        ])

        lbl(c_pattern, 'Product Type')
        self.cb_type = combobox(c_pattern,
            ['LR_SSH', 'HR_PIXC', 'HR_Raster', 'HR_RiverSP'])

        # ── LR_SSH only: level ────────────────────────────────────────────────
        self.level_frame = tk.Frame(c_pattern, bg=CARD)
        self.level_frame.pack(fill='x')
        tk.Label(self.level_frame, text='Data Level / Quality',
                 font=FONT_LABEL, bg=CARD, fg=TEXT, anchor='w').pack(fill='x', pady=(6, 1))
        self.cb_level = combobox(self.level_frame,
                                 ['Expert', 'Basic', 'Unsmoothed', 'WindWave'])

        # ── Shared: cycle + pass ──────────────────────────────────────────────
        lbl(c_pattern, 'Cycle Number  (3 digits, e.g.  048)  — use * for all')
        self.e_cycle = entry(c_pattern, default='*')

        lbl(c_pattern, 'Pass Number  (3 digits, e.g.  001)  — use * for all')
        self.e_pass_id = entry(c_pattern, default='*')

        # ── HR_PIXC only: tile + side ─────────────────────────────────────────
        # Pattern: SWOT_L2_HR_PIXC_048_001_281L_*_*_PID0_01
        self.tile_frame = tk.Frame(c_pattern, bg=CARD)
        tk.Label(self.tile_frame,
                 text='Tile Number  (3 digits, e.g.  281)  — use * for all',
                 font=FONT_LABEL, bg=CARD, fg=TEXT, anchor='w').pack(fill='x', pady=(6, 1))
        tile_row = tk.Frame(self.tile_frame, bg=CARD)
        tile_row.pack(fill='x')
        self.e_tile = tk.Entry(tile_row, font=FONT_ENTRY, bg=ENTRY_BG, fg=TEXT,
                               insertbackground=ACCENT, relief='flat', bd=0,
                               highlightthickness=1, highlightcolor=ACCENT,
                               highlightbackground=MUTED, width=8)
        self.e_tile.insert(0, '*')
        self.e_tile.pack(side='left', ipady=4)
        tk.Label(tile_row, text='  Side:', font=FONT_LABEL,
                 bg=CARD, fg=TEXT).pack(side='left', padx=(10, 4))
        style_s = ttk.Style()
        style_s.configure('S.TCombobox',
                          fieldbackground='#ffffff', background='#ffffff',
                          foreground='#1a2a4a', arrowcolor='#1a6fcc',
                          bordercolor='#7a9ac0', selectbackground='#d0e8ff',
                          selectforeground='#1a2a4a', font=FONT_ENTRY)
        style_s.map('S.TCombobox',
                    fieldbackground=[('readonly', '#ffffff')],
                    foreground=[('readonly', '#1a2a4a')],
                    selectbackground=[('readonly', '#d0e8ff')],
                    selectforeground=[('readonly', '#1a2a4a')])
        self.cb_side = ttk.Combobox(tile_row, values=['*', 'R', 'L'],
                                    style='S.TCombobox',
                                    font=FONT_ENTRY, width=4, state='readonly')
        self.cb_side.current(0)
        self.cb_side.pack(side='left', ipady=4)
        hint(self.tile_frame, 'ℹ  R = Right side, L = Left side')

        # ── HR_Raster only: resolution + projection ───────────────────────────
        # Pattern: SWOT_L2_HR_Raster_100m_UTM41R_N_x_x_x_047_566_056F_*_*_PID0_01
        self.raster_frame = tk.Frame(c_pattern, bg=CARD)
        tk.Label(self.raster_frame, text='Resolution',
                 font=FONT_LABEL, bg=CARD, fg=TEXT, anchor='w').pack(fill='x', pady=(6, 1))
        self.cb_raster_res = combobox(self.raster_frame, ['100m', '250m', '*'])
        tk.Label(self.raster_frame,
                 text='Projection  (e.g.  UTM41R, UTM30N)  — use * for all',
                 font=FONT_LABEL, bg=CARD, fg=TEXT, anchor='w').pack(fill='x', pady=(6, 1))
        self.e_raster_proj = entry(self.raster_frame, default='*')
        tk.Label(self.raster_frame,
                 text='Tile ID  (e.g.  056F)  — use * for all',
                 font=FONT_LABEL, bg=CARD, fg=TEXT, anchor='w').pack(fill='x', pady=(6, 1))
        self.e_raster_tile = entry(self.raster_frame, default='*')
        hint(self.raster_frame,
             'ℹ  e.g. SWOT_L2_HR_Raster_100m_UTM41R_N_x_x_x_047_566_056F_*_*_PID0_01')

        # ── HR_RiverSP only: feature type + continent ─────────────────────────
        # Pattern: SWOT_L2_HR_RiverSP_Reach_048_001_EU_*_*_PID0_01
        self.river_frame = tk.Frame(c_pattern, bg=CARD)
        tk.Label(self.river_frame, text='Feature Type',
                 font=FONT_LABEL, bg=CARD, fg=TEXT, anchor='w').pack(fill='x', pady=(6, 1))
        self.cb_river_type = combobox(self.river_frame, ['Reach', 'Node', '*'])
        tk.Label(self.river_frame,
                 text='Continent Code  (e.g.  EU, NA, AS)  — use * for all',
                 font=FONT_LABEL, bg=CARD, fg=TEXT, anchor='w').pack(fill='x', pady=(6, 1))
        self.e_continent = entry(self.river_frame, default='*')
        hint(self.river_frame,
             'ℹ  EU=Europe  NA=N.America  AS=Asia  AF=Africa  '
             'OC=Oceania  SA=S.America  AR=Arctic  AN=Antarctica')

        # ── Version (shared) ──────────────────────────────────────────────────
        lbl(c_pattern, 'Version  (e.g.  PID0_01, PGD0_01)  — use * for all')
        self.e_version = entry(c_pattern, default='*')

        # ── Pattern preview ───────────────────────────────────────────────────
        lbl(c_pattern, 'Constructed Granule Pattern (preview)')
        self.lbl_pattern = tk.Label(c_pattern, text='', font=FONT_SMALL,
                                    bg=ENTRY_BG, fg=ACCENT, anchor='w',
                                    wraplength=340, justify='left', padx=6, pady=4)
        self.lbl_pattern.pack(fill='x', pady=(2, 0))

        # ── Bind events ───────────────────────────────────────────────────────
        self.cb_type.bind('<<ComboboxSelected>>', lambda e: self._on_type_change())
        for w in (self.cb_shortname, self.cb_level, self.cb_raster_res,
                  self.cb_river_type, self.cb_side):
            w.bind('<<ComboboxSelected>>', lambda e: self._update_preview())
        for w in (self.e_cycle, self.e_pass_id, self.e_tile, self.e_version,
                  self.e_raster_proj, self.e_raster_tile, self.e_continent):
            w.bind('<KeyRelease>', lambda e: self._update_preview())

        # Initial state
        self.tile_frame.pack_forget()
        self.raster_frame.pack_forget()
        self.river_frame.pack_forget()
        self._update_preview()

        # ── Buttons ───────────────────────────────────────────────────────────
        tk.Frame(self, bg=MUTED, height=1).pack(fill='x', padx=20, pady=(8, 10))
        btn_row = tk.Frame(self, bg=BG)
        btn_row.pack(padx=20, pady=(0, 8), fill='x')
        self.btn_dl = tk.Button(btn_row, text='  ▶  START DOWNLOAD  ',
                                font=FONT_BTN, bg=BTN_BG, fg=BTN_FG,
                                activebackground=BTN_ACT, relief='flat', bd=0,
                                padx=16, pady=8, command=self._start_download)
        self.btn_dl.pack(side='left')
        tk.Button(btn_row, text='Clear Log', font=FONT_BTN,
                  bg=CARD, fg=MUTED, activebackground='#1a3050',
                  relief='flat', bd=0, padx=10, pady=8,
                  command=self._clear_log).pack(side='right')

        # ── Log ───────────────────────────────────────────────────────────────
        log_frame = tk.LabelFrame(self, text='  📋  Download Log  ',
                                  font=('Courier New', 9, 'bold'),
                                  bg=CARD, fg=ACCENT, bd=1, relief='flat',
                                  padx=10, pady=8)
        log_frame.pack(padx=20, pady=(0, 16), fill='both', expand=True)
        self.log = scrolledtext.ScrolledText(log_frame, font=FONT_LOG,
                                             bg='#eaf1fb', fg='#1a2a4a',
                                             insertbackground=ACCENT,
                                             relief='flat', bd=0,
                                             height=10, width=80,
                                             state='disabled')
        self.log.pack(fill='both', expand=True)

    # ── Type switcher ─────────────────────────────────────────────────────────

    def _on_type_change(self):
        ptype = self.cb_type.get()
        self.level_frame.pack_forget()
        self.tile_frame.pack_forget()
        self.raster_frame.pack_forget()
        self.river_frame.pack_forget()

        if ptype == 'LR_SSH':
            self.level_frame.pack(fill='x')
        elif ptype == 'HR_PIXC':
            self.tile_frame.pack(fill='x')
        elif ptype == 'HR_Raster':
            self.raster_frame.pack(fill='x')
        elif ptype == 'HR_RiverSP':
            self.river_frame.pack(fill='x')

        self._update_preview()

    # ── Pattern builder ───────────────────────────────────────────────────────

    def _build_pattern(self):
        ptype   = self.cb_type.get()
        cycle   = self.e_cycle.get().strip() or '*'
        pass_id = self.e_pass_id.get().strip() or '*'
        version = self.e_version.get().strip() or '*'

        if ptype == 'LR_SSH':
            # SWOT_L2_LR_SSH_Expert_510_016_*_*_PGD0_01
            level = self.cb_level.get()
            return f'SWOT_L2_LR_SSH_{level}_{cycle}_{pass_id}_*_*_{version}'

        elif ptype == 'HR_PIXC':
            # SWOT_L2_HR_PIXC_048_001_281L_*_*_PID0_01
            tile = self.e_tile.get().strip() or '*'
            side = self.cb_side.get().strip()
            tile_field = f'{tile}{side}' if side != '*' else f'{tile}*'
            return f'SWOT_L2_HR_PIXC_{cycle}_{pass_id}_{tile_field}_*_*_{version}'

        elif ptype == 'HR_Raster':
            # SWOT_L2_HR_Raster_100m_UTM41R_N_x_x_x_047_566_056F_*_*_PID0_01
            res   = self.cb_raster_res.get()
            proj  = self.e_raster_proj.get().strip() or '*'
            tile  = self.e_raster_tile.get().strip() or '*'
            return f'SWOT_L2_HR_Raster_{res}_{proj}_N_x_x_x_{cycle}_{pass_id}_{tile}_*_*_{version}'

        elif ptype == 'HR_RiverSP':
            # SWOT_L2_HR_RiverSP_Reach_048_001_EU_*_*_PID0_01
            rtype     = self.cb_river_type.get()
            continent = self.e_continent.get().strip() or '*'
            return f'SWOT_L2_HR_RiverSP_{rtype}_{cycle}_{pass_id}_{continent}_*_*_{version}'

        return 'SWOT_L2_*'

    def _update_preview(self):
        self.lbl_pattern.config(text=self._build_pattern())

    def _get_pattern(self):
        return self._build_pattern()

    # ── Misc ──────────────────────────────────────────────────────────────────

    def _browse_dir(self):
        d = filedialog.askdirectory()
        if d:
            self.e_local.delete(0, 'end')
            self.e_local.insert(0, d)

    def _log(self, msg):
        self.log.config(state='normal')
        self.log.insert('end', msg + '\n')
        self.log.see('end')
        self.log.config(state='disabled')

    def _clear_log(self):
        self.log.config(state='normal')
        self.log.delete('1.0', 'end')
        self.log.config(state='disabled')

    def _set_busy(self, busy):
        self.btn_dl.config(
            state='disabled' if busy else 'normal',
            text='  ⏳  DOWNLOADING…  ' if busy else '  ▶  START DOWNLOAD  ')

    def _start_download(self):
        username  = self.e_user.get().strip()
        password  = self.e_pass.get().strip()
        local_dir = self.e_local.get().strip()

        if not username or not password:
            messagebox.showerror('Missing credentials',
                                 'Please enter your NASA Earthdata username and password.')
            return
        if not local_dir:
            messagebox.showerror('Missing directory',
                                 'Please select a local output directory.')
            return

        short_name      = self.cb_shortname.get()
        granule_pattern = self._get_pattern()

        self._log(f'Short name:      {short_name}')
        self._log(f'Granule pattern: {granule_pattern}\n')

        self._set_busy(True)
        threading.Thread(
            target=self._download_thread,
            args=(username, password, short_name, granule_pattern, local_dir),
            daemon=True
        ).start()

    def _download_thread(self, username, password, short_name,
                         granule_pattern, local_dir):
        try:
            run_download(username, password, short_name,
                         granule_pattern, local_dir, self._log)
        except Exception as e:
            self._log(f'\n✘ Error: {e}')
        finally:
            self.after(0, lambda: self._set_busy(False))


if __name__ == '__main__':
    app = EarthAccessApp()
    app.mainloop()