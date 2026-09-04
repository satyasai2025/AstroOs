/**
 * Birth data input form.
 */
import React, { useState } from 'react';
import {
  View, Text, TextInput, TouchableOpacity, StyleSheet, ScrollView,
} from 'react-native';

interface BirthFormProps {
  onSubmit: (data: {
    birth_datetime_utc: string;
    latitude: number;
    longitude: number;
    ayanamsa?: string;
    house_system?: string;
  }) => void;
  loading?: boolean;
}

export const BirthForm: React.FC<BirthFormProps> = ({ onSubmit, loading }) => {
  const [date, setDate] = useState('');
  const [time, setTime] = useState('');
  const [latitude, setLatitude] = useState('');
  const [longitude, setLongitude] = useState('');
  const [ayanamsa, setAyanamsa] = useState('lahiri');
  const [houseSystem, setHouseSystem] = useState('W');

  const handleSubmit = () => {
    if (!date || !time || !latitude || !longitude) return;
    onSubmit({
      birth_datetime_utc: `${date}T${time}:00Z`,
      latitude: parseFloat(latitude),
      longitude: parseFloat(longitude),
      ayanamsa,
      house_system: houseSystem,
    });
  };

  return (
    <ScrollView style={styles.container}>
      <Text style={styles.label}>Birth Date (YYYY-MM-DD)</Text>
      <TextInput
        style={styles.input}
        placeholder="1986-06-15"
        value={date}
        onChangeText={setDate}
        keyboardType="default"
        accessibilityLabel="Birth date"
      />

      <Text style={styles.label}>Birth Time (HH:MM, 24h)</Text>
      <TextInput
        style={styles.input}
        placeholder="10:30"
        value={time}
        onChangeText={setTime}
        keyboardType="default"
        accessibilityLabel="Birth time"
      />

      <Text style={styles.label}>Latitude</Text>
      <TextInput
        style={styles.input}
        placeholder="28.6139"
        value={latitude}
        onChangeText={setLatitude}
        keyboardType="decimal-pad"
        accessibilityLabel="Latitude"
      />

      <Text style={styles.label}>Longitude</Text>
      <TextInput
        style={styles.input}
        placeholder="77.2090"
        value={longitude}
        onChangeText={setLongitude}
        keyboardType="decimal-pad"
        accessibilityLabel="Longitude"
      />

      <Text style={styles.label}>Ayanamsa</Text>
      <TextInput
        style={styles.input}
        value={ayanamsa}
        onChangeText={setAyanamsa}
        accessibilityLabel="Ayanamsa"
      />

      <Text style={styles.label}>House System (W/P/K/E)</Text>
      <TextInput
        style={styles.input}
        value={houseSystem}
        onChangeText={setHouseSystem}
        maxLength={1}
        accessibilityLabel="House system"
      />

      <TouchableOpacity
        style={[styles.button, loading && styles.buttonDisabled]}
        onPress={handleSubmit}
        disabled={loading}
        accessibilityRole="button"
        accessibilityLabel="Compute chart"
      >
        <Text style={styles.buttonText}>
          {loading ? 'Computing...' : 'Compute Chart'}
        </Text>
      </TouchableOpacity>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { padding: 16 },
  label: { fontSize: 14, fontWeight: '600', marginTop: 12, color: '#333' },
  input: {
    borderWidth: 1,
    borderColor: '#ccc',
    borderRadius: 8,
    padding: 12,
    fontSize: 16,
    marginTop: 4,
    backgroundColor: '#fff',
  },
  button: {
    backgroundColor: '#2c3e50',
    padding: 16,
    borderRadius: 8,
    alignItems: 'center',
    marginTop: 20,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#fff', fontSize: 16, fontWeight: '600' },
});
