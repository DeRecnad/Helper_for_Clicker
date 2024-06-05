import json
import tkinter as tk
from tkinter import ttk

class Upgrade:
    def __init__(self, name, cost, income_increase, category, unlocked):
        self.name = name
        self.cost = cost
        self.income_increase = income_increase
        self.category = category
        self.unlocked = unlocked

class UpgradeManager:
    def __init__(self, filename):
        self.filename = filename
        self.upgrades = self.load_upgrades_from_file()

    def load_upgrades_from_file(self):
        with open(self.filename, 'r') as file:
            data = json.load(file)
            upgrades = [Upgrade(**upgrade_data) for upgrade_data in data]
        return upgrades

    def save_upgrades_to_file(self):
        with open(self.filename, 'w') as file:
            data = [upgrade.__dict__ for upgrade in self.upgrades]
            json.dump(data, file, indent=4)

    def get_most_profitable_upgrade(self):
        max_profit = 0
        most_profitable_upgrade = None
        for upgrade in self.upgrades:
            if upgrade.unlocked:
                profit = upgrade.income_increase / upgrade.cost
                if profit > max_profit:
                    max_profit = profit
                    most_profitable_upgrade = upgrade
        return most_profitable_upgrade

class App:
    def __init__(self, master):
        self.master = master
        self.upgrade_manager = UpgradeManager("upgrades.json")
        self.most_profitable_upgrade = None

        self.category_var = tk.StringVar()
        self.category_var.set("All")
        self.category_var.trace('w', self.load_upgrades)

        self.scrollbar = tk.Scrollbar(master)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(master, yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)

        self.category_combobox = ttk.Combobox(master, textvariable=self.category_var, values=["All", "Markets", "PR&Team", "Legal", "Special"])
        self.category_combobox.pack()

        self.setup_editing()
        self.load_upgrades()

    def load_upgrades(self, *args):
        self.listbox.delete(0, tk.END)
        category_filter = self.category_var.get() if self.category_var.get() != "All" else None
        for i, upgrade in enumerate(self.upgrade_manager.upgrades):
            if category_filter is None or upgrade.category == category_filter:
                self.listbox.insert(tk.END, f"{upgrade.name}, {upgrade.category} - Cost: {upgrade.cost}, Income Increase: {upgrade.income_increase}")
                self.listbox.itemconfig(tk.END, {'bg': 'green' if upgrade.unlocked else 'red'})

        self.calculate_most_profitable_upgrade()
        self.highlight_most_profitable_upgrade()

    def calculate_most_profitable_upgrade(self):
        self.most_profitable_upgrade = self.upgrade_manager.get_most_profitable_upgrade()
        if self.most_profitable_upgrade:
            print(f"The most profitable upgrade to buy is: {self.most_profitable_upgrade.name}")

    def highlight_most_profitable_upgrade(self):
        if self.most_profitable_upgrade:
            for i, upgrade in enumerate(self.upgrade_manager.upgrades):
                if upgrade == self.most_profitable_upgrade:
                    self.listbox.itemconfig(i, {'bg': 'yellow'})
                else:
                    self.listbox.itemconfig(i, {'bg': 'green' if upgrade.unlocked else 'red'})

    def setup_editing(self):
        self.selected_index = None

        self.edit_frame = tk.Frame(self.master)
        self.edit_frame.pack()

        tk.Label(self.edit_frame, text="Selected Upgrade:").grid(row=0, column=0)
        self.selected_label = tk.Label(self.edit_frame, text="")
        self.selected_label.grid(row=0, column=1)

        tk.Label(self.edit_frame, text="Category:").grid(row=1, column=0)
        self.category_entry = ttk.Combobox(self.edit_frame, values=["Markets", "PR&Team", "Legal", "Special"])
        self.category_entry.grid(row=1, column=1)

        tk.Label(self.edit_frame, text="New Cost:").grid(row=2, column=0)
        self.new_cost_entry = tk.Entry(self.edit_frame)
        self.new_cost_entry.grid(row=2, column=1)

        tk.Label(self.edit_frame, text="New Income Increase:").grid(row=3, column=0)
        self.new_income_entry = tk.Entry(self.edit_frame)
        self.new_income_entry.grid(row=3, column=1)

        tk.Button(self.edit_frame, text="Update", command=self.update_upgrade).grid(row=4, column=0, columnspan=2)

        self.listbox.bind("<ButtonRelease-1>", self.on_select_upgrade)

    def on_select_upgrade(self, event):
        try:
            index = self.listbox.curselection()[0]
            self.selected_index = index
            upgrade = self.upgrade_manager.upgrades[index]
            self.selected_label.config(text=upgrade.name)
            self.category_entry.set(upgrade.category)
            self.new_cost_entry.delete(0, tk.END)
            self.new_cost_entry.insert(0, str(upgrade.cost))
            self.new_income_entry.delete(0, tk.END)
            self.new_income_entry.insert(0, str(upgrade.income_increase))
        except IndexError:
            pass

    def update_upgrade(self):
        if self.selected_index is not None:
            upgrade = self.upgrade_manager.upgrades[self.selected_index]
            upgrade.cost = int(self.new_cost_entry.get())
            upgrade.income_increase = int(self.new_income_entry.get())
            upgrade.category = self.category_entry.get()
            self.upgrade_manager.save_upgrades_to_file()
            self.load_upgrades()
            self.calculate_most_profitable_upgrade()
            self.highlight_most_profitable_upgrade()

def main():
    root = tk.Tk()
    root.title("Upgrade Manager")
    root.geometry("600x400") 
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()
