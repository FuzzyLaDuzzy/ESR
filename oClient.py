import socket
import pickle
import threading
import subprocess
import time
from colorama import Back, Style

class oClient:
    def __init__(self):
        self.pops = [] # Lista pontos de presença
        self.pop = '' # Ponto de presença a ser usado
        self.timeout = 3 # Tempo para timeout em segundos

        self.stream_choosen = ''
        self.streams_list = []

        # RUN!!!
        self.get_points_of_presence()
        threading.Thread(target=self.monitor_points_of_presence).start()        
        self.get_list_of_streams()

        # Escolhe uma stream da lista de streams disponiveis
        print('Escolha a stream:')
        for stream in self.streams_list:
            print(stream)
        self.stream_choosen = input()

        # Display stream
        self.request_stream()
        self.display_stream()

    # Get points of presence from server
    def get_points_of_presence(self):
        server_conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_conn.settimeout(self.timeout)
        while True:
            try:
                # Envia mensagem
                message = str.encode('POPS')
                server_conn.sendto(message,  ('10.0.17.10', 6000))

                # Recebe lista de POPs
                self.pops = pickle.loads(server_conn.recv(2048))
                print(Back.GREEN + 'Pontos de presença obtidos com sucesso.' + Style.RESET_ALL)
                server_conn.close()
                break
            except socket.timeout:
                print(Back.LIGHTYELLOW_EX + 'Timeout - Reenvio de pedido de lista de pontos de presença.' + Style.RESET_ALL)
            except:
                print(Back.RED + 'Servidor não está a atender pedidos.' + Style.RESET_ALL)
                server_conn.close()
                break

    # Get list of streams available to play from the Points of Presence
    def get_list_of_streams(self):
        pop_conn = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        pop_conn.settimeout(self.timeout)
        
        while self.pop == '':
            time.sleep(1)

        while True:
            try:
                # Envia mensagem
                message = str.encode('LISTSTREAMS')
                pop_conn.sendto(message, (self.pop, 6000))

                # Recebe lista de streams
                self.streams_list = pickle.loads(pop_conn.recv(1024))
                print(Back.GREEN + f'Lista de streams obtida com sucesso.')
                pop_conn.close()
                break
            except socket.timeout:
                print(Back.LIGHTYELLOW_EX + 'Timeout - Reenvio de pedido de lista de streams.' + Style.RESET_ALL)
                continue
            except:
                print(Back.RED + 'Servidor não está a atender pedidos.' + Style.RESET_ALL)
                pop_conn.close()
                break

    # Request stream
    def request_stream(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', 6000))

        message = str.encode(f'STREAM {self.stream_choosen}')
        sock.sendto(message, (self.pop, 6000))

    # Cancel stream - UDP
    def cancel_stream(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', 6000))

        message = str.encode(f'NOSTREAM {self.stream_choosen}')
        sock.sendto(message, (self.pop, 6000))  

    # Display video from server (POP) - UDP
    def display_stream(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.bind(('0.0.0.0', 7000))

        ffplay = subprocess.Popen(
            ['ffplay', '-i', 'pipe:0', '-hide_banner'],
            stdin=subprocess.PIPE,
            stderr=subprocess.DEVNULL)

        try:
            while True:
                data, _ = sock.recvfrom(2200)

                packet = pickle.loads(data)
                video = packet['data']

                ffplay.stdin.write(video)
                ffplay.stdin.flush()
        except:
            print(Back.RED + f'Erro showing stream' + Style.RESET_ALL)
        finally:
            sock.close()
            ffplay.stdin.close()
            ffplay.wait()
            self.cancel_stream()

### Monitor the Points of presence 
    def monitor_points_of_presence(self):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(('0.0.0.0', 6000))
        s.settimeout(1)
        while True:
            valores = {}
            for pop in self.pops:
                try:
                    msg = str.encode('PING')
                    start = time.time()
                    s.sendto(msg, (pop, 6000))
                    response = s.recv(1024)
                    response = response.decode()
                    if response:
                        _, latency = response.split(':')
                        end = time.time()
                        volta = start - end
                        valores[pop] = (round(volta + float(latency), 5))
                except socket.timeout:
                    print(Back.LIGHTYELLOW_EX + 'Timeout - Reenvio de pedido PING.' + Style.RESET_ALL)
                    continue

            menor = 999
            current_pop = self.pop
            for pop in valores:
                if valores[pop] < menor:
                    self.pop = pop
                    menor = valores[pop]
                    print(f'Ponto de Presença Modificado {self.pop}')

            if not current_pop == self.pop:
                self.cancel_stream() # Cancela stream vinda do pop atual
                self.request_stream() # Pede a stream ao novo pop

            time.sleep(60)

if __name__ == "__main__":
    client = oClient()