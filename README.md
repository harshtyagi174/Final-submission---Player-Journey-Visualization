# LILA BLACK Player Journey Visualization Tool

## Overview

This is a complete end-to-end pipeline and visualization dashboard for analyzing player movement, events, and interactions in LILA BLACK match telemetry data. The tool processes raw `.nakama-0` (Apache Parquet) files and provides an interactive dashboard for exploring player journeys.

## Features

- **Data Pipeline**: Automated ETL processing of raw telemetry data
- **Event Classification**: Automatic categorization of events (Kill, Death, Loot, Position, etc.)
- **Bot Detection**: Identifies bots (numeric player IDs) vs humans (UUID player IDs)
- **Coordinate Normalization**: Maps pixel coordinates to 0-1 range for consistency
- **Interactive Dashboard**: Streamlit-based visualization with filters and real-time updates
- **Movement Visualization**: Scatter plot showing player positions with event markers
- **Density Heatmap**: Event concentration visualization across the map
- **Timeline Analysis**: Historical view of events throughout the match
- **Player Statistics**: Breakdown of events by type, player type, and individual players

## Project Structure

```
lila-player-visualization/
├── src/
│   └── pipeline.py              # Data processing ETL pipeline
├── app.py                       # Streamlit dashboard
├── data/
│   ├── raw/                     # Raw .nakama-0 files (input)
│   └── processed/               # Processed JSON files (output)
├── requirements.txt             # Python dependencies
├── README.md                    # This file
├── ARCHITECTURE.md              # Technical design document
└── INSIGHTS.md                  # Data insights and recommendations
```

## Installation

### Prerequisites
- Python 3.11+ (Python 3.13 recommended on Windows)
- pip (Python package manager)

> Note: On Windows, if you encounter file-lock errors like `WinError 32` while installing Streamlit, close any running Python/Streamlit sessions and retry.

### Steps

1. **Open a terminal in the project root**:
   ```bash
   cd lila-player-visualization
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**:
   - Command Prompt:
     ```bat
     .\.venv\Scripts\activate.bat
     ```
   - PowerShell:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```

4. **Upgrade packaging tools**:
   ```bash
   python -m pip install --upgrade pip wheel setuptools
   ```

5. **Install dependencies**:
   ```bash
   python -m pip install -r requirements.txt
   ```

6. **If Streamlit install still fails**, install it directly after upgrading pip:
   ```bash
   python -m pip install streamlit
   ```

### Windows helper

If you are on Windows, run the provided helper script:
```bat
windows_setup.bat
```

This will create a `.venv`, activate it, upgrade pip/wheel/setuptools, and install the required dependencies.

## Usage

### 1. Prepare Raw Data

Place your `.nakama-0` files in the `data/raw/` directory. The pipeline expects files with the naming pattern:
```
{player_id}_{match_id}.nakama-0
```

Example:
```
data/raw/
├── 0019c582-574d-4a53-9f77-554519b75b4c_1298e3e2-2776-4038-ba9b-72808b041561.nakama-0
├── 036692b4-8185-422d-823a-9e4c394ba75e_3aabe6a4-59cc-44c1-870d-6791adae5b2f.nakama-0
└── ...
```

### 2. Run the Pipeline

Process raw data into normalized JSON format:

```bash
python src/pipeline.py --input data/raw --output data/processed
```

**Options:**
- `--input` (default: `data/raw`): Directory containing .nakama-0 files
- `--output` (default: `data/processed`): Output directory for processed JSON files

**Example output:**
```
INFO:root:======================================
INFO:root:LILA BLACK Player Journey Pipeline
INFO:root:======================================
INFO:root:Found 1243 .nakama-0 files
INFO:root:Processing file 50/1243
INFO:root:Processed 1243 files into 882 matches
INFO:root:======================================
INFO:root:PROCESSING SUMMARY
INFO:root:======================================
INFO:root:Total Matches: 882
INFO:root:Total Events: 285,342
INFO:root:Total Players: 1,544
INFO:root:======================================
```

### 3. Launch the Dashboard

Start the Streamlit visualization:

```bash
streamlit run app.py
```

If `streamlit` is not available on your PATH after activation, use:

