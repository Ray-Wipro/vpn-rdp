import tkinter as tk
from tkinter import ttk, messagebox
import subprocess
import json
import time
import threading
import logging

# Logging su file
logging.basicConfig(
    filename='log-connessione.txt',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# Carica configurazioni
def carica_configurazioni():
    with open("connessioni-vpn.json", "r") as f:
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

# Avvia connessione
def connetti(cliente, output_callback):
    logging.info(f"Avvio connessione per {cliente['nome_cliente']}")
    output_callback(f"Avvio VPN per {cliente['nome_cliente']}")

    comando = f'"{cliente["vpn_exe"]}" {cliente.get("vpn_argomenti", "")}'
    logging.info(f"Esecuzione: {comando}")
    subprocess.Popen(comando, shell=True)

    if verifica_connessione(cliente["test_ping"], output=output_callback):
        msg = f"Avvio RDP: {cliente['rdp_file']}"
        output_callback(msg)
        logging.info(msg)
        subprocess.Popen(f'mstsc "{cliente["rdp_file"]}"', shell=True)
    else:
        output_callback("Connessione non riuscita. RDP non avviato.")

# GUI principale
class ConnessioneGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Connessione Remota")
        self.root.geometry("400x300")

        self.configs = carica_configurazioni()
        self.cliente_selezionato = tk.StringVar()

        tk.Label(root, text="Seleziona il cliente:", font=("Arial", 12)).pack(pady=10)
        self.combo = ttk.Combobox(root, textvariable=self.cliente_selezionato, state="readonly",
                                  values=[cfg["nome_cliente"] for cfg in self.configs])
        self.combo.pack(pady=5)

        self.bottone = tk.Button(root, text="Connetti", command=self.avvia_connessione)
        self.bottone.pack(pady=10)

        self.output = tk.Text(root, height=10, width=45, state="disabled")
        self.output.pack(pady=10)

    def stampa_output(self, testo):
        self.output.configure(state="normal")
        self.output.insert(tk.END, testo + "\n")
        self.output.see(tk.END)
        self.output.configure(state="disabled")

    def avvia_connessione(self):
        nome = self.cliente_selezionato.get()
        if not nome:
            messagebox.showwarning("Attenzione", "Seleziona un cliente.")
            return

        cliente = next((c for c in self.configs if c["nome_cliente"] == nome), None)
        if not cliente:
            self.stampa_output(f"[ERRORE] Configurazione non trovata per {nome}")
            return

        threading.Thread(target=connetti, args=(cliente, self.stampa_output), daemon=True).start()

# Avvia app
if __name__ == "__main__":
    root = tk.Tk()
    app = ConnessioneGUI(root)
    root.mainloop()
