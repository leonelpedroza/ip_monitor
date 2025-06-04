# ip_monitor_gui.pyw
'''
***************************************************************************
 ip_monitor_gui.pyw               File name

 Description: Simple ICMP monitoring tool with reordering support

 Usage: python ip_monitor_gui.pyw 

 @since version 1.3 
 @return <typnone>
 @Date: GitHub version - June 2025 / Added reordering support
****************************************************************************
'''
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import threading
import time
import json
import csv
import os
from datetime import datetime
import sys
import re
import subprocess
import socket
import winsound  # For Windows system sounds

# Add matplotlib imports for graph visualization
try:
    import matplotlib
    matplotlib.use('TkAgg')  # Use TkAgg backend for tkinter compatibility
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    MATPLOTLIB_AVAILABLE = True
except ImportError:
    MATPLOTLIB_AVAILABLE = False
    print("Matplotlib not available. Graph view will be disabled.")

# Dependency check with improved error handling for .pyw compatibility
try:
    from ping3 import ping
except ImportError:
    # When running as .pyw, standard error might not show
    # Let's use a graphical message and attempt to install the dependency
    error_msg = "The 'ping3' library is missing. Do you want to install it now?"
    if messagebox.askyesno("Missing Dependency", error_msg):
        try:
            # Try to install the dependency
            subprocess.check_call([sys.executable, "-m", "pip", "install", "ping3"])
            # Try importing again after install
            try:
                from ping3 import ping
            except ImportError:
                messagebox.showerror("Installation Failed", 
                    "Could not install ping3. Please run: pip install ping3 from command line.")
                sys.exit(1)
        except Exception as e:
            messagebox.showerror("Installation Error", f"Error installing ping3: {e}")
            sys.exit(1)
    else:
        sys.exit(1)

# Constants
log_timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
LOG_FILE = f"ping_log_{log_timestamp}.csv"
SAVE_FILE = "ips.json"
DEFAULT_PING_INTERVAL = 2  # Default seconds between pings
MAX_HISTORY = 10    # Number of ping history entries to display
# Global ping interval value
PING_INTERVAL = DEFAULT_PING_INTERVAL

class IPMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IP Address Monitor")
        self.root.geometry("1025x600")
        self.root.minsize(600, 400)
        
        # Set application icon from Base64 data
        icondata = '''
        iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAQAAABpN6lAAAAAAmJLR0QA/4ePzL8AAAAJcEhZcwAAAEgAAABIAEbJaz4AAAAJdnBBZwAAAIAAAACAADDhMZoAAAeySURBVHja7ZxtjFxVGcd/z7zty3Qtpa2wRNpUtEnR+NIaIASrwgeMjYGWxLegQbQhMYRGP9AESZuoiVEjxBiMUTSCETVAg62AYEhroqJrhRpsfIEiuLW2S7vLzO7szM7cOY8futud2e7dPWfm3Duz6/3vl7kz5/zvc/57zj3Pec5zLiRIkCBBggQJEiRIkCBBggQJEvyfQSIhXceVrPBMWuBZ/e8SEECuYQ9XRSKs4Tfs1ee7WgC5ky+SAhRFvUsgBOzW+7tWAPks9wJKnSpTBN4lSJMjx2f0F10pgAzyPHkMU0xQliCCPiCkNccUV+uEL8qUR/NuJY9SYUyKUsVEMASUQCZJcaM/Sp8CXIdSpSDlCJreAKlxRXcKsB5lMurmA8hgdwqQo04ZE3XzgUx3CgABQQzN9wq/AhiJ4//fxQJEPvq7XYAlCI+PkwXxGA9Qty2s8E7ZG49t8Qhg9F4tOtUYZptcFYdp8QyBFBvcKkiOt+gy6gHIt/kTfWSt1x6Xs5FJXrcfNl0uAANsYy05hxqK0bQsGwEgoII6rD6VSvTNj1EAqekoGScBgugHQJw9AOlKRzk+AdyWSX1xuWhxCfBNfmJbVFGVy+RH3uPKHRTA6D51WifoMY7INXGYFpcj9D63CnIxV6rLpNkyfAZFh8nI6ZAHndER8uSs7/cm+plkVOZne8Vs92V1XM+AFBtYSxZbyRXIxtE/45sFakzQ69DjDGWJYdqMzxEKKOi4U416HPHFGB0h6nG4tq7wOcria57HnuFTgNdiE+BMdwrwbGwCHOlOAR5Eokm4mIOAA10pgB7mYY3Ds3zIDPsjS/u0TA6xRS6KuPmH+Ip6fAh6FYBAHqdHNnlmncUk3+PrxutsE8GYldVyLZvIe6YtcpSDpuDf3gQJEiRI0ClInKvRboNslmfktPxdbuu0JZ1p/qAcl3EZl6IU5VOds6NzGSIfYSVKQJkSHRSgc2NwECWgwKSYTqYWdU4AQSnJOHWQqc5J0MkkKUMlxjBaFwoQxYmCJSVAV6CFZ4CsZDPr6Gnzzm9v+JyXj5Jz2jaZC8MIf9FXW2iNY/Gt7OL9Trk+4ahxWkozxDrA6jYDKcrfuJ8HtBqRAHIB32LH9K18jOCAMzJ5zvoBVrUdSRKEl9ipf45AALmEA2zk7ImgGlVqbW9PGCqzu3+abWsInEWaLDkMt+iTngWQPM/wNhTDFCUqUuuOZ/h5rUlplj4y7NAhvwLcw06UOhOMS7ULm96IlPYwxnU6aVPYSgB5K0OkqTNOYbrTatsuTKphCvbLBmiO+/Q7NhXtpsGdZDCUKEoAlPk+TzDWej9QgM/Lx899cZIb2hSgl/dwO2+euZSq3iTftdk/sBNgG8oU41IDanzOHGnTXKDpbImaWpt0NQ7KED+Ujef4V+vl/HXxihaeoKzhUgxlOTu/7vPRfKBH+/1uoGiJbzQMaWWTTS0bV/gipOE82G892ZvnQu95YM+pmZXAbpPORoAUSo2ZTlqyqGGDNGnfKxE1pLX33GXWlwAAwRI5D5aj301Wu8IayUngKCCuyXXLbTksrkkay00A5/Xt8hPAETYCNDspU57u3Dib+MsIbYwFVHwJ8CKzkZZTvOjJ1KcbPv/OmwCzrGrHauOLqQxxraSAUXab/3gy9bhU2SwBcJgva7uu8DTkD2yR1RgC7jNPWdWwJO5nM8hzxmqJaW3uJWziNXnB586ICO9gjRw1J31amiBBggTLFPPMArKS7VzBGyxqj3OYR/V1qxtdyE1ssToLWGCIfXanS2Qt23k3A4sWVM7we355fqD0PAHkZr7KBQ4SFtmjP1jU0NvYa2HmLMa4U3+2CKdwB3fR78B6kl36RPNXcxwh2cU99KIodQIC6ov8GbJ8UMzCXpfczZfocWLt4cNS4PCCrF9jN1kn1n52yCscbWJpungXB8mg1ChTsXwbXIocvdwQvhEh7+VxBKVK2fIdc0KKHBmu16OhRT7Ez6EFVmFr4yZqswA/5kaUMkUpO0TqRbP8UW8N/Xk/H8BQoSAuCRGiOX6tu0J/PsQWDGWKjqw9PKx75hVAenmZFUwx6v4+MK1z9fy7spJnmAwVRqXizFpi6/yxfVnLSwhlxqTsxgk6otfPXjWuBi9mAMOEu6EgadaE/DRIlnqLrPnQWeNSUtOszpBVjVeNAsyM/tbCnxL6/VnWlhY8oZmkmenR3wprk6Vz4wG1Vo+rLrisrEVyZNIL61wB6pFEf6N5u6QXW5OYYKcN6DQSATptQKeRCNBpAzqNRICGz8U2Mv+UMJ+8nUB6PbS22+sZm9G0t9UggI5wrGXSk2Y05JcTnGqZ9V8mzNd/Gaf3kTThHyECAA+1TBp6ol+1Ddb9oaxVHvFja3M8oI9fyaoWcvaO8zETmjojK3la+lpgPcYnTGjis7yRpyTVwqB9gU83nj9vTi8s80k94Ux5gtvNAplDWuBmdX+/yKvcYRbI+9YRblH3s+T/5AvNx+/nbo4W5DHSsoFeS8Iij3CXGVmk1Kjsp1fWW58xGOOn3B36VJnBKTnACllvlwwFnOZB9po5z455V7GSlnVW0dYy/zbWy2fJyDr6LAqWGLZ/SYLkxO7wxjjHzdJI9EqQIEGCBAkSJIgH/wOhy7cnpv+HNgAAACV0RVh0ZGF0ZTpjcmVhdGUAMjAxMC0wMi0xMVQxMjo1MDoxOC0wNjowMKdwCasAAAAldEVYdGRhdGU6bW9kaWZ5ADIwMDktMTAtMjJUMjM6MjM6NTYtMDU6MDAtj0NVAAAAAElFTkSuQmCC
        '''
        try:
            icon = tk.PhotoImage(data=icondata)
            self.root.iconphoto(True, icon)
        except Exception as e:
            print(f"Warning: Could not set icon: {e}")

        self.ping_threads = []
        self.stop_event = threading.Event()
        self.rows = []
        self.logging_enabled = tk.BooleanVar(value=True)
        self.monitoring_paused = False
        self.selected_row = None  # Initialize selected_row attribute

        # Ping interval variable
        self.ping_interval = tk.IntVar(value=DEFAULT_PING_INTERVAL)

        self.create_menu()
        self.create_widgets()
        self.initialize_log_file()
        
        # Load settings only (no IPs) - CHANGE 1: Don't load IPs automatically
        self.load_settings()
        
        # Set up unsaved changes flag
        self.has_unsaved_changes = False
        
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Bind window resize event
        self.root.bind("<Configure>", self.on_window_resize)
        self.resize_timer = None

    def create_widgets(self):
        # Top frame for input controls
        top_frame = ttk.Frame(self.root)
        top_frame.pack(side="top", fill="x", padx=10, pady=5)

        label = ttk.Label(top_frame, text="IP/URL ADDRESS:", font=("Arial", 12))
        label.pack(side="left", padx=(0, 5))

        self.ip_entry = ttk.Entry(top_frame, width=35, font=("Arial", 12))
        self.ip_entry.pack(side="left")
        self.ip_entry.bind("<Return>", lambda e: self.add_ip())

        add_button = ttk.Button(top_frame, text="Add", command=self.add_ip)
        add_button.pack(side="left", padx=(10, 0))
        
        # Add Ping Interval spinner next to Add button
        ping_interval_frame = ttk.Frame(top_frame)
        ping_interval_frame.pack(side="left", padx=(20, 0))
        
        ttk.Label(ping_interval_frame, text="Interval (sec):").pack(side="left")
        
        # Spinner for ping interval - using width=3 as requested
        spin_interval = ttk.Spinbox(
            ping_interval_frame, 
            from_=2, 
            to=10, 
            textvariable=self.ping_interval,
            width=3,
            command=self.update_ping_interval,
            wrap=True
        )
        spin_interval.pack(side="left", padx=5)
        # Make sure the entered value is valid with validation
        spin_interval.bind("<FocusOut>", self.validate_ping_interval)
        spin_interval.bind("<Return>", self.validate_ping_interval)

        # Control buttons frame
        control_frame = ttk.Frame(self.root)
        control_frame.pack(side="top", fill="x", padx=10, pady=5)
        
        # Create styled buttons
        button_style = {'width': 15}
        
        # First row of buttons
        buttons_frame1 = ttk.Frame(control_frame)
        buttons_frame1.pack(side="top", fill="x", pady=2)
        
        self.log_check = ttk.Checkbutton(buttons_frame1, text="Enable Logging", variable=self.logging_enabled)
        self.log_check.pack(side="left", padx=5)
        
        tk.Button(buttons_frame1, text="Reset All Stats", command=self.reset_all_stats, **button_style).pack(side="left", padx=5)
        
        self.toggle_all_button = tk.Button(buttons_frame1, text="Stop All Pings", command=self.toggle_all_pings, **button_style)
        self.toggle_all_button.pack(side="left", padx=5)
        
        tk.Button(buttons_frame1, text="Restart All Pings", command=self.restart_all_pings, **button_style).pack(side="left", padx=5)
        
        tk.Button(buttons_frame1, text="Restart Program", command=self.restart_program, **button_style).pack(side="left", padx=5)

        # Add View Graph button
        tk.Button(buttons_frame1, text="View Graph", command=self.show_ping_graph, **button_style).pack(side="left", padx=5)

        # Add a Clear All IPs button
        tk.Button(buttons_frame1, text="Reset & Save Stats", command=self.clear_all_ips, **button_style).pack(side="left", padx=5)
        
        # Add Toggle Pie Charts button
        self.show_pie_charts = tk.BooleanVar(value=False)  # Default to False (hidden)
        self.pie_toggle_button = tk.Button(buttons_frame1, text="Show Pie Charts", 
                                         command=self.toggle_pie_charts, **button_style)
        self.pie_toggle_button.pack(side="left", padx=5)

        # Header frame
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        columns = [
            ("IP/URL Address", 14, "w"),       # IP address column
            ("Last 10 Pings", 24, "center"),    # History circles column
            ("Fastest", 8, "center"),          # Fastest ping column
            ("Slowest", 10, "center"),         # Slowest ping column
            ("Average", 8, "center"),          # Average ping column
            ("Controls", 19, "center")         # Controls column (made wider for bell icon)
        ]
        
        # Create evenly spaced header labels
        for title, width, anchor in columns:
            lbl = tk.Label(header_frame, text=title, font=("Arial", 12, "bold"), 
                    width=width, anchor=anchor)
            lbl.pack(side="left", padx=5)

        # Separator after header
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", padx=10, pady=2)

        # Scrollable frame for IP rows
        container = ttk.Frame(self.root)
        container.pack(fill="both", expand=True, padx=10, pady=5)
        
        self.canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=self.canvas.yview)
        self.display_frame = tk.Frame(self.canvas)  # Changed to tk.Frame for background color support
        
        self.display_frame.bind("<Configure>", 
                              lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        
        self.canvas.create_window((0, 0), window=self.display_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Create frame for pie charts
        self.pie_frame = ttk.Frame(self.root)
        # Don't pack it initially since show_pie_charts defaults to False
        
        # Initialize pie charts list
        self.pie_charts = []

    def validate_ping_interval(self, event=None):
        """Validate and correct the ping interval if needed"""
        try:
            value = int(self.ping_interval.get())
            if value < 2:
                self.ping_interval.set(2)
            elif value > 10:
                self.ping_interval.set(10)
                
            # Update the ping interval for all rows
            self.update_ping_interval()
        except ValueError:
            # Reset to default if not a valid number
            self.ping_interval.set(DEFAULT_PING_INTERVAL)
            
    def update_ping_interval(self, event=None):
        """Apply the new ping interval to all monitoring rows"""
        global PING_INTERVAL
        try:
            value = int(self.ping_interval.get())
            if 2 <= value <= 10:
                PING_INTERVAL = value
        except:
            pass
        # Save settings when interval changes
        self.save_settings()
        
    def save_settings(self):
        """Save application settings including ping interval"""
        try:
            settings = {
                "ping_interval": self.ping_interval.get()
            }
            with open("ip_monitor_settings.json", "w") as f:
                json.dump(settings, f)
        except PermissionError:
            # Try with a different filename if permission denied
            try:
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                alt_filename = f"ip_monitor_settings_{timestamp}.json"
                with open(alt_filename, "w") as f:
                    json.dump(settings, f)
                print(f"Settings saved to alternative file: {alt_filename}")
            except Exception as e:
                print(f"Error saving settings to alternative file: {e}")
        except Exception as e:
            print(f"Error saving settings: {e}")
            
    def load_settings(self):
        """Load application settings including ping interval"""
        global PING_INTERVAL
        try:
            if os.path.exists("ip_monitor_settings.json"):
                with open("ip_monitor_settings.json", "r") as f:
                    settings = json.load(f)
                    if "ping_interval" in settings:
                        interval = int(settings["ping_interval"])
                        if 2 <= interval <= 10:  # Validate within bounds
                            self.ping_interval.set(interval)
                            PING_INTERVAL = interval
        except Exception as e:
            print(f"Error loading settings: {e}")

    def initialize_log_file(self):
        # Create log file with headers if it doesn't exist
        attempts = 0
        max_attempts = 5
        global LOG_FILE
        current_log_file = LOG_FILE
        
        while attempts < max_attempts:
            try:
                with open(current_log_file, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow(["Timestamp", "IP/URL Address", "Status", "Response Time (ms)"])
                # If successful, update the global LOG_FILE variable
                LOG_FILE = current_log_file
                return
            except PermissionError:
                # If permission denied, try a different filename
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + f"_{attempts}"
                current_log_file = f"ping_log_{timestamp}.csv"
                attempts += 1
            except Exception as e:
                # For other errors, just log and return
                print(f"Warning: Could not create log file: {e}")
                return
        
        # If we reached here, we couldn't create a log file after multiple attempts
        print("Warning: Could not create log file after multiple attempts. Logging disabled.")
        self.logging_enabled.set(False)

    def validate_ip_or_url(self, address):
        """Validate if string is a valid IPv4 address or URL."""
        # Check if it's an IP address
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if re.match(ip_pattern, address):
            # Check each octet is between 0-255
            for octet in address.split('.'):
                if not 0 <= int(octet) <= 255:
                    return False
            return True
        
        # Check if it's a URL
        url_pattern = r'^([a-zA-Z0-9]([a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
        if re.match(url_pattern, address):
            # Try to resolve the hostname
            try:
                socket.gethostbyname(address)
                return True
            except:
                return False
        
        return False

    def add_ip(self, address=None):
        address = address or self.ip_entry.get().strip()
        if not address:
            return
            
        # Validate IP/URL address format
        if not self.validate_ip_or_url(address):
            messagebox.showerror("Invalid Address", f"{address} is not a valid IPv4 address or URL.")
            return
            
        # Check for duplicates
        for row in self.rows:
            if row.ip == address:
                messagebox.showinfo("Duplicate", f"{address} is already being monitored.")
                return

        # Create new IP row
        row = IPRow(self.display_frame, address, self.stop_event, self.logging_enabled, self.ping_interval)
        row.parent_app = self  # Set reference to parent app
        self.rows.append(row)
        row.frame.pack(fill="x", pady=3)

        # Add separator after the row
        sep = ttk.Separator(self.display_frame, orient="horizontal")
        sep.pack(fill="x", pady=2)
        row.separator = sep  # Store separator reference for later removal

        # Add context menu
        row.frame.bind("<Button-3>", lambda e, r=row: self.show_context_menu(e, r))
        
        # Add click event to select the row
        row.frame.bind("<Button-1>", lambda e, r=row: self.select_row(r))

        # Start monitoring thread
        thread = threading.Thread(target=row.start_monitoring, daemon=True)
        thread.start()
        self.ping_threads.append(thread)

        # Clear entry field
        self.ip_entry.delete(0, tk.END)
        
        # CHANGE 2: Set unsaved changes flag to true
        self.has_unsaved_changes = True
        
        # Update pie charts
        self.update_pie_charts()

    def select_row(self, row):
        """Select a row and highlight it"""
        # Store the selected row
        self.selected_row = row
        
        # Put the IP/URL in the entry field for editing
        self.ip_entry.delete(0, tk.END)
        self.ip_entry.insert(0, row.ip)
        
        # No need to modify backgrounds as we're handling that based on ping status

    def create_menu(self):
        """Create the application menu bar"""
        menu_bar = tk.Menu(self.root)
        self.root.config(menu=menu_bar)
        
        # File menu
        file_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Save IP List", command=self.save_ips_as)  # CHANGE 3: Changed to save_ips_as
        file_menu.add_command(label="Load IP List", command=self.load_ips)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.on_closing)
        
        # Tools menu
        tools_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Reset All Statistics", command=self.reset_all_stats)
        tools_menu.add_command(label="Stop All Pings", command=self.toggle_all_pings)
        tools_menu.add_command(label="Restart All Pings", command=self.restart_all_pings)
        tools_menu.add_separator()
        tools_menu.add_command(label="Export Statistics", command=lambda: self.clear_all_ips(export_only=True))
        tools_menu.add_command(label="View Ping Graph", command=self.show_ping_graph)
        
        # Help menu
        help_menu = tk.Menu(menu_bar, tearoff=0)
        menu_bar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self.show_about)

    def show_context_menu(self, event, row):
        menu = tk.Menu(self.root, tearoff=0)
        menu.add_command(label="Remove", command=lambda: self.remove_ip(row))
        menu.add_command(label="Copy IP/URL", command=lambda: self.copy_to_clipboard(row.ip))
        menu.add_command(label="Reset Statistics", command=lambda: self.reset_row_stats(row))
        menu.add_checkbutton(label="Sound Notifications", 
                           variable=row.sound_notifications_enabled,
                           command=lambda: self.toggle_sound_notifications(row))
        menu.add_separator()
        # Add move up/down options
        row_index = self.rows.index(row)
        if row_index > 0:
            menu.add_command(label="Move Up", command=lambda: self.move_row_up(row))
        if row_index < len(self.rows) - 1:
            menu.add_command(label="Move Down", command=lambda: self.move_row_down(row))
        menu.tk_popup(event.x_root, event.y_root)

    def move_row_up(self, row):
        """Move a row up in the list"""
        index = self.rows.index(row)
        if index > 0:
            # Swap in the rows list
            self.rows[index], self.rows[index-1] = self.rows[index-1], self.rows[index]
            
            # Redraw all rows
            self.redraw_all_rows()
            
            # Set unsaved changes flag
            self.has_unsaved_changes = True
            
            # Update pie charts
            self.update_pie_charts()
            
            # Update pie charts
            self.update_pie_charts()

    def move_row_down(self, row):
        """Move a row down in the list"""
        index = self.rows.index(row)
        if index < len(self.rows) - 1:
            # Swap in the rows list
            self.rows[index], self.rows[index+1] = self.rows[index+1], self.rows[index]
            
            # Redraw all rows
            self.redraw_all_rows()
            
            # Set unsaved changes flag
            self.has_unsaved_changes = True

    def redraw_all_rows(self):
        """Redraw all rows in the correct order"""
        # First, forget all row frames and separators
        for row in self.rows:
            row.frame.pack_forget()
            if hasattr(row, 'separator'):
                row.separator.pack_forget()
        
        # Now pack them again in the correct order
        for row in self.rows:
            row.frame.pack(fill="x", pady=3)
            if hasattr(row, 'separator'):
                row.separator.pack(fill="x", pady=2)

    def toggle_sound_notifications(self, row):
        """Toggle sound notifications for a specific row"""
        # The row's sound_notifications_enabled variable handles the state
        # Just update the bell icon appearance
        row.update_bell_icon()
        
        # CHANGE 4: Set unsaved changes flag
        self.has_unsaved_changes = True

    def copy_to_clipboard(self, text):
        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()  # Required to finalize clipboard transfer
        
    def remove_ip(self, row):
        row.stop_event.set()
        if hasattr(row, 'separator'):
            row.separator.destroy()  # Remove separator
        row.frame.destroy()
        self.rows.remove(row)
        
        # CHANGE 5: Set unsaved changes flag
        self.has_unsaved_changes = True
        
        # Update pie charts
        self.update_pie_charts()
        
        # Update pie charts
        self.update_pie_charts()

    def toggle_all_pings(self):
        """Toggle between stopping and starting all pings"""
        if not self.monitoring_paused:
            # Stop all pings
            for row in self.rows:
                row.pause_monitoring()
            self.monitoring_paused = True
            self.toggle_all_button.config(text="Start All Pings")
        else:
            # Start all pings
            for row in self.rows:
                row.resume_monitoring()
            self.monitoring_paused = False
            self.toggle_all_button.config(text="Stop All Pings")

    def reset_all_stats(self):
        """Reset statistics for all IP rows"""
        for row in self.rows:
            row.reset_statistics()

    def reset_row_stats(self, row):
        """Reset statistics for a specific row"""
        row.reset_statistics()

    def clear_all_ips(self, export_only=False):
        """Clear all IPs but save statistics to a file before removing everything"""
        action_text = "export statistics" if export_only else "reset and save statistics"
        if messagebox.askyesno("Export/Clear", f"Are you sure you want to {action_text}?"):
            # Generate a unique filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            stats_filename = f"ip_stats_{timestamp}.csv"
            
            # Save current statistics to file
            attempts = 0
            max_attempts = 3
            
            while attempts < max_attempts:
                try:
                    with open(stats_filename, "w", newline="") as f:
                        writer = csv.writer(f)
                        # Write headers
                        writer.writerow(["IP/URL Address", "Fastest (ms)", "Slowest (ms)", "Average (ms)", "Ping Count", "Date", "Time"])
                        
                        # Write data for each row
                        for row in self.rows:
                            fastest = f"{row.fastest*1000:.1f}" if row.fastest != float('inf') else "N/A"
                            slowest = f"{row.slowest*1000:.1f}" if row.slowest > 0 else "N/A"
                            avg = f"{(row.total_time / row.ping_count)*1000:.1f}" if row.ping_count > 0 else "N/A"
                            
                            writer.writerow([
                                row.ip,
                                fastest,
                                slowest,
                                avg,
                                row.ping_count,
                                datetime.now().strftime("%Y-%m-%d"),
                                datetime.now().strftime("%H:%M:%S")
                            ])
                    
                    messagebox.showinfo("Statistics Saved", f"Statistics have been saved to {stats_filename}")
                    break  # Exit the loop if successful
                
                except PermissionError:
                    # Try a different filename if permission denied
                    attempts += 1
                    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + f"_alt{attempts}"
                    stats_filename = f"ip_stats_{timestamp}.csv"
                    
                    if attempts >= max_attempts:
                        messagebox.showwarning("Warning", 
                            "Could not save statistics due to permission issues. Try saving to a different location.")
                        return
                
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save statistics: {e}")
                    return
                
            if not export_only:
                # Stop all monitoring threads and clear UI
                for row in self.rows[:]:  # Create a copy of the list to iterate over
                    row.stop_event.set()
                    if hasattr(row, 'separator'):
                        row.separator.destroy()
                    row.frame.destroy()
                
                # Clear the rows list
                self.rows.clear()
                
                # CHANGE 6: Set unsaved changes flag to false since we've cleared everything
                self.has_unsaved_changes = False
                
                # Reset monitoring state
                self.monitoring_paused = False
                self.toggle_all_button.config(text="Stop All Pings")

    def restart_all_pings(self):
        """Restart ping monitoring for all rows"""
        for row in self.rows:
            row.restart_monitoring()
        if self.monitoring_paused:
            self.monitoring_paused = False
            self.toggle_all_button.config(text="Stop All Pings")

    def restart_program(self):
        """Restart the entire application"""
        if messagebox.askyesno("Restart", "Are you sure you want to restart the application?"):
            # Ask to save changes if needed
            if self.has_unsaved_changes and messagebox.askyesno("Save Changes", 
                                                               "Do you want to save the current IP list before restarting?"):
                if not self.save_ips_as():
                    # User cancelled the save operation
                    return
            
            # Close the current window
            self.root.destroy()
            
            # Start a new process
            try:
                script_path = sys.argv[0]
                subprocess.Popen([sys.executable, script_path])
                sys.exit(0)
            except Exception as e:
                messagebox.showerror("Restart Error", f"Failed to restart program: {e}")
                # Continue running if restart fails

    # CHANGE 7: Modified to prompt for saving before closing
    def on_closing(self):
        """Handle application closing, asking to save IP list if needed"""
        # Ask to save changes if there are unsaved changes
        if self.has_unsaved_changes:
            response = messagebox.askyesnocancel("Save Changes", 
                                       "Do you want to save the current IP list before exiting?")
            
            if response is None:  # Cancel was clicked
                return  # Don't close the application
            
            if response:  # Yes was clicked
                # Try to save, and only exit if save was successful
                if not self.save_ips_as():
                    return  # User cancelled the save dialog
        
        # Stop all monitoring threads
        self.stop_event.set()
        
        # Destroy the main window and exit
        self.root.destroy()

    # CHANGE 8: New method to ask for filename when saving
    def save_ips_as(self):
        """Save IP addresses to a user-specified file"""
        # Ask user for filename
        filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
        save_path = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=filetypes,
            initialfile="ip_list.json",
            title="Save IP List As"
        )
        
        # If user cancelled the dialog
        if not save_path:
            return False
            
        # Save IP addresses along with their notification settings and order
        try:
            ips_data = []
            for row in self.rows:
                ips_data.append({
                    "ip": row.ip,
                    "notifications": row.sound_notifications_enabled.get()
                })
            
            with open(save_path, "w") as f:
                json.dump(ips_data, f)
                
            # Update the global SAVE_FILE variable to the last used file
            global SAVE_FILE
            SAVE_FILE = save_path
            
            # Reset unsaved changes flag
            self.has_unsaved_changes = False
            
            messagebox.showinfo("Success", f"IP list saved to {save_path}")
            return True
            
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save IP addresses: {e}")
            return False

    # CHANGE 9: Updated to ask whether to overwrite or add to current list
    def load_ips(self):
        """Load IP addresses from a file with option to overwrite or add"""
        # Ask user for file to load
        filetypes = [("JSON files", "*.json"), ("All files", "*.*")]
        load_path = filedialog.askopenfilename(
            filetypes=filetypes,
            title="Load IP List"
        )
        
        # If user cancelled the dialog
        if not load_path:
            return False
            
        # Check if there are any existing IPs being monitored
        if self.rows and not self.has_unsaved_changes:
            # No unsaved changes, so just clear existing rows
            should_replace = True
        elif self.rows:
            # Ask if user wants to replace or add
            response = messagebox.askyesnocancel("Load IP List", 
                "Do you want to replace the current IP list?\n\n"
                "Yes = Replace current list\n"
                "No = Add to current list\n"
                "Cancel = Abort operation")
                
            if response is None:  # User clicked Cancel
                return False
                
            should_replace = response  # True for replace, False for add
        else:
            # No existing rows, just load the file
            should_replace = True
            
        try:
            with open(load_path, "r") as f:
                ips_data = json.load(f)
                
            # Clear existing rows if replacing
            if should_replace and self.rows:
                for row in self.rows[:]:  # Create a copy of the list to iterate over
                    row.stop_event.set()
                    if hasattr(row, 'separator'):
                        row.separator.destroy()
                    row.frame.destroy()
                
                # Clear the rows list
                self.rows.clear()
                
            # Add IPs from file
            if isinstance(ips_data, list):
                if len(ips_data) > 0 and isinstance(ips_data[0], dict):
                    # New format with dictionaries
                    for ip_data in ips_data:
                        ip = ip_data.get("ip", "")
                        if ip:
                            self.add_ip(ip)
                            # Set notification settings if available
                            if "notifications" in ip_data and self.rows:
                                last_row = self.rows[-1]
                                last_row.sound_notifications_enabled.set(ip_data["notifications"])
                                last_row.update_bell_icon()
                else:
                    # Old format with just IP strings
                    for ip in ips_data:
                        self.add_ip(ip)
                        
            # Update global SAVE_FILE variable
            global SAVE_FILE
            SAVE_FILE = load_path
            
            # Reset unsaved changes flag since we just loaded
            self.has_unsaved_changes = False
            
            # Update pie charts for loaded IPs
            self.update_pie_charts()
            
            messagebox.showinfo("Success", f"IP list loaded from {load_path}")
            return True
            
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load IP addresses: {e}")
            return False

    def show_ping_graph(self):
        """Show historical ping data in a graph"""
        global LOG_FILE
        if not MATPLOTLIB_AVAILABLE:
            messagebox.showerror("Error", "Matplotlib is not installed. Install it with: pip install matplotlib")
            return
            
        # Check if there's data to display
        if not os.path.exists(LOG_FILE) or not self.rows:
            messagebox.showinfo("No Data", "No ping data available to display.")
            return
            
        # Create graph window
        graph_window = tk.Toplevel(self.root)
        graph_window.title("Ping History Graph")
        graph_window.geometry("800x600")
        graph_window.grab_set()  # Make window modal
        
        # Add controls at the top
        controls_frame = ttk.Frame(graph_window)
        controls_frame.pack(fill="x", padx=10, pady=5)
        
        # IP selection dropdown
        ttk.Label(controls_frame, text="Select IP/URL:").pack(side="left", padx=5)
        
        # Get unique IPs from the monitored rows
        ip_options = [row.ip for row in self.rows]
        
        # Add "All IPs" option
        ip_options.insert(0, "All IPs")
        
        ip_var = tk.StringVar(value=ip_options[0])
        ip_dropdown = ttk.Combobox(controls_frame, textvariable=ip_var, values=ip_options, state="readonly")
        ip_dropdown.pack(side="left", padx=5)
        
        # Time range selection
        ttk.Label(controls_frame, text="Time Range:").pack(side="left", padx=(20, 5))
        time_options = ["Last Hour", "Last 6 Hours", "Last 24 Hours", "All Time"]
        time_var = tk.StringVar(value=time_options[0])
        time_dropdown = ttk.Combobox(controls_frame, textvariable=time_var, values=time_options, state="readonly")
        time_dropdown.pack(side="left", padx=5)
        
        # Refresh button
        refresh_btn = tk.Button(controls_frame, text="Refresh")
        refresh_btn.pack(side="right", padx=5)
        
        # Create matplotlib figure
        figure_frame = ttk.Frame(graph_window)
        figure_frame.pack(fill="both", expand=True, padx=10, pady=5)
        
        fig = Figure(figsize=(8, 6), dpi=100)
        ax = fig.add_subplot(111)
        
        canvas = FigureCanvasTkAgg(fig, master=figure_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)
        
        # Function to load and plot data
        def load_and_plot_data():
            # Clear the plot
            ax.clear()
            
            try:
                # Read the log file
                data = []
                with open(LOG_FILE, "r", newline="") as f:
                    reader = csv.reader(f)
                    headers = next(reader)  # Skip header row
                    
                    for row in reader:
                        if len(row) >= 4:  # Ensure the row has all needed columns
                            timestamp_str = row[0]
                            ip = row[1]
                            status = row[2]
                            response_time = row[3]
                            
                            # Convert timestamp to datetime
                            try:
                                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                # Convert response time to float, handle failed pings
                                if status.lower() == "ok" and response_time != "0":
                                    response_time = float(response_time)
                                else:
                                    response_time = None  # Mark failed pings as None
                                    
                                data.append((timestamp, ip, response_time))
                            except ValueError:
                                continue  # Skip invalid timestamp formats
                
                # Filter by selected IP
                selected_ip = ip_var.get()
                if selected_ip != "All IPs":
                    data = [item for item in data if item[1] == selected_ip]
                
                # Filter by time range
                now = datetime.now()
                selected_time = time_var.get()
                if selected_time == "Last Hour":
                    data = [item for item in data if (now - item[0]).total_seconds() <= 3600]
                elif selected_time == "Last 6 Hours":
                    data = [item for item in data if (now - item[0]).total_seconds() <= 21600]
                elif selected_time == "Last 24 Hours":
                    data = [item for item in data if (now - item[0]).total_seconds() <= 86400]
                
                # No data after filtering
                if not data:
                    ax.text(0.5, 0.5, "No data available for the selected filters", 
                          ha='center', va='center', transform=ax.transAxes)
                    canvas.draw()
                    return
                
                # Sort by timestamp
                data.sort(key=lambda x: x[0])
                
                # Group by IP for "All IPs" view
                if selected_ip == "All IPs":
                    # Get unique IPs
                    unique_ips = set(item[1] for item in data)
                    
                    for ip in unique_ips:
                        # Extract data for this IP
                        ip_data = [(item[0], item[2]) for item in data if item[1] == ip]
                        
                        # Remove None values (failed pings) but keep their timestamps for gaps in the graph
                        timestamps = [item[0] for item in ip_data]
                        response_times = [item[1] if item[1] is not None else float('nan') for item in ip_data]
                        
                        # Plot this IP's data
                        ax.plot(timestamps, response_times, marker='o', markersize=3, linestyle='-', label=ip)
                else:
                    # Single IP view
                    timestamps = []
                    response_times = []
                    failed_pings = []  # Store failed ping timestamps
                    
                    for item in data:
                        timestamps.append(item[0])
                        if item[2] is not None:
                            response_times.append(item[2])
                        else:
                            response_times.append(float('nan'))
                            failed_pings.append(item[0])  # Track failed pings
                    
                    # Plot the line for successful pings
                    ax.plot(timestamps, response_times, marker='o', markersize=4, linestyle='-', color='blue', label='Response Time')
                    
                    # Add red markers for failed pings at y=0
                    if failed_pings:
                        # Plot failed pings as red squares at the bottom of the chart
                        y_min, y_max = ax.get_ylim()
                        failed_y = [0] * len(failed_pings)  # Place at y=0
                        ax.scatter(failed_pings, failed_y, color='red', marker='s', s=50, 
                                 label='Failed Pings', zorder=5)
                        
                        # Add vertical red lines from bottom to indicate failures
                        for failed_time in failed_pings:
                            ax.axvline(x=failed_time, color='red', alpha=0.3, linewidth=1, linestyle='--')
                    
                    # Add legend if there are failed pings
                    if failed_pings:
                        ax.legend()
                
                # Set axis labels and title
                ax.set_xlabel('Time')
                ax.set_ylabel('Response Time (ms)')
                ax.set_title(f'Ping Response Times for {selected_ip}')
                
                # Format x-axis to show time nicely
                fig.autofmt_xdate()
                
                # Add legend if showing multiple IPs
                if selected_ip == "All IPs":
                    ax.legend()
                
                # Add grid
                ax.grid(True, linestyle='--', alpha=0.7)
                
                # Refresh the canvas
                canvas.draw()
                
            except Exception as e:
                messagebox.showerror("Error", f"Failed to load ping data: {e}")
                ax.clear()
                ax.text(0.5, 0.5, f"Error loading data: {str(e)}", 
                      ha='center', va='center', transform=ax.transAxes)
                canvas.draw()
        
        # Bind the refresh function to dropdown changes and button click
        ip_dropdown.bind("<<ComboboxSelected>>", lambda e: load_and_plot_data())
        time_dropdown.bind("<<ComboboxSelected>>", lambda e: load_and_plot_data())
        refresh_btn.config(command=load_and_plot_data)
        
        # Initial load
        load_and_plot_data()
            
    def show_about(self):
        """Show about dialog"""
        about_window = tk.Toplevel(self.root)
        about_window.title("About IP Monitor")
        about_window.geometry("400x320")
        about_window.resizable(False, False)
        about_window.transient(self.root)
        about_window.grab_set()
        
        # Center the window
        about_window.update_idletasks()
        width = about_window.winfo_width()
        height = about_window.winfo_height()
        x = (about_window.winfo_screenwidth() // 2) - (width // 2)
        y = (about_window.winfo_screenheight() // 2) - (height // 2)
        about_window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Add content
        tk.Label(about_window, text="IP Address Monitor", font=("Arial", 16, "bold")).pack(pady=10)
        tk.Label(about_window, text="Version 1.3").pack()
        ttk.Label(about_window, text="A tool for monitoring IP addresses and URLs").pack(pady=5)
        
        features = [
            "• Monitor multiple IP addresses and URLs",
            "• Track ping response times",
            "• Display status with color-coding",
            "• Sound notifications for status changes",
            "• Save and load monitoring configurations",
            "• Export statistics to CSV files",
            "• View ping history in graphs",
            "• Reorder monitoring list with up/down"
        ]
        
        features_frame = ttk.Frame(about_window)
        features_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        for feature in features:
            tk.Label(features_frame, text=feature, anchor="w", justify="left").pack(fill="x", pady=2)
        
        tk.Button(about_window, text="Close", command=about_window.destroy).pack(pady=10)

    def toggle_pie_charts(self):
        """Toggle the display of pie charts"""
        if self.show_pie_charts.get():
            # Hide pie charts
            self.show_pie_charts.set(False)
            self.pie_frame.pack_forget()
            self.pie_toggle_button.config(text="Show Pie Charts")
        else:
            # Show pie charts
            self.show_pie_charts.set(True)
            self.pie_frame.pack(fill="x", padx=10, pady=10)
            self.update_pie_charts()
            self.pie_toggle_button.config(text="Hide Pie Charts")

    def update_pie_charts(self):
        """Update or create pie charts for the first 4 monitored IPs"""
        # Only update if pie charts are visible
        if not self.show_pie_charts.get():
            return
            
        # Clear existing pie charts
        for chart in self.pie_charts:
            chart.destroy()
        self.pie_charts.clear()
        
        # Only show pie charts for the first 4 IPs
        num_charts = min(len(self.rows), 4)
        if num_charts == 0:
            return
            
        # Calculate size based on window width (25% of window width total)
        window_width = self.root.winfo_width()
        if window_width < 100:  # Window not yet rendered
            window_width = 1025  # Use default width
            
        total_width = window_width * 0.25
        chart_size = int(total_width / num_charts) - 20  # Subtract padding
        chart_size = min(chart_size, 195)  # Max size cap increased by 30% (150 * 1.3)
        chart_size = max(chart_size, 104)   # Min size increased by 30% (80 * 1.3)
        
        # Apply 30% increase to calculated size
        chart_size = int(chart_size * 1.3)
        
        # Create pie charts
        for i in range(num_charts):
            row = self.rows[i]
            
            # Create frame for each pie chart
            chart_frame = tk.Frame(self.pie_frame)
            chart_frame.pack(side="left", padx=5)
            
            # Create canvas for pie chart with extra height for label
            canvas = tk.Canvas(chart_frame, width=chart_size, height=chart_size + 50,  # Increased height to accommodate larger chart
                             highlightthickness=0, bg=self.root.cget('bg'))
            canvas.pack()
            
            # Store reference to canvas in the row
            row.pie_canvas = canvas
            row.chart_size = chart_size
            row.pie_items = {}  # Store canvas item IDs for updating
            
            # Draw initial pie chart
            self.draw_pie_chart(row, initial=True)
            
            # Add IP label below the pie
            label = tk.Label(chart_frame, text=row.ip, font=("Arial", 10))
            label.pack()
            
            self.pie_charts.append(chart_frame)
    
    def draw_pie_chart(self, row, initial=False):
        """Draw or update the pie chart for a specific row"""
        if not hasattr(row, 'pie_canvas') or not self.show_pie_charts.get():
            return
            
        # Check if update is already pending for this row
        if not initial and hasattr(row, 'pie_update_pending') and row.pie_update_pending:
            return
            
        # Mark update as pending
        if not initial:
            row.pie_update_pending = True
        
        # Schedule the actual draw
        if initial:
            self._do_draw_pie_chart(row, initial=True)
        else:
            self.root.after(100, lambda: self._do_draw_pie_chart(row))
    
    def _do_draw_pie_chart(self, row, initial=False):
        """Actually draw the pie chart (internal method)"""
        # Clear the pending flag
        if hasattr(row, 'pie_update_pending'):
            row.pie_update_pending = False
        
        if not hasattr(row, 'pie_canvas') or not self.show_pie_charts.get():
            return
            
        canvas = row.pie_canvas
        size = row.chart_size
        
        # Calculate center and radius - make it smaller to fit the ring
        center_x = size // 2
        center_y = size // 2
        ring_width = 10
        radius = (size // 2) - ring_width  # Exact size to touch the ring
        
        # Get extended history
        extended_history = row.extended_history if hasattr(row, 'extended_history') else []
        
        # Initialize items dictionary if needed
        if not hasattr(row, 'pie_items'):
            row.pie_items = {}
            row.last_history_length = 0
            initial = True
        
        # Calculate statistics for ring color
        ok_count = sum(1 for ping in extended_history if ping is True)
        total_count = sum(1 for ping in extended_history if ping is not None)
        
        if total_count > 0:
            ok_percentage = (ok_count / total_count) * 100
            
            # Determine ring color based on success rate
            if ok_percentage == 100:
                ring_color = "blue"
            elif ok_percentage >= 65:
                ring_color = "purple"
            elif ok_percentage >= 45:
                ring_color = "orange"
            elif ok_percentage >= 15:
                ring_color = "darkred"
            elif ok_percentage >= 1:
                ring_color = "lightcoral"
            else:
                ring_color = "red"
        else:
            ring_color = "gray"
            ok_percentage = 0
        
        if initial:
            # Create all elements for the first time
            
            # Create outer ring FIRST (so it's behind everything)
            ring_id = canvas.create_oval(
                center_x - radius, center_y - radius,
                center_x + radius, center_y + radius,
                outline=ring_color, width=ring_width, fill=""
            )
            row.pie_items['ring'] = ring_id
            
            # Create pie segments that go all the way to the center
            for i in range(60):
                start_angle = -90 + (i * 6)
                extent = 6
                
                # Initial color
                if i < len(extended_history):
                    ping_result = extended_history[i]
                    if ping_result is True:
                        color = "green"
                    elif ping_result is False:
                        color = "red"
                    else:
                        color = "gray"
                else:
                    color = "gray"
                
                # Create arc without outline for solid appearance
                arc_id = canvas.create_arc(
                    center_x - radius, center_y - radius,
                    center_x + radius, center_y + radius,
                    start=start_angle, extent=extent,
                    fill=color, outline="",  # No outline
                    style=tk.PIESLICE
                )
                row.pie_items[f'arc_{i}'] = arc_id
            
            # Create percentage text on top with yellow bold font
            text_id = canvas.create_text(
                center_x, center_y,
                text=f"{int(ok_percentage)}%", 
                font=("Arial", 32, "bold"),  # Increased font size proportionally
                fill="yellow"
            )
            row.pie_items['text'] = text_id
            
            # Store the current history length
            row.last_history_length = len(extended_history)
            
        else:
            # Update only what changed
            
            # Check if we have a new ping result (history grew)
            current_length = len(extended_history)
            if current_length > row.last_history_length:
                # New ping added at position 0, update only the first slice
                if extended_history:
                    ping_result = extended_history[0]
                    if ping_result is True:
                        color = "green"
                    elif ping_result is False:
                        color = "red"
                    else:
                        color = "gray"
                    
                    # Update only the first arc (most recent ping)
                    arc_id = row.pie_items.get('arc_0')
                    if arc_id:
                        canvas.itemconfig(arc_id, fill=color)
                
                row.last_history_length = current_length
            
            # Always update ring color and percentage as they depend on overall stats
            ring_id = row.pie_items.get('ring')
            if ring_id:
                canvas.itemconfig(ring_id, outline=ring_color)
            
            # Update percentage text
            text_id = row.pie_items.get('text')
            if text_id:
                canvas.itemconfig(text_id, text=f"{int(ok_percentage)}%")

    def on_window_resize(self, event):
        """Handle window resize events"""
        # Cancel any existing timer
        if hasattr(self, 'resize_timer') and self.resize_timer:
            self.root.after_cancel(self.resize_timer)
        
        # Set a new timer to update pie charts after resize stops
        self.resize_timer = self.root.after(500, self.update_pie_charts)


class IPRow:
    def __init__(self, parent, ip, global_stop_event, logging_enabled, ping_interval=None):
        """Initialize a row for monitoring an IP or URL"""
        self.ip = ip
        self.history = [None] * MAX_HISTORY
        self.extended_history = []  # For pie chart (up to 60 entries)
        self.fastest = float('inf')
        self.slowest = 0
        self.total_time = 0
        self.ping_count = 0
        self.stop_event = threading.Event()
        self.global_stop_event = global_stop_event
        self.logging_enabled = logging_enabled
        self.paused = False
        self.pause_event = threading.Event()
        self.parent_app = None  # Will be set by the parent app
        self.ping_interval = ping_interval  # Reference to the global ping interval
        
        # Previous status for detecting changes (for notifications)
        self.prev_status = None
        
        # Sound notification flag
        self.sound_notifications_enabled = tk.BooleanVar(value=False)

        # Create main frame
        self.frame = tk.Frame(parent)  # Changed to tk.Frame for background color support
        
        # Add up/down arrow buttons at the left
        arrow_frame = tk.Frame(self.frame)
        arrow_frame.pack(side="left", padx=2)
        
        self.up_button = tk.Button(arrow_frame, text="▲", width=2, height=1, 
                                 command=self.move_up, font=("Arial", 8))
        self.up_button.pack()
        
        self.down_button = tk.Button(arrow_frame, text="▼", width=2, height=1,
                                   command=self.move_down, font=("Arial", 8))
        self.down_button.pack()
        
        # IP address label (using tk.Label instead of ttk for consistent styling)
        self.ip_label = tk.Label(self.frame, text=ip, width=16, anchor="w", 
                               font=("Arial", 12, "bold"))
        self.ip_label.pack(side="left", padx=5)

        # Ping history indicators
        self.circle_frame = tk.Frame(self.frame)  # Use tk.Frame instead of ttk.Frame for background color
        self.circle_frame.pack(side="left", padx=5)
        self.circles = []
        
        for i in range(MAX_HISTORY):
            canvas = tk.Canvas(self.circle_frame, width=16, height=16, highlightthickness=0)
            canvas.create_oval(2, 2, 14, 14, fill="gray", tags="oval")
            canvas.pack(side="left", padx=2)
            canvas.tooltip = CreateToolTip(canvas, f"Ping {i+1}")
            self.circles.append(canvas)

        # Statistics labels
        stat_font = ("Arial", 12)
        self.fast_label = tk.Label(self.frame, text="-", width=10, anchor="center", font=stat_font)
        self.fast_label.pack(side="left", padx=5)
        
        self.slow_label = tk.Label(self.frame, text="-", width=10, anchor="center", font=stat_font)
        self.slow_label.pack(side="left", padx=5)
        
        self.avg_label = tk.Label(self.frame, text="-", width=10, anchor="center", font=stat_font)
        self.avg_label.pack(side="left", padx=5)
        
        # Control buttons for this IP
        control_frame = tk.Frame(self.frame)  # Changed to tk.Frame for background color support
        control_frame.pack(side="left", padx=5)
        
        # Replace ttk buttons with tk buttons for better color compatibility
        self.toggle_button = tk.Button(control_frame, text="Stop", width=8,
                                    command=self.toggle_monitoring)
        self.toggle_button.pack(side="left", padx=2)
        
        tk.Button(control_frame, text="Reset", width=8,
                 command=self.reset_statistics).pack(side="left", padx=2)
                 
        tk.Button(control_frame, text="Delete", width=8,
                 command=self.delete_self).pack(side="left", padx=2)
        
        # Draw bell icon - make canvas slightly larger
        self.bell_canvas = tk.Canvas(control_frame, width=24, height=24, highlightthickness=0)
        self.bell_canvas.pack(side="left", padx=2)
        
        # Draw bell icon
        self.bell_icon = self.bell_canvas.create_text(12, 12, text="🔕", font=("Arial", 12), 
                                                 fill="gray", tags="bell")
        
        # Create tooltip for bell icon
        self.bell_canvas.tooltip = CreateToolTip(self.bell_canvas, "Sound notifications disabled")
        
        # Add click handler for the bell icon
        self.bell_canvas.bind("<Button-1>", self.toggle_notifications)
        
        # Update bell icon appearance
        self.update_bell_icon()

    def move_up(self):
        """Request parent to move this row up"""
        if self.parent_app:
            self.parent_app.move_row_up(self)
            
    def move_down(self):
        """Request parent to move this row down"""
        if self.parent_app:
            self.parent_app.move_row_down(self)

    def toggle_notifications(self, event=None):
        """Toggle sound notifications on/off"""
        self.sound_notifications_enabled.set(not self.sound_notifications_enabled.get())
        self.update_bell_icon()
        
        # Mark changes as unsaved if parent app exists
        if hasattr(self, 'parent_app') and self.parent_app:
            self.parent_app.has_unsaved_changes = True
        
    def update_bell_icon(self):
        """Update the bell icon appearance based on notification state"""
        if self.sound_notifications_enabled.get():
            # Use bell emoji with larger, bold font and bright green for better visibility
            self.bell_canvas.itemconfig(self.bell_icon, text="🔔", fill="#00CC00", font=("Arial", 14, "bold"))
            self.bell_canvas.tooltip.text = "Sound notifications enabled"
        else:
            # Use muted bell emoji with normal size font and gray color for disabled state
            self.bell_canvas.itemconfig(self.bell_icon, text="🔕", fill="gray", font=("Arial", 12))
            self.bell_canvas.tooltip.text = "Sound notifications disabled"

    # CHANGE 10: Modified to better handle the bell notification for every ping status change
    def update_display(self, result):
        # Determine current status
        current_status = True if result else False
        
        # Check if there's a change in status regardless of history
        status_changed = self.prev_status is not None and current_status != self.prev_status
        
        # Play sound if notifications are enabled and status changed
        if status_changed and self.sound_notifications_enabled.get():
            try:
                if current_status:  # Changed to successful ping
                    winsound.MessageBeep(winsound.MB_OK)  # This is correct
                else:  # Changed to failed ping
                    winsound.MessageBeep(winsound.MB_ICONHAND)  # Use MB_ICONHAND instead of MB_ICONERROR
            except Exception as e:
                print(f"Error playing sound: {e}")
        
        # Store current status for next comparison
        self.prev_status = current_status
        
        # Update history and statistics
        if result is None:
            self.history.insert(0, False)
            self.extended_history.insert(0, False)
        else:
            self.history.insert(0, True)
            self.extended_history.insert(0, True)
            self.ping_count += 1
            self.total_time += result
            
            # Update fastest time only if this is a valid result
            if result > 0:
                if self.fastest == float('inf'):
                    self.fastest = result
                else:
                    self.fastest = min(self.fastest, result)
                
                self.slowest = max(self.slowest, result)

        # Keep only MAX_HISTORY items for display circles
        self.history = self.history[:MAX_HISTORY]
        
        # Keep only 60 items for pie chart
        self.extended_history = self.extended_history[:60]

        # Update history indicators
        for i, canvas in enumerate(self.circles):
            if i < len(self.history):
                state = self.history[i]
                color = "green" if state else "red" if state is not None else "gray"
                canvas.itemconfig("oval", fill=color)
                
                # Set tooltip text
                tooltip_text = f"Ping {i+1}"
                if i == 0:  # Most recent ping
                    if state and result is not None:
                        tooltip_text = f"Ping {i+1}: {result*1000:.1f} ms"
                    elif state is False:
                        tooltip_text = f"Ping {i+1}: Failed"
                
                # Create new tooltip with updated text if needed
                if hasattr(canvas, 'tooltip'):
                    canvas.tooltip = CreateToolTip(canvas, tooltip_text)

        # Update statistics
        if self.ping_count:
            if self.fastest != float('inf'):
                self.fast_label.config(text=f"{self.fastest*1000:.1f} ms")
            
            if self.slowest > 0:
                self.slow_label.config(text=f"{self.slowest*1000:.1f} ms")
                
            avg = self.total_time / self.ping_count
            self.avg_label.config(text=f"{avg*1000:.1f} ms")
        else:
            self.fast_label.config(text="-")
            self.slow_label.config(text="-")
            self.avg_label.config(text="-")
            
        # Update label color based on the last pings
        self.update_label_color()
        
        # Update pie chart if it exists
        if hasattr(self, 'parent_app') and self.parent_app and hasattr(self, 'pie_canvas') and self.parent_app.show_pie_charts.get():
            self.parent_app.draw_pie_chart(self, initial=False)

    def update_label_color(self):
        """Update the label color and row background based on the ping history"""
        if self.paused:
            self.ip_label.config(fg="gray")
            self.set_row_background("SystemButtonFace")  # Use system default color instead of empty string
            return
            
        # Check if there are 10 valid entries in history
        valid_entries = [h for h in self.history if h is not None]
        if len(valid_entries) < MAX_HISTORY:
            # Not enough data yet
            self.ip_label.config(fg="black")
            self.set_row_background("SystemButtonFace")  # Use system default color instead of empty string
            return
            
        # Check if all pings are successful
        if all(self.history):
            self.ip_label.config(fg="green")
            self.set_row_background("#E6F5E6") # Very light green - more subtle
            return
            
        # Check if all pings failed
        if not any(self.history):
            self.ip_label.config(fg="red")
            self.set_row_background("#FFEDED") # Very light red - more subtle
            return
            
        # Mixed results
        self.ip_label.config(fg="orange")
        self.set_row_background("#FAFAEB") # Very light yellow - more subtle

    def set_row_background(self, color):
        """Set the background color for the entire row"""
        # Set background for the main frame
        self.frame.config(background=color)
        
        # Set background for all tk widgets in the row
        for widget in self.frame.winfo_children():
            if isinstance(widget, (tk.Label, tk.Frame, tk.Canvas)):
                widget.config(background=color)
                
        # Set background for the circle frame and its children
        self.circle_frame.config(background=color)
        
        # Set background for circle canvases
        for canvas in self.circles:
            canvas.config(background=color)
            
        # Set background for the bell canvas
        self.bell_canvas.config(background=color)

    def start_monitoring(self):
        global PING_INTERVAL
        while not self.global_stop_event.is_set() and not self.stop_event.is_set():
            # Check if monitoring is paused
            if self.paused:
                time.sleep(0.5)  # Short sleep to prevent CPU hogging
                continue
                
            try:
                result = ping(self.ip, timeout=1)
            except Exception as e:
                print(f"Ping failed for {self.ip}: {e}")
                result = None

            # Log results if enabled
            if self.logging_enabled.get():
                global LOG_FILE
                try:
                    with open(LOG_FILE, "a", newline="") as f:
                        writer = csv.writer(f)
                        writer.writerow([
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            self.ip,
                            "ok" if result else "fail",
                            f"{result*1000:.2f}" if result else "0"
                        ])
                except PermissionError:
                    # If permission denied, try to create a new log file
                    try:
                        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_alt"
                        new_log_file = f"ping_log_{timestamp}.csv"
                        
                        # Create the new log file with headers
                        with open(new_log_file, "w", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow(["Timestamp", "IP/URL Address", "Status", "Response Time (ms)"])
                            
                        # Update the global LOG_FILE
                        LOG_FILE = new_log_file
                        
                        # Now try to write to the new file
                        with open(LOG_FILE, "a", newline="") as f:
                            writer = csv.writer(f)
                            writer.writerow([
                                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                                self.ip,
                                "ok" if result else "fail",
                                f"{result*1000:.2f}" if result else "0"
                            ])
                    except Exception as e:
                        # If we still can't write, just disable logging
                        print(f"Error writing to log file: {e}")
                        if hasattr(self, 'parent_app') and self.parent_app:
                            self.parent_app.logging_enabled.set(False)
                except Exception as e:
                    print(f"Error writing to log file: {e}")

            # Update UI in the main thread
            if not self.stop_event.is_set():
                self.frame.after(0, self.update_display, result)
            
            # Wait before next ping - use the current ping_interval setting
            try:
                # Try to get the value from the IntVar
                interval = self.ping_interval.get()
            except:
                # Fall back to the global variable if there's an issue
                interval = PING_INTERVAL
                
            time.sleep(interval)

    def toggle_monitoring(self):
        """Toggle monitoring state for this IP"""
        if not self.paused:
            self.pause_monitoring()
        else:
            self.resume_monitoring()

    def pause_monitoring(self):
        """Pause monitoring for this IP"""
        self.paused = True
        self.toggle_button.config(text="Start")
        self.ip_label.config(fg="gray")  # Indicate paused state
        self.set_row_background("SystemButtonFace")  # Use system default color

    def resume_monitoring(self):
        """Resume monitoring for this IP"""
        self.paused = False
        self.toggle_button.config(text="Stop")
        self.update_label_color()  # Update color based on current state

    def reset_statistics(self):
        """Reset all statistics for this IP"""
        self.history = [None] * MAX_HISTORY
        self.extended_history = []
        self.fastest = float('inf')
        self.slowest = 0
        self.total_time = 0
        self.ping_count = 0
        self.prev_status = None  # Reset status tracking for notifications
        
        # Reset UI indicators
        for canvas in self.circles:
            canvas.itemconfig("oval", fill="gray")
            canvas.tooltip = CreateToolTip(canvas, "Ping")
            
        self.fast_label.config(text="-")
        self.slow_label.config(text="-")
        self.avg_label.config(text="-")
        
        # Reset label color and background
        if not self.paused:
            self.ip_label.config(fg="black")
            self.set_row_background("SystemButtonFace")
        else:
            self.ip_label.config(fg="gray")
            self.set_row_background("SystemButtonFace")

    def restart_monitoring(self):
        """Reset statistics and ensure monitoring is active"""
        self.reset_statistics()
        self.resume_monitoring()
        
    def delete_self(self):
        """Remove this row from monitoring"""
        if self.parent_app:
            self.parent_app.remove_ip(self)


class CreateToolTip:
    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tipwindow = None
        widget.bind("<Enter>", self.enter)
        widget.bind("<Leave>", self.leave)

    def enter(self, event=None):
        if self.tipwindow:
            return
        # Get widget position
        x = self.widget.winfo_rootx() + self.widget.winfo_width() // 2
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 5
        
        # Create tooltip window
        self.tipwindow = tw = tk.Toplevel(self.widget)
        tw.wm_overrideredirect(True)
        tw.wm_geometry(f"+{x}+{y}")
        
        # Create tooltip content
        label = tk.Label(tw, text=self.text, justify='left', 
                       background="#ffffe0", relief='solid', 
                       borderwidth=1, font=("Arial", 10))
        label.pack(ipadx=1)

    def leave(self, event=None):
        if self.tipwindow:
            self.tipwindow.destroy()
            self.tipwindow = None


if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = IPMonitorApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Error", f"An unexpected error occurred: {e}")
        sys.exit(1)