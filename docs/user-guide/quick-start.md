# Quick Start Guide

Get up and running with VibeCheck in minutes!

## Basic Usage

### 1. Activate Environment
```bash
cd VibeCheck
poetry shell
```

### 2. Collect Restaurant Data
```python
from vibecheck.data_collection import RestaurantCollector

# Initialize collector
collector = RestaurantCollector(api_key="your_serpapi_key")

# Collect images for restaurants
collector.collect_images(restaurant_names=["Restaurant Name"])
```

### 3. Process Images
```python
from vibecheck.preprocessing import ImagePreprocessor

# Initialize preprocessor
preprocessor = ImagePreprocessor()

# Process collected images
preprocessor.process_directory("restaurant_images/")
```

### 4. Find Similar Restaurants
```python
from vibecheck.similarity import SimilarityMatcher

# Initialize matcher
matcher = SimilarityMatcher()

# Find similar restaurants
similar = matcher.find_similar("Restaurant Name", top_k=5)
print(similar)
```

## Running the Application

### Web Interface
```bash
# Start the web application
poetry run streamlit run app.py
```

Visit `http://localhost:8501` in your browser.

## Example Workflow

Here's a complete example:
```python
from vibecheck import VibeCheck

# Initialize VibeCheck
vc = VibeCheck(api_key="your_key")

# Add a restaurant
vc.add_restaurant("Founding Farmers DC")

# Get recommendations based on aesthetics
recommendations = vc.recommend_similar(
    restaurant_name="Founding Farmers DC",
    top_k=5
)

# Display results
for resto in recommendations:
    print(f"{resto['name']}: {resto['similarity']:.2f}")
```

## Next Steps

- Explore the [API Reference](../reference/) for detailed documentation
- Check out example notebooks in `/notebooks`
- Read the [Contributing Guide](../contributing.md) to contribute
