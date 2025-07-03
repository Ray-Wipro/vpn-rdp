import subprocess
import json
import time
import os
import logging

# Imposta logging su file
logging.basicConfig(
    filename='log-connessione.txt',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def carica_configurazioni():
    with open("connessioni-vpn.json", "r") as f:
        return json.load(f)

def seleziona_cliente(configs):
    print("\nSeleziona una connessione:")
    for i, cfg in enumerate(configs, 1):
        print(f"{i}. {cfg['nome_cliente']}")
    
    while True:
        try:
            scelta = int(input("\nNumero della connessione: "))
            if 1 <= scelta <= len(configs):
                return configs[scelta - 1]
        except ValueError:
            pass
        print("Scelta non valida. Riprova.")

def avvia_vpn(percorso, argomenti):
    comando = f'"{percorso}" {argomenti}'
    print(f"[INFO] Avvio VPN: {comando}")
    logging.info(f"Avvio VPN: {comando}")
    subprocess.Popen(comando, shell=True)

def verifica_connessione(ip, tentativi=5, pausa=7):
    for i in range(tentativi):
        msg = f"Verifica connessione a {ip} (tentativo {i+1})..."
        print(f"[INFO] {msg}")
        logging.info(msg)
        risultato = subprocess.run(["ping", "-n", "1", ip], stdout=subprocess.DEVNULL)
        if risultato.returncode == 0:
            print("[OK] Connessione stabilita.")
            logging.info("Connessione VPN stabilita.")
            return True
        time.sleep(pausa)
    print("[ERRORE] Timeout nella connessione VPN.")
    logging.error("Connessione VPN non riuscita.")
    return False

def avvia_rdp(percorso_rdp):
    print(f"[INFO] Avvio RDP con file: {percorso_rdp}")
    logging.info(f"Avvio RDP con file: {percorso_rdp}")
    subprocess.Popen(f'mstsc "{percorso_rdp}"', shell=True)

def main():
    logging.info("Avvio script interattivo")
    
    configs = carica_configurazioni()
    cliente = seleziona_cliente(configs)
    logging.info(f"Cliente selezionato: {cliente['nome_cliente']}")

    avvia_vpn(cliente["vpn_exe"], cliente.get("vpn_argomenti", ""))
    if verifica_connessione(cliente["test_ping"]):
        avvia_rdp(cliente["rdp_file"])

if __name__ == "__main__":
    main()
