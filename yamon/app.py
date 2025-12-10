"""Main TUI application"""

from textual.app import App, ComposeResult
from textual.containers import Container, Grid
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
    
    .metrics-grid {
        grid-size: 2;
        grid-gutter: 1;
        padding: 1;
    }
    
    .metric-box {
        height: 3;
        border: solid $primary;
        padding: 1;
    }
    
    .metric-label {
        text-style: bold;
    }
    
    .cpu-cores {
        height: auto;
        border: solid $primary;
        padding: 1;
        margin-top: 1;
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
            with Grid(classes="metrics-grid"):
                yield Static("CPU Usage", classes="metric-box metric-label", id="cpu-label")
                yield Static("N/A", classes="metric-box", id="cpu-value")
                
                yield Static("Memory Usage", classes="metric-box metric-label", id="memory-label")
                yield Static("N/A", classes="metric-box", id="memory-value")
                
                yield Static("Network Upload", classes="metric-box metric-label", id="network-up-label")
                yield Static("N/A", classes="metric-box", id="network-up-value")
                
                yield Static("Network Download", classes="metric-box metric-label", id="network-down-label")
                yield Static("N/A", classes="metric-box", id="network-down-value")
            
            yield Static("CPU Cores:", classes="cpu-cores", id="cpu-cores-label")
            yield Static("N/A", classes="cpu-cores", id="cpu-cores-value")
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Called when app is mounted"""
        self.update_timer = self.set_interval(1.0, self.update_metrics)
        self.update_metrics()
    
    def update_metrics(self) -> None:
        """Update all metrics"""
        metrics = self.collector.collect()
        
        # CPU
        cpu_widget = self.query_one("#cpu-value", Static)
        cpu_widget.update(f"{metrics.cpu_percent:.1f}%")
        
        # Memory
        memory_widget = self.query_one("#memory-value", Static)
        memory_used = self.collector.format_bytes(metrics.memory_used)
        memory_total = self.collector.format_bytes(metrics.memory_total)
        memory_widget.update(f"{memory_used} / {memory_total} ({metrics.memory_percent:.1f}%)")
        
        # Network Upload
        network_up_widget = self.query_one("#network-up-value", Static)
        network_up_widget.update(f"{self.collector.format_bytes(metrics.network_sent_rate)}/s")
        
        # Network Download
        network_down_widget = self.query_one("#network-down-value", Static)
        network_down_widget.update(f"{self.collector.format_bytes(metrics.network_recv_rate)}/s")
        
        # CPU Cores
        cpu_cores_widget = self.query_one("#cpu-cores-value", Static)
        cores_str = " | ".join([f"C{i}: {core:.1f}%" for i, core in enumerate(metrics.cpu_per_core)])
        cpu_cores_widget.update(cores_str)
    
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

