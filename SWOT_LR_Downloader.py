import os
import threading
from ftplib import FTP
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

# ─── FTP Logic ────────────────────────────────────────────────────────────────

def connect_ftp(userid, userpass, ftp_host='ftp-access.aviso.altimetry.fr'):
    ftp = FTP(ftp_host)
    ftp.login(user=userid, passwd=userpass)
    return ftp

def download_files(ftp, remote_dir, local_dir, file_names, log_func):
    ftp.cwd(remote_dir)
    os.makedirs(local_dir, exist_ok=True)
    for file_name in file_names:
        local_path = os.path.join(local_dir, file_name)
        with open(local_path, 'wb') as local_file:
            ftp.retrbinary(f'RETR {file_name}', local_file.write)
        log_func(f'  ✔ Downloaded: {file_name}')

# ─── GUI ──────────────────────────────────────────────────────────────────────

class SWOTDownloaderApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title('SWOT Data Downloader')
        self.resizable(False, False)
        self.configure(bg='#0d1b2a')
        self._build_ui()

    def _build_ui(self):
        FONT_TITLE  = ('Courier New', 16, 'bold')
        FONT_LABEL  = ('Courier New', 10)
        FONT_ENTRY  = ('Courier New', 10)
        FONT_BTN    = ('Courier New', 10, 'bold')
        FONT_LOG    = ('Courier New', 9)

        BG       = '#0d1b2a'
        CARD     = '#112233'
        ACCENT   = '#00c8ff'
        TEXT     = '#cce8ff'
        MUTED    = '#4a7fa5'
        ENTRY_BG = '#091624'
        BTN_BG   = '#00c8ff'
        BTN_FG   = '#0d1b2a'
        BTN_ACT  = '#00a0cc'

        # ── Title ─────────────────────────────────────────────────────────────
        header = tk.Frame(self, bg=BG)
        header.pack(fill='x', padx=20, pady=(18, 4))
        tk.Label(header, text='◈  SWOT Data Downloader',
                 font=FONT_TITLE, bg=BG, fg=ACCENT).pack(side='left')
        tk.Label(header, text='AVISO+ FTP Client',
                 font=('Courier New', 9), bg=BG, fg=MUTED).pack(side='right', anchor='s', pady=4)

        tk.Frame(self, bg=ACCENT, height=1).pack(fill='x', padx=20, pady=(0, 10))

        # ── Two-column body ───────────────────────────────────────────────────
        body = tk.Frame(self, bg=BG)
        body.pack(padx=20, pady=0, fill='both')

        left  = tk.Frame(body, bg=BG)
        right = tk.Frame(body, bg=BG)
        left.grid(row=0, column=0, sticky='n', padx=(0, 16))
        right.grid(row=0, column=1, sticky='n')

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

        def entry(parent, show=None, width=28):
            e = tk.Entry(parent, font=FONT_ENTRY, bg=ENTRY_BG, fg=TEXT,
                         insertbackground=ACCENT, relief='flat', bd=0,
                         highlightthickness=1, highlightcolor=ACCENT,
                         highlightbackground=MUTED, show=show, width=width)
            e.pack(fill='x', ipady=4)
            return e

        def combobox(parent, values, default=0):
            style = ttk.Style()
            style.theme_use('clam')
            style.configure('Dark.TCombobox',
                            fieldbackground='#ffffff', background='#ffffff',
                            foreground='#000000', arrowcolor=ACCENT,
                            bordercolor=MUTED, selectbackground='#ffffff',
                            selectforeground='#000000', font=FONT_ENTRY)
            style.map('Dark.TCombobox',
                      fieldbackground=[('readonly', '#ffffff')],
                      foreground=[('readonly', '#000000')],
                      selectbackground=[('readonly', '#ffffff')],
                      selectforeground=[('readonly', '#000000')])
            cb = ttk.Combobox(parent, values=values, state='readonly',
                              style='Dark.TCombobox', font=FONT_ENTRY, width=26)
            cb.current(default)
            cb.pack(fill='x', ipady=4, pady=(0, 2))
            return cb

        # ── LEFT: credentials + local dir ────────────────────────────────────
        c_cred = card(left, '🔐  Credentials')
        lbl(c_cred, 'AVISO Username')
        self.e_user = entry(c_cred)
        lbl(c_cred, 'AVISO Password')
        self.e_pass = entry(c_cred, show='●')

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

        # ── RIGHT: remote path builder ────────────────────────────────────────
        c_remote = card(right, '🛰  Remote Path Configuration')

        lbl(c_remote, 'Product Level')
        self.cb_level = combobox(c_remote,
            ['l2_karin/l2_lr_ssh',
             'l3_karin/l3_lr_wind_wave',
             'l3_karin_nadir/l3_lr_ssh'])

        lbl(c_remote, 'Version')
        self.cb_version = combobox(c_remote,
            ['PID0', 'PGD0', 'PIC0', 'PGC0', 'PIC2', 'v2_0', 'v3_0'])

        lbl(c_remote, 'Type')
        self.cb_type = combobox(c_remote,
            ['Expert', 'Basic', 'Unsmoothed', 'WindWave',
             'Technical', 'Extended', 'Light'])

        # ── Sub-directory (optional) ──────────────────────────────────────────
        lbl(c_remote, 'Sub-directory  (optional)')
        subdir_row = tk.Frame(c_remote, bg=CARD)
        subdir_row.pack(fill='x')

        # Dropdown for common options
        style_sub = ttk.Style()
        style_sub.configure('Sub.TCombobox',
                        fieldbackground='#ffffff', background='#ffffff',
                        foreground='#000000', arrowcolor=ACCENT,
                        bordercolor=MUTED, selectbackground='#ffffff',
                        selectforeground='#000000', font=FONT_ENTRY)
        style_sub.map('Sub.TCombobox',
                  fieldbackground=[('readonly', '#ffffff')],
                  foreground=[('readonly', '#000000')],
                  selectbackground=[('readonly', '#ffffff')],
                  selectforeground=[('readonly', '#000000')])
        self.cb_subdir = ttk.Combobox(subdir_row,
            values=['', 'forward', 'reproc'],
            style='Sub.TCombobox', font=FONT_ENTRY, width=14)
        self.cb_subdir.current(0)
        self.cb_subdir.pack(side='left', ipady=4)

        tk.Label(subdir_row, text='  or custom:',
                 font=('Courier New', 8), bg=CARD, fg=MUTED).pack(side='left')

        # Free-text override
        self.e_subdir_custom = tk.Entry(subdir_row, font=FONT_ENTRY,
                                        bg=ENTRY_BG, fg=TEXT,
                                        insertbackground=ACCENT, relief='flat',
                                        bd=0, highlightthickness=1,
                                        highlightcolor=ACCENT,
                                        highlightbackground=MUTED, width=10)
        self.e_subdir_custom.pack(side='left', padx=(6, 0), ipady=4)

        tk.Label(c_remote,
                 text='ℹ  Leave both blank if the path has no sub-directory',
                 font=('Courier New', 8), bg=CARD, fg=MUTED,
                 anchor='w').pack(fill='x', pady=(3, 4))

        # ── Cycle range ───────────────────────────────────────────────────────
        lbl(c_remote, 'Cycle Range  (start  →  end, inclusive)')
        cyc_row = tk.Frame(c_remote, bg=CARD)
        cyc_row.pack(fill='x')
        self.e_cyc_start = tk.Entry(cyc_row, font=FONT_ENTRY, bg=ENTRY_BG, fg=TEXT,
                                    insertbackground=ACCENT, relief='flat', bd=0,
                                    highlightthickness=1, highlightcolor=ACCENT,
                                    highlightbackground=MUTED, width=6)
        self.e_cyc_start.insert(0, '32')
        self.e_cyc_start.pack(side='left', ipady=4)
        tk.Label(cyc_row, text=' → ', font=FONT_LABEL,
                 bg=CARD, fg=MUTED).pack(side='left')
        self.e_cyc_end = tk.Entry(cyc_row, font=FONT_ENTRY, bg=ENTRY_BG, fg=TEXT,
                                  insertbackground=ACCENT, relief='flat', bd=0,
                                  highlightthickness=1, highlightcolor=ACCENT,
                                  highlightbackground=MUTED, width=6)
        self.e_cyc_end.insert(0, '42')
        self.e_cyc_end.pack(side='left', ipady=4)

        # ── Pass IDs ──────────────────────────────────────────────────────────
        lbl(c_remote, 'Pass IDs  (comma-separated, e.g.  014, 027)')
        self.e_passes = tk.Entry(c_remote, font=FONT_ENTRY, bg=ENTRY_BG, fg=TEXT,
                                 insertbackground=ACCENT, relief='flat', bd=0,
                                 highlightthickness=1, highlightcolor=ACCENT,
                                 highlightbackground=MUTED, width=28)
        self.e_passes.insert(0, '014')
        self.e_passes.pack(fill='x', ipady=4)

        # ── Path preview ──────────────────────────────────────────────────────
        lbl(c_remote, 'Constructed Remote Path (preview)')
        self.lbl_path = tk.Label(c_remote, text='', font=('Courier New', 8),
                                 bg=ENTRY_BG, fg=ACCENT, anchor='w',
                                 wraplength=340, justify='left', padx=6, pady=4)
        self.lbl_path.pack(fill='x', pady=(2, 0))

        for widget in (self.cb_level, self.cb_version, self.cb_type, self.cb_subdir):
            widget.bind('<<ComboboxSelected>>', lambda e: self._update_path_preview())
        self.e_subdir_custom.bind('<KeyRelease>', lambda e: self._update_path_preview())
        self._update_path_preview()

        # ── Buttons ───────────────────────────────────────────────────────────
        tk.Frame(self, bg=MUTED, height=1).pack(fill='x', padx=20, pady=(4, 10))

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
                                             bg='#060f18', fg='#7ecfff',
                                             insertbackground=ACCENT,
                                             relief='flat', bd=0,
                                             height=10, width=80,
                                             state='disabled')
        self.log.pack(fill='both', expand=True)

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _get_subdir(self):
        """Custom text field takes priority over dropdown."""
        custom = self.e_subdir_custom.get().strip()
        return custom if custom else self.cb_subdir.get().strip()

    def _update_path_preview(self):
        subdir = self._get_subdir()
        path = (f'/swot_products/'
                f'{self.cb_level.get()}/'
                f'{self.cb_version.get()}/'
                f'{self.cb_type.get()}/')
        if subdir:
            path += f'{subdir}/'
        path += 'cycle_XXX/'
        self.lbl_path.config(text=path)

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

    # ── Download ──────────────────────────────────────────────────────────────

    def _start_download(self):
        userid    = self.e_user.get().strip()
        userpass  = self.e_pass.get().strip()
        local_dir = self.e_local.get().strip()

        if not userid or not userpass:
            messagebox.showerror('Missing credentials',
                                 'Please enter your username and password.')
            return
        if not local_dir:
            messagebox.showerror('Missing directory',
                                 'Please select a local output directory.')
            return
        try:
            cyc_start = int(self.e_cyc_start.get())
            cyc_end   = int(self.e_cyc_end.get())
        except ValueError:
            messagebox.showerror('Invalid cycle range',
                                 'Cycle start and end must be integers.')
            return

        passes = [p.strip() for p in self.e_passes.get().split(',') if p.strip()]
        if not passes:
            messagebox.showerror('Missing pass IDs',
                                 'Please enter at least one pass ID.')
            return

        subdir = self._get_subdir()
        remote_base = (f'/swot_products/'
                       f'{self.cb_level.get()}/'
                       f'{self.cb_version.get()}/'
                       f'{self.cb_type.get()}/')
        if subdir:
            remote_base += f'{subdir}/'

        self._set_busy(True)
        threading.Thread(
            target=self._download_thread,
            args=(userid, userpass, remote_base, local_dir,
                  cyc_start, cyc_end, passes),
            daemon=True
        ).start()

    def _download_thread(self, userid, userpass, remote_base, local_dir,
                         cyc_start, cyc_end, passes):
        try:
            self._log('Connecting to AVISO FTP…')
            ftp = connect_ftp(userid, userpass)
            self._log('✔ Connected.\n')
            self._log(f'Remote base: {remote_base}\n')

            cycles = [f'cycle_{i:03}' for i in range(cyc_start, cyc_end + 1)]

            for cycle in cycles:
                for pass_id in passes:
                    remote_dir = (remote_base + cycle).replace('\\', '/')
                    self._log(f'── {cycle}  |  pass {pass_id}')
                    self._log(f'   Remote: {remote_dir}')
                    try:
                        ftp.cwd(remote_dir)
                        file_names = [fn for fn in ftp.nlst()
                                      if f'_{pass_id}_' in fn]
                        if not file_names:
                            self._log(f'   ⚠ No files found for pass {pass_id}.')
                            continue
                        download_files(ftp, remote_dir, local_dir,
                                       file_names, self._log)
                    except Exception as e:
                        self._log(f'   ✘ Error: {e}')

            ftp.quit()
            self._log('\n✔ All downloads complete.')
        except Exception as e:
            self._log(f'\n✘ Connection failed: {e}')
        finally:
            self.after(0, lambda: self._set_busy(False))


if __name__ == '__main__':
    app = SWOTDownloaderApp()
    app.mainloop()