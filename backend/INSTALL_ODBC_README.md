# MySQL ODBC Setup for Asterisk

This guide provides step-by-step instructions for setting up MySQL with ODBC for Asterisk to manage SIP endpoint configurations.

## 1. Install Required Packages

First, install the necessary ODBC and MySQL packages:

```bash
sudo apt-get install unixodbc unixodbc-dev python3-dev python3-pip python3-mysqldb
```

## 2. Create MySQL Database

Create the MySQL database for storing Asterisk's PJSIP configuration:

```bash
sudo mysql -e "CREATE DATABASE IF NOT EXISTS asterisk;"
```

## 3. Create MySQL User

Create a dedicated MySQL user with appropriate permissions:

```bash
sudo mysql -e "CREATE USER 'asteriskuser'@'localhost' IDENTIFIED BY 'asteriskpassword'; GRANT ALL PRIVILEGES ON asterisk.* TO 'asteriskuser'@'localhost'; FLUSH PRIVILEGES;"
```

## 4. Install Alembic for Database Migrations

Alembic is used to manage the database schema:

```bash
pip install alembic
```

## 5. Install MySQL ODBC Driver

Download and install the MySQL Connector/ODBC driver:

```bash
wget https://dev.mysql.com/get/Downloads/Connector-ODBC/8.0/mysql-connector-odbc-8.0.23-linux-glibc2.12-x86-64bit.tar.gz
tar -xzvf mysql-connector-odbc-8.0.23-linux-glibc2.12-x86-64bit.tar.gz
sudo cp mysql-connector-odbc-8.0.23-linux-glibc2.12-x86-64bit/lib/libmyodbc8a.so /usr/lib/x86_64-linux-gnu/odbc/
```

## 6. Configure ODBC Driver

Create the ODBC driver configuration file:

```bash
sudo bash -c 'cat > /etc/odbcinst.ini << EOF
[MySQL]
Description = ODBC for MySQL
Driver = /usr/lib/x86_64-linux-gnu/odbc/libmyodbc8a.so
Setup = /usr/lib/x86_64-linux-gnu/odbc/libodbcmyS.so
UsageCount = 2
EOF'
```

## 7. Configure ODBC Data Source

Create the ODBC data source configuration file:

```bash
sudo bash -c 'cat > /etc/odbc.ini << EOF
[asterisk]
Driver = MySQL
Description = MySQL connection to "asterisk" database
Server = localhost
Port = 3306
Database = asterisk
UserName = asteriskuser
Password = asteriskpassword
Socket = /var/run/mysqld/mysqld.sock
EOF'
```

## 8. Configure Asterisk ODBC Resource

Configure Asterisk to use the ODBC data source:

```bash
sudo bash -c 'cat > /etc/asterisk/res_odbc.conf << EOF
;;; odbc setup file

[ENV]

[asterisk]
enabled => yes
dsn => asterisk
username => asteriskuser
password => asteriskpassword
pre-connect => yes
EOF'
```

## 9. Initialize Database Schema with Alembic

Set up the database tables using Alembic:

```bash
cd /usr/src/asterisk-22.1.1/contrib/ast-db-manage/
sudo cp config.ini.sample config.ini
sudo sed -i 's|sqlalchemy.url = mysql://user:pass@localhost/asterisk|sqlalchemy.url = mysql://asteriskuser:asteriskpassword@localhost/asterisk|' config.ini
alembic -c config.ini upgrade head
```

## 10. Restart Asterisk

Apply the changes by restarting Asterisk:

```bash
sudo systemctl restart asterisk
```

## 11. Verify ODBC Connection

Check if the ODBC connection is working:

```bash
sudo asterisk -rx "odbc show"
```

You should see output indicating an active connection:

```
ODBC DSN Settings
-----------------

  Name:   asterisk
  DSN:    asterisk
    Number of active connections: 1 (out of 1)
    Logging: Disabled
```

## Troubleshooting

If the connection fails, check:
- MySQL service is running: `sudo systemctl status mysql`
- ODBC driver exists: `ls -la /usr/lib/x86_64-linux-gnu/odbc/libmyodbc8a.so`
- MySQL user credentials are correct: `mysql -u asteriskuser -pasteriskpassword asterisk -e "SHOW TABLES;"`
- ODBC configuration files are correct: `odbcinst -j`

## Next Steps

With the ODBC connection established, you can now implement endpoint configuration management using AMI UpdateConfig commands.
