/**
 * Component Exports
 *
 * Central export point for all UI components used in the Ingredient Scanner app.
 * Platform-specific components (like ImageCapture) are automatically resolved
 * by React Native's platform-specific extension mechanism (.web.tsx, .native.tsx).
 *
 * @module components
 * @author Uday Tamma
 * @license MIT
 */

// Image capture - platform-specific implementations
// React Native bundler automatically selects .web.tsx for web builds
export { ImageCapture } from './ImageCapture';

// Ingredient analysis visualization components
export { IngredientCard } from './IngredientCard';
export { SafetyMeter } from './SafetyMeter';
export { SafetyBar } from './SafetyBar';
export { RiskBadge } from './RiskBadge';

// User interface components
export { ProfileSelector } from './ProfileSelector';
export { ResultsHeader } from './ResultsHeader';
