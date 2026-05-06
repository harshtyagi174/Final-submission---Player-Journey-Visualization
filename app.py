"""
LILA BLACK Player Journey Visualization Dashboard

Interactive Streamlit dashboard for visualizing player movement, events,
and interactions in match telemetry data.

Run with:
    streamlit run app.py
"""

import streamlit as st
import json
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import plotly.graph_objects as go
from collections import defaultdict

# Page config
st.set_page_config(
    page_title="LILA BLACK Player Journey",
    page_icon="🎮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Title
st.title("🎮 LILA BLACK Player Journey Visualization")
st.markdown("**Interactive analysis of player movement and event patterns**")


@st.cache_data
def load_processed_data(data_dir: str = "data/processed") -> dict:
    """Load all processed match JSON files."""
    data_path = Path(data_dir)
    
    if not data_path.exists():
        return {}
    
    matches = {}
    for json_file in sorted(data_path.glob("match_*.json")):
        try:
            with open(json_file, 'r') as f:
                match_data = json.load(f)
                match_id = match_data.get('match_id', json_file.stem)
                matches[match_id] = match_data
        except Exception as e:
            st.warning(f"Failed to load {json_file.name}: {e}")
    
    return matches


def get_event_colors() -> dict:
    """Get consistent color mapping for event types."""
    return {
        'Kill': '#FF6B6B',  # Red
        'BotKill': '#FF8C8C',  # Light Red
        'Death': '#FFB6B6',  # Very Light Red
        'Loot': '#4ECDC4',  # Teal
        'Position': '#95E1D3',  # Light Teal
        'Other': '#999999'  # Gray
    }


def create_movement_plot(events: list, filters: dict) -> go.Figure:
    """Create scatter plot of player movement."""
    df = pd.DataFrame(events)
    
    # Apply filters
    if filters['event_types']:
        df = df[df['event_type'].isin(filters['event_types'])]
    
    if filters['player_type'] == 'Human':
        df = df[df['is_bot'] == False]
    elif filters['player_type'] == 'Bot':
        df = df[df['is_bot'] == True]
    
    if filters['time_range']:
        min_time, max_time = filters['time_range']
        df = df[(df['timestamp'] >= min_time) & (df['timestamp'] <= max_time)]
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No events match the selected filters")
        return fig
    
    # Prepare data
    colors = get_event_colors()
    df['color'] = df['event_type'].map(colors)
    df['player_type'] = df['is_bot'].apply(lambda x: 'Bot' if x else 'Human')
    
    # Create traces for each event type
    fig = go.Figure()
    
    for event_type in df['event_type'].unique():
        event_df = df[df['event_type'] == event_type]
        
        fig.add_trace(go.Scatter(
            x=event_df['pixel_x'],
            y=event_df['pixel_y'],
            mode='markers',
            name=event_type,
            marker=dict(
                size=8,
                color=colors.get(event_type, '#999999'),
                opacity=0.7,
                line=dict(
                    width=2 if event_type in ['Kill', 'Death'] else 0,
                    color='white' if event_type in ['Kill', 'Death'] else None
                )
            ),
            text=[
                f"<b>{row['event_type']}</b><br>"
                f"Player: {row['player_id']}<br>"
                f"Type: {'Bot' if row['is_bot'] else 'Human'}<br>"
                f"Position: ({row['pixel_x']:.2f}, {row['pixel_y']:.2f})<br>"
                f"Time: {row['timestamp']}ms"
                for _, row in event_df.iterrows()
            ],
            hovertemplate='%{text}<extra></extra>',
            showlegend=True
        ))
    
    # Layout
    fig.update_layout(
        title="Player Movement Map",
        xaxis_title="X Position (Normalized)",
        yaxis_title="Y Position (Normalized)",
        hovermode='closest',
        height=600,
        template='plotly_dark',
        xaxis=dict(range=[0, 1]),
        yaxis=dict(range=[0, 1]),
        showlegend=True,
        legend=dict(x=1.05, y=1, xanchor='left', yanchor='top')
    )
    
    fig.update_yaxes(scaleanchor="x", scaleratio=1)
    
    return fig


def create_heatmap(events: list, filters: dict, grid_size: int = 20) -> go.Figure:
    """Create heatmap of event density."""
    df = pd.DataFrame(events)
    
    # Apply same filters as movement plot
    if filters['event_types']:
        df = df[df['event_type'].isin(filters['event_types'])]
    
    if filters['player_type'] == 'Human':
        df = df[df['is_bot'] == False]
    elif filters['player_type'] == 'Bot':
        df = df[df['is_bot'] == True]
    
    if filters['time_range']:
        min_time, max_time = filters['time_range']
        df = df[(df['timestamp'] >= min_time) & (df['timestamp'] <= max_time)]
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No events match the selected filters")
        return fig
    
    # Create 2D histogram
    heatmap_data = np.zeros((grid_size, grid_size))
    
    for _, row in df.iterrows():
        x_idx = int(row['pixel_x'] * (grid_size - 1))
        y_idx = int(row['pixel_y'] * (grid_size - 1))
        x_idx = max(0, min(x_idx, grid_size - 1))
        y_idx = max(0, min(y_idx, grid_size - 1))
        heatmap_data[y_idx, x_idx] += 1
    
    fig = go.Figure(data=go.Heatmap(
        z=heatmap_data,
        colorscale='Viridis',
        showscale=True,
        colorbar=dict(title="Event Count")
    ))
    
    fig.update_layout(
        title="Event Density Heatmap",
        xaxis_title="X Position (Grid)",
        yaxis_title="Y Position (Grid)",
        height=600,
        template='plotly_dark'
    )
    
    return fig


def create_timeline(events: list, filters: dict) -> go.Figure:
    """Create timeline of events over time."""
    df = pd.DataFrame(events)
    
    # Apply filters
    if filters['event_types']:
        df = df[df['event_type'].isin(filters['event_types'])]
    
    if filters['player_type'] == 'Human':
        df = df[df['is_bot'] == False]
    elif filters['player_type'] == 'Bot':
        df = df[df['is_bot'] == True]
    
    if df.empty:
        fig = go.Figure()
        fig.add_annotation(text="No events match the selected filters")
        return fig
    
    # Count events by type over time
    df_sorted = df.sort_values('timestamp')
    df_sorted['bin'] = pd.cut(df_sorted['timestamp'], bins=20)
    
    # Create histogram
    colors = get_event_colors()
    fig = go.Figure()
    
    for event_type in df_sorted['event_type'].unique():
        event_df = df_sorted[df_sorted['event_type'] == event_type]
        event_counts = event_df.groupby('bin').size()
        
        fig.add_trace(go.Bar(
            x=[str(b) for b in event_counts.index],
            y=event_counts.values,
            name=event_type,
            marker_color=colors.get(event_type, '#999999'),
            opacity=0.7
        ))
    
    fig.update_layout(
        title="Event Timeline (Binned)",
        xaxis_title="Time (Bins)",
        yaxis_title="Event Count",
        barmode='stack',
        height=400,
        template='plotly_dark',
        hovermode='x unified'
    )
    
    return fig


def main():
    """Main app logic."""
    # Load data
    matches = load_processed_data()
    
    if not matches:
        st.error("No processed data found. Please run the pipeline first:\n```\npython src/pipeline.py --input <raw-data-dir> --output data/processed\n```")
        return
    
    # Sidebar for controls
    st.sidebar.header("⚙️ Controls")
    
    # Match selector
    match_ids = sorted(matches.keys())
    selected_match = st.sidebar.selectbox(
        "Select Match",
        match_ids,
        help="Choose a match to visualize"
    )
    
    # Get selected match data
    match_data = matches[selected_match]
    events = match_data.get('events', [])
    
    if not events:
        st.warning(f"No events in match {selected_match}")
        return
    
    # Display match info
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Events", match_data.get('event_count', 0))
    with col2:
        st.metric("Players", match_data.get('player_count', 0))
    with col3:
        st.metric("Map", match_data.get('map_id', 'Unknown'))
    with col4:
        duration_s = match_data.get('duration_ms', 0) / 1000
        st.metric("Duration", f"{duration_s:.1f}s")
    
    st.divider()
    
    # Filters
    st.sidebar.subheader("🔍 Filters")
    
    # Event type filter
    event_types = sorted(set(e['event_type'] for e in events))
    selected_events = st.sidebar.multiselect(
        "Event Types",
        event_types,
        default=event_types,
        help="Select which event types to display"
    )
    
    # Player type filter
    has_bots = any(e['is_bot'] for e in events)
    has_humans = any(not e['is_bot'] for e in events)
    
    player_type_options = []
    if has_humans:
        player_type_options.append('Human')
    if has_bots:
        player_type_options.append('Bot')
    player_type_options.append('Both')
    
    player_type = st.sidebar.selectbox(
        "Player Type",
        player_type_options,
        help="Filter by human players or bots"
    )
    
    # Timeline filter
    timestamps = [e['timestamp'] for e in events if e['timestamp']]
    if timestamps:
        min_time, max_time = min(timestamps), max(timestamps)
        
        selected_range = st.sidebar.slider(
            "Timeline (ms)",
            min_time, max_time, (min_time, max_time),
            help="Select time window to visualize"
        )
    else:
        selected_range = None
    
    # Build filters
    filters = {
        'event_types': selected_events,
        'player_type': 'Both' if player_type == 'Both' else player_type,
        'time_range': selected_range
    }
    
    # Main content
    st.subheader("📊 Visualizations")
    
    # Movement plot and heatmap side by side
    col1, col2 = st.columns(2)
    
    with col1:
        st.plotly_chart(create_movement_plot(events, filters), use_container_width=True)
    
    with col2:
        st.plotly_chart(create_heatmap(events, filters), use_container_width=True)
    
    # Timeline
    st.plotly_chart(create_timeline(events, filters), use_container_width=True)
    
    # Statistics
    st.subheader("📈 Statistics")
    
    df = pd.DataFrame(events)
    
    # Apply filters for stats
    if filters['event_types']:
        df = df[df['event_type'].isin(filters['event_types'])]
    if filters['player_type'] != 'Both':
        is_bot = filters['player_type'] == 'Bot'
        df = df[df['is_bot'] == is_bot]
    if filters['time_range']:
        min_time, max_time = filters['time_range']
        df = df[(df['timestamp'] >= min_time) & (df['timestamp'] <= max_time)]
    
    # Event breakdown
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.write("**Event Breakdown**")
        event_counts = df['event_type'].value_counts()
        st.bar_chart(event_counts)
    
    with col2:
        st.write("**Player Type Distribution**")
        player_counts = df['is_bot'].apply(lambda x: 'Bot' if x else 'Human').value_counts()
        st.bar_chart(player_counts)
    
    with col3:
        st.write("**Top Players by Events**")
        top_players = df['player_id'].value_counts().head(10)
        st.bar_chart(top_players)
    
    # Detailed event table
    st.subheader("📋 Event Details")
    
    if not df.empty:
        # Create display dataframe
        display_df = df[[
            'player_id', 'event_type', 'is_bot', 'timestamp', 'pixel_x', 'pixel_y'
        ]].copy()
        
        display_df['is_bot'] = display_df['is_bot'].apply(lambda x: 'Bot' if x else 'Human')
        display_df = display_df.rename(columns={
            'player_id': 'Player ID',
            'event_type': 'Event Type',
            'is_bot': 'Type',
            'timestamp': 'Time (ms)',
            'pixel_x': 'X (Norm)',
            'pixel_y': 'Y (Norm)'
        })
        
        st.dataframe(display_df, use_container_width=True)
    else:
        st.info("No events match the selected filters.")


if __name__ == '__main__':
    main()
