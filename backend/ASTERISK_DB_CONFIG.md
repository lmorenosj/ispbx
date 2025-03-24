# Asterisk Database Integration Configuration Guide

This document outlines all the necessary configuration changes to make Asterisk work properly with a MySQL database backend. Following these steps will ensure that your PBX system uses the database for endpoint configuration, dialplan entries, and other components.

## 1. Database Configuration

### MySQL Database Setup

Ensure the MySQL database is properly set up with the following settings:

- **Database Name**: asterisk
- **Username**: asteriskuser
- **Password**: asteriskpassword
- **Host**: localhost
- **Port**: 3306

### Required Tables

The following tables must exist in the database:

- `ps_endpoints` - SIP endpoint configuration
- `ps_aors` - Address of Record for endpoints
- `ps_auths` - Authentication information
- `ps_contacts` - Contact information for registered endpoints
- `extensions` - Dialplan entries

## 2. ODBC Configuration

### /etc/odbc.ini

Ensure the ODBC connection to the MySQL database is properly configured:

```ini
[asterisk]
Driver = MySQL
Description = MySQL connection to "asterisk" database
Server = localhost
Port = 3306
Database = asterisk
UserName = asteriskuser
Password = asteriskpassword
Socket = /var/run/mysqld/mysqld.sock
```

### /etc/asterisk/res_odbc.conf

Configure Asterisk's ODBC resource:

```ini
[asterisk]
enabled => yes
dsn => asterisk
username => asteriskuser
password => asteriskpassword
pre-connect => yes
```

## 3. Asterisk Configuration Files

### /etc/asterisk/extconfig.conf

This file maps Asterisk configuration sections to database tables. Ensure the following lines are uncommented:

```ini
[settings]
ps_endpoints => odbc,asterisk
ps_auths => odbc,asterisk
ps_aors => odbc,asterisk
ps_domain_aliases => odbc,asterisk
ps_endpoint_id_ips => odbc,asterisk
ps_contacts => odbc,asterisk
extensions => odbc,asterisk
```

### /etc/asterisk/extensions.conf

Configure the dialplan to use the realtime database:

```ini
[general]
static = yes
writeprotect = no

[from-internal]
; Use the realtime database for extensions
switch => Realtime/from-internal@extensions
```

### /etc/asterisk/modules.conf

Ensure the ODBC modules are preloaded:

```ini
preload => res_odbc.so
preload => res_config_odbc.so
```

## 4. Dialplan Management

### Adding Extensions to the Database

To add dialplan entries to the database, use SQL commands like:

```sql
INSERT INTO extensions (context, exten, priority, app, appdata) VALUES 
('from-internal', '1000', 1, 'NoOp', 'Call to extension 1000'),
('from-internal', '1000', 2, 'Dial', 'PJSIP/1000,20'),
('from-internal', '1000', 3, 'Hangup', '');
```

### Reloading the Dialplan

After making changes to the database, reload the dialplan with:

```
asterisk -rx "dialplan reload"
```

## 5. Common Issues and Troubleshooting

### Extension Not Found in Context

If you see an error like:
```
Call to extension 'XXXX' rejected because extension not found in context 'from-internal'
```

Check the following:

1. Verify the extension exists in the database:
   ```sql
   SELECT * FROM extensions WHERE context='from-internal' AND exten='XXXX';
   ```

2. Ensure the `extensions => odbc,asterisk` line is uncommented in extconfig.conf

3. Verify the switch statement in extensions.conf:
   ```
   switch => Realtime/from-internal@extensions
   ```

4. Reload the dialplan after making changes:
   ```
   asterisk -rx "dialplan reload"
   ```

### Syntax Errors in extensions.conf

If you see warnings like:
```
WARNING: pbx_config.c: Can't use 'next' priority on the first entry
```

Make sure your static extensions.conf file doesn't have syntax errors. When using database integration, it's best to keep the static file minimal and rely on the database for most configuration.

## 6. AMI Integration

When using the AMI (Asterisk Manager Interface) to manage endpoints, ensure you reload the configuration after making changes:

```python
# Use PJSIPReload action to reload PJSIP configuration
reload_result = await ami_client.manager.send_action({
    'Action': 'PJSIPReload'
})

# Force a device state refresh
state_result = await ami_client.manager.send_action({
    'Action': 'DeviceStateList'
})
```

## 7. Verifying Configuration

To verify that Asterisk is properly using the database configuration:

1. Check if realtime is enabled:
   ```
   asterisk -rx "core show settings" | grep -i realtime
   ```

2. View the configured endpoints:
   ```
   asterisk -rx "pjsip show endpoints"
   ```

3. View the dialplan:
   ```
   asterisk -rx "dialplan show from-internal"
   ```

4. Check the status of ODBC connections:
   ```
   asterisk -rx "odbc show"
   ```

By following this guide, your Asterisk system should be properly configured to use the database for all configuration components, ensuring consistent and reliable operation.
