import socket
from flask import Flask, jsonify, request
import threading
import time

# --- Konfiguracija ---
HOST = '0.0.0.0'
TCP_PORT = 30002
FLASK_PORT = 5000

# Stanja škatle
STANJA_SKATLE = {
    "PRISPELO": "Prispelo",
    "ODPRAVLJENO": "Odpravljeno",
    "ZAKLENJENA": "Zaklenjena",
    "ODKLENJENA": "Odklenjena"
}

# Trenutno stanje škatle
trenutno_stanje = "NI_PODATKOV"
stanje_lock = threading.Lock()

# 🆕 Zgodovina akcij (stanje, cas)
zgodovina_akcij = []
zgodovina_lock = threading.Lock()

# --- REST API Strežnik (Flask) ---
app = Flask(__name__)

@app.route('/stanje', methods=['GET'])
def get_stanje():
    """Vrne trenutno stanje škatle (JSON)."""
    with stanje_lock:
        status = trenutno_stanje
    return jsonify({
        "status": "OK",
        "stanje_skatle": status,
        "cas_prejema": time.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/zgodovina', methods=['GET'])
def get_zgodovina():
    """Vrne zgodovino akcij v HTML formatu (tabela)."""
    with zgodovina_lock:
        history = list(zgodovina_akcij) # Kopija za varno branje
        
    html_table = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Zgodovina Akcij Škatle</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; }
            h1 { color: #333; }
            table { width: 60%; border-collapse: collapse; margin-top: 20px; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: left; }
            th { background-color: #f2f2f2; }
            .status-ok { color: green; font-weight: bold; }
            .status-warning { color: orange; }
            .refresh { margin-top: 15px; }
        </style>
        <meta http-equiv="refresh" content="5"> </head>
    <body>
        <h1>📦 Zgodovina Stanja Škatle</h1>
        <p class="status-ok">Trenutno stanje: <strong>{}</strong></p>
        
        <table>
            <thead>
                <tr>
                    <th>Čas Dejanja</th>
                    <th>Stanje Škatle</th>
                </tr>
            </thead>
            <tbody>
    """.format(trenutno_stanje) # Dodaj trenutno stanje v glavo
    
    # Dodaj vrstice v tabelo (od najnovejše proti najstarejši)
    for cas, stanje in reversed(history):
        html_table += f"<tr><td>{cas}</td><td>{stanje}</td></tr>"
        
    html_table += """
            </tbody>
        </table>
        <p class="refresh">Stran se samodejno osveži vsakih 5 sekund.</p>
    </body>
    </html>
    """
    return html_table

def run_flask_server():
    """Zažene Flask strežnik v ločeni niti."""
    local_ip = socket.gethostbyname(socket.gethostname())
    print(f"🌍 REST API Strežnik zagnan:")
    print(f"  - Trenutno stanje (JSON): http://{local_ip}:{FLASK_PORT}/stanje")
    print(f"  - **Zgodovina (HTML): http://{local_ip}:{FLASK_PORT}/zgodovina**")
    app.run(host='0.0.0.0', port=FLASK_PORT)

# --- TCP/IP Strežnik (Sprejemanje podatkov od robota) ---

def tcp_server_thread():
    """Zažene TCP/IP strežnik za sprejemanje podatkov od robota."""
    global trenutno_stanje
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind((HOST, TCP_PORT))
        s.listen()
        print(f"🤖 TCP/IP Strežnik čaka na povezavo robota na vratih {TCP_PORT}...")
        
        while True:
            try:
                conn, addr = s.accept()
                print(f"Povezava vzpostavljena od: {addr}")
                
                with conn:
                    while True:
                        data = conn.recv(1024)
                        if not data:
                            print(f"Povezava z {addr} prekinjena.")
                            break
                        
                        sporocilo = data.decode('utf-8').strip()
                        
                        if sporocilo in STANJA_SKATLE:
                            novo_stanje = STANJA_SKATLE[sporocilo]
                            trenutni_cas = time.strftime("%Y-%m-%d %H:%M:%S")
                            
                            # 🔒 Posodobi trenutno stanje in zgodovino z lockom
                            with stanje_lock:
                                trenutno_stanje = novo_stanje
                                
                            with zgodovina_lock:
                                # Dodaj novo dejanje v zgodovino
                                zgodovina_akcij.append((trenutni_cas, novo_stanje))
                                
                            print(f"✅ NOVO STANJE: {trenutno_stanje} ob {trenutni_cas}")
                        else:
                            print(f"⚠️ Neveljavno sporočilo od robota: '{sporocilo}'")
                        
                        conn.sendall(b"OK")
                        
            except Exception as e:
                print(f"Napaka v TCP/IP strežniku: {e}")
                time.sleep(1)

# --- Zagon aplikacije ---

if __name__ == '__main__':
    # 1. Zaženi TCP/IP strežnik v ločeni niti
    tcp_thread = threading.Thread(target=tcp_server_thread)
    tcp_thread.daemon = True
    tcp_thread.start()
    
    # 2. Zaženi REST API strežnik (ta nit blokira)
    run_flask_server()
