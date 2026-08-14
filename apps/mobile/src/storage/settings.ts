/**
 * AstroOS Mobile — Settings persistence.
 *
 * Persists the API connection settings across app restarts. The API key is
 * stored in the platform Keychain/Keystore when `react-native-keychain` is
 * linked; otherwise it falls back to AsyncStorage so the app still works.
 */
import AsyncStorage from '@react-native-async-storage/async-storage';
import * as Keychain from 'react-native-keychain';
import { Config } from '../config';

const SETTINGS_KEY = '@astroos/settings';
const KEYCHAIN_SERVICE = 'com.astroos.mobile.apikey';

interface PersistedSettings {
  baseUrl: string;
  pushEnabled: boolean;
}

async function storeApiKey(value: string): Promise<void> {
  try {
    if (value) {
      await Keychain.setGenericPassword('astroos-api-key', value, {
        service: KEYCHAIN_SERVICE,
      });
    } else {
      await Keychain.resetGenericPassword({ service: KEYCHAIN_SERVICE });
    }
    return;
  } catch {
    // Keychain native module not linked — fall back to AsyncStorage.
  }
  if (value) {
    await AsyncStorage.setItem(`${SETTINGS_KEY}:apikey`, value);
  } else {
    await AsyncStorage.removeItem(`${SETTINGS_KEY}:apikey`);
  }
}

async function loadApiKey(): Promise<string> {
  try {
    const creds = await Keychain.getGenericPassword({ service: KEYCHAIN_SERVICE });
    if (creds) {
      return creds.password;
    }
  } catch {
    // Fall through to AsyncStorage.
  }
  return (await AsyncStorage.getItem(`${SETTINGS_KEY}:apikey`)) ?? '';
}

/**
 * Load persisted settings into the in-memory Config. Safe to call on startup.
 */
export async function loadSettings(): Promise<void> {
  try {
    const raw = await AsyncStorage.getItem(SETTINGS_KEY);
    if (raw) {
      const parsed = JSON.parse(raw) as Partial<PersistedSettings>;
      if (parsed.baseUrl) Config.apiBaseUrl = parsed.baseUrl;
      if (typeof parsed.pushEnabled === 'boolean') Config.pushEnabled = parsed.pushEnabled;
    }
    Config.apiKey = await loadApiKey();
  } catch {
    // Ignore corrupt settings — fall back to defaults.
  }
}

/**
 * Persist the current settings and update Config.
 */
export async function saveSettings(
  baseUrl: string,
  apiKey: string,
  pushEnabled: boolean,
): Promise<void> {
  Config.apiBaseUrl = baseUrl;
  Config.apiKey = apiKey;
  Config.pushEnabled = pushEnabled;

  const settings: PersistedSettings = { baseUrl, pushEnabled };
  await AsyncStorage.setItem(SETTINGS_KEY, JSON.stringify(settings));
  await storeApiKey(apiKey);
}
