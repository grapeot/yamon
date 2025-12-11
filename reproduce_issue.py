
from yamon.chart import ChartRenderer

def test_renderer_dimensions():
    renderer = ChartRenderer(width=50, height=12)
    values = [float(i) for i in range(100)]
    
    print("--- Test Dynamic Render (100x12) ---")
    # Request width=100, height=12
    # Expect output width ~100 (plus padding chars potentially if axis added? No, axis is part of string)
    # The current implementation prepends "max |" to the line.
    
    output = renderer.render(values, show_y_axis=True, width=100, height=12)
    lines = output.split('\n')
    
    print(f"Line count: {len(lines)}")
    # Check max line width (some lines might be shorter if empty, but here full)
    max_line_width = max(len(l) for l in lines)
    print(f"Max line width: {max_line_width}")
    
    if len(lines) == 12:
        print("PASS: Output height matches requested height (12)")
    else:
        print(f"FAIL: Output height {len(lines)} != 12")
        
    # Width check: The chart body is 100 char. + Y axis label width (e.g. "100.0 |")
    # "100.0" is 5 chars. " |" is 2 chars. Total ~7 chars prefix.
    # So expected width approx 107.
    if max_line_width >= 100:
        print("PASS: Output width reflects dynamic sizing")
    else:
        print(f"FAIL: Output width {max_line_width} < 100")

    print("\n--- Test Dynamic Network Chart (80x10) ---")
    sent = [float(i) for i in range(100)]
    recv = [float(i) for i in range(100)]
    output = renderer.render_network_split(sent, recv, show_y_axis=True, width=80, height=10)
    lines = output.split('\n')
    print(f"Line count: {len(lines)}")
    max_line_width = max(len(l) for l in lines)
    print(f"Max line width: {max_line_width}")
    
    if len(lines) == 10:
        print("PASS: Network chart height matches requested height (10)")
    else:
        print(f"FAIL: Network chart height {len(lines)} != 10")
        
    if max_line_width >= 80:
         print("PASS: Network chart width reflects dynamic sizing")

if __name__ == "__main__":
    test_renderer_dimensions()
