/**
 * Utility to get the correct base path for assets in both development and production.
 * 
 * In development: base path is '/'
 * On GitHub Pages: base path is '/pylimer-predictor-website/'
 * 
 * This ensures that all asset paths work correctly regardless of deployment environment.
 */

/**
 * Gets the base path for the application.
 * Uses Vite's import.meta.env.BASE_URL which is automatically set based on the 
 * base configuration in vite.config.ts
 */
export function getBasePath(): string {
  return import.meta.env.BASE_URL;
}

/**
 * Creates an asset path by prepending the correct base path.
 * 
 * @param path - The relative path to the asset (e.g., 'models/m-.onnx')
 * @returns The full path with base path prepended
 * 
 * @example
 * // In development: getAssetPath('models/m-.onnx') -> '/models/m-.onnx'
 * // On GitHub Pages: getAssetPath('models/m-.onnx') -> '/pylimer-predictor-website/models/m-.onnx'
 */
export function getAssetPath(path: string): string {
  const basePath = getBasePath();
  // Remove leading slash from path if present to avoid double slashes
  const cleanPath = path.startsWith('/') ? path.slice(1) : path;
  // Ensure base path ends with slash and append the clean path
  return basePath.endsWith('/') ? basePath + cleanPath : basePath + '/' + cleanPath;
}
