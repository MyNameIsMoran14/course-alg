import flet as ft
import sqlite3
import random
import re
from datetime import datetime

# --- АЛГОРИТМ БОУЕРА-МУРА ---
def boyer_moore_search(text, pattern):
    if not text or not pattern: return False
    n, m = len(text), len(pattern)
    if m == 0: return False
    char_table = {pattern[i]: max(1, m - i - 1) for i in range(m - 1)}
    skip = 0
    while n - skip >= m:
        if text[skip:skip + m] == pattern: return True
        if skip + m < n: skip += char_table.get(text[skip + m], m)
        else: break
    return False

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
        elif key > root.key: root.right = self.insert(root.right, key, r_type, equip)
        else: # Если ключ совпадает, обновляем данные (для удаления оборудования)
            root.room_type = r_type
            root.equipment = equip
            return root
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
    def __init__(self, passport, fio, checkout_date="Проживает"):
        self.passport, self.fio = passport, fio
        self.checkout_date = checkout_date
        self.next = None

class HashTable:
    def __init__(self, size=10):
        self.size, self.table = size, [None] * size
    def _hash(self, key): return sum(ord(c) for c in str(key)) % self.size
    def insert(self, passport, fio, date="Проживает"):
        idx = self._hash(passport)
        if not self.table[idx]: self.table[idx] = HashNode(passport, fio, date)
        else:
            curr = self.table[idx]
            while curr:
                if curr.passport == passport:
                    curr.checkout_date = date
                    curr.fio = fio
                    return
                if not curr.next: break
                curr = curr.next
            curr.next = HashNode(passport, fio, date)

# --- 3. СЛОЕНЫЙ СПИСОК ---
class SkipNode:
    def __init__(self, key, passport, level):
        self.key, self.passport = str(key), passport
        self.forward = [None] * (level + 1)

