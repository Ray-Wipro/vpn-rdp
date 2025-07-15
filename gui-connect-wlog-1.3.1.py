import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import time
import threading
import logging
import sys

APP_VERSION = "1.2.3"

# Logging
logging.basicConfig(
    filename='log-connessione.txt',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Caricamento configurazioni
def carica_configurazioni():
    with open("connessioni-vpn.json", "r", encoding="utf-8") as f:
        return json.load(f)

# Verifica connessione
def verifica_connessione(ip, tentativi=5, pausa=7, output=None):
    if tentativi <= 0:
        msg = "Nessun tentativo di connessione, il tipo di VPN non richiede verifica."
        logging.info(msg)
        return True
    for i in range(tentativi):
        msg = f"Verifica connessione a {ip} (tentativo {i+1})..."
        logging.info(msg)
        if output: output(msg)
        risultato = subprocess.run(["ping", "-n", "1", ip], stdout=subprocess.DEVNULL)
        if risultato.returncode == 0:
            msg = "Connessione VPN stabilita."
            logging.info(msg)
            if output: output(f"[OK] {msg}")
            return True
        time.sleep(pausa)
    msg = "Timeout nella connessione VPN."
    logging.error(msg)
    if output: output(f"[ERRORE] {msg}")
    return False

# Avvio VPN
def avvia_vpn(cfg, output):
    metodo = cfg.get("vpn_metodo", "FRT")
    output(f"[VPN] Metodo: {metodo}")

    match metodo:
        case "FRT":
            exe = cfg.get("vpn_exe")
            if exe:
                args = " ".join(cfg.get("vpn_argomenti", []))
                subprocess.Popen(f'"{exe}" {args}', shell=True)
            else:
                output("[ERRORE] vpn_exe non specificato per metodo FRT")
        case "NTC":
            exe = cfg.get("vpn_exe", r"C:\\Program Files\\SonicWall\\SSL-VPN\\NetExtender\\NETCLI.exe")
            cmd = [exe, "connect",
                   "-s", cfg["vpn_server"],
                   "-u", cfg["vpn_user"],
                   "-p", cfg["vpn_pass"],
                   "-d", cfg["vpn_domain"]]
            try:
                subprocess.Popen(cmd)
            except FileNotFoundError:
                output(f"[ERRORE] File non trovato: {exe}")
        case "OVP":
            exe = cfg.get("vpn_exe")
            if exe:
                try:
                    subprocess.Popen([exe])
                    output("[WARNING] OpenVPN Connect avviato. Eseguire la connessione manualmente dal client OpenVPN.")
                    output("[DEBUG] Ricordarsi di scollegare la VPN al termine della connessione.")
                except FileNotFoundError:
                    output(f"[ERRORE] File non trovato: {exe}")
            else:
                output("[ERRORE] vpn_exe non specificato per metodo OVP")
        case "CYL":
            url = cfg.get("vpn_exe", "https://users.mdlz.cyolo.io/")
            output("[INFO] Metodo CYOLO selezionato. Apertura browser...")
            try:
                import webbrowser
                webbrowser.open(url)
            except Exception as e:
                output(f"[ERRORE] Impossibile aprire il browser: {e}")
            output("[INFO] Attendere il completamento dell'accesso manuale prima di aprire RDP che verrà scaricato.")
        case _:
            output(f"[ERRORE] Metodo VPN non riconosciuto: {metodo}")

# Connessione completa
# def connetti(cfg_impianto, cfg_rdp, output_callback):
#     output_callback(f"Avvio connessione per {cfg_rdp['rdp_nome']}")
#     avvia_vpn(cfg_impianto, output_callback)

#     # valori di default per i tentativi e la pausa
#     tentativi = cfg_impianto.get("vpn_tentativi", 5)
#     pausa = cfg_impianto.get("vpn_pausa", 7)

#     if verifica_connessione(cfg_rdp["rdp_ip"], tentativi=tentativi, pausa=pausa, output=output_callback):
#         msg = f"Avvio RDP: {cfg_rdp['rdp_file']}"
#         output_callback(msg)
#         logging.info(msg)
#         subprocess.Popen(f'mstsc "{cfg_rdp["rdp_file"]}"', shell=True)
#     else:
#         output_callback("Connessione non riuscita. RDP non avviato.")
def connetti(cfg_impianto, cfg_rdp, output_callback):
    output_callback(f"Avvio connessione per {cfg_rdp['rdp_nome']}")
    avvia_vpn(cfg_impianto, output_callback)

    tentativi = cfg_impianto.get("vpn_tentativi", 5)
    pausa = cfg_impianto.get("vpn_pausa", 7)

    metodo = cfg_impianto.get("vpn_metodo")
    match metodo:
        case "CYL":
            output_callback("[INFO] Connessione Cyolo: verifica ping disattivata.")
            msg = f"Avvio RDP: {cfg_rdp['rdp_file']}"
            output_callback(msg)
            logging.info(msg)
            subprocess.Popen(f'mstsc "{cfg_rdp["rdp_file"]}"', shell=True)
        case _:
            if cfg_rdp["rdp_file"] == "":
                output_callback("[INFO] Nessun file RDP specificato, connessione VPN avviata senza RDP.")
                return
            if verifica_connessione(cfg_rdp["rdp_ip"], tentativi=tentativi, pausa=pausa, output=output_callback):
                msg = f"Avvio RDP: {cfg_rdp['rdp_file']}"
                output_callback(msg)
                logging.info(msg)
                subprocess.Popen(f'mstsc "{cfg_rdp["rdp_file"]}"', shell=True)
            else:
                output_callback("Connessione non riuscita. RDP non avviato.")

# GUI
class ConnessioneGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("VPN RSC (Remote Scalable Connections)")
#        self.root.geometry("624x644")
        self.root.geometry("675x675")

        self.configs = carica_configurazioni()
        self.impianto_selezionato = tk.StringVar()
        self.rdp_selezionato = tk.StringVar()

        self.label_impianto = tk.Label(root, text="", font=("Arial", 14, "bold"), fg="blue")
        self.label_impianto.pack(pady=4)

        tk.Label(root, text="Seleziona impianto:", font=("Arial", 12)).pack(pady=5)
        impianti = sorted([cfg.get("impianto", "[non definito]") for cfg in self.configs])
        self.combo_impianti = ttk.Combobox(root, textvariable=self.impianto_selezionato, state="readonly",
                                           values=impianti, width=60)
        self.combo_impianti.pack(pady=5)
        self.combo_impianti.bind("<<ComboboxSelected>>", self.aggiorna_rdp)

        tk.Label(root, text="Seleziona collegamento RDP:", font=("Arial", 11)).pack()
        self.combo_rdp = ttk.Combobox(root, textvariable=self.rdp_selezionato, state="readonly", width=60)
        self.combo_rdp.pack(pady=5)

        self.bottone = tk.Button(root, text="Connetti", command=self.avvia_connessione)
        self.bottone.pack(pady=10)

        # visualizzazione del campo informazioni
        # self.memo_box = tk.Text(root, height=6, width=86, wrap=tk.WORD, font=("Arial", 10), foreground="green", bg="black")
        # self.memo_box.pack(pady=10)
        # self.memo_box.configure(state="disabled")

        memo_frame = tk.Frame(root)
        memo_frame.pack(pady=5)

#        self.memo_box = tk.Text(memo_frame, height=8, width=86, wrap=tk.WORD, font=("Arial", 10), foreground="green", bg="black")
        self.memo_box = tk.Text(
            memo_frame,
            height=8,
            width=86,
            wrap=tk.WORD,
            font=("Arial", 10),
            foreground="#00FF00",  # oppure "#39FF14"
            bg="black"
        )

        scrollbar = tk.Scrollbar(memo_frame, command=self.memo_box.yview)
        self.memo_box.configure(yscrollcommand=scrollbar.set)

        self.memo_box.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.memo_box.configure(state="disabled")

        self.output = tk.Text(root, height=17, width=80, state="disabled")
        self.output.pack(pady=10)

        # Definizione stili log
        self.output.tag_config("INFO", foreground="black")
        self.output.tag_config("OK", foreground="green")
        self.output.tag_config("WARNING", foreground="orange")
        self.output.tag_config("ERROR", foreground="red")
        self.output.tag_config("DEBUG", foreground="blue")

        self.footer_label = tk.Label(root, text=f"gui-connect-wlog v{APP_VERSION}", font=("Arial", 8), fg="gray")
        self.footer_label.pack(side="bottom", pady=5)

    def stampa_output(self, testo):
        self.output.configure(state="normal")

        # Determina il tag da usare in base al testo
        if not testo:
            return

        match testo:
            case _ if "[ERRORE]" in testo or "[ERROR]" in testo:
                tag = "ERROR"
            case _ if "[WARNING]" in testo:
                tag = "WARNING"
            case _ if "[OK]" in testo:
                tag = "OK"
            case _ if "[DEBUG]" in testo:
                tag = "DEBUG"
            case _:
                tag = "INFO"

        self.output.insert(tk.END, testo + "\n", tag)
        self.output.see(tk.END)
        self.output.configure(state="disabled")

    def aggiorna_rdp(self, event=None):
        nome_impianto = self.impianto_selezionato.get()
        # visualizza il nome dell'impianto selezionato
        if not nome_impianto:
            self.label_impianto.config(text="Nessun impianto selezionato")
            self.combo_rdp['values'] = []
            return
        self.label_impianto.config(text=f"{nome_impianto}")

        impianto_cfg = next((c for c in self.configs if c.get("impianto") == nome_impianto), None)
        if not impianto_cfg:
            self.combo_rdp['values'] = []
            return

        rdp_nomi = [rdp["rdp_nome"] for rdp in impianto_cfg.get("rdp_list", [])]
        self.combo_rdp['values'] = rdp_nomi
        self.combo_rdp.set('')

        memo = impianto_cfg.get("memo", "")
        self.memo_box.configure(state="normal")
        self.memo_box.delete("1.0", tk.END)
        self.memo_box.insert(tk.END, memo)
        self.memo_box.configure(state="disabled")

    # def avvia_connessione(self):
    #     impianto = self.impianto_selezionato.get()
    #     rdp_nome = self.rdp_selezionato.get()
    #     if not impianto or not rdp_nome:
    #         messagebox.showwarning("Attenzione", "Seleziona impianto e RDP.")
    #         return

    #     impianto_cfg = next((c for c in self.configs if c.get("impianto") == impianto), None)
    #     rdp_cfg = next((r for r in impianto_cfg.get("rdp_list", []) if r["rdp_nome"] == rdp_nome), None)

    #     if not impianto_cfg or not rdp_cfg:
    #         self.stampa_output("[ERRORE] Configurazione mancante.")
    #         return

    #     threading.Thread(target=connetti, args=(impianto_cfg, rdp_cfg, self.stampa_output), daemon=True).start()


    def avvia_connessione(self):
        impianto = self.impianto_selezionato.get()
        rdp_nome = self.rdp_selezionato.get()

        if not impianto:
            messagebox.showwarning("Attenzione", "Seleziona un impianto.")
            return

        impianto_cfg = next((c for c in self.configs if c.get("impianto") == impianto), None)

        if not impianto_cfg:
            self.stampa_output("[ERRORE] Configurazione impianto mancante.")
            return

        # Se non ci sono rdp da selezionare, avvia solo la VPN
        if not impianto_cfg.get("rdp_list"):
            self.stampa_output("[INFO] Nessun collegamento RDP configurato. Avvio sola connessione VPN.")
            threading.Thread(target=connetti, args=(impianto_cfg, {"rdp_nome": "-", "rdp_file": "", "rdp_ip": "127.0.0.1"}, self.stampa_output), daemon=True).start()
            return

        if not rdp_nome:
            messagebox.showwarning("Attenzione", "Seleziona un collegamento RDP.")
            return

        rdp_cfg = next((r for r in impianto_cfg.get("rdp_list", []) if r["rdp_nome"] == rdp_nome), None)

        if not rdp_cfg:
            self.stampa_output("[ERRORE] Configurazione RDP mancante.")
            return

        threading.Thread(target=connetti, args=(impianto_cfg, rdp_cfg, self.stampa_output), daemon=True).start()

# Avvio
if __name__ == "__main__":
    root = tk.Tk()
    app = ConnessioneGUI(root)
    root.mainloop()
