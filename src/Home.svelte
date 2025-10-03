<script>
  import FeatureWarning from "./components/FeatureWarning.svelte";
  import { getBasePath } from "./utils/basePath";

  let predictorLink = getBasePath() + "/predictor";
</script>

<div class="container-fluid">
  <!-- Hero Section -->
  <div class="row">
    <div class="col-lg-8">
      <div class="card">
        <div class="card-body">
          <h1 class="card-title">Welcome to Polymer Predictor!</h1>
          <p class="card-text lead">
            Advanced physics-based and machine learning tools for predicting
            polymer properties.
          </p>

          <a href={predictorLink} class="btn btn-primary btn-lg">
            <i class="fas fa-chart-line"></i>
            Start Predictions
          </a>

          <p class="card-text mt-3">
            This platform provides cutting-edge physics-based and machine
            learning predictions for polymer properties. Get started for free!
          </p>
        </div>
      </div>
    </div>

    <div class="col-lg-4">
      <div class="card">
        <div class="card-header">
          <h5 class="mb-0">Key Features</h5>
        </div>
        <div class="card-body">
          <ul class="list-group list-group-flush">
            <li class="list-group-item d-flex align-items-center">
              <i class="fas fa-brain text-primary me-2"></i>
              Neural Network Predictions
            </li>
            <li class="list-group-item d-flex align-items-center">
              <i class="fas fa-chart-bar text-success me-2"></i>
              <a
                href="https://doi.org/10.1021/acs.macromol.3c02544"
                class="text-decoration-none"
              >
                MMT Property Analysis
              </a>
            </li>
            <li class="list-group-item d-flex align-items-center">
              <i class="fas fa-balance-scale text-info me-2"></i>
              <a
                href="https://doi.org/10.1021/acspolymersau.5c00036"
                class="text-decoration-none"
              >
                Force Balance Procedure
              </a>
            </li>
            <li class="list-group-item d-flex align-items-center">
              <i class="fas fa-wave-square text-warning me-2"></i>
              <a
                href="https://doi.org/10.1021/acs.macromol.4c01429"
                class="text-decoration-none"
              >
                Normal Mode Analysis
              </a>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </div>

  <!-- Feature Warning Section -->
  <FeatureWarning />

  <!-- About Section -->
  <div class="row mt-4">
    <div class="col-12">
      <div class="card">
        <div class="card-header">
          <h2 class="mb-0">About Polymer Predictor</h2>
        </div>
        <div class="card-body">
          <p class="card-text">
            Polymer Predictor is an innovative platform that leverages advanced
            physics-based and machine learning techniques for predicting polymer
            properties. Our mission is to empower researchers and industry
            professionals with powerful tools that enhance understanding and
            manipulation of polymer materials while significantly reducing time
            and costs associated with expensive trial-and-error processes.
          </p>
        </div>
      </div>
    </div>
  </div>

  <!-- Explanation & Contact Section -->
  <div class="row mt-4">
    <div class="col-lg-6">
      <div class="card h-100">
        <div class="card-header">
          <h3 class="mb-0">How It Works</h3>
        </div>
        <div class="card-body">
          <p class="card-text">
            This tool utilizes a WebAssembly version of the
            <a
              href="https://github.com/GenieTim/pylimer-tools"
              class="text-decoration-none"
              title="GitHub Repository of pylimer-tools"
            >
              pylimer-tools
            </a>
            library, enabling fast and efficient execution of polymer property predictions
            directly in your browser.
          </p>

          <div class="alert alert-warning" role="alert">
            <h6 class="alert-heading">
              <i class="fas fa-exclamation-triangle"></i>
              Important Notes
            </h6>
            <ul class="mb-0">
              <li>Requires a modern browser with WebAssembly support</li>
              <li>All computations run locally - no data sent to servers</li>
              <li>Ensures complete privacy and data security</li>
              <li>No automatic error reporting or usage analytics</li>
            </ul>
          </div>

          <p class="card-text">
            <small class="text-muted">
              Please consider providing feedback or contributing to the
              <a
                href="https://github.com/GenieTim/pylimer-predictor-website"
                class="text-decoration-none"
                title="GitHub Repository of pylimer-predictor-website"
                >polymer-predictor-website</a
              >
              repository to help improve the tool.
            </small>
          </p>
        </div>
      </div>
    </div>

    <div class="col-lg-6">
      <div class="card">
        <div class="card-header">
          <h3 class="mb-0">Contact & Support</h3>
        </div>
        <div class="card-body">
          <p class="card-text">
            Have questions or need assistance (again, we don't get automatic
            error reports)? We're here to help! Reach out to us at
            <a
              href="mailto:support@bernhard-webstudio.ch"
              class="text-decoration-none"
              title="Email Support"
            >
              <i class="fas fa-envelope"></i>
              support@bernhard-webstudio.ch
            </a>
            or open an issue on the
            <a
              href="https://github.com/GenieTim/pylimer-predictor-website"
              class="text-decoration-none"
              title="GitHub Repository of polymer-predictor-website"
              >GitHub repository</a
            > of this site.
          </p>
        </div>
      </div>
    </div>
  </div>
</div>
