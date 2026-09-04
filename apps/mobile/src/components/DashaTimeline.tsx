/**
 * Dasha timeline component — shows Mahadasha periods with active period.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';

interface DashaPeriod {
  lord: string;
  start: string;
  end: string;
  is_active?: boolean;
}

interface DashaTimelineProps {
  periods: DashaPeriod[];
  system?: string;
}

export const DashaTimeline: React.FC<DashaTimelineProps> = ({
  periods,
  system = 'Vimshottari',
}) => {
  if (!periods.length) {
    return (
      <View style={styles.container}>
        <Text style={styles.empty}>No Dasha data available.</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <Text style={styles.title}>{system} Mahadasha</Text>
      {periods.map((p, i) => (
        <View
          key={`${p.lord}-${i}`}
          style={[styles.period, p.is_active && styles.activePeriod]}
        >
          <View style={styles.periodHeader}>
            <Text style={[styles.lord, p.is_active && styles.activeLord]}>
              {p.lord}
            </Text>
            {p.is_active && <Text style={styles.activeBadge}>ACTIVE</Text>}
          </View>
          <Text style={styles.dates}>
            {p.start} → {p.end}
          </Text>
        </View>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  container: { padding: 16 },
  title: { fontSize: 18, fontWeight: '700', marginBottom: 12, color: '#2c3e50' },
  empty: { fontSize: 14, color: '#999', fontStyle: 'italic' },
  period: {
    padding: 12,
    marginVertical: 4,
    borderRadius: 8,
    backgroundColor: '#f5f5f5',
    borderLeftWidth: 3,
    borderLeftColor: '#bdc3c7',
  },
  activePeriod: {
    backgroundColor: '#e8f4f8',
    borderLeftColor: '#2980b9',
  },
  periodHeader: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  lord: { fontSize: 16, fontWeight: '600', color: '#333' },
  activeLord: { color: '#2980b9' },
  activeBadge: {
    fontSize: 10,
    fontWeight: '700',
    color: '#fff',
    backgroundColor: '#2980b9',
    paddingHorizontal: 6,
    paddingVertical: 2,
    borderRadius: 4,
    overflow: 'hidden',
  },
  dates: { fontSize: 12, color: '#777', marginTop: 4 },
});
