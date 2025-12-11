import socket
from flask import Flask, jsonify, request, Response
import threading
import time
import traceback

# --- Konfiguracija ---
HOST = "192.168.65.102"  # Poslušaj na vseh vmesnikih
TCP_PORT = 50000  # Vrata za komunikacijo z robotom
FLASK_PORT = 5000  # Vrata za REST API
REFRESH_INTERVAL = 5 # Sekunde za avtomatsko osveževanje spletne strani

# Stanja škatle (Ključi so sporočila, ki jih mora poslati robot)
STANJA_SKATLE = {
    "PRISPELA": "Prispela škatla",
    "ODPRAVLJENA": "Odpravljena škatla",
    "ZAKLENJENA": "Zaklenjena škatla",
    "ODKLENJENA": "Odklenjena škatla",
    "ODPRTA": "Odprta škatla",
    "ZAPRTA": "Zaprta škatla"
}

# --- Globalne spremenljivke in Locki ---
trenutno_stanje = "NI_PODATKOV_ROBOT_SE_NI_POVEZAL"
stanje_lock = threading.Lock()

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
    try:
        # Varno preberi podatke
        with zgodovina_lock:
            history = list(zgodovina_akcij) 
        
        with stanje_lock:
            current_status = trenutno_stanje
            
        # Sestavljanje HTML
        html_table = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <title>Stanje Robota UR5: Zgodovina Akcij</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f7f6; }}
                h1 {{ color: #004d99; border-bottom: 2px solid #004d99; padding-bottom: 10px; }}
                h2 {{ color: #333; }}
                table {{ width: 75%; border-collapse: collapse; margin-top: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); background-color: white;}}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #cce6ff; color: #333; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .status-ok {{ color: #28a745; font-weight: bold; font-size: 1.1em; }}
                .refresh {{ margin-top: 20px; font-style: italic; color: #6c757d;}}
            </style>
            <meta http-equiv="refresh" content="{REFRESH_INTERVAL}"> 
        </head>
        <body>
            <h1>📦 UR5 Nadzorna Plošča in Zgodovina Stanja</h1>
            <h2>Trenutno stanje: <span class="status-ok">{current_status}</span></h2>
            
            <table>
                <thead>
                    <tr>
                        <th>Čas Dejanja</th>
                        <th>Stanje Škatle</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        # Dodaj vrstice v tabelo (od najnovejše proti najstarejši)
        for cas, stanje in reversed(history):
            html_table += f"<tr><td>{cas}</td><td>{stanje}</td></tr>"
            
        html_table += f"""
                </tbody>
            </table>
            <p class="refresh">Stran se samodejno osveži vsakih {REFRESH_INTERVAL} sekund.</p>
        </body>
        </html>
        """
        
        return Response(html_table, mimetype='text/html; charset=utf-8')

    except Exception as e:
        # Poročanje o napaki, če sestavljanje HTML-ja ne uspe
        error_trace = traceback.format_exc()
        print(f"❌ KRITIČNA NAPAKA pri sestavljanju HTML: {e}")
        
        error_html = f"""
        <h1>Internal Server Error (500) pri /zgodovina</h1>
        <p>Prišlo je do napake pri generiranju HTML tabele. Preverite konzolo strežnika za podrobnosti.</p>
        <pre>{error_trace}</pre>
        """
        return Response(error_html, status=500, mimetype='text/html; charset=utf-8')

# --- TCP/IP Strežnik (Sprejemanje podatkov od robota) ---

def tcp_server_thread():
    """Zažene TCP/IP strežnik za sprejemanje podatkov od robota in beleženje zgodovine."""
    global trenutno_stanje
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind((HOST, TCP_PORT))
            s.listen()
            print(f"🤖 TCP/IP Strežnik čaka na povezavo robota na vratih {TCP_PORT}...")
        except Exception as e:
            print(f"FATALNA NAPAKA: Ne morem zagnati TCP strežnika na vratih {TCP_PORT}. Napaka: {e}")
            return # Izhod iz niti
        
        while True:
            try:
                conn, addr = s.accept()
                print(f"Povezava vzpostavljena od: {addr}")
                
                with conn:
                    while True:
                        # Prejmi podatke (npr. 1024 bajtov)
                        data = conn.recv(1024)
                        if not data:
                            print(f"Povezava z {addr} prekinjena.")
                            break
                        
                        # Dekodiranje in čiščenje prejetih podatkov (String, kot v vaši kodi)
                        sporocilo = data.decode('utf-8').strip()
                        
                        # Preveri, ali je prejeto sporočilo veljavno stanje
                        if sporocilo in STANJA_SKATLE:
                            novo_stanje = STANJA_SKATLE[sporocilo]
                            trenutni_cas = time.strftime("%Y-%m-%d %H:%M:%S")
                            
                            # POSODOBI TRENUTNO STANJE IN ZGODOVINO Z LOCKOM
                            with stanje_lock:
                                trenutno_stanje = novo_stanje
                                
                            with zgodovina_lock:
                                # Dodaj novo dejanje v zgodovino
                                zgodovina_akcij.append((trenutni_cas, novo_stanje))
                                
                            print(f"✅ NOVO STANJE: {trenutno_stanje} (Sporočilo: '{sporocilo}') ob {trenutni_cas}")
                        else:
                            print(f"⚠️ Neveljavno sporočilo od robota: '{sporocilo}'")
                        
                        # Pošlji potrdilo nazaj robotu
                        conn.sendall(b"OK")
                        
            except Exception as e:
                print(f"Napaka v TCP/IP strežniku (med povezavo): {e}")
                time.sleep(1)

# --- Zagon aplikacije ---

if __name__ == '__main__':
    # Poskusimo dobiti LAN IP za izpis
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1" 
        
    # Inicializiraj zgodovino z začetnim stanjem
    with zgodovina_lock:
        zgodovina_akcij.append((time.strftime("%Y-%m-%d %H:%M:%S"), trenutno_stanje))

    # 1. Zaženi TCP/IP strežnik v ločeni niti
    tcp_thread = threading.Thread(target=tcp_server_thread)
    tcp_thread.daemon = True
    tcp_thread.start()
    
    # 2. Zaženi REST API strežnik
    print(f"\n{'='*50}")
    print(f"🤖 STREŽNIK ZA ROBOTA ZAGNAN")
    print(f"  - TCP Poslušanje na vratih: {TCP_PORT}")
    print(f"  - Za ogled ZGODOVINE odpri: http://{local_ip}:{FLASK_PORT}/zgodovina")
    print(f"{'='*50}\n")
    
    app.run(host='0.0.0.0', port=FLASK_PORT)
