# ISPBX Frontend Testing Guide

This document provides instructions for manually testing the frontend interface of the ISPBX system. These examples focus on the endpoint management functionality.

## Prerequisites

- The ISPBX backend server must be running
- A modern web browser (Chrome, Firefox, Edge, etc.)
- Access to the ISPBX dashboard at `http://localhost:8000` (or your configured URL)

## Dashboard Overview

The ISPBX dashboard consists of two main sections:
1. **Extension Status** - Displays all configured SIP endpoints with their current status
2. **Call Monitor** - Shows active calls in the system

## Testing Endpoint Management

### 1. Viewing Endpoints

When you load the dashboard, you should see:
- A table of existing endpoints with their status
- A refresh button in the top-right corner
- An "Add Endpoint" button in the Extension Status card header

If the endpoint list is empty, you'll see a "No endpoints available" message.

### 2. Adding a New Endpoint

1. Click the "Add Endpoint" button in the Extension Status card header
2. In the modal dialog that appears, fill in the following fields:
   - **Extension**: Enter a numeric extension (e.g., `1001`)
   - **Name**: Enter a display name (e.g., `Test User`)
   - **Password**: Enter a secure password
   - **Context**: Leave as default (`from-internal`) or change if needed
   - **Codecs**: Select desired codecs (G.722 is selected by default)
3. Click the "Save" button
4. Verify that:
   - A success message appears
   - The modal closes
   - The dashboard refreshes automatically
   - The new endpoint appears in the table

Example values for testing:
```
Extension: 1001
Name: Test User 1
Password: securepass1
Context: from-internal
Codecs: G.722, ulaw
```

### 3. Editing an Existing Endpoint

1. Find an existing endpoint in the table
2. Click the edit (pencil) icon in the Actions column
3. In the modal dialog that appears:
   - The extension field should be pre-filled and disabled
   - Other fields should be pre-filled with current values
   - The password field should be empty (for security)
4. Make changes to one or more fields:
   - **Name**: Change the display name
   - **Password**: Leave empty to keep the existing password, or enter a new one
   - **Context**: Change if needed
   - **Codecs**: Select different codecs
5. Click the "Save" button
6. Verify that:
   - A success message appears
   - The modal closes
   - The dashboard refreshes automatically
   - The endpoint in the table reflects your changes

Example edit:
```
Name: Updated User 1
Password: (leave empty to keep existing, or enter a new password)
Context: from-internal
Codecs: G.722, alaw
```

### 4. Deleting an Endpoint

1. Find an existing endpoint in the table
2. Click the delete (trash) icon in the Actions column
3. In the confirmation dialog that appears:
   - Verify that the correct extension number is shown
4. Click the "Delete" button
5. Verify that:
   - A success message appears
   - The modal closes
   - The dashboard refreshes automatically
   - The endpoint is removed from the table

### 5. Testing the Refresh Button

1. Click the "Refresh" button in the top-right corner
2. Verify that:
   - The refresh indicator (spinner) appears briefly
   - The endpoint table updates with the latest data
   - The connection status indicator shows "Connected" if the backend is running

## Testing Error Scenarios

### 1. Creating a Duplicate Endpoint

1. Add an endpoint with extension `1002`
2. Try to add another endpoint with the same extension `1002`
3. Verify that:
   - An error message appears in the modal
   - The modal stays open
   - The form shows validation errors

### 2. Invalid Input Validation

Test the form validation by attempting to submit with invalid or missing values:

1. Click "Add Endpoint"
2. Leave the Extension field empty
3. Click "Save"
4. Verify that form validation prevents submission

Repeat with other required fields:
- Empty Name
- Empty Password (for new endpoints)

### 3. Connection Issues

To test connection issues:

1. Stop the backend server
2. Refresh the page or click the "Refresh" button
3. Verify that:
   - The connection status shows "Disconnected"
   - An appropriate error message is displayed

## Browser Console Testing

For developers, the browser console provides valuable debugging information:

1. Open your browser's developer tools (F12 or right-click > Inspect)
2. Go to the Console tab
3. Perform various operations (add, edit, delete endpoints)
4. Observe the console logs:
   - Connection status messages
   - API request details
   - Success and error messages
   - Refresh operation logs

## Testing Tips

1. **Clear browser cache**: If you encounter unexpected behavior, try clearing your browser cache and reloading the page.

2. **Test across browsers**: Verify that the interface works correctly in different browsers (Chrome, Firefox, Safari, etc.).

3. **Responsive design**: Test the dashboard on different screen sizes to ensure the responsive design works properly.

4. **Rapid operations**: Test performing multiple operations in quick succession to ensure the system handles concurrent actions correctly.

5. **Network throttling**: Use browser developer tools to simulate slower network connections and verify the UI provides appropriate feedback during delays.
