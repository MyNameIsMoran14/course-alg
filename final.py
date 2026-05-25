import flet as ft
import sqlite3
import random
import re
from datetime import datetime

# АЛГОРИТМ БОУЕРА-МУРА
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

# АВЛ-ДЕРЕВО
class AVLNode:
    def __init__(self, key, r_type, seats, rooms, toilet, equipment):
        self.key, self.room_type = key, r_type
        self.seats, self.rooms, self.has_toilet = seats, rooms, toilet
        self.equipment = equipment
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
    
    def insert(self, root, key, r_type, seats, rooms, toilet, equip):
        if not root: return AVLNode(key, r_type, seats, rooms, toilet, equip)
        if key < root.key: root.left = self.insert(root.left, key, r_type, seats, rooms, toilet, equip)
        elif key > root.key: root.right = self.insert(root.right, key, r_type, seats, rooms, toilet, equip)
        else:
            root.room_type, root.seats, root.rooms, root.has_toilet, root.equipment = r_type, seats, rooms, toilet, equip
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

    def search(self, root, key):
        if not root or root.key == key: return root
        if key < root.key: return self.search(root.left, key)
        return self.search(root.right, key)

# ХЕШ-ТАБЛИЦА 
class HashNode:
    def __init__(self, passport, fio, birth, address, goal, checkout_date="Проживает"):
        self.passport, self.fio = passport, fio
        self.birth, self.address, self.goal = birth, address, goal
        self.checkout_date = checkout_date
        self.next = None

class HashTable:
    def __init__(self, size=10):
        self.size, self.table = size, [None] * size
    def _hash(self, key):
        idx = sum(ord(c) for c in str(key)) % self.size
        print(f"DEBUG: Ключ {key} получил индекс {idx}")
        return sum(ord(c) for c in str(key)) % self.size
    
    def insert(self, passport, fio, birth, address, goal, date="Проживает"):
        idx = self._hash(passport)
        if not self.table[idx]: self.table[idx] = HashNode(passport, fio, birth, address, goal, date)
        else:
            curr = self.table[idx]
            while curr:
                if curr.passport == passport:
                    curr.fio, curr.birth, curr.address, curr.goal, curr.checkout_date = fio, birth, address, goal, date
                    return
                if not curr.next: break
                curr = curr.next
            curr.next = HashNode(passport, fio, birth, address, goal, date)

    def search(self, passport):
        idx = self._hash(passport)
        curr = self.table[idx]
        while curr:
            if curr.passport == passport: return curr
            curr = curr.next
        return None

# СЛОЕНЫЙ СПИСОК
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

