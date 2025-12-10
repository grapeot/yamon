"""ASCII chart rendering for terminal"""

from typing import List, Optional
import math


class ChartRenderer:
    """Render ASCII charts from historical data"""
    
    # Unicode block characters for smoother charts
    BLOCKS = [
        ' ',      # 0/8
        '▁',      # 1/8
        '▂',      # 2/8
        '▃',      # 3/8
        '▄',      # 4/8
        '▅',      # 5/8
        '▆',      # 6/8
        '▇',      # 7/8
        '█',      # 8/8
    ]
    
    # Simple ASCII characters (fallback)
    ASCII_BLOCKS = [' ', '.', ':', '|', '#']
    
    def __init__(self, width: int = 50, height: int = 10, use_unicode: bool = True):
        self.width = width
        self.height = height
        self.use_unicode = use_unicode
    
    def render(self, values: List[float], min_value: Optional[float] = None, 
               max_value: Optional[float] = None) -> str:
        """Render a chart from a list of values"""
        if not values:
            return ' ' * self.width
        
        # Normalize values to chart height
        if min_value is None:
            min_value = min(values) if values else 0
        if max_value is None:
            max_value = max(values) if values else 100
        
        # Avoid division by zero
        value_range = max_value - min_value
        if value_range == 0:
            value_range = 1
        
        # Scale values to chart coordinates
        scaled = []
        for value in values:
            normalized = (value - min_value) / value_range
            scaled.append(int(normalized * self.height))
        
        # Render chart (right to left, newest on right)
        chart_lines = []
        for row in range(self.height):
            line = []
            for col in range(self.width):
                # Map column to data index (rightmost = newest)
                data_idx = len(scaled) - self.width + col
                if data_idx < 0:
                    line.append(' ')
                elif data_idx < len(scaled):
                    bar_height = scaled[data_idx]
                    # Invert row (0 is top, height-1 is bottom)
                    if row >= (self.height - bar_height):
                        line.append(self._get_block_char(bar_height, row))
                    else:
                        line.append(' ')
                else:
                    line.append(' ')
            chart_lines.append(''.join(line))
        
        return '\n'.join(chart_lines)
    
    def _get_block_char(self, bar_height: int, current_row: int) -> str:
        """Get appropriate block character for bar height"""
        if self.use_unicode:
            # Use Unicode block characters
            # Calculate which block character to use based on position in bar
            row_in_bar = current_row - (self.height - bar_height)
            if row_in_bar < 0:
                return ' '
            
            # For full blocks, use solid block
            if bar_height >= self.height:
                return '█'
            
            # For partial blocks at top, use appropriate character
            if row_in_bar == bar_height - 1 and bar_height < self.height:
                # Top of bar - use partial block
                fraction = (bar_height % 1) if bar_height < self.height else 1.0
                block_idx = min(int(fraction * 8), 8)
                return self.BLOCKS[block_idx]
            
            return '█'
        else:
            # Use simple ASCII
            return '#'
    
    def render_simple(self, values: List[float], width: int = None) -> str:
        """Render a simple one-line chart"""
        if width is None:
            width = self.width
        
        if not values:
            return ' ' * width
        
        # Get latest values
        latest = values[-width:] if len(values) > width else values
        
        # Normalize
        min_val = min(latest) if latest else 0
        max_val = max(latest) if latest else 100
        range_val = max_val - min_val if max_val != min_val else 1
        
        # Render
        chart = []
        for value in latest:
            normalized = (value - min_val) / range_val
            height = int(normalized * 8)  # 8 levels
            chart.append(self.BLOCKS[min(height, 8)])
        
        return ''.join(chart)
    
    def render_sparkline(self, values: List[float], width: int = None) -> str:
        """Render a sparkline chart (single line)"""
        if width is None:
            width = self.width
        
        if not values:
            return '─' * width
        
        # Get latest values
        latest = values[-width:] if len(values) > width else values
        
        # Normalize
        min_val = min(latest) if latest else 0
        max_val = max(latest) if latest else 100
        range_val = max_val - min_val if max_val != min_val else 1
        
        # Sparkline characters: ▁▂▃▄▅▆▇█
        spark_chars = ['▁', '▂', '▃', '▄', '▅', '▆', '▇', '█']
        
        chart = []
        for value in latest:
            normalized = (value - min_val) / range_val
            char_idx = min(int(normalized * 8), 7)
            chart.append(spark_chars[char_idx])
        
        return ''.join(chart)

