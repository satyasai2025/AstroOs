/**
 * D1 chart rendering (simplified North Indian style).
 *
 * Displays planet positions in a 12-house diamond layout using SVG.
 */
import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import Svg, { Polygon, Text as SvgText } from 'react-native-svg';

interface ChartViewProps {
  chart: Record<string, unknown>;
  title?: string;
}

const HOUSE_POINTS: Record<number, string> = {
  1: '100,0 200,0 200,100 100,100',
  2: '0,0 100,0 100,100 0,100',
  3: '200,0 300,0 300,100 200,100',
  4: '0,100 100,100 100,200 0,200',
  5: '200,100 300,100 300,200 200,200',
  6: '100,100 200,100 200,200 100,200',
  7: '0,200 100,200 100,300 0,300',
  8: '200,200 300,200 300,300 200,300',
  9: '0,300 100,300 100,400 0,400',
  10: '200,300 300,300 300,400 200,400',
  11: '100,300 200,300 200,400 100,400',
  12: '100,200 200,200 200,300 100,300',
};

const HOUSE_CENTERS: Record<number, { x: number; y: number }> = {
  1: { x: 150, y: 50 },
  2: { x: 50, y: 50 },
  3: { x: 250, y: 50 },
  4: { x: 50, y: 150 },
  5: { x: 250, y: 150 },
  6: { x: 150, y: 150 },
  7: { x: 50, y: 250 },
  8: { x: 250, y: 250 },
  9: { x: 50, y: 350 },
  10: { x: 250, y: 350 },
  11: { x: 150, y: 350 },
  12: { x: 150, y: 250 },
};

export const ChartView: React.FC<ChartViewProps> = ({ chart, title }) => {
  const houses = (chart?.houses ?? []) as Array<{ number: number; planets: string[] }>;
  const ascendant = (chart?.ascendant as { rashi?: string }) ?? {};

  return (
    <View style={styles.container}>
      {title && <Text style={styles.title}>{title}</Text>}
      <Text style={styles.ascendant}>Ascendant: {ascendant.rashi ?? '--'}</Text>
      <Svg width={300} height={400} viewBox="0 0 300 400">
        {/* Render houses */}
        {Object.entries(HOUSE_POINTS).map(([num, points]) => {
          const n = parseInt(num, 10);
          const house = houses.find((h) => h.number === n);
          const planets = house?.planets ?? [];
          const center = HOUSE_CENTERS[n];
          return (
            <React.Fragment key={num}>
              <Polygon
                points={points}
                fill={n % 2 === 0 ? '#f9f9f9' : '#fff'}
                stroke="#333"
                strokeWidth={1}
              />
              <SvgText
                x={center.x}
                y={center.y - 8}
                textAnchor="middle"
                fontSize={10}
                fill="#666"
              >
                {n}
              </SvgText>
              <SvgText
                x={center.x}
                y={center.y + 8}
                textAnchor="middle"
                fontSize={9}
                fill="#2c3e50"
              >
                {planets.slice(0, 3).join(', ')}
              </SvgText>
            </React.Fragment>
          );
        })}
      </Svg>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { alignItems: 'center', padding: 16 },
  title: { fontSize: 18, fontWeight: '700', marginBottom: 8, color: '#2c3e50' },
  ascendant: { fontSize: 14, color: '#555', marginBottom: 12 },
});
