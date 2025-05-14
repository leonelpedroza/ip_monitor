# ip_monitor_gui.pyw
'''
***************************************************************************
 ip_monitor_guy.pyw               Nombre del archivo

 Description: Simple ICMP monitoring tool

 Usage: python ip_monitor_guy.pyw 

 @since version 1.1 
 @return <typnone>
 @Date: GitHub version - May 13 2025 / Spaghetti code version - June 2020
****************************************************************************
'''
import tkinter as tk
from tkinter import ttk, messagebox
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
MAX_HISTORY = 10    # Number of ping history entries to display - increased from 8 to 10
# Global ping interval value
PING_INTERVAL = DEFAULT_PING_INTERVAL

class IPMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("IP Address Monitor")
        self.root.geometry("1000x600")
        self.root.minsize(600, 400)
        
        # Set application icon from Base64 data
        icondata = '''
        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
        '''
        icon = tk.PhotoImage(data=icondata)
        self.root.iconphoto(True, icon)

        self.ping_threads = []
        self.stop_event = threading.Event()
        self.rows = []
        self.logging_enabled = tk.BooleanVar(value=True)
        self.monitoring_paused = False

        # Ping interval variable
        self.ping_interval = tk.IntVar(value=DEFAULT_PING_INTERVAL)

        self.create_menu()
        self.create_widgets()
        self.initialize_log_file()
        
        # Load settings first, then IPs
        self.load_settings()
        self.load_ips()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

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

        # Add Ping Interval spinner to the right side
        ping_interval_frame = ttk.Frame(buttons_frame1)
        ping_interval_frame.pack(side="right", padx=10)
        
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

        # Header frame
        header_frame = ttk.Frame(self.root)
        header_frame.pack(fill="x", padx=10, pady=5)
        
        columns = [
            ("IP/URL Address", 14, "w"),       # IP address column
            ("Last 10 Pings", 24, "center"),    # History circles column - updated from "Last 8 Pings" and increased width
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
        self.save_ips()  # Save immediately after adding

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
        file_menu.add_command(label="Save IP List", command=self.save_ips)
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
        menu.tk_popup(event.x_root, event.y_root)

    def toggle_sound_notifications(self, row):
        """Toggle sound notifications for a specific row"""
        # The row's sound_notifications_enabled variable handles the state
        # Just update the bell icon appearance
        row.update_bell_icon()

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
        self.save_ips()  # Save immediately after removal

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
                
                # Delete the saved JSON file if it exists
                if os.path.exists(SAVE_FILE):
                    try:
                        os.remove(SAVE_FILE)
                    except Exception as e:
                        print(f"Warning: Failed to delete saved IPs file: {e}")
                
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
            # Save current state
            self.save_ips()
            
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

    def on_closing(self):
        self.stop_event.set()
        self.save_ips()
        self.root.destroy()

    def save_ips(self):
        global SAVE_FILE
        try:
            # Save IP addresses along with their notification settings
            ips_data = []
            for row in self.rows:
                ips_data.append({
                    "ip": row.ip,
                    "notifications": row.sound_notifications_enabled.get()
                })
            
            try:
                with open(SAVE_FILE, "w") as f:
                    json.dump(ips_data, f)
            except PermissionError:
                # Try with a different filename if permission denied
                timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
                alt_filename = f"ips_{timestamp}.json"
                with open(alt_filename, "w") as f:
                    json.dump(ips_data, f)
                print(f"IP data saved to alternative file: {alt_filename}")
                # Update the global SAVE_FILE variable
                SAVE_FILE = alt_filename
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save IP addresses: {e}")

    def load_ips(self):
        try:
            # If no parameter is passed, load from default file
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, "r") as f:
                    ips_data = json.load(f)
                    
                    # Check if it's the new format or old format
                    if isinstance(ips_data, list):
                        if isinstance(ips_data[0], dict) if ips_data else False:
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
            return True
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to load saved IP addresses: {e}")
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
                    # Single IP view, just plot its data
                    timestamps = [item[0] for item in data]
                    response_times = [item[2] if item[2] is not None else float('nan') for item in data]
                    
                    ax.plot(timestamps, response_times, marker='o', markersize=4, linestyle='-', color='blue')
                
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
        about_window.geometry("400x300")
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
        tk.Label(about_window, text="Version 1.2").pack()
        ttk.Label(about_window, text="A tool for monitoring IP addresses and URLs").pack(pady=5)
        
        features = [
            "• Monitor multiple IP addresses and URLs",
            "• Track ping response times",
            "• Display status with color-coding",
            "• Sound notifications for status changes",
            "• Save and load monitoring configurations",
            "• Export statistics to CSV files",
            "• View ping history in graphs"
        ]
        
        features_frame = ttk.Frame(about_window)
        features_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        for feature in features:
            tk.Label(features_frame, text=feature, anchor="w", justify="left").pack(fill="x", pady=2)
        
        tk.Button(about_window, text="Close", command=about_window.destroy).pack(pady=10)


