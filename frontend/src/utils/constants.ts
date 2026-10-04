// Fixed 3D coordinate layout for known devices in the network topology
export const DEVICE_COORDINATES: Record<string, [number, number, number]> = {
  'R1': [-6, 3, 0],
  'R2': [6, 3, 0],
  'CORE-SW1': [-3, -1, 2],
  'CORE-SW2': [3, -1, 2],
  'FW1': [0, 4, -3],
  'AP1': [0, -4, 4],
}

// Known topology links between devices
export const KNOWN_LINKS = [
  { source: 'R1', target: 'R2', label: 'Core Interconnect (Gi0/0 - Gi0/0)' },
  { source: 'R1', target: 'CORE-SW1', label: 'Uplink 1 (Gi0/1 - Gi1/0/1)' },
  { source: 'R2', target: 'CORE-SW2', label: 'Uplink 2 (Gi0/1 - Gi1/0/1)' },
  { source: 'CORE-SW1', target: 'CORE-SW2', label: 'Peer Link (Gi1/0/2 - Gi1/0/2)' },
  { source: 'R1', target: 'FW1', label: 'Perimeter 1' },
  { source: 'R2', target: 'FW1', label: 'Perimeter 2' },
  { source: 'CORE-SW1', target: 'AP1', label: 'Distribution 1' },
  { source: 'CORE-SW2', target: 'AP1', label: 'Distribution 2' },
]

export const POLLING_INTERVALS = {
  HEALTH: 10000,
  DEVICES: 15000,
  ALERTS: 5000,
  METRICS: 5000,
}