# ыыыы flet делает вылет-вылет
def main(page: ft.Page):
    page.title = "САОД Алгоритмы и структуры данных: Гостиница"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.window_width, page.window_height = 1000, 800

    tree_root = [None]
    tree_engine = AVLTree()
    hash_engine = HashTable()
    skip_engine = SkipList()

    conn = sqlite3.connect("hotel_data.db", check_same_thread=False)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS rooms (id TEXT PRIMARY KEY, type TEXT, seats INT, rooms_cnt INT, toilet INT, equip TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS guests (passport TEXT PRIMARY KEY, fio TEXT, birth INT, address TEXT, goal TEXT, checkout_date TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS journal (room_id TEXT, guest_pass TEXT)")
    conn.commit()

    def reload_all_data():
        tree_root[0] = None
        hash_engine.table = [None] * 10
        skip_engine.header = SkipNode("-1", "", 3)
        skip_engine.level = 0
        cur.execute("SELECT * FROM rooms")
        for r in cur.fetchall(): tree_root[0] = tree_engine.insert(tree_root[0], r[0], r[1], r[2], r[3], r[4], r[5])
        cur.execute("SELECT * FROM guests")
        for g in cur.fetchall(): hash_engine.insert(g[0], g[1], g[2], g[3], g[4], g[5])
        cur.execute("SELECT * FROM journal")
        for j in cur.fetchall(): skip_engine.insert(j[0], j[1])

    reload_all_data()
    content_area = ft.Column(expand=True)

    def toggle_theme(e):
        page.theme_mode = ft.ThemeMode.DARK if page.theme_mode == ft.ThemeMode.LIGHT else ft.ThemeMode.LIGHT
        e.control.icon = ft.Icons.LIGHT_MODE if page.theme_mode == ft.ThemeMode.DARK else ft.Icons.DARK_MODE
        page.update()

    # Поиск жильцов комнаты 
    def get_room_guests(room_id):
        guests_info = []
        curr = skip_engine.header.forward[0]
        while curr:
            if curr.key == room_id:
                g_node = hash_engine.search(curr.passport)
                if g_node and g_node.checkout_date == "Проживает":
                    guests_info.append(f"{g_node.fio} ({g_node.passport})")
            curr = curr.forward[0]
        return ", ".join(guests_info) if guests_info else "Свободен"

    # Поиск комнаты, в которой сейчас живет гость
    def get_guest_room(passport):
        curr = skip_engine.header.forward[0]
        while curr:
            if curr.passport == passport:
                return f"Комната {curr.key}"
            curr = curr.forward[0]
        return "Не заселен"

    def show_rooms(e=None):
        content_area.controls.clear()
        rid = ft.TextField(label="№ (Л/П/О/М + 3 цифры)", width=140) #люкс/полу-люкс/одноместный/многоместный
        rtype = ft.TextField(label="Тип номера", width=100)
        rseats = ft.TextField(label="Мест", width=70)
        rcnt = ft.TextField(label="Комнат", width=70)
        rtoilet = ft.Checkbox(label="Санузел")
        requip = ft.TextField(label="Оборудование", expand=True)
        search_f = ft.TextField(label="Поиск по оборуд. (БМ) или точный №", width=300)
        res_list = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=400)

        def update_ui(filter_str=""):
            res_list.controls.clear()
            if filter_str and re.match(r"^[ЛПОМ]\d{3}$", filter_str.upper()):
                node = tree_engine.search(tree_root[0], filter_str.upper())
                if node:
                    live_guests = get_room_guests(node.key)
                    res_list.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"ГОСТИНЫЧНЫЙ НОМЕР {node.key}", weight="bold", size=16),
                                ft.Text(f"Тип: {node.room_type} | Комнат: {node.rooms} | Мест всего: {node.seats} | Санузел: {'Есть' if node.has_toilet else 'Нет'}"),
                                ft.Text(f"Оборудование: {node.equipment}", italic=True),
                                ft.Text(f"Текущие постояльцы: {live_guests}", color="blue", weight="bold")
                            ]), padding=10, border=ft.border.all(1, "blue"), border_radius=10
                        )
                    )
                else:
                    res_list.controls.append(ft.Text("Номер не найден!", color="red"))
                page.update(); return

            # поиск по оборудованию через БМ
            nodes = []
            tree_engine.pre_order(tree_root[0], nodes)
            for n in nodes:
                if not filter_str or boyer_moore_search(n.equipment.lower(), filter_str.lower()):
                    live_guests = get_room_guests(n.key)
                    res_list.controls.append(
                        ft.Row([
                            ft.Text(f"[{n.key}] Мест: {n.seats} | С/У: {'Да' if n.has_toilet else 'Нет'} | Оборуд: {n.equipment}\nПостояльцы: {live_guests}", expand=True),
                            ft.IconButton(ft.Icons.DELETE, tooltip="Удалить номер полностью", on_click=lambda _, r=n.key: delete_room_full(r))
                        ])
                    )
            page.update()

        def add_ev(e):
            if not re.match(r"^[ЛПОМ]\d{3}$", rid.value.upper()):
                page.snack_bar = ft.SnackBar(ft.Text("Формат номера: Буква(Л,П,О,М) и 3 цифры!")); page.snack_bar.open = True
                page.update(); return
            try:
                tree_root[0] = tree_engine.insert(tree_root[0], rid.value.upper(), rtype.value, int(rseats.value or 1), int(rcnt.value or 1), int(rtoilet.value), requip.value)
                cur.execute("INSERT OR REPLACE INTO rooms VALUES (?, ?, ?, ?, ?, ?)", (rid.value.upper(), rtype.value, int(rseats.value or 1), int(rcnt.value or 1), int(rtoilet.value), requip.value))
                conn.commit(); update_ui()
            except ValueError:
                page.snack_bar = ft.SnackBar(ft.Text("Ошибка в числовых полях!")); page.snack_bar.open = True; page.update()

        def delete_room_full(r_id):
            cur.execute("DELETE FROM rooms WHERE id = ?", (r_id,))
            conn.commit(); reload_all_data(); update_ui()

        def clear_all_rooms(e):
            cur.execute("DELETE FROM rooms"); conn.commit(); reload_all_data(); update_ui()

        content_area.controls.extend([
            ft.Row([rid, rtype, rseats, rcnt, rtoilet, requip, ft.IconButton(ft.Icons.ADD, on_click=add_ev)]),
            ft.Row([search_f, ft.FilledButton("Поиск", on_click=lambda _: update_ui(search_f.value)), ft.OutlinedButton("Очистить базу комнат", on_click=clear_all_rooms, icon=ft.Icons.DELETE_FOREVER)]),
            ft.Divider(), res_list
        ])
        update_ui()

    def show_guests(e=None):
        content_area.controls.clear()
        search_g = ft.TextField(label="Поиск по ФИО или точному паспорту (БМ)", width=400)
        res_list = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=500)

        def update_ui(filter_str=""):
            res_list.controls.clear()
            
            # поиск по первичному ключу 
            if filter_str and re.match(r"^\d{4}-\d{6}$", filter_str):
                g_node = hash_engine.search(filter_str)
                if g_node:
                    current_status = get_guest_room(g_node.passport) if g_node.checkout_date == "Проживает" else f"Выселен ({g_node.checkout_date})"
                    res_list.controls.append(
                        ft.Container(
                            content=ft.Column([
                                ft.Text(f"ПОСТОЯЛЕЦ: {g_node.fio}", weight="bold", size=16),
                                ft.Text(f"Паспорт: {g_node.passport} | Год рождения: {g_node.birth} г."),
                                ft.Text(f"Адрес: {g_node.address} | Цель визита: {g_node.goal}"),
                                ft.Text(f"Статус размещения: {current_status}", color="green" if g_node.checkout_date == "Проживает" else "grey", weight="bold")
                            ]), padding=10, border=ft.border.all(1, "green"), border_radius=10
                        )
                    )
                else:
                    res_list.controls.append(ft.Text("Постоялец с таким паспортом не найден.", color="red"))
                page.update(); return

            # ыыыы щбщий список + поиск по ФИО через БМ
            for i in range(hash_engine.size):
                curr = hash_engine.table[i]
                while curr:
                    if not filter_str or boyer_moore_search(curr.fio.lower(), filter_str.lower()):
                        color = "green" if curr.checkout_date == "Проживает" else "grey"
                        room_where = get_guest_room(curr.passport) if curr.checkout_date == "Проживает" else f"Выехал ({curr.checkout_date})"
                        res_list.controls.append(
                            ft.Container(
                                content=ft.Row([
                                    ft.Icon(ft.Icons.PERSON, color=color), 
                                    ft.Text(f"{curr.fio} ({curr.passport}) | {curr.birth}г.\nСтатус: {room_where}", expand=True), 
                                    ft.IconButton(ft.Icons.DELETE, tooltip="Удалить анкету", on_click=lambda _, p=curr.passport: delete_guest_card(p))
                                ]), padding=5, border=ft.border.all(1, "black12"), border_radius=10
                            )
                        )
                    curr = curr.next
            page.update()

        def delete_guest_card(passport):
            cur.execute("DELETE FROM guests WHERE passport = ?", (passport,))
            cur.execute("DELETE FROM journal WHERE guest_pass = ?", (passport,))
            conn.commit(); reload_all_data(); update_ui()

        def clear_all_guests(e):
            cur.execute("DELETE FROM guests"); cur.execute("DELETE FROM journal"); conn.commit(); reload_all_data(); update_ui()

        content_area.controls.extend([
            ft.Row([search_g, ft.FilledButton("Найти", on_click=lambda _: update_ui(search_g.value)), ft.OutlinedButton("Очистить реестр", on_click=clear_all_guests, icon=ft.Icons.DELETE_FOREVER)]),
            ft.Divider(), res_list
        ])
        update_ui()

    def show_journal(e=None):
        content_area.controls.clear()
        jid = ft.TextField(label="№ Номера", width=110)
        jpass = ft.TextField(label="Паспорт (1234-123456)", width=180)
        jfio = ft.TextField(label="ФИО постояльца", width=150)
        jbirth = ft.TextField(label="Год рождения", width=100)
        jaddr = ft.TextField(label="Адрес", width=150)
        jgoal = ft.TextField(label="Цель прибытия", expand=True)
        res_list = ft.Column(scroll=ft.ScrollMode.ALWAYS, height=350)

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
            target_room = jid.value.upper()
            
            if not re.match(r"^\d{4}-\d{6}$", jpass.value):
                page.snack_bar = ft.SnackBar(ft.Text("Неверный формат паспорта! (Надо: 1234-123456)")); page.snack_bar.open = True; page.update(); return

            #САМАЯ НУЖНАЯ ПРОВЕРКА НА МЕСТА В МОЕЙ ЖИЗНИ (места в номере)
            room_node = tree_engine.search(tree_root[0], target_room)
            if not room_node:
                page.snack_bar = ft.SnackBar(ft.Text("Этого номера вообще нет в базе комнат!")); page.snack_bar.open = True; page.update(); return
            
            # Считаем сколько людей сейчас реально живут в этой комнате
            current_occupied = 0
            check_curr = skip_engine.header.forward[0]
            while check_curr:
                if check_curr.key == target_room:
                    g_node = hash_engine.search(check_curr.passport)
                    if g_node and g_node.checkout_date == "Проживает":
                        current_occupied += 1
                check_curr = check_curr.forward[0]

            if current_occupied >= room_node.seats:
                page.snack_bar = ft.SnackBar(ft.Text(f"Заселение отклонено! В номере {target_room} мест всего: {room_node.seats}, и они все заняты!")); page.snack_bar.open = True; page.update(); return
            
            skip_engine.insert(target_room, jpass.value)
            cur.execute("INSERT INTO journal VALUES (?, ?)", (target_room, jpass.value))
            cur.execute("INSERT OR REPLACE INTO guests VALUES (?, ?, ?, ?, ?, ?)", 
                        (jpass.value, jfio.value or "Гость", int(jbirth.value or 2000), jaddr.value, jgoal.value, "Проживает"))
            conn.commit(); reload_all_data(); update_ui()

        def checkout_ev(room_id, passport):
            now = datetime.now().strftime("%d.%m %H:%M")
            cur.execute("DELETE FROM journal WHERE room_id = ? AND guest_pass = ?", (room_id, passport))
            cur.execute("UPDATE guests SET checkout_date = ? WHERE passport = ?", (now, passport))
            conn.commit(); reload_all_data(); update_ui()

        content_area.controls.extend([
            ft.Row([jid, jpass, jfio]),
            ft.Row([jbirth, jaddr, jgoal, ft.IconButton(ft.Icons.ADD_BUSINESS, on_click=add_ev)]), 
            ft.Divider(), res_list
        ])
        update_ui()

    theme_btn = ft.IconButton(ft.Icons.DARK_MODE, on_click=toggle_theme)
    page.add(
        ft.Row([
            ft.Row([
                ft.FilledButton("Номера", icon=ft.Icons.HOTEL, on_click=show_rooms),
                ft.FilledButton("Журнал", icon=ft.Icons.BOOK, on_click=show_journal),
                ft.FilledButton("Реестр", icon=ft.Icons.PEOPLE, on_click=show_guests),
            ], expand=True, alignment="center"),
            theme_btn
        ]),
        ft.Divider(), content_area
    )
    show_rooms()

ft.run(main)