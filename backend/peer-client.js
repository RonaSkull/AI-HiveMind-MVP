import Hyperswarm from 'hyperswarm';

const swarm = new Hyperswarm();
const topicString = 'ai-nft-market-v3'; // Must match the agent's topic
const topicBuffer = Buffer.alloc(32).fill(topicString);

console.log('Peer client starting, attempting to connect to topic:', topicString);

// Join the topic as a client
swarm.join(topicBuffer, {
  server: false, // Act as a client
  client: true
});

swarm.on('connection', (socket, peerInfo) => {
  console.log('Connected to a peer (AI Agent):', peerInfo.publicKey.toString('hex'));

  socket.on('data', (data) => {
    console.log('Received data from AI Agent:');
    try {
      const message = JSON.parse(data.toString());
      console.log(JSON.stringify(message, null, 2));
      // Here you could add logic to act on the announcement,
      // e.g., verify the NFT on the blockchain or attempt to buy it.
    } catch (e) {
      console.log('Raw data:', data.toString());
    }
  });

  socket.on('error', (err) => {
    console.error('Connection error with peer:', err);
  });

  socket.on('close', () => {
    console.log('Connection closed with peer.');
    // Optionally, try to reconnect or exit
    // process.exit(0);
  });

  // Send a simple handshake or request if needed by the agent
  // socket.write(JSON.stringify({ type: 'PEER_CLIENT_HELLO' }));
});

console.log('Peer client is attempting to connect to peers on the topic...');

// Keep the process alive for P2P communication
// Handle graceful shutdown if needed
process.on('SIGINT', () => {
  console.log('Shutting down peer client...');
  swarm.leave(topicBuffer).then(() => {
    console.log('Left Hyperswarm topic.');
    return swarm.destroy();
  }).then(() => {
    console.log('Hyperswarm instance destroyed.');
    process.exit(0);
  }).catch(err => {
    console.error('Error during shutdown:', err);
    process.exit(1);
  });
});
