import Hyperswarm from 'hyperswarm';
import crypto from 'crypto'; // For generating a unique ID for the client if needed

const TOPIC_STRING = 'ai-nft-market-v3';
const topicBuffer = Buffer.alloc(32).fill(TOPIC_STRING);

console.log(`P2P Test Client attempting to join Hyperswarm topic: ${TOPIC_STRING}`);

const swarm = new Hyperswarm();

// Client acts as a client, looking for servers
swarm.join(topicBuffer, {
  server: false, // This instance is a client
  client: true   // Actively look for servers
});

swarm.on('connection', (socket, peerInfo) => {
  console.log(`\n[CLIENT] Connected to a peer: ${peerInfo.publicKey.toString('hex').substring(0, 10)}...`);
  console.log('[CLIENT] Waiting for NFT announcements...\n');

  // Original socket.on('data') is now part of the new logic above this section in the previous chunk
  // This section is being replaced by the logic block that includes the noMessageTimer


  socket.on('error', (error) => {
    console.error(`[CLIENT] Connection error with peer ${peerInfo.publicKey.toString('hex').substring(0,10)}...:`, error.message);
  });

  socket.on('close', () => {
    console.log(`[CLIENT] Connection closed with peer: ${peerInfo.publicKey.toString('hex').substring(0,10)}...`);
  });
});

console.log('[CLIENT] Searching for peers... Will wait for connections/messages. Press Ctrl+C to exit.');

  let messageReceived = false;
  const noMessageTimeoutDuration = 45000; // 45 seconds to wait for a message after connection
  let noMessageTimer;

  socket.on('data', (data) => {
    messageReceived = true;
    if (noMessageTimer) clearTimeout(noMessageTimer);
    try {
      const message = JSON.parse(data.toString());
      console.log('[CLIENT] Received announcement from peer:');
      console.dir(message, { depth: null });
      console.log('\n--------------------------------------------------\n');
      // Optionally, you could close the connection after receiving an announcement if testing one-shot
      // socket.end(); 
      // For this test, let's keep it open for a bit or until Ctrl+C
    } catch (error) {
      console.error('[CLIENT] Error parsing message from peer or invalid data format:', error);
      console.log('[CLIENT] Raw data received:', data.toString());
    }
  });

  // Set a timeout to close if no message is received after connection
  noMessageTimer = setTimeout(() => {
    if (!messageReceived) {
      console.log(`[CLIENT] No messages received from peer ${peerInfo.publicKey.toString('hex').substring(0,10)}... after ${noMessageTimeoutDuration/1000} seconds. Closing this connection.`);
      socket.end(); // Close this specific socket
    }
  }, noMessageTimeoutDuration);

// Graceful shutdown
process.on('SIGINT', async () => {
  console.log('\n[CLIENT] Shutting down P2P test client...');
  try {
    await swarm.leave(topicBuffer);
    console.log('[CLIENT] Left Hyperswarm topic.');
    await swarm.destroy();
    console.log('[CLIENT] Hyperswarm instance destroyed.');
    process.exit(0);
  } catch (err) {
    console.error('[CLIENT] Error during shutdown:', err);
    process.exit(1);
  }
});
