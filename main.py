import networkx as nx
import matplotlib.pyplot as plt
import random
import tkinter as tk
from tkinter import ttk, messagebox

class NetworkResilienceApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Моделирование устойчивости сетей к случайным атакам")

        self.network_type = tk.StringVar(value="Случайная (Erdős–Rényi)")
        self.n = tk.IntVar(value=10)
        self.p = tk.DoubleVar(value=0.5)
        self.m = tk.IntVar(value=2)
        self.k = tk.IntVar(value=4)
        self.reconnect_prob = tk.DoubleVar(value=0.1)

        self.G = None
        self.removed_nodes = set()
        self.giant_component_sizes = []
        self.average_shortest_paths = []
        self.removed_fractions = []
        self.critical_threshold = None

        self.create_widgets()

    def create_widgets(self):
        ttk.Label(self.root, text="Тип сети:").grid(row=0, column=0, padx=10, pady=5)
        network_type_menu = ttk.Combobox(self.root, textvariable=self.network_type, values=["Случайная (Erdős–Rényi)", "Scale-free (Barabási–Albert)", "Small-world (Watts–Strogatz)"])
        network_type_menu.grid(row=0, column=1, padx=10, pady=5)

        ttk.Label(self.root, text="Количество узлов:").grid(row=1, column=0, padx=10, pady=5)
        ttk.Entry(self.root, textvariable=self.n).grid(row=1, column=1, padx=10, pady=5)

        ttk.Label(self.root, text="Вероятность связи (0-1):").grid(row=2, column=0, padx=10, pady=5)
        ttk.Entry(self.root, textvariable=self.p).grid(row=2, column=1, padx=10, pady=5)

        ttk.Label(self.root, text="Количество ребер для каждого нового узла:").grid(row=3, column=0, padx=10, pady=5)
        ttk.Entry(self.root, textvariable=self.m).grid(row=3, column=1, padx=10, pady=5)

        ttk.Label(self.root, text="Степень каждого узла:").grid(row=4, column=0, padx=10, pady=5)
        ttk.Entry(self.root, textvariable=self.k).grid(row=4, column=1, padx=10, pady=5)

        ttk.Label(self.root, text="Вероятность переподключения (0-1):").grid(row=5, column=0, padx=10, pady=5)
        ttk.Entry(self.root, textvariable=self.reconnect_prob).grid(row=5, column=1, padx=10, pady=5)

        ttk.Button(self.root, text="Создать сеть", command=self.create_network).grid(row=6, column=0, columnspan=2, pady=10)
        ttk.Button(self.root, text="Удалить узел", command=self.remove_node).grid(row=7, column=0, columnspan=2, pady=10)
        ttk.Button(self.root, text="Анализ", command=self.analyze).grid(row=8, column=0, columnspan=2, pady=10)
        ttk.Button(self.root, text="Выход", command=self.root.quit).grid(row=9, column=0, columnspan=2, pady=10)

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

        self.removed_nodes = set()
        self.giant_component_sizes = []
        self.average_shortest_paths = []
        self.removed_fractions = []
        self.critical_threshold = None

        self.visualize_graph()

    def remove_node(self):
        if self.G is None:
            messagebox.showerror("Ошибка", "Сеть не создана.")
            return

        if len(self.G.nodes) == 0:
            messagebox.showinfo("Информация", "Граф пуст. Атака невозможна.")
            return

        plt.close()  # Закрыть предыдущее окно графа

        node_to_remove = random.choice(list(self.G.nodes))
        self.removed_nodes.add(node_to_remove)
        self.G.remove_node(node_to_remove)
        print(f"Удален узел: {node_to_remove}")

        giant_size = self.giant_component_size()
        self.giant_component_sizes.append(giant_size)
        self.average_shortest_paths.append(self.average_shortest_path_length())
        self.removed_fractions.append(len(self.removed_nodes) / self.n.get())

        if self.critical_threshold is None and giant_size < 2:
            self.critical_threshold = len(self.removed_nodes) / self.n.get()

        self.visualize_graph()

    def analyze(self):
        if self.G is None:
            messagebox.showerror("Ошибка", "Сеть не создана.")
            return

        plt.figure(figsize=(12, 6))

        plt.subplot(1, 2, 1)
        plt.plot(self.removed_fractions, self.giant_component_sizes, marker='o')
        plt.xlabel('Доля удалённых узлов')
        plt.ylabel('Размер гигантской компоненты')
        plt.title('Размер гигантской компоненты vs доля удалённых узлов')
        if self.critical_threshold is not None:
            plt.axvline(x=self.critical_threshold, color='r', linestyle='--', label='Критический порог')
            plt.legend()

        plt.subplot(1, 2, 2)
        plt.plot(self.removed_fractions, self.average_shortest_paths, marker='o')
        plt.xlabel('Доля удалённых узлов')
        plt.ylabel('Средний кратчайший путь')
        plt.title('Средний кратчайший путь vs доля удалённых узлов')

        plt.tight_layout()
        plt.show()

    def visualize_graph(self):
        if self.G is None:
            return

        pos = nx.spring_layout(self.G)
        node_colors = ['red' if node in self.removed_nodes else 'green' for node in self.G.nodes]
        plt.figure()
        nx.draw(self.G, pos, with_labels=True, node_color=node_colors, edge_color='black')
        plt.show()

    def giant_component_size(self):
        if len(self.G.nodes) == 0:
            return 0
        largest_cc = max(nx.connected_components(self.G), key=len)
        return len(largest_cc)

    def average_shortest_path_length(self):
        if len(self.G.nodes) == 0:
            return float('inf')
        return nx.average_shortest_path_length(self.G)

if __name__ == "__main__":
    root = tk.Tk()
    app = NetworkResilienceApp(root)
    root.mainloop()