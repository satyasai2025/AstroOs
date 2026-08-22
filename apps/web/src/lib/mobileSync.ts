/**
 * AstroOS — Local-First Mobile Sync Client Library (Module 21, Priority 6)
 */

import { api } from "@/lib/api";

export interface PairingGenerateResponse {
  session_id: string;
  pin_code: string;
  qr_payload: string;
  expires_at_iso: string;
  ttl_seconds: number;
  protocol_version: string;
}

export interface PairingVerifyResponse {
  device_id: string;
  device_secret_token: string;
  protocol_version: string;
  paired_at_iso: string;
}

export interface PairedDevice {
  device_id: string;
  device_name: string;
  device_type: string;
  paired_at_iso: string;
  last_seen_at_iso: string;
  last_sync_at_iso?: string | null;
  revoked_at_iso?: string | null;
  is_active: boolean;
  protocol_version: string;
}

export interface PairedDeviceListResponse {
  devices: PairedDevice[];
  total_active: number;
}

export interface SyncConflictItem {
  conflict_id: string;
  entity_id: string;
  entity_type: string;
  winning_revision: number;
  losing_revision: number;
  winning_device_id: string;
  losing_device_id: string;
  winning_payload_hash: string;
  losing_payload_hash: string;
  resolution_reason: string;
  created_at_iso: string;
}

export interface SyncConflictListResponse {
  conflicts: SyncConflictItem[];
  total_count: number;
}

export interface SyncStatusResponse {
  server_cursor: number;
  total_entities: number;
  total_tombstones: number;
  active_paired_devices: number;
  total_conflicts_recorded: number;
  protocol_version: string;
  supported_entity_types: string[];
}

export async function generatePairingSession(params?: {
  lan_host?: string;
  lan_port?: number;
}): Promise<PairingGenerateResponse> {
  return api.post<PairingGenerateResponse>("/api/v1/sync/pairing/generate", params || {});
}

export async function verifyPairingSession(params: {
  session_id: string;
  ephemeral_secret?: string;
  pin_code?: string;
  device_name: string;
  device_type?: string;
}): Promise<PairingVerifyResponse> {
  return api.post<PairingVerifyResponse>("/api/v1/sync/pairing/verify", params);
}

export async function listPairedDevices(): Promise<PairedDeviceListResponse> {
  return api.get<PairedDeviceListResponse>("/api/v1/sync/devices");
}

export async function revokePairedDevice(deviceId: string): Promise<{ status: string; revoked_device_id: string }> {
  return api.delete<{ status: string; revoked_device_id: string }>(`/api/v1/sync/devices/${deviceId}`);
}

export async function getSyncStatus(): Promise<SyncStatusResponse> {
  return api.get<SyncStatusResponse>("/api/v1/sync/status");
}

export async function listSyncConflicts(): Promise<SyncConflictListResponse> {
  return api.get<SyncConflictListResponse>("/api/v1/sync/conflicts");
}
