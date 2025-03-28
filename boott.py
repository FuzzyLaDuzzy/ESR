import socket
import pickle
import threading

#Map with neighbours
neighbours = {
    'server' : ['10.0.16.1', '10.0.17.1'],
    'n1': ['10.0.0.20','10.0.1.20','10.0.7.1','10.0.5.1'],
    'n2': [ '10.0.5.2', '10.0.3.2',  '10.0.4.2','10.0.6.1'],
    'n3': ['10.0.8.2', '10.0.7.2','10.0.6.2','10.0.9.2'],
    'n4': [ '10.0.10.2', '10.0.4.1','10.0.5.2','10.0.11.2'],
    'n5': [ '10.0.8.1', '10.0.26.1'],
    'n6': [ '10.0.12.2', '10.0.11.1'],
    'n7': [ '10.0.25.1', '10.0.24.1', '10.0.9.1','10.0.10.1','10.0.13.1'],
    'n8': [ '10.0.23.1', '10.0.24.2',],
    'n9': ['10.0.21.1', '10.0.26.2','10.0.22.2','10.0.25.2'],
    'n10': ['10.0.15.2', '10.0.12.1',  '10.0.14.2','10.0.13.2'],
    'n11': ['10.0.20.1', '10.0.21.2'],
    'n12': ['10.0.19.1', '10.0.17.10', '10.0.20.2'],
    'n13': ['10.0.18.2', '10.0.16.10', '10.0.15.1'],
    'n14': ['10.0.19.2', '10.0.18.1', '10.0.14.1', '10.0.23.2', '10.0.22.1'],
    'n15': ['10.0.16.1', '10.0.17.1'],
    'n16': ['10.0.0.20', '10.0.0.1'],  
    'n17': ['10.0.1.20', '10.0.1.1'],
    'n18': ['10.0.2.20', '10.0.2.1'],
    'n19': ['10.0.3.20', '10.0.3.1']
    
}

class Bootstrapper:
    def __init__(self):
        # Create socket
        bootstrapper = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        bootstrapper.bind(('0.0.0.0', 5000))

        print('Bootstrapper listening for connections!')
        try:
            while True:
                bootstrapper.listen()
                conn, addr = bootstrapper.accept()
                threading.Thread(target= self.handler, args=(conn, addr)).start()
        finally:
            bootstrapper.close()

    # Bootstrapper connection handler
    def handler(self, connection, address):
        ip = str(address[0])
        print(f"[INFO] {ip} connection started.")

        data = connection.recv(1024).decode('utf-8')

        if data.startswith('NEIGHBOURS'):

            # Return node neighbours
            _, node_id = data.split()
            response = pickle.dumps(neighbours[node_id])

        connection.send(response)
        print(f"Response sent to {ip}.")

        connection.close()
        print(f"{ip} connection closed.")

if __name__ == "__main__":
    bootstrapper = Bootstrapper()