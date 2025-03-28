# ESR - Enhanced Streaming Relay Network

This project implements a distributed streaming relay network designed to efficiently deliver video streams to clients. It utilizes a peer-to-peer (P2P) architecture with a central bootstrapper for initial node discovery and a dynamic distribution tree for optimized stream delivery.

## Project Structure

The project consists of the following core components:

* **`boott.py` (Bootstrapper):**

  * Acts as a central registry for nodes in the network.
  * Maintains a list of neighbors for each node.
  * Handles initial node discovery by providing neighbor information upon request.
  * Uses TCP for communication.
* **`oServer.py` (Server):**

  * Represents a specialized node that hosts and streams video content.
  * Maintains a list of available videos.
  * Manages client connections and stream requests.
  * Builds and maintains a distribution tree for efficient stream delivery.
  * Communicates with the bootstrapper to get its initial list of neighbors.
  * Uses UDP for streaming and distribution tree management.
  * Uses TCP for initial communication with the bootstrapper.
* **`oNode.py` (Node):**

  * Represents a general node in the network that can relay streams.
  * Connects to the bootstrapper to discover neighbors.
  * Participates in building and maintaining the distribution tree.
  * Receives and relays stream packets to clients.
  * Manages client connections and stream requests.
  * Uses UDP for streaming, distribution tree management, and communication with other nodes.
  * Uses TCP for initial communication with the bootstrapper.
* **`oClient.py` (Client):**

  * Represents a client that requests and plays video streams.
  * Connects to the server to get a list of available streams.
  * Connects to a Point of Presence (POP) to receive the stream.
  * Monitors the latency of different POPs and switches to the best one.
  * Uses UDP for receiving streams and communicating with POPs.
  * Uses ffplay to display the received video stream.

## Key Features

* **Bootstrapper:** Centralized node discovery for easy network setup.
* **Distribution Tree:** Dynamic tree structure for efficient stream distribution.
* **Points of Presence (POPs):** Multiple entry points for clients to connect to the network.
* **Adaptive POP Selection:** Clients monitor POP latency and switch to the best one.
* **Stream Management:** Nodes and servers manage client connections and stream requests.
* **UDP Streaming:** Efficient video delivery using UDP.
* **Neighbor Discovery:** Nodes discover their neighbors through the bootstrapper.
* **Keep-Alive:** Nodes can check if their neighbors are alive.
* **Video Streaming:** The server can stream multiple videos.
* **CBR:** The server streams the videos using Constant Bit Rate.

## Dependencies

* **Python 3.x**
* **`colorama`:** For colored terminal output.
  ```bash
  pip install colorama
  ```
* **`ffplay`:** For playing the video stream.
  ```bash
  sudo apt-get install ffmpeg
  ```

## Setup and Execution

1. **Clone the Repository:**

   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```
2. **Start the Bootstrapper:**

   ```bash
   python boott.py
   ```

   * This will start listening for Nodes to connect.
3. **Start Nodes:**

   ```bash
   python oNode.py <node_name>
   ```

   * Replace `<node_name>` with a unique name for each node (e.g., `n1`, `n2`, `n3`, etc.).
   * Start multiple nodes in different terminals.
4. **Start the Server:**

   ```bash
   python oServer.py
   ```

   * Make sure to create a `videos` folder in the same directory as `oServer.py` and put some video files inside.
5. **Start Clients:**

   ```bash
   python oClient.py
   ```

   * Start multiple clients in different terminals.

## Network Configuration

* The bootstrapper listens on port `5000` (TCP).
* Nodes and the server communicate with each other on port `6000` (UDP).
* Nodes and the server receive video streams on port `7000` (UDP).
* The nodes use port `6001` (UDP) to check if the neighbours are alive.
* The server uses port `6000` (UDP) to receive client requests.
* The client uses port `6000` (UDP) to send requests and port `7000` (UDP) to receive video.
* The IP addresses in `boott.py` (neighbors), `oServer.py` (pops), and `oClient.py` (server address) should be configured according to your network setup.
* The server, nodes and client should be in the same network.

## How it Works

1. **Initialization:**

   * The bootstrapper starts and listens for connections.
   * The server and nodes start and connect to the bootstrapper to get their initial list of neighbors.
2. **Distribution Tree Building:**

   * The server periodically sends `BUILDTREE` messages to its neighbors.
   * Nodes receive `BUILDTREE` messages and forward them to their neighbors, keeping track of the best path (lowest latency and fewest jumps) to the server.
   * This process creates a dynamic distribution tree rooted at the server.
3. **Client Connection:**

   * Clients connect to the server to get a list of available POPs.
   * Clients connect to a POP to get a list of available streams.
   * Clients choose a stream and request it from the POP.
4. **Stream Delivery:**

   * The server streams the requested video to its children in the distribution tree.
   * Nodes receive the stream and relay it to their children.
   * Clients receive the stream from their parent node.
5. **Adaptive POP Selection:**

   * Clients periodically ping different POPs to measure their latency.
   * If a better POP is found, the client switches to it.
6. **Keep Alive:**

   * The nodes send a message to their neighbours to check if they are alive.
   * If a node is offline, the distribution tree is rebuilt.

## Future Improvements

* **Stream Overlap Issue:** When multiple streams are sent to the same client over a single port, subsequent stream requests can result in interleaved frames from different streams. To resolve this, the server should allocate a unique port for each client upon receiving a new stream request.

## Authors

* [Flávio SIlva]

## License

[Your License]
