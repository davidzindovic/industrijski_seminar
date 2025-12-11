#
# TCP/IP communication with UR robot
#
# authors: 	Sebastjan Slajpah, sebastjan.slajpah@fe.uni-lj.si
# 		Peter Kmecl, peterk.kmecl@fe.uni-lj.si
#
#			2024 @ robolab
#			www.robolab.si
#

import socket, struct, time, threading

###Config###
ip = "192.168.65.102"
port = 50000

###globals###
global thread_running, thread_list, conn_list
thread_running = True
thread_list = []
conn_list = []


def main():
	try:
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		s.bind((ip, port))
		s.settimeout(1)
		s.listen()
		while True:
			try:
				conn, addr = s.accept()
				print(addr)
				conn_list.append(conn)
				t = threading.Thread(target=client_handler, args=(conn, addr, ))
				t.start()
				thread_list.append(t)
				print("Connected to by", addr, "!")
			except TimeoutError as e:
				pass
	except KeyboardInterrupt as e:
		print("KI, exiting main")
	finally:
		for c in conn_list:
			c.close()
		thread_running = False
		


def client_handler(conn, addr):
    global thread_running
    
    # Dodamo zanko za neprekinjeno branje sporočil
    while thread_running: 
        try:
            # Preberi podatke
            data = conn.recv(1024)
            
            # Preveri, če je povezava prekinjena (prazni podatki)
            if not data:
                print(f"Povezava z {addr} prekinjena.")
                break # Izhod iz zanke
            
            print(f"Client ({addr}): {data.decode('ascii')}")
            
        except ConnectionResetError:
            # Obravnava izgube povezave (npr. robot prekine povezavo)
            print(f"Povezava z {addr} resetirana.")
            break
        except Exception as e:
            # Splošna obravnava napak
            if thread_running:
                 print(f"Napaka v client_handlerju za {addr}: {e}")
            break
    
    # Zapri povezavo, ko se zanka konča
    try:
        conn.close()
    except:
        pass 
    
    print(f"Izhod iz client_handlerja za {addr}.")
		



if __name__ == "__main__":
	main()
