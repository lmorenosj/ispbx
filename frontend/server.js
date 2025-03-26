/**
 * ISPBX Static Web Server
 * 
 * This is a simple Express server that serves the static frontend files
 * and provides a direct connection to the backend Socket.IO server.
 */

const express = require('express');
const path = require('path');
const fs = require('fs');
const app = express();
const PORT = process.env.PORT || 5000;

// Setup EJS as the view engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'templates'));

// Serve static files from the 'static' directory
app.use('/static', express.static(path.join(__dirname, 'static')));

// Helper function to render HTML with includes
function renderWithIncludes(res, templatePath) {
  fs.readFile(templatePath, 'utf8', (err, data) => {
    if (err) {
      console.error('Error reading template:', err);
      return res.status(500).send('Error loading page');
    }
    
    // Process includes
    data = data.replace(/{% include '([^']+)' %}/g, (match, includePath) => {
      try {
        return fs.readFileSync(path.join(__dirname, 'templates', includePath), 'utf8');
      } catch (includeErr) {
        console.error(`Error including ${includePath}:`, includeErr);
        return '<!-- Include error -->';
      }
    });
    
    res.send(data);
  });
}

// Serve HTML templates
app.get('/', (req, res) => {
  renderWithIncludes(res, path.join(__dirname, 'templates', 'index.html'));
});

app.get('/dashboard', (req, res) => {
  renderWithIncludes(res, path.join(__dirname, 'templates', 'index.html'));
});

app.get('/cdr', (req, res) => {
  renderWithIncludes(res, path.join(__dirname, 'templates', 'cdr.html'));
});

app.get('/endpoint', (req, res) => {
  renderWithIncludes(res, path.join(__dirname, 'templates', 'endpoint-dashboard.html'));
});

app.get('/queues', (req, res) => {
  renderWithIncludes(res, path.join(__dirname, 'templates', 'queue-dashboard.html'));
});

// Fallback route - serve index.html for any other routes
app.get('*', (req, res) => {
  renderWithIncludes(res, path.join(__dirname, 'templates', 'index.html'));
});

// Start the server
app.listen(PORT, () => {
  console.log(`ISPBX Frontend server running on port ${PORT}`);
  console.log(`Open http://localhost:${PORT} in your browser`);
});
