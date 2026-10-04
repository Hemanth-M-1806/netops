// Core network domain types — mirrors the backend's Pydantic schemas

export type DeviceType = 'router' | 'switch' | 'firewall' | 'loadbalancer' | 'access_point' | 'other'
export type DeviceStatus = 'UP' | 'DOWN' | 'WARNING' | 'CRITICAL' | 'MAINTENANCE' | 'UNKNOWN'
export type InterfaceType = 'ethernet' | 'loopback' | 'vlan' | 'tunnel' | 'other'
export type InterfaceStatus = 'UP' | 'DOWN' | 'ADMIN_DOWN' | 'ERROR' | 'UNKNOWN'
export type Severity = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL'

// ---- Device ----------------------------------------------------------------

export interface Device {
  id: number
  device_id: number
  hostname: string
  ip_address: string
  device_type: DeviceType
  status: DeviceStatus
  location: string | null
  description: string | null
  created_at: string
  updated_at: string
}

export interface DeviceListResponse {
  total: number
  items: Device[]
}

// ---- Interface -------------------------------------------------------------

export interface NetworkInterface {
  id: number
  interface_id: number
  interface_name: string
  device_id: number
  name: string
  interface_type: InterfaceType
  status: InterfaceStatus
  speed_bps: number | null
  description: string | null
  created_at: string
  updated_at: string
  hostname: string | null
}

export interface InterfaceListResponse {
  items: NetworkInterface[]
}

// ---- Metrics ---------------------------------------------------------------

export interface MetricSample {
  id: number
  interface_id: number
  rx_bytes: number
  tx_bytes: number
  packet_drops: number
  errors: number
  measured_at: string
  ingested_at: string
}

export interface MetricListResponse {
  interface_id: number
  items: MetricSample[]
}

// ---- Risk Score ------------------------------------------------------------

export interface ScoreComponents {
  utilisation: number
  packet_drops: number
  errors: number
  trend: number
}

export interface RiskScore {
  interface_id: number
  severity_score: number
  severity_label: Severity
  impact_score: number
  max_z: number
  anomaly_flagged: boolean
  components: ScoreComponents
}

// ---- Alerts ----------------------------------------------------------------

export interface Alert {
  id: number
  interface_id: number
  severity: Severity
  alert_type: string
  message: string
  resolved: boolean
  triggered_at: string
  resolved_at: string | null
  interface_name: string | null
  hostname: string | null
}

export interface AlertListResponse {
  total: number
  items: Alert[]
}

// ---- Copilot ---------------------------------------------------------------

export type ChatRole = 'user' | 'assistant' | 'system'

export interface ChatMessage {
  id: number
  session_id: string
  role: ChatRole
  content: string
  token_count: number | null
  created_at: string
}

export interface CopilotRequest {
  session_id: string
  content: string
  device_id?: number
  interface_id?: number
}

export interface CopilotResponse {
  assistant_message: ChatMessage
  context_metrics_used: number
  context_alerts_used: number
}

// ---- Health ----------------------------------------------------------------

export interface HealthResponse {
  status: 'healthy' | 'degraded'
  database: 'connected' | 'unreachable'
  version: string
}

// ---- Topology (frontend computed) ------------------------------------------

export interface TopologyNode {
  id: string
  device: Device
  x: number
  y: number
  z: number
  interfaces: NetworkInterface[]
  riskScore: number | null
  alertCount: number
}

export interface TopologyLink {
  id: string
  source: string  // device hostname
  target: string  // device hostname
  traffic: number // 0..1 normalised
  healthy: boolean
}

// ---- Telemetry ingest (to backend) ----------------------------------------

export interface IngestSample {
  interface_id: number
  rx_bytes: number
  tx_bytes: number
  packet_drops: number
  errors: number
  measured_at: string
}

export interface IngestRequest {
  source: string
  samples: IngestSample[]
}

export interface IngestResponse {
  accepted: number
  rejected: number
}
