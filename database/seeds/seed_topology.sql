-- ============================================================
-- Seed data — demo network topology
-- Matches simulator/app/topology/blueprint.py exactly so the
-- simulator's resolver always finds real device & interface IDs.
-- ============================================================
-- Run after schema.sql:
--   mysql -u netops -p netops < database/seeds/seed_topology.sql
-- ============================================================

-- Disable FK checks so we can truncate in any order.
SET FOREIGN_KEY_CHECKS = 0;
TRUNCATE TABLE interface_metrics;
TRUNCATE TABLE alerts;
TRUNCATE TABLE interfaces;
TRUNCATE TABLE devices;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- DEVICES
-- ------------------------------------------------------------
INSERT INTO devices (id, hostname, ip_address, device_type, status, description) VALUES
  (1,  'R1',        '10.0.0.1',  'router',       'UP', 'Core router 1'),
  (2,  'R2',        '10.0.0.2',  'router',       'UP', 'Core router 2'),
  (3,  'CORE-SW1',  '10.0.0.10', 'switch',       'UP', 'Core switch 1'),
  (4,  'CORE-SW2',  '10.0.0.11', 'switch',       'UP', 'Core switch 2'),
  (5,  'FW1',       '10.0.0.20', 'firewall',     'UP', 'Edge firewall'),
  (6,  'AP1',       '10.0.0.30', 'access_point', 'UP', 'Wireless AP');

-- ------------------------------------------------------------
-- INTERFACES
-- id ordering: device_id * 10 + local_idx (keeps IDs predictable)
-- ------------------------------------------------------------

-- R1
INSERT INTO interfaces (id, device_id, name, interface_type, status, speed_bps, description) VALUES
  (10, 1, 'Gi0/0',    'ethernet', 'UP', 10000000000, 'Uplink to CORE-SW1'),
  (11, 1, 'Gi0/1',    'ethernet', 'UP', 10000000000, 'Uplink to CORE-SW2'),
  (12, 1, 'Lo0',      'loopback', 'UP', 1000000000,  'Management loopback'),
  (13, 1, 'Gi0/2',    'ethernet', 'UP', 1000000000,  'Local branch uplink');

-- R2
INSERT INTO interfaces (id, device_id, name, interface_type, status, speed_bps, description) VALUES
  (20, 2, 'Gi0/0',    'ethernet', 'UP', 10000000000, 'Uplink to CORE-SW1'),
  (21, 2, 'Gi0/1',    'ethernet', 'UP', 10000000000, 'Uplink to CORE-SW2'),
  (22, 2, 'Lo0',      'loopback', 'UP', 1000000000,  'Management loopback');

-- CORE-SW1
INSERT INTO interfaces (id, device_id, name, interface_type, status, speed_bps, description) VALUES
  (30, 3, 'Gi1/0/1',  'ethernet', 'UP', 10000000000, 'Access port 1'),
  (31, 3, 'Gi1/0/2',  'ethernet', 'UP', 10000000000, 'Access port 2'),
  (32, 3, 'Gi1/0/3',  'ethernet', 'UP', 1000000000,  'Access port 3'),
  (33, 3, 'Gi1/0/4',  'ethernet', 'UP', 1000000000,  'Access port 4'),
  (34, 3, 'Vlan10',   'vlan',     'UP', 10000000000, 'User VLAN 10');

-- CORE-SW2
INSERT INTO interfaces (id, device_id, name, interface_type, status, speed_bps, description) VALUES
  (40, 4, 'Gi1/0/1',  'ethernet', 'UP', 10000000000, 'Access port 1'),
  (41, 4, 'Gi1/0/2',  'ethernet', 'UP', 10000000000, 'Access port 2'),
  (42, 4, 'Vlan10',   'vlan',     'UP', 10000000000, 'User VLAN 10'),
  (43, 4, 'Vlan20',   'vlan',     'UP', 10000000000, 'Server VLAN 20');

-- FW1
INSERT INTO interfaces (id, device_id, name, interface_type, status, speed_bps, description) VALUES
  (50, 5, 'eth0',     'ethernet', 'UP', 10000000000, 'Outside (WAN)'),
  (51, 5, 'eth1',     'ethernet', 'UP', 10000000000, 'Inside (LAN)');

-- AP1
INSERT INTO interfaces (id, device_id, name, interface_type, status, speed_bps, description) VALUES
  (60, 6, 'eth0',     'ethernet', 'UP', 1000000000,  'Wired uplink'),
  (61, 6, 'wlan0',    'ethernet', 'UP', 1000000000,  'Wireless radio 2.4/5GHz'),
  (62, 6, 'wlan1',    'ethernet', 'UP', 1200000000,  'Wireless radio 5GHz');
