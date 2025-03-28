import socket
import pickle
import sys
import threading
import time
import ast
from colorama import Back, Style

class Node:
    def __init__(self, name):
        self.timeout = 1

        # Node name
        self.name = name

        # List of neighbours
        self.neighbours = {}

        # Distribution Tree Information
        self.flow_current_flood = 0
        self.flow_latency = 999
        self.flow_jump = 999
        self.flow_parent = ''

        # List of streams
        # Key:stream & Value:list of clients (neighbours)
        self.streams = {}
        self.streams_list = []

        # Create server socket
        self.server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.server.bind(('0.0.0.0', 6000))

        # running
        self.get_neighbours_from_bootstrapper()
        #threading.Thread(target=self.keep_alive).start()
        threading.Thread(target=self.passthrough_streams).start()

        print(Back.BLUE + 'Node running.')
        try:
            while True:
                data, addr = self.server.recvfrom(1024)
                threading.Thread(target=self.handler, args=(data, addr)).start()
        finally:
            self.server.close()

    # Handler for clients
    def handler(self, data, address):
        msg = data.decode('utf-8')
        if msg.startswith('BUILDTREE'):

            # Save better flow and send to neighbours
            ip = address[0]
            _, current_flood, t, latency, jump, streams = msg.split(':')

            self.streams_list = ast.literal_eval(streams)

            current_parent = self.flow_parent

            total_latency = float(latency) + time.time() - float(t)
            
            if total_latency < self.flow_latency or (total_latency == self.flow_latency and int(jump) + 1 <= self.jump) or current_flood > self.flow_current_flood:
                self.flow_jump = int(jump) + 1
                self.flow_parent = ip
                self.flow_latency = round(total_latency, 5)
                print(Back.BLUE + f'Arvore de distribuição construída: {self.flow_parent} - {self.flow_latency} - {self.flow_jump}' + Style.RESET_ALL)
            self.build_distribution_tree(ip)

            if not current_parent == self.flow_parent:
                # Cancela as streams vindas do pai :')
                for stream in self.streams:
                    self.server.sendto(f'NOSTREAM {stream}'.encode(), (current_parent, 6000))

                # Pede as streams necessárias ao novo pai :)
                for stream in self.streams:
                    self.server.sendto(f'STREAM {stream}'.encode(), (current_parent, 6000))

        elif msg.startswith('STREAM'):

            # Adiciona o cliente à lista de clientes de uma stream requisitada
            client = str(address[0])
            _, stream_id = msg.split()

            # Se não tem fluxo da stream, pede a stream ao nodo pai
            if stream_id not in self.streams:
                self.streams[stream_id] = []
                self.server.sendto(msg.encode('utf-8'), (self.flow_parent, 6000))
                print(Back.BLUE + f'New stream added - {stream_id}.' + Style.RESET_ALL)

            if client not in self.streams[stream_id]:
                self.streams[stream_id].append(client)
                print(Back.BLUE + f'New client added to "{stream_id}" clients list.' + Style.RESET_ALL)

        elif msg.startswith('NOSTREAM'):

            # Remove o cliente da lista de clientes de uma stream
            client = str(address[0])
            _, stream_id = msg.split()
            if stream_id in self.streams:
                self.streams[stream_id].remove(client)
                print(Back.BLUE + f'Client removed from "{stream_id}" clients list.' + Style.RESET_ALL)
                if self.streams[stream_id] == 0:
                    self.server.sendto(msg.encode('utf-8'), (self.flow_parent, 6000))
                    print(Back.BLUE + f'Stream "{stream_id}" removed from this node.' + Style.RESET_ALL)

        elif msg.startswith('PARENT'):

            # Devolve o IP do nodo pai
            response = self.flow_parent.encode()
            self.server.sendto(response, address)
            print(Back.BLUE + f'Sending my parent to {address[0]}.' + Style.RESET_ALL)

        elif msg.startswith('LISTSTREAMS'):

            # Devolve a lista de streams disponiveis
            response = self.streams_list
            self.server.sendto(pickle.dumps(response), address)
            print(Back.BLUE + f'Stream list sended to {address[0]}.' + Style.RESET_ALL)

        elif msg.startswith('PING'):

            print(Back.BLUE + f"Received from {address[0]}: PING" + Style.RESET_ALL)
            msg = f'LATENCY:{self.flow_latency}'.encode()
            self.server.sendto(msg, address)

        elif msg.startswith('KEEPALIVE'):

            print(Back.BLUE + f"Received from {address[0]}: KEEPALIVE" + Style.RESET_ALL)
            msg = 'ALIVE'.encode()
            self.server.sendto(msg, address)

    # Build distribution tree 
    def build_distribution_tree(self, address):
        for neighbour in self.neighbours:
            # Check if neighbour is NOT his parent
            if not neighbour == address:
                message = str.encode(f'BUILDTREE:{self.flow_current_flood}:{time.time()}:{self.flow_latency}:{self.flow_jump}:{self.streams_list}')
                self.server.sendto(message, (neighbour, 6000))

    # Retransmit received streams packets
    def passthrough_streams(self):
        streams = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        streams.bind(('0.0.0.0', 7000))
        try:
            while True:
                data, addr = streams.recvfrom(2200)
                self.send_packet(streams, data)
        finally:
            self.server.close()

    # Send packet to clients
    def send_packet(self, socket, data):
        packet = pickle.loads(data)
        stream_id = packet['id']
        for client in self.streams[stream_id]:
            socket.sendto(data, (client, 7000))

    # Check if neighbours are alive
    def keep_alive(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', 6001))
        sock.timeout(self.timeout)

        neighbours_online = 0

        while True:
            try:
                for neighbour in self.neighbours:
                    message = str.encode('LISTSTREAMS')
                    sock.sendto(message, (neighbour, 6000))

                    data, addr = sock.recvfrom(1024)
                    if data.decode() == 'ALIVE':
                        neighbours_online += 1
                        self.neighbours[neighbour] = True

                if neighbours_online == 1:
                    print()
                    message = str.encode('PARENT')
                    sock.sendto(message, (self.flow_parent, 6000))

                    data, addr = sock.recvfrom(1024)
                    parent = data.decode()
                    self.neighbours[parent] = False # Adiciona avô aos vizinhos

            except socket.timeout:
                pass
            finally:
                sock.close()
            time.sleep(60) # per minute

    # Get list of streams available to play from parent
    def get_list_of_streams(self):
        pop_conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        pop_conn.settimeout(self.timeout)
        while True:
            try:
                # Envia mensagem
                message = str.encode('LISTSTREAMS')
                pop_conn.sendto(message, (self.flow_parent, 6000))

                # Receive list of Streams
                self.streams_list = pop_conn.recv(1024).decode()
                print(f'List of Streams obtained. STREAMS: {self.streams_list}')
            except socket.timeout:
                print('Timeout - Reenvio de pedido de lista de streams.')
                continue
            except:
                print('Servidor não está a atender pedidos.')
            finally:
                pop_conn.close()
                break

    # Get neighbours from bootstrapper
    def get_neighbours_from_bootstrapper(self):
        bs_conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            # Conexão com boostrapper
            bs_conn.connect(('10.0.17.10', 5000))

            # Envia mensagem
            message = str.encode(f'NEIGHBOURS {self.name}')
            bs_conn.send(message)

            # Recebe lista de vizinhos
            neighbours = pickle.loads(bs_conn.recv(2048))
            for neighbour in neighbours:
                self.neighbours[neighbour] = False # Guarda como offline
            print('Vizinhos obtidos com sucesso.')
        except:
            print('Bootstrapper offline.')
            sys.exit(1)
        finally:
            bs_conn.close()

if __name__ == "__main__":

    if len(sys.argv) != 2:
        print("Usage: oNode.py <node_name>")
        sys.exit(1)

    node = Node(sys.argv[1])
