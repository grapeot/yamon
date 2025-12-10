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
    
    #left-column, #right-column {
        width: 1fr;
        padding: 1;
    }
    
    #cpu-label, #memory-label, #network-up-label, #network-down-label,
    #gpu-label, #ane-label, #cpu-power-label, #gpu-power-label,
    #ane-power-label, #system-power-label {
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
            with Horizontal():
                with Vertical(id="left-column"):
                    yield Static("CPU Usage: 0.0%", id="cpu-label")
                    yield Static("", classes="chart-box", id="cpu-chart")
                    
                    yield Static("Memory Usage: 0.0%", id="memory-label")
                    yield Static("", classes="chart-box", id="memory-chart")
                    
                    yield Static("Network ↑ Upload: 0.0 B/s", id="network-up-label")
                    
                    yield Static("Network ↓ Download: 0.0 B/s", id="network-down-label")
                    yield Static("", classes="chart-box", id="network-chart")
                    
                    yield Static("GPU Usage: N/A", id="gpu-label")
                    
                    yield Static("ANE Usage: N/A", id="ane-label")
                
                with Vertical(id="right-column"):
                    yield Static("CPU Power: N/A", id="cpu-power-label")
                    
                    yield Static("GPU Power: N/A", id="gpu-power-label")
                    
                    yield Static("ANE Power: N/A", id="ane-power-label")
                    
                    yield Static("System Power: N/A", id="system-power-label")
                    yield Static("", classes="chart-box", id="power-chart")
            
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
        
        # Network Upload - update label with value
        network_up_label = self.query_one("#network-up-label", Static)
        sent_rate_str = self.collector.format_bytes(int(metrics.network_sent_rate))
        network_up_label.update(f"Network ↑ Upload: {sent_rate_str}/s")
        
        # Network Download - update label with value
        network_down_label = self.query_one("#network-down-label", Static)
        recv_rate_str = self.collector.format_bytes(int(metrics.network_recv_rate))
        network_down_label.update(f"Network ↓ Download: {recv_rate_str}/s")
        
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
        
        # CPU Power - update label with value
        cpu_power_label = self.query_one("#cpu-power-label", Static)
        if metrics.cpu_power is not None:
            cpu_power_label.update(f"CPU Power: {metrics.cpu_power:.2f} W")
        else:
            cpu_power_label.update("CPU Power: N/A")
        
        # GPU Power - update label with value
        gpu_power_label = self.query_one("#gpu-power-label", Static)
        if metrics.gpu_power is not None:
            gpu_power_label.update(f"GPU Power: {metrics.gpu_power:.2f} W")
        else:
            gpu_power_label.update("GPU Power: N/A")
        
        # ANE Power - update label with value
        ane_power_label = self.query_one("#ane-power-label", Static)
        if metrics.ane_power is not None:
            ane_power_label.update(f"ANE Power: {metrics.ane_power:.2f} W")
        else:
            ane_power_label.update("ANE Power: N/A")
        
        # System Power - update label with value
        system_power_label = self.query_one("#system-power-label", Static)
        if metrics.system_power is not None:
            system_power_label.update(f"System Power: {metrics.system_power:.2f} W")
        else:
            system_power_label.update("System Power: N/A")
        
        # Update charts
        self._update_charts()
    
    def _update_charts(self) -> None:
        """Update history charts"""
        # CPU Usage Chart - use full height chart
        cpu_values = self.history.cpu_percent.get_values()
        if cpu_values:
            cpu_chart = self.chart_renderer.render(cpu_values, min_value=0, max_value=100)
            try:
                cpu_chart_widget = self.query_one("#cpu-chart", Static)
                cpu_chart_widget.update(cpu_chart)
            except Exception as e:
                # Widget might not exist yet
                pass
        
        # Memory Usage Chart - use full height chart
        memory_values = self.history.memory_percent.get_values()
        if memory_values:
            memory_chart = self.chart_renderer.render(memory_values, min_value=0, max_value=100)
            try:
                memory_chart_widget = self.query_one("#memory-chart", Static)
                memory_chart_widget.update(memory_chart)
            except Exception:
                pass
        
        # Network Chart (combine upload and download)
        sent_values = self.history.network_sent_rate.get_values()
        recv_values = self.history.network_recv_rate.get_values()
        if sent_values or recv_values:
            # Normalize network values for display (convert to MB/s)
            sent_mb = [v / (1024 * 1024) for v in sent_values] if sent_values else []
            recv_mb = [v / (1024 * 1024) for v in recv_values] if recv_values else []
            
            # Combine into a single chart showing both
            max_len = max(len(sent_mb), len(recv_mb))
            combined = []
            for i in range(max_len):
                sent_val = sent_mb[i] if i < len(sent_mb) else 0
                recv_val = recv_mb[i] if i < len(recv_mb) else 0
                combined.append(max(sent_val, recv_val))  # Show the higher value
            
            if combined:
                # Find max value for scaling
                max_val = max(combined) if combined else 1
                network_chart = self.chart_renderer.render(combined, min_value=0, max_value=max(1, max_val * 1.1))
                try:
                    network_chart_widget = self.query_one("#network-chart", Static)
                    network_chart_widget.update(network_chart)
                except Exception:
                    pass
        
        # Power Chart (combine CPU, GPU, ANE)
        cpu_power_values = self.history.cpu_power.get_values()
        gpu_power_values = self.history.gpu_power.get_values()
        ane_power_values = self.history.ane_power.get_values()
        
        if cpu_power_values or gpu_power_values or ane_power_values:
            # Combine power values (sum or max)
            max_len = max(
                len(cpu_power_values) if cpu_power_values else 0,
                len(gpu_power_values) if gpu_power_values else 0,
                len(ane_power_values) if ane_power_values else 0
            )
            combined_power = []
            for i in range(max_len):
                cpu_val = cpu_power_values[i] if i < len(cpu_power_values) else 0
                gpu_val = gpu_power_values[i] if i < len(gpu_power_values) else 0
                ane_val = ane_power_values[i] if i < len(ane_power_values) else 0
                combined_power.append(cpu_val + gpu_val + ane_val)  # Sum of all power
            
            if combined_power:
                # Find max value for scaling
                max_power = max(combined_power) if combined_power else 1
                power_chart = self.chart_renderer.render(combined_power, min_value=0, max_value=max(1, max_power * 1.1))
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

