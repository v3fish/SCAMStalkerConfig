import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import configparser
import subprocess
from pathlib import Path
import os
import shutil

class MovementConfigEditor:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("SCAM - Stalker Configurator Aiming & Movement")
        self.window.geometry("1000x800")

        self.load_default_config()
        self.v3fish_config = self.load_ini_file('default_ini/v3fish_recommended.ini')
        self.xy_fix_config = self.load_ini_file('default_ini/xysensitivityfix.ini')
        self.sync_sensitivity = tk.BooleanVar(value=False)
        self.setup_gui()

    def load_default_config(self):
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read('default_ini/default_values.ini')
        
        self.default_config = {}
        self.descriptions = {}
        
        for section in config.sections():
            self.default_config[section] = {}
            self.descriptions[section] = {}
            for key, value in config.items(section):
                if key.startswith(';'):
                    continue
                    
                parts = value.split(';', 1)
                raw_value = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else ''
                
                try:
                    if raw_value.lower() in ['true', 'false']:
                        self.default_config[section][key] = raw_value.lower() == 'true'
                    elif '.' in raw_value:
                        self.default_config[section][key] = float(raw_value)
                    else:
                        self.default_config[section][key] = int(raw_value)
                except ValueError:
                    self.default_config[section][key] = raw_value
                    
                if description:
                    self.descriptions[section][key] = description

    def setup_gui(self):
        top_frame = ttk.Frame(self.window)
        top_frame.pack(fill='x', padx=5, pady=5)

        # Preset controls
        preset_frame = ttk.Frame(top_frame)
        preset_frame.pack(side='top', fill='x', padx=5, pady=5)
        
        ttk.Label(preset_frame, text="Custom Presets:").pack(side='left', padx=5)
        self.preset_var = tk.StringVar()
        self.preset_combo = ttk.Combobox(preset_frame, textvariable=self.preset_var)
        self.preset_combo.pack(side='left', padx=5)
        
        ttk.Button(preset_frame, text="Load Preset", command=self.load_custom_preset).pack(side='left', padx=5)
        ttk.Button(preset_frame, text="Save Preset", command=self.save_preset).pack(side='left', padx=5)
        ttk.Button(preset_frame, text="Create Mod", command=self.create_mod).pack(side='right', padx=5)

        # Recommended presets frame
        recommended_frame = ttk.Frame(top_frame)
        recommended_frame.pack(side='top', fill='x', pady=10)
        
        buttons_frame = ttk.Frame(recommended_frame)
        buttons_frame.pack(expand=True)
        
        ttk.Button(buttons_frame, text="Default", command=self.load_default).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="V3Fish Recommended", command=self.load_v3fish).pack(side='left', padx=5)
        ttk.Button(buttons_frame, text="XY Sensitivity Aim Fix", command=self.load_xy_fix).pack(side='left', padx=5)


        if os.path.exists('custom_ini'):
            self.load_presets()

        container = ttk.Frame(self.window)
        container.pack(fill='both', expand=True, padx=5, pady=5)
        
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        main_frame = ttk.Frame(canvas)
        main_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))

        canvas.create_window((0, 0), window=main_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        notebook = ttk.Notebook(main_frame)
        notebook.pack(fill='both', expand=True)

        self.entries = {}
        self.checkboxes = {}
        
        # Create regular sections first
        for section in self.default_config:
            if section not in ['MovementParams', 'Aiming']:
                frame = ttk.Frame(notebook)
                notebook.add(frame, text=section)
                self.setup_section_frame(frame, section)

        # Create MovementParams section
        if 'MovementParams' in self.default_config:
            frame = ttk.Frame(notebook)
            notebook.add(frame, text='MovementParams')
            self.setup_movement_frame(frame)
        
        # Create Aiming section last
        aiming_frame = ttk.Frame(notebook)
        notebook.add(aiming_frame, text="Aiming")
        
        # Add sync checkbox
        if 'Aiming' in self.default_config and 'SyncTurnRate' in self.default_config['Aiming']:
            self.sync_sensitivity.set(self.default_config['Aiming']['SyncTurnRate'])
            
        sync_check = ttk.Checkbutton(aiming_frame, text="Sync Turn/Look Rate", 
                                    variable=self.sync_sensitivity,
                                    command=self.sync_sensitivity_rates)
        sync_check.grid(row=0, column=1, padx=5, pady=2, sticky='w')
        
        # Add aiming controls
        for row, key in enumerate(['BaseTurnRate', 'BaseLookUpRate'], 1):
            ttk.Label(aiming_frame, text=key).grid(row=row, column=0, padx=5, pady=2, sticky='e')
            
            entry = ttk.Entry(aiming_frame)
            entry.insert(0, str(self.default_config['MovementParams'][key]))
            entry.grid(row=row, column=1, padx=5, pady=2, sticky='w')
            entry.bind('<KeyRelease>', lambda e, k=key: self.validate_aiming_entry(k))
            self.entries[('MovementParams', key)] = entry
            
            # Default value and description
            default_value = str(self.default_config['MovementParams'][key])
            ttk.Label(aiming_frame, text=f"Default: {default_value}", font=('Arial', 8)).grid(
                row=row, column=2, padx=5, pady=2, sticky='w')
            ttk.Label(aiming_frame, text=self.descriptions['MovementParams'][key], font=('Arial', 8)).grid(
                row=row, column=3, padx=5, pady=2, sticky='w')

    def setup_section_frame(self, frame, section):
        row = 0
        for key, value in self.default_config[section].items():
            ttk.Label(frame, text=key).grid(row=row, column=0, padx=5, pady=2, sticky='e')
            
            if isinstance(value, bool):
                var = tk.BooleanVar(value=value)
                checkbox = ttk.Checkbutton(frame, variable=var)
                checkbox.grid(row=row, column=1, padx=5, pady=2, sticky='w')
                self.checkboxes[(section, key)] = var
            else:
                entry = ttk.Entry(frame)
                entry.insert(0, str(value))
                entry.grid(row=row, column=1, padx=5, pady=2, sticky='w')
                entry.bind('<KeyRelease>', lambda e, s=section, k=key: self.validate_entry(s, k))
                self.entries[(section, key)] = entry
            
            # Default value and description
            if not isinstance(value, bool):
                ttk.Label(frame, text=f"Default: {value}", font=('Arial', 8)).grid(
                    row=row, column=2, padx=5, pady=2, sticky='w')
            
            if section in self.descriptions and key in self.descriptions[section]:
                ttk.Label(frame, text=self.descriptions[section][key], font=('Arial', 8)).grid(
                    row=row, column=3, padx=5, pady=2, sticky='w')
            row += 1

    def setup_movement_frame(self, frame):
        row = 0
        for key, value in self.default_config['MovementParams'].items():
            if key not in ['BaseTurnRate', 'BaseLookUpRate']:
                ttk.Label(frame, text=key).grid(row=row, column=0, padx=5, pady=2, sticky='e')
                
                if isinstance(value, bool):
                    var = tk.BooleanVar(value=value)
                    checkbox = ttk.Checkbutton(frame, variable=var)
                    checkbox.grid(row=row, column=1, padx=5, pady=2, sticky='w')
                    self.checkboxes[('MovementParams', key)] = var
                else:
                    entry = ttk.Entry(frame)
                    entry.insert(0, str(value))
                    entry.grid(row=row, column=1, padx=5, pady=2, sticky='w')
                    entry.bind('<KeyRelease>', lambda e, k=key: self.validate_entry('MovementParams', k))
                    self.entries[('MovementParams', key)] = entry
                
                # Default value and description
                if not isinstance(value, bool):
                    ttk.Label(frame, text=f"Default: {value}", font=('Arial', 8)).grid(
                        row=row, column=2, padx=5, pady=2, sticky='w')
                
                if 'MovementParams' in self.descriptions and key in self.descriptions['MovementParams']:
                    ttk.Label(frame, text=self.descriptions['MovementParams'][key], font=('Arial', 8)).grid(
                        row=row, column=3, padx=5, pady=2, sticky='w')
                row += 1

    def sync_sensitivity_rates(self):
        if self.sync_sensitivity.get():
            turn_value = self.entries[('MovementParams', 'BaseTurnRate')].get()
            try:
                value = int(turn_value)
                self.entries[('MovementParams', 'BaseLookUpRate')].delete(0, tk.END)
                self.entries[('MovementParams', 'BaseLookUpRate')].insert(0, str(value))
                self.validate_entry('MovementParams', 'BaseLookUpRate')
            except ValueError:
                pass

    def validate_aiming_entry(self, key):
        entry = self.entries[('MovementParams', key)]
        current_value = entry.get()
        try:
            value = int(current_value)
            if self.sync_sensitivity.get():
                # Update both entries
                for rate_key in ['BaseTurnRate', 'BaseLookUpRate']:
                    entry = self.entries[('MovementParams', rate_key)]
                    default_value = str(self.default_config['MovementParams'][rate_key])
                    entry.delete(0, tk.END)
                    entry.insert(0, str(value))
                    entry.configure(foreground='green' if str(value) != default_value else 'black')
            else:
                # Update only the current entry
                default_value = str(self.default_config['MovementParams'][key])
                entry.configure(foreground='green' if current_value != default_value else 'black')
        except ValueError:
            entry.configure(foreground='red')

    def validate_entry(self, section, key):
        entry = self.entries[(section, key)]
        default_value = str(self.default_config[section][key])
        current_value = entry.get()

        try:
            if not current_value:
                entry.configure(foreground='red')
                return False

            if '.' in current_value:
                float(current_value)
            else:
                int(current_value)

            entry.configure(foreground='green' if str(current_value) != default_value else 'black')
            return True
        except ValueError:
            entry.configure(foreground='red')
            return False

    def has_invalid_entries(self):
        return any(entry.cget('foreground') == 'red' or not entry.get() 
                  for entry in self.entries.values())

    def has_changes(self):
        # Check normal entries
        for (section, key), entry in self.entries.items():
            current_value = entry.get()
            default_value = str(self.default_config[section][key])
            if current_value != default_value:
                return True
                
        # Check checkboxes and sync sensitivity
        for (section, key), checkbox in self.checkboxes.items():
            current_value = checkbox.get()
            default_value = self.default_config[section][key]
            if current_value != default_value:
                return True
                
        if 'Aiming' in self.default_config and 'SyncTurnRate' in self.default_config['Aiming']:
            if self.sync_sensitivity.get() != self.default_config['Aiming']['SyncTurnRate']:
                return True
        return False

    def load_presets(self):
        if not os.path.exists('custom_ini'):
            return
        presets = [f.replace('.ini', '') for f in os.listdir('custom_ini') if f.endswith('.ini')]
        self.preset_combo['values'] = presets

    def load_default(self):
        self.sync_sensitivity.set(False)
        self.update_entries(self.default_config)

    def load_xy_fix(self):
        self.update_entries(self.xy_fix_config)

    def load_v3fish(self):
        self.update_entries(self.v3fish_config)

    def load_custom_preset(self, event=None):
        selected = self.preset_var.get()
        if not selected:
            return
        config = self.load_ini_file(f'custom_ini/{selected}.ini')
        self.update_entries(config)

    def update_entries(self, config):
        # Reset all entries to default values
        for (section, key), entry in self.entries.items():
            default_value = str(self.default_config[section][key])
            entry.delete(0, tk.END)
            entry.insert(0, default_value)
            entry.configure(foreground='black')
            
        for (section, key), checkbox in self.checkboxes.items():
            default_value = self.default_config[section][key]
            checkbox.set(default_value)

        # Update with new values
        for section in config:
            for key, value in config[section].items():
                if section == 'Aiming' and key == 'SyncTurnRate':
                    self.sync_sensitivity.set(value)
                elif isinstance(value, bool):
                    if (section, key) in self.checkboxes:
                        self.checkboxes[(section, key)].set(value)
                else:
                    if (section, key) in self.entries:
                        entry = self.entries[(section, key)]
                        entry.delete(0, tk.END)
                        entry.insert(0, str(value))
                        self.validate_entry(section, key)

    def save_preset(self):
        if self.has_invalid_entries():
            messagebox.showerror("Error", "Please verify all values are correct!")
            return
            
        if not self.has_changes():
            messagebox.showwarning("Warning", "Make changes before saving a preset!")
            return

        selected = self.preset_var.get()
        if selected:
            if not messagebox.askyesno("Confirm Overwrite", f"Do you want to overwrite the preset '{selected}'?"):
                return
            name = selected
        else:
            name = simpledialog.askstring("Save Preset", "Enter preset name:")
            if not name:
                return
            
        config = {}
        for section in self.default_config:
            if section != 'Aiming':
                changed_values = {}
                for key, value in self.default_config[section].items():
                    if isinstance(value, bool):
                        current_value = self.checkboxes[(section, key)].get()
                        if current_value != value:
                            changed_values[key] = current_value
                    else:
                        current_value = self.entries[(section, key)].get()
                        default_value = str(value)
                        if current_value != default_value:
                            try:
                                if '.' in current_value:
                                    changed_values[key] = float(current_value)
                                else:
                                    changed_values[key] = int(current_value)
                            except ValueError:
                                messagebox.showerror("Error", f"Invalid value for {key}!")
                                return
                if changed_values:
                    config[section] = changed_values

        # Add Aiming section if sync is checked
        if self.sync_sensitivity.get():
            config['Aiming'] = {'SyncTurnRate': True}

        if not os.path.exists('custom_ini'):
            os.makedirs('custom_ini')
            
        self.save_ini_file(config, f'custom_ini/{name}.ini')
        self.load_presets()
        messagebox.showinfo("Success", "Preset saved successfully!")

    def create_mod(self):
        if self.has_invalid_entries():
            messagebox.showerror("Error", "Please verify all values are correct!")
            return

        if not self.has_changes():
            messagebox.showwarning("Warning", "Make changes before creating a mod!")
            return

        config = {}
        for section in self.default_config:
            if section != 'Aiming':  # Skip Aiming section for mod creation
                changed_values = {}
                for key, value in self.default_config[section].items():
                    if isinstance(value, bool):
                        current_value = self.checkboxes[(section, key)].get()
                        if current_value != value:
                            changed_values[key] = current_value
                    else:
                        current_value = self.entries[(section, key)].get()
                        default_value = str(value)
                        if current_value != default_value:
                            try:
                                if '.' in current_value:
                                    changed_values[key] = float(current_value)
                                else:
                                    changed_values[key] = int(current_value)
                            except ValueError:
                                messagebox.showerror("Error", f"Invalid value for {key}!")
                                return
                if changed_values:
                    config[section] = changed_values

        mod_path = Path('z_SCAMMovementAiming_P/Stalker2/Content/GameLite/GameData/ObjPrototypes')
        mod_path.mkdir(parents=True, exist_ok=True)
        
        cfg_content = "CustomPlayer : struct.begin {refurl=../ObjPrototypes.cfg; refkey=Player}\n"
        for section, values in config.items():
            cfg_content += f"   {section} : struct.begin\n"
            for key, value in values.items():
                cfg_content += f"      {key} = {value}\n"
            cfg_content += "   struct.end\n"
        cfg_content += "struct.end"
        
        with open(mod_path / 'SCAM.cfg', 'w') as f:
            f.write(cfg_content)
        
        if os.path.exists('repak/repak.exe'):
            try:
                subprocess.run(['repak/repak.exe', 'pack', 'z_SCAMMovementAiming_P'])
                # Remove the directory after successful packing
                shutil.rmtree('z_SCAMMovementAiming_P')
                messagebox.showinfo("Success", "Mod created successfully!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create mod: {str(e)}")
        else:
            messagebox.showerror("Error", "repak.exe not found in repak folder!")

    def load_ini_file(self, filename):
        config = configparser.ConfigParser()
        config.optionxform = str
        config.read(filename)
        
        result = {}
        for section in config.sections():
            result[section] = {}
            for key, value in config.items(section):
                if key.startswith(';'):
                    continue
                    
                value = value.split(';')[0].strip()
                    
                try:
                    if value.lower() in ['true', 'false']:
                        result[section][key] = value.lower() == 'true'
                    elif '.' in value:
                        result[section][key] = float(value)
                    else:
                        result[section][key] = int(value)
                except ValueError:
                    result[section][key] = value
        return result

    def save_ini_file(self, config, filename):
        ini = configparser.ConfigParser()
        ini.optionxform = str
        for section, values in config.items():
            if values:
                ini[section] = {k: str(v) for k, v in values.items()}
            
        with open(filename, 'w') as f:
            ini.write(f)

    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    app = MovementConfigEditor()
    app.run()