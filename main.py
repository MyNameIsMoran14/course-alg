import flet as ft
import sqlite3
import random

# --- 1. АВЛ-ДЕРЕВО ---
class AVLNode:
    def __init__(self, key, room_type, equipment):
        self.key, self.room_type, self.equipment = key, room_type, equipment
        self.left = self.right = None
        self.height = 1

class AVLTree:
    def get_height(self, n): return n.height if n else 0
    def get_balance(self, n): return self.get_height(n.left) - self.get_height(n.right) if n else 0
    def rotate_right(self, y):
        x, T2 = y.left, y.left.right
        x.right, y.left = y, T2
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        x.height = 1 + max(self.get_height(x.left), self.get_height(x.right))
        return x
    def rotate_left(self, x):
        y, T2 = x.right, x.right.left
        y.left, x.right = x, T2
        x.height = 1 + max(self.get_height(x.left), self.get_height(x.right))
        y.height = 1 + max(self.get_height(y.left), self.get_height(y.right))
        return y
    def insert(self, root, key, r_type, equip):
        if not root: return AVLNode(key, r_type, equip)
        if key < root.key: root.left = self.insert(root.left, key, r_type, equip)
        else: root.right = self.insert(root.right, key, r_type, equip)
        root.height = 1 + max(self.get_height(root.left), self.get_height(root.right))
        b = self.get_balance(root)
        if b > 1 and key < root.left.key: return self.rotate_right(root)
        if b < -1 and key > root.right.key: return self.rotate_left(root)
        if b > 1 and key > root.left.key:
            root.left = self.rotate_left(root.left)
            return self.rotate_right(root)
        if b < -1 and key < root.right.key:
            root.right = self.rotate_right(root.right)
            return self.rotate_left(root)
        return root
    def pre_order(self, root, result):
        if root:
            result.append(root)
            self.pre_order(root.left, result)
            self.pre_order(root.right, result)

# --- 2. ХЕШ-ТАБЛИЦА ---
class HashNode:
    def __init__(self, passport, fio):
        self.passport, self.fio = passport, fio
        self.next = None

class HashTable:
    def __init__(self, size=10):
        self.size, self.table = size, [None] * size
    def _hash(self, key):
        return sum(ord(c) for c in str(key)) % self.size
    def insert(self, passport, fio):
        idx = self._hash(passport)
        new_node = HashNode(passport, fio)
        if not self.table[idx]: self.table[idx] = new_node
        else:
            curr = self.table[idx]
            while curr.next: curr = curr.next
            curr.next = new_node

# --- 3. СЛОЕНЫЙ СПИСОК ---
class SkipNode:
    def __init__(self, key, passport, level):
        self.key, self.passport = key, passport
        self.forward = [None] * (level + 1)

class SkipList:
    def __init__(self, max_lvl=3):
        self.max_lvl, self.level = max_lvl, 0
        self.header = SkipNode(-1, "", max_lvl)
    def insert(self, key, passport):
        update = [None] * (self.max_lvl + 1)
        curr = self.header
        for i in range(self.level, -1, -1):
            while curr.forward[i] and curr.forward[i].key < key: curr = curr.forward[i]
            update[i] = curr
        lvl = 0
        while random.random() < 0.5 and lvl < self.max_lvl: lvl += 1
        if lvl > self.level:
            for i in range(self.level + 1, lvl + 1): update[i] = self.header
            self.level = lvl
        new_node = SkipNode(key, passport, lvl)
        for i in range(lvl + 1):
            new_node.forward[i] = update[i].forward[i]
            update[i].forward[i] = new_node

