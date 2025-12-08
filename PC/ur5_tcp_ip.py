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


	try:
		### STRING ###
		# send string "ack"
		input("Press Enter to send string...")
		send_string = "ack"
		conn.send(send_string.encode("ascii"))
		time.sleep(0.5)
		
		#for i in range(10):
		#	print("ACK send")

		# read string
		data = conn.recv(1024)
		print(f"Client: {data.decode('ascii')}")

		### INTEGER ###
		# send one integer
		input("Press Enter to send int...")
		send_int = 7
		data = struct.pack('>i', send_int)
		conn.send(data)
		print("int send")

		# receive one integer
		data = conn.recv(1024)
		number = struct.unpack(">i", data)
		print("Client: ", str(number[0]))

	except Exception as e:
		print("\n\nKI, exiting client handler")
	

	# while thread_running:
	# 	data = conn.recv(1024)
	# 	if not data:
	# 		break
	# 	number = struct.unpack("i", data)
	# 	print("Received", str(number), "from", addr)
		



if __name__ == "__main__":
	main()
