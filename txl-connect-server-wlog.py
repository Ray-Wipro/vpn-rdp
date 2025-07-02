import subprocess
import json
import time
import os
import sys
import logging

# === CONFIGURAZIONE LOGGING ===
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Log su file
file_handler = logging.FileHandler('log-connessione.txt', mode='a', encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_format = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
file_handler.setFormatter(file_format)
logger.addHandler(file_handler)

# Log su console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_format = logging.Formatter('[%(levelname)s] %(message)s')
console_handler.setFormatter(console_format)
logger.addHandler(console_handler)


# === FUNZIONI ===

def carica_config(cliente_nome):
    try:
        with open("connessioni-vpn.json", "r", encoding="utf-8") as f:
            config_list = json.load(f)
    except Exception as e:
        logger.exception("Errore nel caricamento del file JSON")
        return None

    for cliente in config_list:
        if cliente.get("nome_cliente", "").lower() == cliente_nome.lower():
            return cliente

    logger.error(f"Cliente '{cliente_nome}' non trovato nel file JSON")
    return None


def avvia_vpn(percorso, argomenti):
    comando = [percorso] + argomenti
    try:
        logger.info(f"Avvio VPN: {' '.join(comando)}")
        subprocess.Popen(comando, shell=False)
    except Exception as e:
        logger.exception("Errore durante l'avvio della VPN")


def verifica_connessione(ip, tentativi=5, pausa=3):
    for i in range(tentativi):
        logger.info(f"Verifica connessione a {ip} (tentativo {i + 1})...")
        risultato = subprocess.run(["ping", "-n", "1", ip], stdout=subprocess.DEVNULL)
        if risultato.returncode == 0:
            logger.info("Connessione VPN attiva.")
            return True
        time.sleep(pausa)

    logger.error("Timeout nella connessione VPN.")
    return False


def avvia_rdp(percorso_rdp):
    try:
        logger.info(f"Avvio RDP con file: {percorso_rdp}")
        subprocess.Popen(['mstsc', percorso_rdp], shell=False)
    except Exception as e:
        logger.exception("Errore durante l'avvio del desktop remoto")


# === MAIN ===

""" def main():
    logger.info("Avvio script di connessione")

    if len(sys.argv) != 2:
        logger.error("Numero di argomenti errato. Uso: python script.py <nome_cliente>")
        print("Uso: python script.py <nome_cliente>")
        return

    cliente_nome = sys.argv[1]
    logger.info(f"Parametro ricevuto: {cliente_nome}")

    config = carica_config(cliente_nome)
    if not config:
        logger.error("Configurazione non trovata. Interruzione.")
        return

    avvia_vpn(config["vpn_exe"], config.get("vpn_argomenti", []))
    if verifica_connessione(config["test_ping"]):
        avvia_rdp(config["rdp_file"])
    else:
        logger.error("Connessione VPN non riuscita. RDP non avviato.")
 """

def main():
    logger.info("Avvio script di connessione")

    if len(sys.argv) != 2:
        logger.error("Numero di argomenti errato. Uso: python script.py <nome_cliente>")
        print("Uso: python script.py <nome_cliente>")
        return

    cliente_nome = sys.argv[1]
    logger.info(f"Parametro ricevuto: {cliente_nome}")

    config = carica_config(cliente_nome)
    if not config:
        logger.error("Configurazione non trovata. Interruzione.")
        return

    # Verifica preventiva: VPN già connessa?
    logger.info("Verifica preventiva connessione VPN...")
    if verifica_connessione(config["test_ping"]):
        logger.info("VPN già attiva. Procedo direttamente con RDP.")
        avvia_rdp(config["rdp_file"])
        return

    # VPN non attiva: apri FortiClient
    avvia_vpn(config["vpn_exe"], config.get("vpn_argomenti", []))
    input("[ATTENDERE] Premi Invio quando la VPN è connessa per procedere con la verifica...")

    if verifica_connessione(config["test_ping"]):
        avvia_rdp(config["rdp_file"])
    else:
        logger.error("Connessione VPN non riuscita. RDP non avviato.")

if __name__ == "__main__":
    main()
