/**
 * AstroOS Mobile — Root App Component
 *
 * Local-first React Native app for chart computation and research.
 * Connects to the user's local AstroOS API by default.
 */
import React, { useEffect } from 'react';
import { AppNavigator } from './src/navigation/AppNavigator';
import { loadSettings } from './src/storage/settings';

const App: React.FC = () => {
  useEffect(() => {
    loadSettings();
  }, []);

  return <AppNavigator />;
};

export default App;
