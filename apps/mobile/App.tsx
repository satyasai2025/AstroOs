/**
 * AstroOS Mobile — Root App Component
 *
 * Local-first React Native app for chart computation and research.
 * Connects to the user's local AstroOS API by default.
 */
import React from 'react';
import { AppNavigator } from './src/navigation/AppNavigator';

const App: React.FC = () => <AppNavigator />;

export default App;
