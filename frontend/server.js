/**
 * ISPBX Static Web Server
 * 
 * This is a simple Express server that serves the static frontend files
 * and provides a direct connection to the backend Socket.IO server.
 */

const express = require('express');
const path = require('path');
const app = express();
const PORT = process.env.PORT || 5000;

// Serve static files from the 'static' directory
app.use('/static', express.static(path.join(__dirname, 'static')));

// Serve the main HTML file for all routes (for SPA routing)
app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'static', 'index.html'));
});

// Start the server
app.listen(PORT, () => {
  console.log(`ISPBX Frontend server running on port ${PORT}`);
  console.log(`Open http://localhost:${PORT} in your browser`);
});