class IPRow:
    def __init__(self, parent, ip, global_stop_event, logging_enabled, ping_interval=None):
        """Initialize a row for monitoring an IP or URL"""
        self.ip = ip
        self.history = [None] * MAX_HISTORY
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
        
        # IP address label (using tk.Label instead of ttk for consistent styling)
        self.ip_label = tk.Label(self.frame, text=ip, width=18, anchor="w", 
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
        self.bell_icon = self.bell_canvas.create_text(12, 12, text="🔔", font=("Arial", 12), 
                                                 fill="gray", tags="bell")
        
        # Create tooltip for bell icon
        self.bell_canvas.tooltip = CreateToolTip(self.bell_canvas, "Sound notifications disabled")
        
        # Add click handler for the bell icon
        self.bell_canvas.bind("<Button-1>", self.toggle_notifications)
        
        # Update bell icon appearance
        self.update_bell_icon()

    def toggle_notifications(self, event=None):
        """Toggle sound notifications on/off"""
        self.sound_notifications_enabled.set(not self.sound_notifications_enabled.get())
        self.update_bell_icon()
        
    def update_bell_icon(self):
        """Update the bell icon appearance based on notification state"""
        if self.sound_notifications_enabled.get():
            # Use a larger, bold font and bright green for better visibility
            self.bell_canvas.itemconfig(self.bell_icon, fill="#00CC00", font=("Arial", 14, "bold"))
            self.bell_canvas.tooltip.text = "Sound notifications enabled"
        else:
            # Use normal size font and gray color for disabled state
            self.bell_canvas.itemconfig(self.bell_icon, fill="gray", font=("Arial", 12))
            self.bell_canvas.tooltip.text = "Sound notifications disabled"

    def update_display(self, result):
        # Determine current status
        current_status = True if result else False if result is None else None
        
        # Check if there's a change in status
        status_changed = self.prev_status is not None and current_status != self.prev_status
        
        # Play sound if notifications are enabled and status changed
        if status_changed and self.sound_notifications_enabled.get():
            try:
                if current_status:  # Changed to successful ping
                    winsound.MessageBeep(winsound.MB_OK)
                else:  # Changed to failed ping
                    winsound.MessageBeep(winsound.MB_ICONERROR)
            except Exception as e:
                print(f"Error playing sound: {e}")
        
        # Store current status for next comparison
        self.prev_status = current_status
        
        if result is None:
            self.history.insert(0, False)
        else:
            self.history.insert(0, True)
            self.ping_count += 1
            self.total_time += result
            
            # Update fastest time only if this is a valid result
            if result > 0:
                if self.fastest == float('inf'):
                    self.fastest = result
                else:
                    self.fastest = min(self.fastest, result)
                
                self.slowest = max(self.slowest, result)

        # Keep only MAX_HISTORY items
        self.history = self.history[:MAX_HISTORY]

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
            
        # Update label color based on the last 8 pings
        self.update_label_color()

    def update_label_color(self):
        """Update the label color and row background based on the ping history"""
        if self.paused:
            self.ip_label.config(fg="gray")
            self.set_row_background("SystemButtonFace")  # Use system default color instead of empty string
            return
            
        # Check if there are 10 valid entries in history (updated from 8)
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