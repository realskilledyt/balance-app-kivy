from kivy.app import App
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen, SlideTransition
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.popup import Popup
from kivy.properties import StringProperty
from kivy.clock import Clock
from kivy.metrics import dp
import json, os, datetime

from kivy.utils import platform
from kivy.core.window import Window
if platform != "android":
    Window.size = (430, 820)
    Window.minimum_width = 430
    Window.minimum_height = 820
    Window.resizable = False



# ---------- STORAGE ----------
def app_dir():
    return App.get_running_app().user_data_dir if App.get_running_app() else os.getcwd()

DATA_PATH = os.path.join(app_dir(), "user_data.json")
LAST_USER_PATH = os.path.join(app_dir(), "last_user.txt")


def load_all():
    if not os.path.exists(DATA_PATH):
        with open(DATA_PATH, "w") as f: json.dump({}, f)
    with open(DATA_PATH, "r") as f:
        try: return json.load(f)
        except: return {}


def save_all(data):
    with open(DATA_PATH, "w") as f:
        json.dump(data, f, indent=4)


# ---------- USER MODEL ----------
class UserState:
    def __init__(self, username):
        self.username = username
        self.data = load_all()

        if username not in self.data:
            self.data[username] = {"password": "059909Mno88", "balance": 0, "logs": []}
            save_all(self.data)

    @property
    def balance(self):
        return float(self.data[self.username]["balance"])

    @balance.setter
    def balance(self, val):
        self.data[self.username]["balance"] = float(val)
        save_all(self.data)

    @property
    def logs(self):
        return self.data[self.username]["logs"]

    def add_log(self, type_text, amount, is_add):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        change = f"+${amount:.2f}" if is_add else f"-${amount:.2f}"
        self.logs.append({"type": type_text or "Transaction", "date": now, "change": change})
        save_all(self.data)

    def delete_log(self, log):
        try:
            self.logs.remove(log)
            save_all(self.data)
        except:
            pass

    def check_password(self, pw):
        return self.data[self.username]["password"] == pw


# ---------- UI SCREENS ----------
class LoginScreen(Screen):
    def on_enter(self):
        def focus_field(*_):
            if "user_field" in self.ids:
                setattr(self.ids.user_field, "focus", True)
        Clock.schedule_once(focus_field, 0.2)
        Clock.schedule_once(self._try_autologin, 0.3)

    def _try_autologin(self, *_):
        if os.path.exists(LAST_USER_PATH):
            with open(LAST_USER_PATH, "r") as f:
                u = f.read().strip()
            data = load_all()
            if u in data:
                self.login(u, data[u]["password"], autologin=True)

    def do_login(self):
        u = self.ids.user_field.text.strip()
        p = self.ids.pass_field.text.strip()
        self.login(u, p)

    def login(self, u, p, autologin=False):
        data = load_all()
        if u in data and data[u]["password"] == p:
            with open(LAST_USER_PATH, "w") as f: f.write(u)
            app = App.get_running_app()
            app.user_state = UserState(u)
            app.goto_dashboard()
        else:
            if not autologin:
                self.ids.error_label.text = "Invalid username or password"


class AmountPopup(Popup):
    title_text = StringProperty("")
    mode = StringProperty("Add")

    def save_txn(self):
        app = App.get_running_app()
        type_text = self.ids.type_input.text.strip()

        try:
            amt = float(self.ids.amount_input.text.strip())
        except:
            self.ids.amount_input.text = ""
            return

        if self.mode == "Add":
            app.user_state.balance += amt
            app.user_state.add_log(type_text, amt, True)
        else:
            app.user_state.balance -= amt
            app.user_state.add_log(type_text, amt, False)

        self.dismiss()
        app.refresh_dashboard()


class FilterPopup(Popup):
    def apply(self):
        app = App.get_running_app()
        date_str = self.ids.date_input.text.strip()

        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")
        except:
            self.ids.date_input.text = ""
            return

        app.filter_date = date_str
        self.dismiss()
        app.refresh_dashboard()


class LogItem(BoxLayout):
    title = StringProperty("")
    date = StringProperty("")
    change = StringProperty("")
    raw = dict()

    def delete_me(self):
        app = App.get_running_app()
        app.user_state.delete_log(self.raw)
        app.refresh_dashboard()


class DashboardScreen(Screen):
    pass


class RootManager(ScreenManager):
    pass


KV = open("ui.kv", encoding="utf8").read()


# ---------- MAIN APP ----------
class BalanceKivyApp(App):
    user_state = None
    filter_date = None

    def build(self):
        Builder.load_string(KV)
        sm = RootManager(transition=SlideTransition())
        sm.add_widget(LoginScreen(name="login"))
        sm.add_widget(DashboardScreen(name="dash"))
        return sm

    def goto_dashboard(self):
        self.root.current = "dash"
        Clock.schedule_once(self.refresh_dashboard, 0.15)

    def sign_out(self):
        if os.path.exists(LAST_USER_PATH):
            os.remove(LAST_USER_PATH)
        self.root.current = "login"

    def open_amount_popup(self, mode):
        AmountPopup(title_text=f"{mode} Balance", mode=mode).open()

    def open_filter_popup(self):
        FilterPopup().open()

    def refresh_dashboard(self, *_):
        if not self.root or "dash" not in self.root.screen_names:
            return

        dash = self.root.get_screen("dash")

        # Wait until widgets exist
        need_ids = ("balance_lbl", "logs_grid")
        if any(i not in dash.ids for i in need_ids):
            Clock.schedule_once(self.refresh_dashboard, 0.1)
            return

        # set balance
        dash.ids.balance_lbl.text = f"${self.user_state.balance:.2f}"

        today = datetime.date.today()
        logs = []

        for log in reversed(self.user_state.logs):
            d = datetime.datetime.strptime(log["date"], "%Y-%m-%d %H:%M:%S").date()
            if self.filter_date:
                if str(d) == self.filter_date:
                    logs.append(log)
            else:
                if (today - d).days <= 30:
                    logs.append(log)

        grid = dash.ids.logs_grid
        grid.clear_widgets()

        grouped = {}
        for log in logs:
            d = datetime.datetime.strptime(log["date"], "%Y-%m-%d %H:%M:%S").date()
            delta = (today - d).days
            if delta == 0: key = "Today"
            elif delta == 1: key = "Yesterday"
            else: key = d.strftime("%d/%m/%Y")
            grouped.setdefault(key, []).append(log)

        from kivy.uix.label import Label

        for day, items in grouped.items():
            grid.add_widget(Label(
                text=day,
                size_hint_y=None,
                height=dp(28),
                color=(0.7,0.7,0.7,1),
                halign="left",
                valign="middle",
                text_size=(1000, dp(28))
            ))
            for log in items:
                li = LogItem(title=log["type"], date=log["date"], change=log["change"])
                li.raw = log
                grid.add_widget(li)


if __name__ == "__main__":
    BalanceKivyApp().run()
