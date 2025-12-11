import socket
from flask import Flask, jsonify, request
import threading
import time
import random

# --- Konfiguracija ---
HOST = '0.0.0.0'  # Poslušaj na vseh vmesnikih
TCP_PORT = 30002  # Vrata za komunikacijo z robotom (ali katera koli druga vrata)
FLASK_PORT = 5000  # Vrata za REST API

print_once=1

# Stanja škatle
STANJA_SKATLE = {
    "PRISPELO": "Prispelo",
    "ODPRAVLJENO": "Odpravljeno",
    "ZAKLENJENA": "Zaklenjena",
    "ODKLENJENA": "Odklenjena"
}

stanja=["PRISPELO","ODPRAVLJENO","ZAKLENJENA","ODKLENJENA"]

# Trenutno stanje škatle
trenutno_stanje = "NI_PODATKOV"
stanje_lock = threading.Lock()

# --- REST API Strežnik (Flask) ---
app = Flask(__name__)

@app.route('/stanje', methods=['GET'])
def get_stanje():
    """Vrne trenutno stanje škatle."""
    with stanje_lock:
        status = trenutno_stanje
    return jsonify({
        "status": "OK",
        "stanje_skatle": status,
        "cas_prejema": time.strftime("%Y-%m-%d %H:%M:%S")
    })

def run_flask_server():
    """Zažene Flask strežnik v ločeni niti."""
    print(f"🌍 REST API Strežnik zagnan na http://{socket.gethostbyname(socket.gethostname())}:{FLASK_PORT}/stanje")
    # Uporabljamo 0.0.0.0, da je dostopno z zunanjih naslovov
    app.run(host='0.0.0.0', port=FLASK_PORT)

# --- TCP/IP Strežnik (Sprejemanje podatkov od robota) ---

def tcp_server_thread():
    """Zažene TCP/IP strežnik za sprejemanje podatkov od robota."""
    global trenutno_stanje, print_once
    

        
    while True:
        try:
            if True:
                while True:

                    sporocilo=random.choice(stanja)

                    # Preveri, ali je prejeto sporočilo veljavno stanje
                    if sporocilo in STANJA_SKATLE:
                        with stanje_lock:
                            trenutno_stanje = STANJA_SKATLE[sporocilo]
                        
                        print(f"✅ NOVO STANJE: {trenutno_stanje}")
                    else:
                        print(f"⚠️ Neveljavno sporočilo od robota: '{sporocilo}'")

                    
        except Exception as e:
            print(f"Napaka v TCP/IP strežniku: {e}")
            time.sleep(1)

# --- Zagon aplikacije ---

if __name__ == '__main__':
    # 1. Zaženi TCP/IP strežnik v ločeni niti
    tcp_thread = threading.Thread(target=tcp_server_thread)
    tcp_thread.daemon = True # Nit se ustavi, ko se ustavi glavni program
    tcp_thread.start()
    
    while True:
        # 2. Zaženi REST API strežnik (ta nit blokira, zato mora biti zadnja)
        run_flask_server()
