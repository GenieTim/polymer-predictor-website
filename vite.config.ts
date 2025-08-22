import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// Adjust the base path for GitHub Pages deployments. When served from
// https://<user>.github.io/<repo>/ assets need the repo sub-path.
// If you later use a custom domain (CNAME) you can set base back to '/'.
const repoName = 'pylimer-predictor-website'
const isCI = process.env.GITHUB_ACTIONS === 'true'

export default defineConfig({
  plugins: [svelte()],
  base: isCI ? `/${repoName}/` : '/',
})