class SkipList:
    def __init__(self, max_lvl=3):
        self.max_lvl, self.level = max_lvl, 0
        self.header = SkipNode("-1", "", max_lvl)
    def insert(self, key, passport):
        key = str(key)
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
    page.window.width, page.window_height = 900, 800

    tree_root = [None]
    tree_engine = AVLTree()
    hash_engine = HashTable()
    skip_engine = SkipList()

    conn = sqlite3.connect("hotel_data.db", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS rooms (id TEXT PRIMARY KEY, type TEXT, equip TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS guests (passport TEXT PRIMARY KEY, fio TEXT, checkout_date TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS journal (room_id TEXT, guest_pass TEXT)")
    conn.commit()

    def reload_all_data():
        tree_root[0] = None
        hash_engine.table = [None] * 10
        skip_engine.header = SkipNode("-1", "", 3)
        skip_engine.level = 0
        cur.execute("SELECT * FROM rooms")
        for r in cur.fetchall(): tree_root[0] = tree_engine.insert(tree_root[0], r[0], r[1], r[2])
        cur.execute("SELECT * FROM guests")
        for g in cur.fetchall(): hash_engine.insert(g[0], g[1], g[2])
        cur.execute("SELECT * FROM journal")
        for j in cur.fetchall(): skip_engine.insert(j[0], j[1])

    reload_all_data()
    content_area = ft.Column(expand=True)

    def show_rooms(e=None):
        content_area.controls.clear()
        rid = ft.TextField(label="№ (Напр: 101)", width=120)
        rtype = ft.TextField(label="Тип", width=150)
        requip = ft.TextField(label="Оборудование", expand=True)
        search_f = ft.TextField(label="Поиск по оборуд.", width=250)
        res_list = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=400)

        def update_ui(filter_str=""):
            res_list.controls.clear()
            nodes = []
            tree_engine.pre_order(tree_root[0], nodes)
            for n in nodes:
                if not filter_str or boyer_moore_search(n.equipment.lower(), filter_str.lower()):
                    res_list.controls.append(
                        ft.Row([
                            ft.Text(f"Номер {n.key}: {n.room_type} [{n.equipment}]", expand=True),
                            ft.IconButton(ft.Icons.DELETE_SWEEP, tooltip="Удалить оборудование", 
                                          on_click=lambda _, r=n.key, t=n.room_type: clear_equip(r, t))
                        ])
                    )
            page.update()

        def add_ev(e):
            if not rid.value: return
            tree_root[0] = tree_engine.insert(tree_root[0], rid.value, rtype.value, requip.value)
            cur.execute("INSERT OR REPLACE INTO rooms VALUES (?, ?, ?)", (rid.value, rtype.value, requip.value))
            conn.commit(); update_ui()

        def clear_equip(r_id, r_type):
            tree_root[0] = tree_engine.insert(tree_root[0], r_id, r_type, "") # Стираем в дереве
            cur.execute("UPDATE rooms SET equip = '' WHERE id = ?", (r_id,)) # Стираем в БД
            conn.commit(); update_ui()

        content_area.controls.extend([
            ft.Row([rid, rtype, requip, ft.IconButton(ft.Icons.ADD, on_click=add_ev)]),
            ft.Row([search_f, ft.FilledButton("Поиск", on_click=lambda _: update_ui(search_f.value))]),
            ft.Divider(), res_list
        ])
        update_ui()

    def show_guests(e=None):
        content_area.controls.clear()
        search_g = ft.TextField(label="Поиск по ФИО или паспорту (БМ)", width=400) # Поле поиска
        res_list = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=500)

        def update_ui(filter_str=""):
            res_list.controls.clear()
            for i in range(hash_engine.size):
                curr = hash_engine.table[i]
                while curr:
                    # Проверяем, подходит ли гость под фильтр (по ФИО или паспорту)
                    match_fio = not filter_str or boyer_moore_search(curr.fio.lower(), filter_str.lower())
                    match_pass = not filter_str or boyer_moore_search(curr.passport.lower(), filter_str.lower())
                    
                    if match_fio or match_pass:
                        color = "green" if curr.checkout_date == "Проживает" else "grey"
                        res_list.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.PERSON, color=color), 
                                    ft.Text(f"{curr.fio} ({curr.passport})", expand=True), 
                                    ft.Text(curr.checkout_date, italic=True, color=color)
                                ]), 
                                padding=5, 
                                border=ft.border.all(1, "black12"), 
                                border_radius=10
                            )
                        )
                    curr = curr.next
            page.update()

        # Добавляем кнопку и поле поиска на экран
        content_area.controls.extend([
            ft.Row([
                search_g, 
                ft.FilledButton("Найти", on_click=lambda _: update_ui(search_g.value))
            ]),
            ft.Divider(),
            res_list
        ])
        update_ui()

    def show_journal(e=None):
        content_area.controls.clear()
        jid, jpass, jfio = ft.TextField(label="№ Номера", width=120), ft.TextField(label="Паспорт", width=180), ft.TextField(label="ФИО", expand=True)
        res_list = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=400)

        def update_ui():
            res_list.controls.clear()
            curr = skip_engine.header.forward[0]
            while curr:
                rk, ps = curr.key, curr.passport
                res_list.controls.append(ft.Row([ft.Text(f"Номер {rk} — Паспорт {ps}", expand=True), ft.FilledButton("Выселить", bgcolor="red", on_click=lambda _, r=rk, p=ps: checkout_ev(r, p))]))
                curr = curr.forward[0]
            page.update()

        def add_ev(e):
            if not jid.value or not jpass.value: return
            skip_engine.insert(jid.value, jpass.value)
            cur.execute("INSERT INTO journal VALUES (?, ?)", (jid.value, jpass.value))
            cur.execute("INSERT OR REPLACE INTO guests VALUES (?, ?, ?)", (jpass.value, jfio.value or "Гость", "Проживает"))
            conn.commit(); reload_all_data(); update_ui()

        def checkout_ev(room_id, passport):
            now = datetime.now().strftime("%d.%m %H:%M")
            # ФИКС: Удаляем конкретную запись по номеру И паспорту
            cur.execute("DELETE FROM journal WHERE room_id = ? AND guest_pass = ?", (room_id, passport))
            cur.execute("UPDATE guests SET checkout_date = ? WHERE passport = ?", (now, passport))
            conn.commit(); reload_all_data(); update_ui()

        content_area.controls.extend([ft.Row([jid, jpass, jfio, ft.IconButton(ft.Icons.ADD_BUSINESS, on_click=add_ev)]), ft.Divider(), res_list])
        update_ui()

    page.add(ft.Row([ft.FilledButton("Номера", icon=ft.Icons.HOTEL, on_click=show_rooms), ft.FilledButton("Журнал", icon=ft.Icons.BOOK, on_click=show_journal), ft.FilledButton("Реестр", icon=ft.Icons.PEOPLE, on_click=show_guests)], alignment="center"), ft.Divider(), content_area)
    show_rooms()

ft.run(main)

# нужно при удалении обордования удаять строку вообще из бд