```bash
python -m streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## Dashboard Features

### Match Selection
- Dropdown to select from all processed matches
- Displays match metadata (events, players, map, duration)

### Filters
- **Event Types**: Select which event types to display (Kill, Death, Loot, Position, etc.)
- **Player Type**: Filter for human players, bots, or both
- **Timeline**: Select a time window (ms) to focus on specific moments in the match

### Visualizations

1. **Movement Map** (Scatter Plot)
   - Shows player positions with event markers
   - Color-coded by event type
   - Hover for detailed event information
   - Bold outline for significant events (Kill, Death)

2. **Event Density Heatmap**
   - Shows where events cluster on the map
   - Darker areas indicate more events
   - Grid-based representation

3. **Event Timeline**
   - Stacked bar chart showing event distribution over time
   - Binned into 20 equal time intervals
   - Color-coded by event type

### Statistics
- Event breakdown by type
- Player type distribution
- Top 10 players by event count
- Detailed event table with filtering and sorting

## Data Processing Details

### Input Format
- **File Type**: Apache Parquet (despite `.nakama-0` extension)
- **Filename Pattern**: `{player_id}_{match_id}.nakama-0`
- **Bot Detection**: Player ID is numeric (e.g., "1440") → Bot; UUID format → Human

### Output Format
Each processed match is saved as JSON with the following structure:

```json
{
  "match_id": "match-uuid",
  "map_id": "AmbroseValley",
  "player_count": 42,
  "duration_ms": 1200000,
  "event_count": 285,
  "events": [
    {
      "match_id": "match-uuid",
      "player_id": "player-uuid",
      "is_bot": false,
      "timestamp": 5000,
      "event_type": "Kill",
      "x": 1024.5,
      "y": 768.3,
      "pixel_x": 0.512,
      "pixel_y": 0.384,
      "player_name": "PlayerName"
    },
    ...
  ]
}
```

### Event Classification
- **Kill**: Player eliminated another player
- **BotKill**: Bot eliminated another player
- **Death**: Player was eliminated
- **Loot**: Player picked up items
- **Position**: Position update (movement)
- **Other**: Unclassified events

### Coordinate Normalization
Raw pixel coordinates are normalized to 0-1 range for:
- Consistency across different map sizes
- Simplified visualization and heatmap generation
- Better statistical analysis

## Deployment

### Local Development
```bash
streamlit run app.py
```

### Streamlit Cloud

1. Push the project to GitHub
2. Connect your repository to Streamlit Cloud (https://streamlit.io/cloud)
3. Deploy with a single click
4. Access your app at `https://<username>-<reponame>-<hash>.streamlit.app`

### Docker (Optional)

Create a `Dockerfile`:
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8501
CMD ["streamlit", "run", "app.py"]
```

Build and run:
```bash
docker build -t lila-player-viz .
docker run -p 8501:8501 lila-player-viz
```

## Configuration

### Environment Variables (Optional)

Create a `.streamlit/config.toml` file to customize the dashboard:

```toml
[theme]
primaryColor = "#FF6B6B"
backgroundColor = "#1a1a1a"
secondaryBackgroundColor = "#262630"
textColor = "#fafafa"

[server]
maxUploadSize = 200
enableXsrfProtection = false
```

## Troubleshooting

### No data displays in the dashboard
- Ensure you've run the pipeline: `python src/pipeline.py`
- Check that `data/processed/` contains `.json` files
- Look for error messages in the pipeline logs

### Out of memory errors
- The pipeline processes all files at once; for very large datasets, consider:
  - Processing data by date range
  - Increasing system RAM
  - Running on a server with more resources

### Slow performance
- Large heatmaps (grid_size > 30) can be slow
- Reduce the time window using the timeline filter
- Consider pre-filtering on specific event types

## Technical Stack

- **Backend**: Python 3.11+
- **Data Processing**: pandas, numpy, pyarrow
- **Frontend**: Streamlit
- **Visualization**: Plotly
- **Deployment**: Streamlit Cloud / Docker

## Performance Metrics

- **Pipeline Processing**: ~2-5 seconds per 100 files (depends on system)
- **Data Processing**: 1,243 files (1.2 GB) → 882 matches in <60 seconds
- **Dashboard Load**: <500ms for typical match
- **Memory Usage**: ~500MB for full dataset

## Known Limitations

1. Very large matches (>10,000 events) may be slow in the heatmap
2. Timeline slider is binned to 20 intervals for performance
3. Coordinate normalization assumes different pixel ranges per match
4. Real-time data ingestion not yet supported (batch processing only)

## Future Enhancements

- [ ] Real-time data streaming
- [ ] Player path tracing and trajectory analysis
- [ ] Minimap overlay support
- [ ] Advanced filtering (by opponent, by location)
- [ ] Performance profiling and heat intensity metrics
- [ ] Export visualizations as images/videos
- [ ] Multiplayer comparison mode
- [ ] Machine learning-based anomaly detection

## License

Project created for LILA BLACK player telemetry analysis.

## Support

For issues or questions, please refer to the ARCHITECTURE.md document for technical details.
