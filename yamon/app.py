"""Main TUI application"""

from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widgets import Static, Header, Footer
from textual import work
from textual.timer import Timer
import asyncio

from yamon.collector import MetricsCollector


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
    
    .metrics-grid {
        grid-size-columns: 2;
        grid-gutter: 1;
        padding: 1;
    }
    
    .metric-box {
        height: 3;
        border: solid $primary;
        padding: 1;
        width: 1fr;
    }
    
    #cpu-value, #memory-value, #network-up-value, #network-down-value,
    #gpu-value, #ane-value, #cpu-power-value, #gpu-power-value,
    #ane-power-value, #system-power-value {
        content-align: left middle;
    }
    
    #cpu-label, #memory-label, #network-up-label, #network-down-label,
    #gpu-label, #ane-label, #cpu-power-label, #gpu-power-label,
    #ane-power-label, #system-power-label {
        text-style: bold;
        padding: 0 1;
    }
    
    #cpu-cores-container {
        margin-top: 1;
    }
    
    .cpu-cores {
        height: auto;
        border: solid $primary;
        padding: 1;
    }
    """
    
    BINDINGS = [
        ("q", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
    ]
    
    def __init__(self):
        super().__init__()
        self.collector = MetricsCollector()
        self.update_timer: Timer | None = None
    
    def compose(self) -> ComposeResult:
        """Create child widgets"""
        yield Header(show_clock=True)
        
        with Container(id="main-container"):
            with Horizontal():
                with Vertical():
                    yield Static("CPU Usage", id="cpu-label")
                    yield Static("0.0%", classes="metric-box", id="cpu-value")
                    
                    yield Static("Memory Usage", id="memory-label")
                    yield Static("0.0 B / 0.0 B (0.0%)", classes="metric-box", id="memory-value")
                    
                    yield Static("Network ↑ Upload", id="network-up-label")
                    yield Static("0.0 B/s", classes="metric-box", id="network-up-value")
                    
                    yield Static("Network ↓ Download", id="network-down-label")
                    yield Static("0.0 B/s", classes="metric-box", id="network-down-value")
                    
                    yield Static("GPU Usage", id="gpu-label")
                    yield Static("N/A", classes="metric-box", id="gpu-value")
                    
                    yield Static("ANE Usage", id="ane-label")
                    yield Static("N/A", classes="metric-box", id="ane-value")
                
                with Vertical():
                    yield Static("CPU Power", id="cpu-power-label")
                    yield Static("N/A", classes="metric-box", id="cpu-power-value")
                    
                    yield Static("GPU Power", id="gpu-power-label")
                    yield Static("N/A", classes="metric-box", id="gpu-power-value")
                    
                    yield Static("ANE Power", id="ane-power-label")
                    yield Static("N/A", classes="metric-box", id="ane-power-value")
                    
                    yield Static("System Power", id="system-power-label")
                    yield Static("N/A", classes="metric-box", id="system-power-value")
            
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
        except Exception as e:
            # If collection fails, show error
            error_widget = self.query_one("#cpu-value", Static)
            error_widget.update(f"Error: {e}")
            return
        
        # CPU
        cpu_widget = self.query_one("#cpu-value", Static)
        cpu_text = f"{metrics.cpu_percent:.1f}%"
        cpu_widget.update(cpu_text)
        cpu_widget.refresh()
        
        # Memory
        memory_widget = self.query_one("#memory-value", Static)
        memory_used = self.collector.format_bytes(metrics.memory_used)
        memory_total = self.collector.format_bytes(metrics.memory_total)
        memory_text = f"{memory_used} / {memory_total} ({metrics.memory_percent:.1f}%)"
        memory_widget.update(memory_text)
        memory_widget.refresh()
        
        # Network Upload
        network_up_widget = self.query_one("#network-up-value", Static)
        sent_rate_str = self.collector.format_bytes(int(metrics.network_sent_rate))
        network_up_widget.update(f"{sent_rate_str}/s")
        network_up_widget.refresh()
        
        # Network Download
        network_down_widget = self.query_one("#network-down-value", Static)
        recv_rate_str = self.collector.format_bytes(int(metrics.network_recv_rate))
        network_down_widget.update(f"{recv_rate_str}/s")
        network_down_widget.refresh()
        
        # CPU Cores
        cpu_cores_widget = self.query_one("#cpu-cores-value", Static)
        cores_str = " | ".join([f"C{i}: {core:.1f}%" for i, core in enumerate(metrics.cpu_per_core)])
        cpu_cores_widget.update(cores_str)
        
        # GPU Usage
        gpu_widget = self.query_one("#gpu-value", Static)
        if metrics.gpu_usage is not None:
            gpu_widget.update(f"{metrics.gpu_usage:.1f}%")
        else:
            gpu_widget.update("N/A")
        
        # ANE Usage
        ane_widget = self.query_one("#ane-value", Static)
        if metrics.ane_usage is not None:
            ane_widget.update(f"{metrics.ane_usage:.1f}%")
        else:
            ane_widget.update("N/A")
        
        # CPU Power
        cpu_power_widget = self.query_one("#cpu-power-value", Static)
        if metrics.cpu_power is not None:
            cpu_power_widget.update(f"{metrics.cpu_power:.2f} W")
        else:
            cpu_power_widget.update("N/A")
        
        # GPU Power
        gpu_power_widget = self.query_one("#gpu-power-value", Static)
        if metrics.gpu_power is not None:
            gpu_power_widget.update(f"{metrics.gpu_power:.2f} W")
        else:
            gpu_power_widget.update("N/A")
        
        # ANE Power
        ane_power_widget = self.query_one("#ane-power-value", Static)
        if metrics.ane_power is not None:
            ane_power_widget.update(f"{metrics.ane_power:.2f} W")
        else:
            ane_power_widget.update("N/A")
        
        # System Power
        system_power_widget = self.query_one("#system-power-value", Static)
        if metrics.system_power is not None:
            system_power_widget.update(f"{metrics.system_power:.2f} W")
        else:
            system_power_widget.update("N/A")
    
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

