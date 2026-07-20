/**
 * Settings screen — API connection, push toggles, cache management.
 */
import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, SafeAreaView, Switch, ScrollView,
} from 'react-native';
import { Config } from '../config';
import { cacheClear, cacheSize } from '../storage/offline';

export const SettingsScreen: React.FC = () => {
  const [baseUrl, setBaseUrl] = useState(Config.apiBaseUrl);
  const [apiKey, setApiKey] = useState(Config.apiKey);
  const [pushEnabled, setPushEnabled] = useState(Config.pushEnabled);
  const [cacheCount, setCacheCount] = useState<number>(0);
  const [saved, setSaved] = useState(false);

  React.useEffect(() => {
    cacheSize().then(setCacheCount);
  }, []);

  const handleSave = () => {
    Config.apiBaseUrl = baseUrl;
    Config.apiKey = apiKey;
    Config.pushEnabled = pushEnabled;
    setSaved(true);
    setTimeout(() => setSaved(false), 2000);
  };

  const handleClearCache = async () => {
    await cacheClear();
    setCacheCount(0);
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView>
        <Text style={styles.header}>Settings</Text>

        <Text style={styles.label}>API Base URL</Text>
        <TextInput
          style={styles.input}
          value={baseUrl}
          onChangeText={setBaseUrl}
          autoCapitalize="none"
          autoCorrect={false}
          accessibilityLabel="API Base URL"
        />

        <Text style={styles.label}>API Key</Text>
        <TextInput
          style={styles.input}
          value={apiKey}
          onChangeText={setApiKey}
          secureTextEntry
          accessibilityLabel="API Key"
        />

        <View style={styles.toggleRow}>
          <Text style={styles.toggleLabel}>Push Notifications</Text>
          <Switch
            value={pushEnabled}
            onValueChange={setPushEnabled}
            accessibilityLabel="Enable push notifications"
          />
        </View>
        <Text style={styles.hint}>
          Push notifications require FCM (Android) or APNs (iOS). Offline chart
          computation works without push.
        </Text>

        <View style={styles.cacheRow}>
          <Text style={styles.label}>Cached items: {cacheCount}</Text>
          <TouchableOpacity
            onPress={handleClearCache}
            style={styles.clearButton}
            accessibilityRole="button"
          >
            <Text style={styles.clearButtonText}>Clear Cache</Text>
          </TouchableOpacity>
        </View>

        <TouchableOpacity
          style={styles.saveButton}
          onPress={handleSave}
          accessibilityRole="button"
          accessibilityLabel="Save settings"
        >
          <Text style={styles.saveButtonText}>{saved ? 'Saved ✓' : 'Save'}</Text>
        </TouchableOpacity>

        <Text style={styles.version}>AstroOS v{Config.appVersion}</Text>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: { fontSize: 24, fontWeight: '700', textAlign: 'center', color: '#2c3e50', margin: 16 },
  label: { fontSize: 14, fontWeight: '600', color: '#333', marginHorizontal: 16, marginTop: 12 },
  input: {
    borderWidth: 1, borderColor: '#ccc', borderRadius: 8, padding: 12,
    fontSize: 16, margin: 16, marginTop: 4, backgroundColor: '#fff',
  },
  toggleRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', marginHorizontal: 16, marginTop: 16,
  },
  toggleLabel: { fontSize: 16, color: '#333' },
  hint: { fontSize: 12, color: '#999', marginHorizontal: 16, marginTop: 4 },
  cacheRow: {
    flexDirection: 'row', justifyContent: 'space-between',
    alignItems: 'center', marginTop: 20,
  },
  clearButton: {
    backgroundColor: '#e74c3c', padding: 8, borderRadius: 6, marginRight: 16,
  },
  clearButtonText: { color: '#fff', fontSize: 12, fontWeight: '600' },
  saveButton: {
    backgroundColor: '#2c3e50', padding: 16, borderRadius: 8,
    alignItems: 'center', margin: 16, marginTop: 24,
  },
  saveButtonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
  version: { textAlign: 'center', color: '#bbb', fontSize: 12, marginBottom: 24 },
});
