import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import time
import threading
import logging
import sys

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
    metodo = cfg.get("vpn_metodo", "forticlient")
    output(f"[VPN] Metodo: {metodo}")

    if metodo == "forticlient":
        exe = cfg["vpn_exe"]
        args = " ".join(cfg.get("vpn_argomenti", []))
        subprocess.Popen(f'"{exe}" {args}', shell=True)
    elif metodo == "netcli":
        exe = r"C:\\Program Files\\SonicWall\\SSL-VPN\\NetExtender\\NETCLI.exe"
        cmd = [exe, "connect",
               "-s", cfg["vpn_server"],
               "-u", cfg["vpn_user"],
               "-p", cfg["vpn_pass"],
               "-d", cfg["vpn_domain"]]
        subprocess.Popen(cmd)
    else:
        output(f"[ERRORE] Metodo VPN non riconosciuto: {metodo}")

# Connessione completa

def connetti(cfg_impianto, cfg_rdp, output_callback):
    output_callback(f"Avvio connessione per {cfg_rdp['nome_cliente']}")
    avvia_vpn(cfg_impianto, output_callback)

    tentativi = cfg_impianto.get("vpn_tentativi", 5)
    pausa = cfg_impianto.get("vpn_pausa", 7)

    if verifica_connessione(cfg_rdp["test_ping"], tentativi=tentativi, pausa=pausa, output=output_callback):
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
        self.root.title("Connessione Remota Scalabile")
        self.root.geometry("580x600")

        self.configs = carica_configurazioni()
        self.impianto_selezionato = tk.StringVar()
        self.rdp_selezionato = tk.StringVar()

        tk.Label(root, text="Seleziona impianto:", font=("Arial", 12)).pack(pady=5)
        impianti = [cfg["impianto"] for cfg in self.configs]
        self.combo_impianti = ttk.Combobox(root, textvariable=self.impianto_selezionato, state="readonly",
                                           values=impianti)
        self.combo_impianti.pack(pady=5)
        self.combo_impianti.bind("<<ComboboxSelected>>", self.aggiorna_rdp)

        self.label_impianto = tk.Label(root, text="", font=("Arial", 11, "bold"), fg="blue")
        self.label_impianto.pack(pady=5)

        tk.Label(root, text="Seleziona collegamento RDP:", font=("Arial", 11)).pack()
        self.combo_rdp = ttk.Combobox(root, textvariable=self.rdp_selezionato, state="readonly")
        self.combo_rdp.pack(pady=5)

        self.bottone = tk.Button(root, text="Connetti", command=self.avvia_connessione)
        self.bottone.pack(pady=10)

        tk.Label(root, text="Memo:", font=("Arial", 10, "bold")).pack()
        self.memo_box = tk.Text(root, height=6, width=70)
        self.memo_box.pack(pady=5)
        self.memo_box.configure(state="disabled")

        self.output = tk.Text(root, height=10, width=70, state="disabled")
        self.output.pack(pady=10)

    def stampa_output(self, testo):
        self.output.configure(state="normal")
        self.output.insert(tk.END, testo + "\n")
        self.output.see(tk.END)
        self.output.configure(state="disabled")

    def aggiorna_rdp(self, event=None):
        nome_impianto = self.impianto_selezionato.get()
        self.label_impianto.config(text=f"Impianto selezionato: {nome_impianto}")

        impianto_cfg = next((c for c in self.configs if c["impianto"] == nome_impianto), None)
        if not impianto_cfg:
            self.combo_rdp['values'] = []
            return

        rdp_nomi = [rdp["nome_cliente"] for rdp in impianto_cfg.get("rdp_list", [])]
        self.combo_rdp['values'] = rdp_nomi
        self.combo_rdp.set('')

        memo = impianto_cfg.get("memo", "")
        self.memo_box.configure(state="normal")
        self.memo_box.delete("1.0", tk.END)
        self.memo_box.insert(tk.END, memo)
        self.memo_box.configure(state="disabled")

    def avvia_connessione(self):
        impianto = self.impianto_selezionato.get()
        rdp_nome = self.rdp_selezionato.get()
        if not impianto or not rdp_nome:
            messagebox.showwarning("Attenzione", "Seleziona impianto e RDP.")
            return

        impianto_cfg = next((c for c in self.configs if c["impianto"] == impianto), None)
        rdp_cfg = next((r for r in impianto_cfg.get("rdp_list", []) if r["nome_cliente"] == rdp_nome), None)

        if not impianto_cfg or not rdp_cfg:
            self.stampa_output("[ERRORE] Configurazione mancante.")
            return

        threading.Thread(target=connetti, args=(impianto_cfg, rdp_cfg, self.stampa_output), daemon=True).start()

# Avvio
if __name__ == "__main__":
    root = tk.Tk()
    app = ConnessioneGUI(root)
    root.mainloop()