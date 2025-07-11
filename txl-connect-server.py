import subprocess
import json
import time
import os
import sys
import logging

# Imposta logging su file
logging.basicConfig(
    filename='log-connessione.txt',
    level=logging.DEBUG,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

def carica_config(cliente_nome):
    with open("connessioni-vpn.json", "r") as f:
        config = json.load(f)
    for cliente in config:
        if cliente["nome_cliente"].lower() == cliente_nome.lower():
            return cliente
    return None

def avvia_vpn(percorso, argomenti):
    comando = f'"{percorso}" {argomenti}'
    print(f"[INFO] Avvio VPN: {comando}")
    subprocess.Popen(comando, shell=True)

def verifica_connessione(ip, tentativi=5, pausa=3):
    for i in range(tentativi):
        print(f"[INFO] Verifica connessione a {ip} (tentativo {i+1})...")
        risultato = subprocess.run(["ping", "-n", "1", ip], stdout=subprocess.DEVNULL)
        if risultato.returncode == 0:
            print("[OK] Connessione stabilita.")
            return True
        time.sleep(pausa)
    print("[ERRORE] Timeout nella connessione VPN.")
    return False

def avvia_rdp(percorso_rdp):
    print(f"[INFO] Avvio RDP con file: {percorso_rdp}")
    subprocess.Popen(f'mstsc "{percorso_rdp}"', shell=True)

def main():
    logging.info("Avvio script")

    if len(sys.argv) != 2:
        logging.error("Numero di argomenti errato. Uso corretto: python script.py <nome_config>")
        print("Uso: python connetti_cliente.py <nome_cliente>")
        return

    cliente_nome = sys.argv[1]
    config = carica_config(cliente_nome)
    logging.info(f"Parametro ricevuto: {config}")

    if not config:
        print(f"[ERRORE] Cliente '{cliente_nome}' non trovato.")
        return

    avvia_vpn(config["vpn_exe"], config.get("vpn_argomenti", []))
    if verifica_connessione(config["test_ping"]):
        avvia_rdp(config["rdp_file"])

if __name__ == "__main__":
    main()
