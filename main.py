import sqlite3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp

# =========================
# BASE DE DATOS
# =========================
def db():
    return sqlite3.connect("tienda.db")

def crear_tablas():
    conn = db()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS productos(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT,
        precio REAL,
        stock INTEGER
    )
    """)
    c.execute("""
    CREATE TABLE IF NOT EXISTS ventas(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        producto TEXT,
        cantidad INTEGER,
        total REAL,
        fecha TEXT
    )
    """)
    conn.commit()
    conn.close()

# =========================
# LÓGICA
# =========================
def agregar_producto(nombre, precio, stock):
    conn = db()
    c = conn.cursor()
    c.execute("INSERT INTO productos(nombre,precio,stock) VALUES(?,?,?)",
              (nombre, precio, stock))
    conn.commit()
    conn.close()

def obtener_productos():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM productos ORDER BY nombre")
    r = c.fetchall()
    conn.close()
    return r

def vender_producto(idp, cantidad):
    conn = db()
    c = conn.cursor()
    c.execute("SELECT nombre,precio,stock FROM productos WHERE id=?", (idp,))
    p = c.fetchone()
    if not p:
        conn.close(); return "Producto no existe"
    nombre, precio, stock = p
    if stock < cantidad:
        conn.close(); return "Stock insuficiente"
    total = precio * cantidad
    c.execute("UPDATE productos SET stock=? WHERE id=?", (stock-cantidad, idp))
    c.execute("""INSERT INTO ventas(producto,cantidad,total,fecha)
                 VALUES(?,?,?,datetime('now'))""",
              (nombre, cantidad, total))
    conn.commit(); conn.close()
    return f"Venta OK • Total ${total:.2f}"

def obtener_ventas():
    conn = db()
    c = conn.cursor()
    c.execute("SELECT * FROM ventas ORDER BY id DESC LIMIT 50")
    r = c.fetchall()
    conn.close()
    return r

# =========================
# WIDGETS CON ESTILO
# =========================
class Card(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(0.96, 0.97, 0.98, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._u, size=self._u)
    def _u(self, *a):
        self.rect.pos = self.pos
        self.rect.size = self.size

class Header(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            Color(0.12, 0.36, 0.62, 1)
            self.rect = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._u, size=self._u)
    def _u(self, *a):
        self.rect.pos = self.pos
        self.rect.size = self.size

# =========================
# INTERFAZ
# =========================
class Sistema(BoxLayout):
    def __init__(self, **kw):
        super().__init__(orientation="vertical", **kw)

        # HEADER
        h = Header(size_hint_y=None, height=dp(64), padding=dp(12))
        h.add_widget(Label(
            text="[b]TIENDA & ABARROTES[/b]",
            markup=True, color=(1,1,1,1), font_size="20sp"
        ))
        self.add_widget(h)

        # CONTENIDO
        content = BoxLayout(padding=dp(10), spacing=dp(10))
        self.add_widget(content)

        # IZQUIERDA: INVENTARIO
        left = Card(orientation="vertical", padding=dp(10), spacing=dp(8))
        content.add_widget(left)

        left.add_widget(Label(text="Inventario", bold=True, font_size="16sp"))
        self.scroll = ScrollView()
        self.lista = Label(size_hint_y=None)
        self.lista.bind(texture_size=self.lista.setter("size"))
        self.scroll.add_widget(self.lista)
        left.add_widget(self.scroll)

        # DERECHA: ACCIONES
        right = Card(orientation="vertical", padding=dp(10), spacing=dp(8))
        content.add_widget(right)

        right.add_widget(Label(text="Venta rápida", bold=True))
        self.idp = TextInput(hint_text="ID producto", multiline=False)
        self.cant = TextInput(hint_text="Cantidad", multiline=False)
        right.add_widget(self.idp)
        right.add_widget(self.cant)
        btn_v = Button(text="VENDER", background_color=(0.12,0.62,0.28,1))
        btn_v.bind(on_press=self.vender)
        right.add_widget(btn_v)

        right.add_widget(Label(text="Agregar producto", bold=True))
        self.nom = TextInput(hint_text="Nombre")
        self.pre = TextInput(hint_text="Precio")
        self.stk = TextInput(hint_text="Stock")
        right.add_widget(self.nom)
        right.add_widget(self.pre)
        right.add_widget(self.stk)
        btn_a = Button(text="AGREGAR", background_color=(0.12,0.36,0.62,1))
        btn_a.bind(on_press=self.agregar)
        right.add_widget(btn_a)

        btn_h = Button(text="HISTORIAL DE VENTAS")
        btn_h.bind(on_press=self.historial)
        right.add_widget(btn_h)

        self.msg = Label(text="")
        right.add_widget(self.msg)

        self.actualizar()

    def actualizar(self):
        txt = ""
        for p in obtener_productos():
            txt += f"ID {p[0]}  |  {p[1]}  |  ${p[2]:.2f}  |  Stock {p[3]}\n"
        self.lista.text = txt or "Sin productos"

    def vender(self, *_):
        if not self.idp.text or not self.cant.text:
            self.msg.text = "Completa ID y cantidad"; return
        self.msg.text = vender_producto(int(self.idp.text), int(self.cant.text))
        self.actualizar()

    def agregar(self, *_):
        if not self.nom.text or not self.pre.text or not self.stk.text:
            self.msg.text = "Completa todos los campos"; return
        agregar_producto(self.nom.text, float(self.pre.text), int(self.stk.text))
        self.msg.text = "Producto agregado"
        self.actualizar()

    def historial(self, *_):
        txt = "VENTAS (últimas 50)\n"
        for v in obtener_ventas():
            txt += f"{v[1]} x{v[2]} = ${v[3]:.2f} • {v[4]}\n"
        self.lista.text = txt

# =========================
# APP
# =========================
class TiendaApp(App):
    def build(self):
        crear_tablas()
        if len(obtener_productos()) == 0:
            agregar_producto("Coca Cola", 18.5, 10)
            agregar_producto("Sabritas", 20, 5)
        return Sistema()

if __name__ == "__main__":
    TiendaApp().run()
