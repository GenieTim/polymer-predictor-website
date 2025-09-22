<script lang="ts">
  // This component displays a warning message if the browser does not support WebAssembly or any of the required features.

  import { simd, exceptionsFinal } from "wasm-feature-detect";
</script>

<div class="row">
  <noscript>
    <div class="alert alert-danger" role="alert">
      Your browser does not support WebAssembly. Please use a modern browser to
      access all features of this application.
    </div>
  </noscript>
  {#await simd then value}
    {#if !value}
      <div class="alert alert-danger" role="alert">
        Your browser does not support WebAssembly SIMD. Please use a modern
        browser to access all features of this application.
      </div>
    {/if}
  {/await}
  {#await exceptionsFinal then value}
    {#if !value}
      <div class="alert alert-danger" role="alert">
        Your browser does not support WebAssembly Exception Handling. Please use
        a modern browser to access all features of this application.
      </div>
    {/if}
  {/await}
</div>
