import socket
from flask import Flask, jsonify, request, Response # Uvozimo Response
import threading
import time
import random
import traceback # Uvozimo za boljši izpis napak

# --- Konfiguracija ---
FLASK_PORT = 5000
SIMULATION_INTERVAL = 4 

# Stanja škatle
STANJA_SKATLE = {
    "PRISPELO": "Prispelo",
    "ODPRAVLJENO": "Odpravljeno",
    "ZAKLENJENA": "Zaklenjena",
    "ODKLENJENA": "Odklenjena"
}
KLJUCI_STANJ = list(STANJA_SKATLE.keys())

# --- Globalne spremenljivke in Locki ---
trenutno_stanje = "ZAGON_SIMULACIJE"
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
    """Vrne zgodovino akcij v HTML formatu (tabela).
       Dodana robustna obravnava napak in kodiranje.
    """
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
            <meta charset="UTF-8"> <title>SIMULACIJA: Zgodovina Akcij Škatle</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f4f7f6; }}
                h1 {{ color: #0056b3; border-bottom: 2px solid #0056b3; padding-bottom: 10px; }}
                h2 {{ color: #333; }}
                table {{ width: 75%; border-collapse: collapse; margin-top: 25px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); background-color: white;}}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #e6f7ff; color: #333; font-weight: bold; }}
                tr:nth-child(even) {{ background-color: #f9f9f9; }}
                .status-ok {{ color: #28a745; font-weight: bold; font-size: 1.1em; }}
                .refresh {{ margin-top: 20px; font-style: italic; color: #6c757d;}}
            </style>
            <meta http-equiv="refresh" content="{SIMULATION_INTERVAL}"> 
        </head>
        <body>
            <h1>⚙️ SIMULACIJA Stanja Škatle</h1>
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
            <p class="refresh">Stran se samodejno osveži vsakih {SIMULATION_INTERVAL} sekund.</p>
        </body>
        </html>
        """
        
        # Vrne HTML z ustreznim Content-Type in kodiranjem
        return Response(html_table, mimetype='text/html; charset=utf-8')

    except Exception as e:
        # Če pride do napake, jo izpišemo v konzolo in jo prikažemo na strani
        error_trace = traceback.format_exc()
        print(f"❌ KRITIČNA NAPAKA pri sestavljanju HTML: {e}")
        print(error_trace)
        
        error_html = f"""
        <h1>Internal Server Error (500) pri /zgodovina</h1>
        <p>Prišlo je do napake pri generiranju HTML tabele. Preverite konzolo strežnika za podrobnosti.</p>
        <pre>{error_trace}</pre>
        """
        return Response(error_html, status=500, mimetype='text/html; charset=utf-8')

# --- Nit za simulacijo stanja ---

def simulation_thread():
    """Simulira prejemanje stanj vsakih SIMULATION_INTERVAL sekund."""
    global trenutno_stanje
    
    print(f"🔄 Zagon simulacije: novo stanje generirano vsakih {SIMULATION_INTERVAL} sekund.")
    
    # Dodaj začetno stanje v zgodovino ob zagonu
    with zgodovina_lock:
        zgodovina_akcij.append((time.strftime("%Y-%m-%d %H:%M:%S"), trenutno_stanje))
        
    while True:
        try:
            # 1. Izberi naključno stanje
            nakljucni_kljuc = random.choice(KLJUCI_STANJ)
            novo_stanje = STANJA_SKATLE[nakljucni_kljuc]
            trenutni_cas = time.strftime("%Y-%m-%d %H:%M:%S")
            
            # 2. Posodobi trenutno stanje in zgodovino
            with stanje_lock:
                trenutno_stanje = novo_stanje
                
            with zgodovina_lock:
                zgodovina_akcij.append((trenutni_cas, novo_stanje))
                
            print(f"✅ SIMULACIJA: Generirano NOVO STANJE: {trenutno_stanje} ob {trenutni_cas}")
            
            time.sleep(SIMULATION_INTERVAL)
            
        except Exception as e:
            print(f"❌ Napaka v simulacijski niti: {e}. Čakam 1 sekundo.")
            time.sleep(1)

# --- Zagon aplikacije ---

if __name__ == '__main__':
    # Poskusimo dobiti LAN IP
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        local_ip = s.getsockname()[0]
        s.close()
    except Exception:
        local_ip = "127.0.0.1" 

    # 1. Zaženi simulacijsko nit
    sim_thread = threading.Thread(target=simulation_thread)
    sim_thread.daemon = True
    sim_thread.start()
    
    # 2. Zaženi REST API strežnik
    print(f"\n{'='*50}")
    print(f"🤖 STREŽNIK ZA SIMULACIJO STANJA ZAGNAN")
    print(f"  - Za ogled ZGODOVINE odpri: http://{local_ip}:{FLASK_PORT}/zgodovina")
    print(f"{'='*50}\n")
    
    app.run(host='0.0.0.0', port=FLASK_PORT)
