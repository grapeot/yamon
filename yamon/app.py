"""Main TUI application"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Header, Footer
from textual import work
from textual.timer import Timer
import asyncio

from yamon.collector import MetricsCollector
from yamon.history import MetricsHistory
from yamon.chart import ChartRenderer


class MetricsDisplay(Static):
    """Display metrics widget"""
    
    def __init__(self, title: str, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.title = title
        self.value = "N/A"
    
    def update_value(self, value: str):
        """Update displayed value"""
        self.value = value
        self.update(f"{self.title}: {value}")


class YamonApp(App):
    """Main application"""
    
    CSS = """
    Screen {
        background: $surface;
    }
    
    #main-container {
        height: 1fr;
    }
    
    Horizontal {
        width: 1fr;
        height: auto;
    }
    
    #row1-col1, #row1-col2, #row2-col1, #row2-col2, #row3-col1, #row3-col2 {
        width: 1fr;
        padding: 1;
    }
    
    #cpu-label, #memory-label, #network-label,
    #gpu-label, #ane-label, #system-power-label {
        text-style: bold;
        padding: 0 1;
        height: auto;
    }
    
    #cpu-cores-container {
        margin-top: 1;
    }
    
    .cpu-cores {
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    
    #charts-container {
        margin-top: 1;
        padding: 1;
        height: auto;
    }
    
    .chart-label {
        text-style: bold;
        padding: 0 1;
        margin-top: 1;
        height: auto;
    }
    
    .chart-box {
        border: solid $primary;
        padding: 1;
        height: auto;
        width: 1fr;
        min-height: 6;
        max-height: 8;
        margin-top: 0;
        margin-bottom: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]
    
    def __init__(self):
        super().__init__()
        self.collector = MetricsCollector()
        self.history = MetricsHistory(max_size=60)  # 60 seconds of history
        self.chart_renderer = ChartRenderer(width=50, height=10, use_unicode=True)
        self.update_timer: Timer | None = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            # Row 1: CPU Usage (left) and Power (right)
            with Horizontal():
                with Vertical(id="row1-col1"):
                    yield Static("CPU Usage: 0.0%", id="cpu-label")
                    yield Static("", classes="chart-box", id="cpu-chart")
                
                with Vertical(id="row1-col2"):
                    yield Static("Power: N/A", id="system-power-label")
                    yield Static("", classes="chart-box", id="power-chart")
            
            # Row 2: Memory Usage (left) and GPU Usage (right)
            with Horizontal():
                with Vertical(id="row2-col1"):
                    yield Static("Memory Usage: 0.0%", id="memory-label")
                    yield Static("", classes="chart-box", id="memory-chart")
                
                with Vertical(id="row2-col2"):
                    yield Static("GPU Usage: N/A", id="gpu-label")
                    yield Static("", classes="chart-box", id="gpu-chart")
            
            # Row 3: Network (left) and ANE Usage (right)
            with Horizontal():
                with Vertical(id="row3-col1"):
                    yield Static("Network: ↑ 0.0 B/s, ↓ 0.0 B/s", id="network-label")
                    yield Static("", classes="chart-box", id="network-chart")
                
                with Vertical(id="row3-col2"):
                    yield Static("ANE Usage: N/A", id="ane-label")
                    yield Static("", classes="chart-box", id="ane-chart")
            
            with Container(id="cpu-cores-container"):
                yield Static("CPU Cores:", classes="cpu-cores", id="cpu-cores-label")
                yield Static("N/A", classes="cpu-cores", id="cpu-cores-value")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app is mounted"""
        self.update_timer = self.set_interval(1.0, self.update_metrics)
        self.update_metrics()
    
    def update_metrics(self) -> None:
        """Update all metrics"""
        try:
            metrics = self.collector.collect()
            # Add to history
            self.history.add_metrics(metrics)
        except Exception as e:
            # If collection fails, show error
            error_label = self.query_one("#cpu-label", Static)
            error_label.update(f"CPU Usage: Error: {e}")
            return
        
        # CPU - update label with value
        cpu_label = self.query_one("#cpu-label", Static)
        cpu_label.update(f"CPU Usage: {metrics.cpu_percent:.1f}%")
        
        # Memory - update label with value
        memory_label = self.query_one("#memory-label", Static)
        memory_label.update(f"Memory Usage: {metrics.memory_percent:.1f}%")
        
        # Network - update label with both upload and download
        network_label = self.query_one("#network-label", Static)
        sent_rate_str = self.collector.format_bytes(int(metrics.network_sent_rate))
        recv_rate_str = self.collector.format_bytes(int(metrics.network_recv_rate))
        network_label.update(f"Network: ↑ {sent_rate_str}/s, ↓ {recv_rate_str}/s")
        
        # CPU Cores
        cpu_cores_widget = self.query_one("#cpu-cores-value", Static)
        cores_str = " | ".join([f"C{i}: {core:.1f}%" for i, core in enumerate(metrics.cpu_per_core)])
        cpu_cores_widget.update(cores_str)
        
        # GPU Usage - update label with value
        gpu_label = self.query_one("#gpu-label", Static)
        if metrics.gpu_usage is not None:
            gpu_label.update(f"GPU Usage: {metrics.gpu_usage:.1f}%")
        else:
            gpu_label.update("GPU Usage: N/A")
        
        # ANE Usage - update label with value
        ane_label = self.query_one("#ane-label", Static)
        if metrics.ane_usage is not None:
            ane_label.update(f"ANE Usage: {metrics.ane_usage:.1f}%")
        else:
            ane_label.update("ANE Usage: N/A")
        
        # Power - update label with all power values
        system_power_label = self.query_one("#system-power-label", Static)
        power_parts = []
        if metrics.cpu_power is not None:
            power_parts.append(f"CPU: {metrics.cpu_power:.2f}W")
        if metrics.gpu_power is not None:
            power_parts.append(f"GPU: {metrics.gpu_power:.2f}W")
        if metrics.ane_power is not None:
            power_parts.append(f"ANE: {metrics.ane_power:.2f}W")
        if metrics.system_power is not None:
            power_parts.append(f"System: {metrics.system_power:.2f}W")
        
        if power_parts:
            system_power_label.update(f"Power: {', '.join(power_parts)}")
        else:
            system_power_label.update("Power: N/A")
        
        # Update charts
        self._update_charts()
    
    def _update_charts(self) -> None:
        """Update history charts"""
        # CPU Usage Chart - use full height chart with Y-axis
        cpu_values = self.history.cpu_percent.get_values()
        if cpu_values:
            cpu_chart = self.chart_renderer.render(cpu_values, min_value=0, max_value=100, show_y_axis=True)
            try:
                cpu_chart_widget = self.query_one("#cpu-chart", Static)
                cpu_chart_widget.update(cpu_chart)
            except Exception as e:
                # Widget might not exist yet
                pass
        
        # Memory Usage Chart - use full height chart with Y-axis
        memory_values = self.history.memory_percent.get_values()
        if memory_values:
            memory_chart = self.chart_renderer.render(memory_values, min_value=0, max_value=100, show_y_axis=True)
            try:
                memory_chart_widget = self.query_one("#memory-chart", Static)
                memory_chart_widget.update(memory_chart)
            except Exception:
                pass
        
        # Network Chart - split chart (upload top, download bottom)
        sent_values = self.history.network_sent_rate.get_values()
        recv_values = self.history.network_recv_rate.get_values()
        if sent_values or recv_values:
            network_chart = self.chart_renderer.render_network_split(sent_values, recv_values, show_y_axis=True)
            try:
                network_chart_widget = self.query_one("#network-chart", Static)
                network_chart_widget.update(network_chart)
            except Exception:
                pass
        
        # GPU Usage Chart
        gpu_usage_values = self.history.gpu_usage.get_values()
        if gpu_usage_values:
            gpu_chart = self.chart_renderer.render(gpu_usage_values, min_value=0, max_value=100, show_y_axis=True)
            try:
                gpu_chart_widget = self.query_one("#gpu-chart", Static)
                gpu_chart_widget.update(gpu_chart)
            except Exception:
                pass
        
        # ANE Usage Chart
        ane_usage_values = self.history.ane_usage.get_values()
        if ane_usage_values:
            ane_chart = self.chart_renderer.render(ane_usage_values, min_value=0, max_value=100, show_y_axis=True)
            try:
                ane_chart_widget = self.query_one("#ane-chart", Static)
                ane_chart_widget.update(ane_chart)
            except Exception:
                pass
        
        # Power Chart - try stacked chart, fallback to combined
        cpu_power_values = self.history.cpu_power.get_values()
        gpu_power_values = self.history.gpu_power.get_values()
        ane_power_values = self.history.ane_power.get_values()
        
        if cpu_power_values or gpu_power_values or ane_power_values:
            # Try stacked chart
            max_len = max(
                len(cpu_power_values) if cpu_power_values else 0,
                len(gpu_power_values) if gpu_power_values else 0,
                len(ane_power_values) if ane_power_values else 0
            )
            
            if max_len > 0:
                # Calculate max for scaling
                combined_power = []
                for i in range(max_len):
                    cpu_val = cpu_power_values[i] if i < len(cpu_power_values) else 0
                    gpu_val = gpu_power_values[i] if i < len(gpu_power_values) else 0
                    ane_val = ane_power_values[i] if i < len(ane_power_values) else 0
                    combined_power.append(cpu_val + gpu_val + ane_val)
                
                max_power = max(combined_power) if combined_power else 1
                
                # Try stacked chart (CPU bottom, GPU middle, ANE top)
                try:
                    power_chart = self.chart_renderer.render_stacked(
                        cpu_power_values if cpu_power_values else [],
                        gpu_power_values if gpu_power_values else [],
                        ane_power_values if ane_power_values else [],
                        min_value=0,
                        max_value=max(1, max_power * 1.1),
                        show_y_axis=True
                    )
                except Exception:
                    # Fallback to simple combined chart
                    power_chart = self.chart_renderer.render(combined_power, min_value=0, max_value=max(1, max_power * 1.1), show_y_axis=True)
                
                try:
                    power_chart_widget = self.query_one("#power-chart", Static)
                    power_chart_widget.update(power_chart)
                except Exception:
                    pass
    
    def action_refresh(self) -> None:
        """Manual refresh"""
        self.update_metrics()
    
    def action_quit(self) -> None:
        """Quit application"""
        self.exit()


def main():
    """Main entry point"""
    app = YamonApp()
    app.run()


if __name__ == "__main__":
    main()