# --- ПРИЛОЖЕНИЕ ---
def main(page: ft.Page):
    page.title = "САОД Гостиница"
    page.window_width, page.window_height = 800, 650

    # Состояние и БД
    tree_root = [None]
    tree_engine = AVLTree()
    hash_engine = HashTable()
    skip_engine = SkipList()

    # Работа с БД
    conn = sqlite3.connect("hotel_data.db", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS rooms (id INTEGER PRIMARY KEY, type TEXT, equip TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS guests (passport TEXT PRIMARY KEY, fio TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS journal (room_id INTEGER, guest_pass TEXT)")
    conn.commit()

    # Загрузка данных из БД в структуры при старте
    def load_data():
        # Загрузка номеров
        cur.execute("SELECT * FROM rooms")
        for r in cur.fetchall():
            tree_root[0] = tree_engine.insert(tree_root[0], r[0], r[1], r[2])
        # Загрузка гостей
        cur.execute("SELECT * FROM guests")
        for g in cur.fetchall():
            hash_engine.insert(g[0], g[1])
        # Загрузка журнала
        cur.execute("SELECT * FROM journal")
        for j in cur.fetchall():
            skip_engine.insert(j[0], j[1])

    load_data()
    
    content_area = ft.Column(expand=True)

    # 1. ЭКРАН НОМЕРОВ
    def show_rooms(e=None):
        content_area.controls.clear()
        rid = ft.TextField(label="№ Номера", width=100)
        rtype = ft.TextField(label="Тип", width=150)
        requip = ft.TextField(label="Оборудование", expand=True)
        res_list = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=400)

        def update_ui():
            res_list.controls.clear()
            nodes = []
            tree_engine.pre_order(tree_root[0], nodes)
            for n in nodes:
                res_list.controls.append(ft.Text(f"Комната {n.key}: {n.room_type} ({n.equipment})"))
            page.update()

        def add_ev(e):
            try:
                val = int(rid.value)
                # В дерево
                tree_root[0] = tree_engine.insert(tree_root[0], val, rtype.value, requip.value)
                # В БД
                cur.execute("INSERT OR REPLACE INTO rooms VALUES (?, ?, ?)", (val, rtype.value, requip.value))
                conn.commit()
                rid.value = ""; rtype.value = ""; requip.value = ""
                update_ui()
            except: pass

        content_area.controls.extend([
            ft.Text("АВЛ-Дерево: Номера", size=18, weight="bold"),
            ft.Row([rid, rtype, requip, ft.IconButton(icon=ft.Icons.ADD, on_click=add_ev)]),
            ft.Divider(),
            res_list
        ])
        update_ui()

    # 2. ЭКРАН ПОСТОЯЛЬЦЕВ
    def show_guests(e=None):
        content_area.controls.clear()
        pass_in = ft.TextField(label="Паспорт", width=200)
        fio_in = ft.TextField(label="ФИО", expand=True)
        res_list = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=400)

        def update_ui():
            res_list.controls.clear()
            for i in range(hash_engine.size):
                curr = hash_engine.table[i]
                while curr:
                    res_list.controls.append(ft.Text(f"Ячейка[{i}] {curr.fio} (Паспорт: {curr.passport})"))
                    curr = curr.next
            page.update()

        def add_ev(e):
            if pass_in.value and fio_in.value:
                # В хеш
                hash_engine.insert(pass_in.value, fio_in.value)
                # В БД
                cur.execute("INSERT OR REPLACE INTO guests VALUES (?, ?)", (pass_in.value, fio_in.value))
                conn.commit()
                pass_in.value = ""; fio_in.value = ""
                update_ui()

        content_area.controls.extend([
            ft.Text("Хеш-таблица: Постояльцы", size=18, weight="bold"),
            ft.Row([pass_in, fio_in, ft.IconButton(icon=ft.Icons.PERSON_ADD, on_click=add_ev)]),
            ft.Divider(),
            res_list
        ])
        update_ui()

    # 3. ЭКРАН ЖУРНАЛА
    def show_journal(e=None):
        content_area.controls.clear()
        jid = ft.TextField(label="№ Номера", width=120)
        jpass = ft.TextField(label="Паспорт гостя", expand=True)
        res_list = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=400)

        def update_ui():
            res_list.controls.clear()
            curr = skip_engine.header.forward[0]
            while curr:
                res_list.controls.append(ft.Text(f"Заселение: №{curr.key} -> Паспорт {curr.passport}"))
                curr = curr.forward[0]
            page.update()

        def add_ev(e):
            try:
                r_id = int(jid.value)
                # В список
                skip_engine.insert(r_id, jpass.value)
                # В БД
                cur.execute("INSERT INTO journal VALUES (?, ?)", (r_id, jpass.value))
                conn.commit()
                jid.value = ""; jpass.value = ""
                update_ui()
            except: pass

        content_area.controls.extend([
            ft.Text("Слоеный список: Журнал", size=18, weight="bold"),
            ft.Row([jid, jpass, ft.IconButton(icon=ft.Icons.ASSIGNMENT, on_click=add_ev)]),
            ft.Divider(),
            res_list
        ])
        update_ui()

    # Сборка интерфейса
    page.add(
        ft.Row([
            ft.ElevatedButton("Номера", icon=ft.Icons.HOTEL, on_click=show_rooms),
            ft.ElevatedButton("Постояльцы", icon=ft.Icons.PEOPLE, on_click=show_guests),
            ft.ElevatedButton("Журнал", icon=ft.Icons.BOOK, on_click=show_journal),
        ], alignment=ft.MainAxisAlignment.CENTER),
        ft.Divider(),
        content_area
    )
    
    show_rooms()

ft.app(target=main)

