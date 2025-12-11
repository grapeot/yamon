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
               max_value: Optional[float] = None, show_y_axis: bool = True) -> str:
        """Render a chart from a list of values"""
        if not values:
            empty_chart = ' ' * self.width
            if show_y_axis:
                return f"{max_value or 0:.1f}\n" + '\n'.join([empty_chart] * self.height) + f"\n{min_value or 0:.1f}"
            return empty_chart
        
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
        
        # Get latest values (rightmost = newest)
        latest_scaled = scaled[-self.width:] if len(scaled) > self.width else scaled
        # Pad with spaces on the left if we have fewer values than width
        if len(latest_scaled) < self.width:
            padding = [' '] * (self.width - len(latest_scaled))
            latest_scaled = padding + latest_scaled
        
        # Render chart (right to left, newest on right)
        chart_lines = []
        for row in range(self.height):
            line = []
            for col in range(self.width):
                data_idx = col  # Now we're using latest_scaled which is already aligned
                if data_idx < len(latest_scaled):
                    bar_height = latest_scaled[data_idx] if isinstance(latest_scaled[data_idx], int) else 0
                    # Invert row (0 is top, height-1 is bottom)
                    if row >= (self.height - bar_height):
                        line.append(self._get_block_char(bar_height, row))
                    else:
                        line.append(' ')
                else:
                    line.append(' ')
            chart_lines.append(''.join(line))
        
        chart_text = '\n'.join(chart_lines)
        
        # Add Y-axis labels
        if show_y_axis:
            # Format max and min values
            max_str = f"{max_value:.1f}"
            min_str = f"{min_value:.1f}"
            # Pad to same width
            max_width = max(len(max_str), len(min_str))
            max_str = max_str.rjust(max_width)
            min_str = min_str.rjust(max_width)
            
            # Add labels to each line
            lines_with_labels = []
            lines_with_labels.append(f"{max_str} │")
            for i, line in enumerate(chart_lines):
                lines_with_labels.append(f"{' ' * max_width} │{line}")
            lines_with_labels.append(f"{min_str} │")
            
            return '\n'.join(lines_with_labels)
        
        return chart_text
    
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
    
    def render_network_split(self, sent_values: List[float], recv_values: List[float], 
                            width: int = None, show_y_axis: bool = True) -> str:
        """Render network chart with upload (top) and download (bottom) split"""
        if width is None:
            width = self.width
        
        if not sent_values and not recv_values:
            empty_chart = ' ' * width
            if show_y_axis:
                return f"0.0\n" + '\n'.join([empty_chart] * self.height) + f"\n0.0"
            return empty_chart
        
        # Convert to MB/s
        sent_mb = [v / (1024 * 1024) for v in sent_values] if sent_values else []
        recv_mb = [v / (1024 * 1024) for v in recv_values] if recv_values else []
        
        # Get latest values
        sent_latest = sent_mb[-width:] if len(sent_mb) > width else sent_mb
        recv_latest = recv_mb[-width:] if len(recv_mb) > width else recv_mb
        
        # Pad with zeros on the left
        if len(sent_latest) < width:
            sent_latest = [0.0] * (width - len(sent_latest)) + sent_latest
        if len(recv_latest) < width:
            recv_latest = [0.0] * (width - len(recv_latest)) + recv_latest
        
        # Find max values for scaling (can use different scales)
        sent_max = max(sent_latest) if sent_latest else 1
        recv_max = max(recv_latest) if recv_latest else 1
        
        # Use separate scales or combined scale
        overall_max = max(sent_max, recv_max, 1)
        sent_max = max(sent_max, overall_max * 0.1)  # Ensure some range
        recv_max = max(recv_max, overall_max * 0.1)
        
        # Split height in half
        half_height = self.height // 2
        
        # Scale values
        sent_scaled = []
        for val in sent_latest:
            normalized = val / sent_max if sent_max > 0 else 0
            sent_scaled.append(int(normalized * half_height))
        
        recv_scaled = []
        for val in recv_latest:
            normalized = val / recv_max if recv_max > 0 else 0
            recv_scaled.append(int(normalized * half_height))
        
        # Render chart
        chart_lines = []
        
        # Top half: upload (inverted, growing down from top)
        for row in range(half_height):
            line = []
            for col in range(width):
                bar_height = sent_scaled[col]
                if row < bar_height:
                    line.append('█')
                else:
                    line.append(' ')
            chart_lines.append(''.join(line))
        
        # Middle separator
        chart_lines.append('─' * width)
        
        # Bottom half: download (growing up from bottom)
        for row in range(half_height):
            line = []
            for col in range(width):
                bar_height = recv_scaled[col]
                if row >= (half_height - bar_height):
                    line.append('█')
                else:
                    line.append(' ')
            chart_lines.append(''.join(line))
        
        chart_text = '\n'.join(chart_lines)
        
        # Add Y-axis labels
        if show_y_axis:
            sent_max_str = f"{sent_max:.1f}"
            recv_max_str = f"{recv_max:.1f}"
            max_width = max(len(sent_max_str), len(recv_max_str))
            
            lines_with_labels = []
            lines_with_labels.append(f"{sent_max_str.rjust(max_width)} │")  # Top max
            for i, line in enumerate(chart_lines[:half_height]):
                lines_with_labels.append(f"{' ' * max_width} │{line}")
            lines_with_labels.append(f"{' ' * max_width} │{chart_lines[half_height]}")  # Separator
            for i, line in enumerate(chart_lines[half_height+1:]):
                lines_with_labels.append(f"{' ' * max_width} │{line}")
            lines_with_labels.append(f"{recv_max_str.rjust(max_width)} │")  # Bottom max
            
            return '\n'.join(lines_with_labels)
        
        return chart_text
    
    def render_stacked(self, bottom_values: List[float], middle_values: List[float], 
                      top_values: List[float], width: int = None, 
                      min_value: Optional[float] = None, max_value: Optional[float] = None,
                      show_y_axis: bool = True) -> str:
        """Render a stacked chart with three layers"""
        if width is None:
            width = self.width
        
        # Combine all values for max calculation
        all_values = []
        max_len = max(
            len(bottom_values) if bottom_values else 0,
            len(middle_values) if middle_values else 0,
            len(top_values) if top_values else 0
        )
        
        for i in range(max_len):
            bottom = bottom_values[i] if i < len(bottom_values) else 0
            middle = middle_values[i] if i < len(middle_values) else 0
            top = top_values[i] if i < len(top_values) else 0
            all_values.append(bottom + middle + top)
        
        if not all_values:
            empty_chart = ' ' * width
            if show_y_axis:
                return f"{max_value or 0:.1f}\n" + '\n'.join([empty_chart] * self.height) + f"\n{min_value or 0:.1f}"
            return empty_chart
        
        # Get latest values
        bottom_latest = (bottom_values[-width:] if len(bottom_values) > width else bottom_values) if bottom_values else []
        middle_latest = (middle_values[-width:] if len(middle_values) > width else middle_values) if middle_values else []
        top_latest = (top_values[-width:] if len(top_values) > width else top_values) if top_values else []
        all_latest = all_values[-width:] if len(all_values) > width else all_values
        
        # Pad with zeros
        if len(bottom_latest) < width:
            bottom_latest = [0.0] * (width - len(bottom_latest)) + bottom_latest
        if len(middle_latest) < width:
            middle_latest = [0.0] * (width - len(middle_latest)) + middle_latest
        if len(top_latest) < width:
            top_latest = [0.0] * (width - len(top_latest)) + top_latest
        
        # Normalize
        if min_value is None:
            min_value = 0
        if max_value is None:
            max_value = max(all_latest) if all_latest else 1
        
        value_range = max_value - min_value
        if value_range == 0:
            value_range = 1
        
        # Scale to chart coordinates
        bottom_scaled = [int((v / value_range) * self.height) for v in bottom_latest]
        middle_scaled = [int((v / value_range) * self.height) for v in middle_latest]
        top_scaled = [int((v / value_range) * self.height) for v in top_latest]
        
        # Render stacked chart
        chart_lines = []
        for row in range(self.height):
            line = []
            for col in range(width):
                bottom_h = bottom_scaled[col]
                middle_h = middle_scaled[col]
                top_h = top_scaled[col]
                
                total_h = bottom_h + middle_h + top_h
                row_from_bottom = self.height - 1 - row
                
                if row_from_bottom < bottom_h:
                    line.append('█')  # Bottom layer
                elif row_from_bottom < bottom_h + middle_h:
                    line.append('▓')  # Middle layer
                elif row_from_bottom < bottom_h + middle_h + top_h:
                    line.append('▒')  # Top layer
                else:
                    line.append(' ')
            chart_lines.append(''.join(line))
        
        chart_text = '\n'.join(chart_lines)
        
        # Add Y-axis labels
        if show_y_axis:
            max_str = f"{max_value:.1f}"
            min_str = f"{min_value:.1f}"
            max_width = max(len(max_str), len(min_str))
            
            lines_with_labels = []
            lines_with_labels.append(f"{max_str.rjust(max_width)} │")
            for line in chart_lines:
                lines_with_labels.append(f"{' ' * max_width} │{line}")
            lines_with_labels.append(f"{min_str.rjust(max_width)} │")
            
            return '\n'.join(lines_with_labels)
        
        return chart_text

