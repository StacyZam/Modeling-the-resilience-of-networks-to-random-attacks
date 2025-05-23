#######################################################################################################################
#######                                                                                                         #######
####### Моделирование устойчивости сетей к случайным атакам                                                     #######
#######                 version 0.3                                                                             #######
####### Дипломная работа                                                                                        #######
####### Github: https://github.com/StacyZam/Modeling-the-resilience-of-networks-to-random-attacks               #######
#######                                                                                                         #######
#######################################################################################################################

import networkx as nx
import matplotlib.pyplot as plt
import random
import tkinter as tk
from tkinter import ttk, messagebox, LabelFrame, Text, Scrollbar

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

class NetworkResilienceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Моделирование устойчивости сетей к случайным атакам")
        self.root.geometry("1600x680")  # Set the main window size

        self.network_type = tk.StringVar(value="Случайная (Erdős–Rényi)")
        self.n = tk.IntVar(value=10)
        self.p = tk.DoubleVar(value=0.5)
        self.m = tk.IntVar(value=2)
        self.k = tk.IntVar(value=4)
        self.reconnect_prob = tk.DoubleVar(value=0.1)

        self.G = None
        self.removed_nodes = []  # Store removed nodes in order of removal (list instead of set)
        self.giant_component_sizes = []
        self.average_shortest_paths = []
        self.removed_fractions = []
        self.critical_threshold = None
        self.pos = None
        self.node_colors = {} # Store node colors

        # Matplotlib figures and axes
        self.graph_fig, self.graph_ax = plt.subplots(figsize=(6, 6))  # Graph figure
        self.analysis_fig, self.analysis_ax = plt.subplots(figsize=(6, 4))  # Analysis figure

        self.graph_canvas = None
        self.analysis_canvas = None
        self.ax2 = None  # Add an attribute to store the second y-axis

        self.removed_nodes_text = None  # Text widget to display removed nodes
        self.removed_nodes_scrollbar = None

        # Input widgets
        self.n_label = None
        self.n_entry = None
        self.p_label = None
        self.p_entry = None
        self.m_label = None
        self.m_entry = None
        self.k_label = None
        self.k_entry = None
        self.reconnect_prob_label = None
        self.reconnect_prob_entry = None

        self.create_widgets()
        self.create_graph_area()
        self.create_analysis_area()
        self.create_removed_nodes_area()

    def create_widgets(self):
        # --- Input Frame ---
        input_frame = LabelFrame(self.root, text="Параметры сети", padx=5, pady=5)
        input_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nw")

        ttk.Label(input_frame, text="Тип сети:").grid(row=0, column=0, padx=5, pady=2, sticky="w")
        network_type_menu = ttk.Combobox(input_frame, textvariable=self.network_type, values=["Случайная (Erdős–Rényi)", "Scale-free (Barabási–Albert)", "Small-world (Watts–Strogatz)"])
        network_type_menu.grid(row=0, column=1, padx=5, pady=2, sticky="w")
        network_type_menu.bind("<<ComboboxSelected>>", self.update_input_fields)  # Bind event

        # Initialize input fields (initially only n is visible)
        self.n_label = ttk.Label(input_frame, text="Количество узлов:")
        self.n_label.grid(row=1, column=0, padx=5, pady=2, sticky="w")
        self.n_entry = ttk.Entry(input_frame, textvariable=self.n)
        self.n_entry.grid(row=1, column=1, padx=5, pady=2, sticky="w")

        self.p_label = ttk.Label(input_frame, text="Вероятность связи (0-1):")
        self.p_entry = ttk.Entry(input_frame, textvariable=self.p)

        self.m_label = ttk.Label(input_frame, text="Количество ребер для каждого нового узла:")
        self.m_entry = ttk.Entry(input_frame, textvariable=self.m)

        self.k_label = ttk.Label(input_frame, text="Степень каждого узла:")
        self.k_entry = ttk.Entry(input_frame, textvariable=self.k)

        self.reconnect_prob_label = ttk.Label(input_frame, text="Вероятность переподключения (0-1):")
        self.reconnect_prob_entry = ttk.Entry(input_frame, textvariable=self.reconnect_prob)

        # --- Button Frame ---
        button_frame = LabelFrame(self.root, text="Действия", padx=5, pady=5)
        button_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nw")

        ttk.Button(button_frame, text="Создать сеть", command=self.create_network).grid(row=0, column=0, padx=5, pady=2, sticky="w")
        ttk.Button(button_frame, text="Удалить узел", command=self.remove_node).grid(row=1, column=0, padx=5, pady=2, sticky="w")
        ttk.Button(button_frame, text="Активировать случайную атаку", command=self.activate_random_attack).grid(row=2, column=0, padx=5, pady=2, sticky="w") # Add new button
        ttk.Button(button_frame, text="Анализ", command=self.analyze).grid(row=3, column=0, padx=5, pady=2, sticky="w")
        ttk.Button(button_frame, text="Выход", command=self.root.quit).grid(row=4, column=0, padx=5, pady=2, sticky="w")

        self.update_input_fields()  # Initialize visibility

    def create_graph_area(self):
        graph_frame = LabelFrame(self.root, text="Граф сети", padx=5, pady=5)  # LabelFrame for graph
        graph_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew", rowspan=2)  # Adjusted rowspan

        self.graph_canvas = FigureCanvasTkAgg(self.graph_fig, master=graph_frame) # Use graph_frame as master
        self.graph_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True) # Use pack instead of grid
        self.graph_ax.axis('off')

    def create_analysis_area(self):
        analysis_frame = LabelFrame(self.root, text="Анализ устойчивости", padx=5, pady=5)  # LabelFrame for analysis
        analysis_frame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew", rowspan=1)  # Adjusted rowspan

        self.analysis_canvas = FigureCanvasTkAgg(self.analysis_fig, master=analysis_frame)  # Use analysis_frame as master
        self.analysis_canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=True)  # Use pack instead of grid

    def create_removed_nodes_area(self):
        removed_nodes_frame = LabelFrame(self.root, text="Удалённые узлы", padx=5, pady=5)
        removed_nodes_frame.grid(row=1, column=2, padx=10, pady=10, sticky="nsew")

        self.removed_nodes_text = Text(removed_nodes_frame, height=10, width=20, wrap=tk.WORD)  # Added wrap=tk.WORD for text wrapping
        self.removed_nodes_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.removed_nodes_scrollbar = Scrollbar(removed_nodes_frame, command=self.removed_nodes_text.yview)
        self.removed_nodes_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.removed_nodes_text['yscrollcommand'] = self.removed_nodes_scrollbar.set

    def create_network(self):
        n = self.n.get()
        if self.network_type.get() == "Случайная (Erdős–Rényi)":
            p = self.p.get()
            self.G = nx.erdos_renyi_graph(n, p)
        elif self.network_type.get() == "Scale-free (Barabási–Albert)":
            m = self.m.get()
            self.G = nx.barabasi_albert_graph(n, m)
        elif self.network_type.get() == "Small-world (Watts–Strogatz)":
            k = self.k.get()
            p = self.reconnect_prob.get()
            self.G = nx.watts_strogatz_graph(n, k, p)
        else:
            messagebox.showerror("Ошибка", "Неверный выбор типа сети.")
            return

        self.removed_nodes = []  # Clear the list, not set
        self.giant_component_sizes = []
        self.average_shortest_paths = []
        self.removed_fractions = []
        self.critical_threshold = None

        self.pos = nx.spring_layout(self.G)
        self.node_colors = {node: 'green' for node in self.G.nodes()} # Assign initial color

        self.visualize_graph()
        self.analyze()  # Ensure analysis is also updated when the network is created.
        self.update_removed_nodes_display()  # Clear and update the text box

    def remove_node(self):
        if self.G is None:
            messagebox.showerror("Ошибка", "Сеть не создана.")
            return

        if len(self.G.nodes) == 0:
            messagebox.showinfo("Информация", "Граф пуст. Атака невозможна.")
            return

        # Select a node that has not been removed yet
        available_nodes = list(set(self.G.nodes) - set(self.removed_nodes))
        if not available_nodes:
            messagebox.showinfo("Информация", "Все узлы уже удалены.")
            return

        node_to_remove = random.choice(available_nodes)
        self.removed_nodes.append(node_to_remove)  # Append to the list

        # Remove edges connected to the node, but keep the node
        neighbors = list(nx.neighbors(self.G, node_to_remove))
        for neighbor in neighbors:
            self.G.remove_edge(node_to_remove, neighbor)

        self.G.remove_node(node_to_remove)
        #self.node_colors[node_to_remove] = 'red' # Change node color
        print(f"Удален узел: {node_to_remove}")

        giant_size = self.giant_component_size()
        self.giant_component_sizes.append(giant_size)
        self.average_shortest_paths.append(self.average_shortest_path_length())
        self.removed_fractions.append(len(self.removed_nodes) / self.n.get())

        if self.critical_threshold is None and giant_size < 2:
            self.critical_threshold = len(self.removed_nodes) / self.n.get()
            self.update_removed_nodes_display(critical_point=True)  # Update with critical point message
        else:
            self.update_removed_nodes_display()  # Update without critical point message

        self.visualize_graph()
        self.analyze()  # Automatically update the analysis plot

    def activate_random_attack(self):
        if self.G is None:
            messagebox.showerror("Ошибка", "Сеть не создана.")
            return

        self.root.after(1000, self.remove_node_and_update)  # Start the attack with a delay

    def remove_node_and_update(self):
        if self.G and len(self.G.nodes) > 0 and self.critical_threshold is None:
            self.remove_node()
            self.root.after(1000, self.remove_node_and_update)  # Continue the attack with a delay
        else:
            if self.critical_threshold is not None:
                messagebox.showinfo("Информация", "Случайная атака завершена. Достигнут критический порог.")
            else:
                messagebox.showinfo("Информация", "Случайная атака завершена. Все узлы изолированы.")

    def analyze(self):
        if self.G is None:
            messagebox.showerror("Ошибка", "Сеть не создана.")
            return

        self.analysis_ax.clear()  # Clear previous plots

        # Plot the giant component size
        self.analysis_ax.plot(self.removed_fractions, self.giant_component_sizes, marker='o', label='Размер гигантской компоненты')
        self.analysis_ax.set_xlabel('Доля удалённых узлов')
        self.analysis_ax.set_ylabel('Размер гигантской компоненты')
        self.analysis_ax.set_title('Размер гигантской компоненты vs доля удалённых узлов')

        # Create or reuse the second y-axis
        if self.ax2 is None:
            self.ax2 = self.analysis_ax.twinx()
            self.ax2.set_ylabel('Средний кратчайший путь', color='red')
            self.ax2.tick_params(axis='y', labelcolor='red')
        else:
            # Clear the previous plot on ax2
            self.ax2.cla()
            self.ax2.set_ylabel('Средний кратчайший путь', color='red')  # Set label again
            self.ax2.tick_params(axis='y', labelcolor='red')  # Set tick parameters again

        # Plot the average shortest path on the second y-axis
        self.ax2.plot(self.removed_fractions, self.average_shortest_paths, marker='x', color='red', label='Средний кратчайший путь')

        if self.critical_threshold is not None:
            self.analysis_ax.axvline(x=self.critical_threshold, color='r', linestyle='--', label='Критический порог')

        # Combine legends from both axes
        lines, labels = self.analysis_ax.get_legend_handles_labels()
        lines2, labels2 = [self.ax2.get_lines()[0]], ['Средний кратчайший путь']  # Corrected legend
        self.analysis_ax.legend(lines + lines2, labels + labels2, loc='upper right')

        self.analysis_canvas.draw()

    def visualize_graph(self):
        if self.G is None:
            return

        self.graph_ax.clear()

        # Get node colors from the dictionary
        node_colors = [self.node_colors[node] for node in self.G.nodes()]

        nx.draw(self.G, self.pos, with_labels=True, node_color=node_colors, edge_color='black', ax=self.graph_ax)
        self.graph_canvas.draw()

    def giant_component_size(self):
        if len(self.G.nodes) == 0:
            return 0
        largest_cc = max(nx.connected_components(self.G), key=len)
        return len(largest_cc)

    def average_shortest_path_length(self):
        if len(self.G.nodes) == 0:
            return float('inf')
        if nx.is_connected(self.G):
            return nx.average_shortest_path_length(self.G)
        else:
            return float('inf')

    def update_removed_nodes_display(self, critical_point=False):
        self.removed_nodes_text.delete("1.0", tk.END)  # Clear the text box
        for node in self.removed_nodes:
            self.removed_nodes_text.insert(tk.END, str(node) + "\n")

        if critical_point:
            self.removed_nodes_text.insert(tk.END, "\nДОСТИГНУТ КРИТИЧЕСКИЙ ПОРОГ\n")

    def update_input_fields(self, event=None):
        network_type = self.network_type.get()

        # Hide all input fields first
        self.p_label.grid_remove()
        self.p_entry.grid_remove()
        self.m_label.grid_remove()
        self.m_entry.grid_remove()
        self.k_label.grid_remove()
        self.k_entry.grid_remove()
        self.reconnect_prob_label.grid_remove()
        self.reconnect_prob_entry.grid_remove()

        # Then show only the relevant ones
        if network_type == "Случайная (Erdős–Rényi)":
            self.p_label.grid(row=2, column=0, padx=5, pady=2, sticky="w")
            self.p_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        elif network_type == "Scale-free (Barabási–Albert)":
            self.m_label.grid(row=2, column=0, padx=5, pady=2, sticky="w")
            self.m_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")
        elif network_type == "Small-world (Watts–Strogatz)":
            self.k_label.grid(row=2, column=0, padx=5, pady=2, sticky="w")
            self.k_entry.grid(row=2, column=1, padx=5, pady=2, sticky="w")
            self.reconnect_prob_label.grid(row=3, column=0, padx=5, pady=2, sticky="w")
            self.reconnect_prob_entry.grid(row=3, column=1, padx=5, pady=2, sticky="w")

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkResilienceApp(root)
    root.mainloop()
