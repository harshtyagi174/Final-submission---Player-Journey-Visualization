"""
LILA BLACK Player Journey Data Pipeline

Process raw telemetry data (.nakama-0 parquet files) into normalized JSON format
for visualization. Handles parsing, normalization, event classification, and
bot detection.

Usage:
    python pipeline.py --input data/raw --output data/processed
"""

import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from collections import defaultdict
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PlayerJourneyPipeline:
    """Main pipeline for processing player journey data."""
    
    def __init__(self, input_dir: str, output_dir: str):
        """Initialize pipeline with input/output directories."""
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Data storage
        self.matches = defaultdict(lambda: {
            'events': [],
            'player_count': set(),
            'duration_ms': 0,
            'map_id': None
        })
        
        logger.info(f"Pipeline initialized: input={self.input_dir}, output={self.output_dir}")
    
    def is_bot(self, player_id: str) -> bool:
        """Detect if player_id is a bot (numeric ID) or human (UUID)."""
        try:
            int(player_id)
            return True
        except ValueError:
            return False
    
    def classify_event(self, event_str: str) -> str:
        """Classify event type from event string."""
        event_lower = str(event_str).lower()
        
        # Map event strings to types
        if 'kill' in event_lower:
            return 'Kill' if not self.is_bot_event(event_str) else 'BotKill'
        elif 'death' in event_lower or 'killed' in event_lower or 'storm' in event_lower:
            return 'Death'
        elif 'loot' in event_lower:
            return 'Loot'
        elif 'position' in event_lower:
            return 'Position'
        else:
            return 'Other'
    
    def is_bot_event(self, event_str: str) -> bool:
        """Check if event involves a bot."""
        return 'bot' in str(event_str).lower()
    
    def normalize_coordinates(self, events: List[Dict]) -> Tuple[List[Dict], float, float, float, float]:
        """Normalize coordinates to 0-1 range."""
        if not events:
            return events, 0, 1, 0, 1
        
        # Extract coordinates
        x_coords = []
        y_coords = []
        for evt in events:
            if 'x' in evt and 'y' in evt and evt['x'] is not None and evt['y'] is not None:
                x_coords.append(float(evt['x']))
                y_coords.append(float(evt['y']))
        
        if not x_coords:
            logger.warning("No valid coordinates found")
            return events, 0, 1, 0, 1
        
        # Calculate bounds
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)
        
        # Avoid division by zero
        range_x = max_x - min_x or 1.0
        range_y = max_y - min_y or 1.0
        
        # Normalize
        for evt in events:
            if 'x' in evt and 'y' in evt and evt['x'] is not None and evt['y'] is not None:
                evt['pixel_x'] = (float(evt['x']) - min_x) / range_x
                evt['pixel_y'] = (float(evt['y']) - min_y) / range_y
        
        return events, min_x, max_x, min_y, max_y
    
    def load_parquet_file(self, file_path: Path) -> Optional[pd.DataFrame]:
        """Load a single parquet file (.nakama-0 file)."""
        try:
            df = pd.read_parquet(file_path)
            logger.debug(f"Loaded {file_path.name}: {len(df)} rows")
            return df
        except Exception as e:
            logger.error(f"Failed to load {file_path}: {e}")
            return None
    
    def parse_dataframe(self, df: pd.DataFrame, player_id: str, match_id: str) -> List[Dict]:
        """Convert DataFrame to normalized event list."""
        events = []
        
        if df.empty:
            logger.warning(f"Empty DataFrame for {player_id} in match {match_id}")
            return events
        
        for _, row in df.iterrows():
            try:
                # Extract event data
                event = {
                    'match_id': match_id,
                    'player_id': player_id,
                    'is_bot': self.is_bot(player_id),
                    'timestamp': int(row.get('timestamp', 0)) if row.get('timestamp') is not None else 0,
                    'event_type': self.classify_event(row.get('event_type', 'Other')),
                    'x': float(row.get('x', 0)) if row.get('x') is not None else 0,
                    'y': float(row.get('y', 0)) if row.get('y') is not None else 0,
                }
                
                # Add optional fields
                if 'player_name' in row and row['player_name']:
                    event['player_name'] = str(row['player_name'])
                if 'opponent_id' in row and row['opponent_id']:
                    event['opponent_id'] = str(row['opponent_id'])
                
                events.append(event)
            except Exception as e:
                logger.warning(f"Error parsing row for {player_id}: {e}")
                continue
        
        return events
    
    def process_file(self, file_path: Path):
        """Process a single .nakama-0 file."""
        # Parse filename: {player_id}_{match_id}.nakama-0
        filename = file_path.stem
        try:
            parts = filename.rsplit('_', 1)
            if len(parts) != 2:
                logger.warning(f"Invalid filename format: {filename}")
                return
            
            player_id, match_id = parts
        except Exception as e:
            logger.error(f"Failed to parse filename {filename}: {e}")
            return
        
        # Load data
        df = self.load_parquet_file(file_path)
        if df is None:
            return
        
        # Parse events
        events = self.parse_dataframe(df, player_id, match_id)
        if not events:
            return
        
        # Store events
        self.matches[match_id]['events'].extend(events)
        self.matches[match_id]['player_count'].add(player_id)
        
        # Infer map and duration
        if 'map_id' in df.columns:
            map_val = df['map_id'].iloc[0]
            if map_val:
                self.matches[match_id]['map_id'] = str(map_val)
        
        timestamps = [e['timestamp'] for e in events if e['timestamp']]
        if timestamps:
            self.matches[match_id]['duration_ms'] = max(self.matches[match_id]['duration_ms'], max(timestamps))
    
    def process_all_files(self):
        """Process all .nakama-0 files in input directory."""
        if not self.input_dir.exists():
            logger.error(f"Input directory does not exist: {self.input_dir}")
            return
        
        # Find all .nakama-0 files
        nakama_files = list(self.input_dir.glob('**/*.nakama-0'))
        logger.info(f"Found {len(nakama_files)} .nakama-0 files")
        
        for i, file_path in enumerate(nakama_files, 1):
            if i % 50 == 0:
                logger.info(f"Processing file {i}/{len(nakama_files)}")
            self.process_file(file_path)
        
        logger.info(f"Processed {len(nakama_files)} files into {len(self.matches)} matches")
    
    def normalize_matches(self):
        """Normalize all matches after loading."""
        for match_id, match_data in self.matches.items():
            # Normalize coordinates
            events, min_x, max_x, min_y, max_y = self.normalize_coordinates(match_data['events'])
            match_data['events'] = events
            
            # Convert player_count set to int
            match_data['player_count'] = len(match_data['player_count'])
            
            # Default map if not found
            if not match_data['map_id']:
                match_data['map_id'] = 'Unknown'
            
            logger.debug(f"Match {match_id}: {len(events)} events, {match_data['player_count']} players")
    
    def save_matches(self):
        """Save processed matches to JSON files."""
        if not self.matches:
            logger.warning("No matches to save")
            return
        
        for match_id, match_data in self.matches.items():
            try:
                output_file = self.output_dir / f"match_{match_id}.json"
                
                # Prepare output
                output = {
                    'match_id': match_id,
                    'map_id': match_data['map_id'],
                    'player_count': match_data['player_count'],
                    'duration_ms': match_data['duration_ms'],
                    'event_count': len(match_data['events']),
                    'events': match_data['events']
                }
                
                # Save JSON
                with open(output_file, 'w') as f:
                    json.dump(output, f, indent=2)
                
                logger.debug(f"Saved {output_file}")
            except Exception as e:
                logger.error(f"Failed to save match {match_id}: {e}")
        
        logger.info(f"Saved {len(self.matches)} matches to {self.output_dir}")
    
    def generate_summary(self) -> Dict:
        """Generate processing summary."""
        total_events = sum(len(m['events']) for m in self.matches.values())
        total_players = sum(m['player_count'] for m in self.matches.values())
        
        summary = {
            'timestamp': datetime.now().isoformat(),
            'total_matches': len(self.matches),
            'total_events': total_events,
            'total_players': total_players,
            'output_directory': str(self.output_dir),
            'matches': {
                match_id: {
                    'event_count': len(data['events']),
                    'player_count': data['player_count'],
                    'duration_ms': data['duration_ms'],
                    'map_id': data['map_id']
                }
                for match_id, data in self.matches.items()
            }
        }
        
        return summary
    
    def run(self):
        """Execute the full pipeline."""
        logger.info("=" * 60)
        logger.info("LILA BLACK Player Journey Pipeline")
        logger.info("=" * 60)
        
        # Process files
        self.process_all_files()
        
        # Normalize
        self.normalize_matches()
        
        # Save
        self.save_matches()
        
        # Summary
        summary = self.generate_summary()
        logger.info("\n" + "=" * 60)
        logger.info("PROCESSING SUMMARY")
        logger.info("=" * 60)
        logger.info(f"Total Matches: {summary['total_matches']}")
        logger.info(f"Total Events: {summary['total_events']}")
        logger.info(f"Total Players: {summary['total_players']}")
        logger.info("=" * 60)
        
        return summary


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description='Process LILA BLACK player telemetry data'
    )
    parser.add_argument(
        '--input',
        type=str,
        default='data/raw',
        help='Input directory containing .nakama-0 files'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='data/processed',
        help='Output directory for processed JSON files'
    )
    
    args = parser.parse_args()
    
    pipeline = PlayerJourneyPipeline(args.input, args.output)
    pipeline.run()


if __name__ == '__main__':
    main()
