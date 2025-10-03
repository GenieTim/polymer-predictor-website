# Polymer Predictor Website

A web application for predicting polymer properties using physics-based and machine learning methods. Built with Svelte, TypeScript, and Vite.

## Features

- **Neural Network Predictions**: Machine learning models for polymer property estimation
- **MMT Property Analysis**: Mean-field theory calculations for polymer networks
- **ANT Force Balance**: Advanced numerical techniques for polymer mechanics
- **Normal Mode Analysis**: Dynamic modulus predictions through vibrational analysis
- **Client-side Processing**: All computations run locally using WebAssembly
- **Multiple Polymer Types**: Support for PDMS and other polymer systems

## Getting Started

The installation of this website is available at [polymer-predictor.ethz.ch](https://polymer-predictor.ethz.ch).
The following information is for developers who want to build/modify/run/host the website themselves.

### Prerequisites

- Node.js 18 or higher
- Modern browser with WebAssembly support

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

### Build

```bash
npm run build
```

### Preview

```bash
npm run preview
```

## Architecture

The application uses WebAssembly builds of the [pylimer-tools](https://github.com/GenieTim/pylimer-tools) library to perform polymer property calculations entirely in the browser. This ensures:

- Complete data privacy (no server communication)
- Fast local computation
- Offline capability once loaded

## Key Components

- **Prediction Interface**: Interactive form for setting polymer parameters
- **Multiple Predictors**: ANT, MMT, NMA, and Neural Network methods
- **Real-time Results**: Live updates as predictions complete
- **Progress Tracking**: Visual feedback during computation

## Related Research

- [MMT Analysis](https://doi.org/10.1021/acs.macromol.3c02544)
- [Force Balance Procedure](https://doi.org/10.1021/acspolymersau.5c00036)
- [Normal Mode Analysis](https://doi.org/10.1021/acs.macromol.4c01429)

## Contributing

Issues and pull requests are welcome. See the [GitHub repository](https://github.com/GenieTim/pylimer-predictor-website) for more details.
