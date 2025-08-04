# ARC-AGI 2 Dataset Exploration Framework

A comprehensive analysis framework for exploring the 1,000 training tasks in the ARC-AGI 2 (Abstraction and Reasoning Corpus - Artificial General Intelligence) dataset. This toolkit provides deep insights into visual reasoning patterns, transformations, and cognitive primitives required for solving these puzzles.

## 🎯 Overview

The ARC-AGI 2 dataset contains 1,000 unique visual reasoning tasks that challenge both humans and AI systems. This framework provides:

- **Pattern Recognition**: Identifies spatial patterns, symmetries, and transformations
- **Task Categorization**: Classifies tasks by complexity and cognitive requirements  
- **Statistical Analysis**: Comprehensive data insights and correlations
- **Visualization Suite**: Interactive charts, grids, and analysis dashboards
- **Human Performance Analysis**: Studies solving patterns and success rates
- **Report Generation**: Detailed analysis summaries and recommendations

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Phidancer/philo-dancer.git
cd philo-dancer

# Install dependencies
pip install -r requirements.txt

# Download ARC-AGI 2 dataset (if not already available)
python scripts/download_dataset.py
```

### Basic Usage

```python
from arc_agi_framework import DataLoader, PatternAnalyzer, Visualizer

# Load dataset
loader = DataLoader()
tasks = loader.load_training_data()

# Analyze patterns
analyzer = PatternAnalyzer()
patterns = analyzer.analyze_all_tasks(tasks)

# Generate visualizations
viz = Visualizer()
viz.create_analysis_dashboard(patterns)
```