/**
 * Home screen — birth data entry and chart computation entry point.
 */
import React, { useState } from 'react';
import {
  View, Text, StyleSheet, SafeAreaView, StatusBar, ScrollView,
} from 'react-native';
import { BirthForm } from '../components/BirthForm';
import { ChartView } from '../components/ChartView';
import { DashaTimeline } from '../components/DashaTimeline';
import { useChart } from '../hooks/useChart';

export const HomeScreen: React.FC = () => {
  const { chart, loading, error, fromCache, compute } = useChart();
  const [showDetail, setShowDetail] = useState(false);

  const dashaPeriods = (
    (chart?.dasha_summary as Array<{ lord: string; start: string; end: string; is_active?: boolean }>)
    ?? []
  );

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#fff" />
      <ScrollView>
        <Text style={styles.header}>AstroOS</Text>
        <Text style={styles.subtitle}>Vedic Astrology Research</Text>

        {!chart && (
          <BirthForm onSubmit={compute} loading={loading} />
        )}

        {error && (
          <View style={styles.errorBox}>
            <Text style={styles.errorText}>{error}</Text>
          </View>
        )}

        {chart && (
          <View>
            {fromCache && (
              <View style={styles.cacheBadge}>
                <Text style={styles.cacheText}>Offline — cached data</Text>
              </View>
            )}

            <ChartView chart={chart} title="D1 Birth Chart" />

            {dashaPeriods.length > 0 && (
              <DashaTimeline periods={dashaPeriods} />
            )}

            <View style={styles.yogaSummary}>
              <Text style={styles.yogaTitle}>Active Yogas</Text>
              {((chart?.yogas as Array<{ yoga_name: string; strength_score?: number }>) ?? [])
                .filter((y) => y.yoga_name)
                .slice(0, 5)
                .map((y, i) => (
                  <Text key={i} style={styles.yogaItem}>
                    • {y.yoga_name}
                    {y.strength_score != null ? ` (${y.strength_score}/100)` : ''}
                  </Text>
                ))}
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#fff' },
  header: {
    fontSize: 28, fontWeight: '700', textAlign: 'center',
    color: '#2c3e50', marginTop: 16,
  },
  subtitle: {
    fontSize: 14, textAlign: 'center', color: '#777', marginBottom: 16,
  },
  errorBox: {
    backgroundColor: '#fce4e4', padding: 12, margin: 16,
    borderRadius: 8, borderLeftWidth: 3, borderLeftColor: '#e74c3c',
  },
  errorText: { color: '#c0392b', fontSize: 14 },
  cacheBadge: {
    backgroundColor: '#fef9e7', padding: 8, margin: 16,
    borderRadius: 6, alignItems: 'center',
  },
  cacheText: { color: '#f39c12', fontSize: 12, fontWeight: '600' },
  yogaSummary: { padding: 16 },
  yogaTitle: { fontSize: 16, fontWeight: '700', color: '#2c3e50', marginBottom: 8 },
  yogaItem: { fontSize: 14, color: '#555', marginVertical: 2 },
});
