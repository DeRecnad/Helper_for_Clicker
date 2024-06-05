import json
import tkinter as tk
from tkinter import ttk
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.backend_bases import MouseEvent


def format_cost(cost):
    num = float('{:.3g}'.format(cost))
    magnitude = 0
    while abs(num) >= 1000:
        magnitude += 1
        num /= 1000.0
    return '{}{}'.format('{:f}'.format(num).rstrip('0').rstrip('.'), ['', 'K', 'M', 'B', 'T'][magnitude])
    return str(cost)


class Tooltip:
    def __init__(self, graph, points, names):
        self.graph = graph
        self.points = points
        self.names = names
        self.tooltip = tk.Label(self.graph.get_tk_widget(), text='', bg='white', borderwidth=1, relief='solid')
        self.tooltip.place(x=0, y=0)
        self.tooltip.place_forget()

    def show_tooltip(self, event):
        idx = event.ind[0]
        if 0 <= idx < len(self.names):
            x, y = event.x, event.y
            self.tooltip.config(text=self.names[idx])
            self.tooltip.place(x=x, y=y, anchor='nw')

    def hide_tooltip(self, event):
        self.tooltip.place_forget()


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

    def get_top_profitable_upgrades(self, top_n=3):
        profitable_upgrades = sorted(
            [upgrade for upgrade in self.upgrades if upgrade.unlocked],
            key=lambda x: x.income_increase / x.cost,
            reverse=True
        )
        return profitable_upgrades[:top_n]


class App:
    def __init__(self, master):
        self.master = master
        self.upgrade_manager = UpgradeManager("upgrades.json")
        self.top_upgrades = None

        self.category_var = tk.StringVar()
        self.category_var.set("All")
        self.category_var.trace('w', self.load_upgrades)

        self.scrollbar = tk.Scrollbar(master)
        self.scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.listbox = tk.Listbox(master, yscrollcommand=self.scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.scrollbar.config(command=self.listbox.yview)

        self.category_combobox = ttk.Combobox(master, textvariable=self.category_var,
                                              values=["All", "Markets", "PR&Team", "Legal", "Special"])
        self.category_combobox.pack()

        self.setup_editing()
        self.setup_top_upgrades_display()
        self.setup_graph_display()
        self.load_upgrades()

    def load_upgrades(self, *args):
        self.listbox.delete(0, tk.END)
        category_filter = self.category_var.get() if self.category_var.get() != "All" else None
        self.upgrade_manager.load_upgrades_from_file()
        for i, upgrade in enumerate(self.upgrade_manager.upgrades):
            if category_filter is None or upgrade.category == category_filter:
                self.listbox.insert(tk.END,
                                    f"{upgrade.name}, {upgrade.category} - Cost: {upgrade.cost}, Income Increase: {upgrade.income_increase}")
                self.listbox.itemconfig(tk.END, {'bg': 'green' if upgrade.unlocked else 'red'})

        self.calculate_top_profitable_upgrades()
        self.highlight_top_profitable_upgrades()
        self.update_graph()

    def calculate_top_profitable_upgrades(self):
        self.top_upgrades = self.upgrade_manager.get_top_profitable_upgrades()
        self.display_top_profitable_upgrades()

    def highlight_top_profitable_upgrades(self):
        if self.top_upgrades:
            category_filter = self.category_var.get() if self.category_var.get() != "All" else None
            for i, upgrade in enumerate(self.upgrade_manager.upgrades):
                if category_filter is None or upgrade.category == category_filter:
                    if i < self.listbox.size():
                        if upgrade == self.top_upgrades[0]:
                            self.listbox.itemconfig(i, {'bg': 'cyan'})  # Топ 1 - голубой
                        elif upgrade == self.top_upgrades[1]:
                            self.listbox.itemconfig(i, {'bg': 'yellow'})  # Топ 2 - желтый
                        elif upgrade == self.top_upgrades[2]:
                            self.listbox.itemconfig(i, {'bg': 'orange'})  # Топ 3 - оранжевый
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
            upgrade.category = self.category_entry.get()
            upgrade.cost = int(self.new_cost_entry.get())
            upgrade.income_increase = int(self.new_income_entry.get())
            self.upgrade_manager.save_upgrades_to_file()
            self.load_upgrades()

    def setup_top_upgrades_display(self):
        self.top_upgrade_labels = []
        for i in range(3):
            label = tk.Label(self.master, text="", bg="white")
            label.pack()
            self.top_upgrade_labels.append(label)

    def display_top_profitable_upgrades(self):
        if self.top_upgrades:
            for i, upgrade in enumerate(self.top_upgrades):
                roi_hours = upgrade.cost / upgrade.income_increase
                self.top_upgrade_labels[i].config(
                    text=f"{upgrade.name} - Cost: {upgrade.cost}, Income Increase: {upgrade.income_increase}, ROI (hours): {roi_hours:.2f}")

    def setup_graph_display(self):
        self.figure = plt.figure(figsize=(5, 4))
        self.subplot = self.figure.add_subplot(111)
        self.graph = FigureCanvasTkAgg(self.figure, master=self.master)
        self.graph.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

    def update_graph(self):
        if self.upgrade_manager.upgrades:
            upgrades_sorted = sorted([upgrade for upgrade in self.upgrade_manager.upgrades if upgrade.unlocked],
                                     key=lambda upgrade: upgrade.cost)
            x = [upgrade.cost for upgrade in upgrades_sorted]
            y = [upgrade.income_increase for upgrade in upgrades_sorted]
            colors = ['cyan' if upgrade in self.top_upgrades else 'grey' for upgrade in upgrades_sorted]
            names = [upgrade.name for upgrade in upgrades_sorted]

            self.subplot.clear()

            points = self.subplot.scatter(x, y, color=colors, s=10)
            self.subplot.set_xlabel('Upgrade Cost')
            self.subplot.set_ylabel('Income Increase')
            self.subplot.set_title('Upgrade Cost vs. Income Increase')

            min_income = min(y)
            max_income = max(y)
            self.subplot.set_ylim(min_income, max_income * 1.1)

            max_cost = max(x)
            num_ticks = 8  # Количество меток на оси X
            x_ticks = np.linspace(0, max_cost, num_ticks)

            # Установка меток и их форматирование на оси X
            self.subplot.set_xticks(x_ticks)
            self.subplot.set_xticklabels([format_cost(cost) for cost in x_ticks])

            # Нарисовать диагональную линию
            self.subplot.plot([0, max_cost], [0, max_income], color='black', linestyle='--', linewidth=0.5)

            # Обновление графика
            self.graph.draw()

            # Создание подсказки для точек на графике
            tooltip = Tooltip(self.graph, points, names)
            self.graph.mpl_connect('motion_notify_event', tooltip.show_tooltip)
            self.graph.mpl_connect('axes_leave_event', tooltip.hide_tooltip)


def main():
    root = tk.Tk()
    root.title("Upgrade Manager")
    app = App(root)
    root.mainloop()

if __name__ == "__main__":
    main()


