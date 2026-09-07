"""
RANSOM - Kivy Android App
เกม jumpscare + minigame สไตล์ Roblox Doors
"""

import random
from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.graphics import (
    Color, Rectangle, Ellipse, Line, RoundedRectangle
)

# --------- ตรวจว่ารันบน Android จริงหรือเปล่า ---------
try:
    from android.permissions import request_permissions, Permission
    from jnius import autoclass
    IS_ANDROID = True
except ImportError:
    IS_ANDROID = False

# --------- ค่าคงที่ ---------
GOLD_NEEDED       = 500    # ทองที่ต้องเก็บ
COUNTDOWN_SEC     = 75     # เวลานับถอยหลัง (วินาที)
MAX_COINS         = 6      # เหรียญสูงสุดบนหน้าจอพร้อมกัน
COIN_SPAWN_RATE   = 0.55   # วินาที/เหรียญใหม่
GOLD_PER_COIN     = 25     # ทองต่อการแตะ 1 เหรียญ
COIN_R            = 38     # รัศมีเหรียญ (px)
FLASH_DUR         = 0.10   # วินาทีต่อการกระพริบ
FLASH_TIMES       = 7      # ครั้งที่กระพริบ
JUMPSCARE_HOLD    = 1.8    # วินาทีค้างหน้า jumpscare

# --------- สี ---------
CLR_BG_DARK   = (0.04, 0.02, 0.00, 1)
CLR_RED       = (0.72, 0.00, 0.00, 1)
CLR_CARD_BG   = (0.06, 0.04, 0.04, 1)
CLR_GOLD      = (1.00, 0.82, 0.00, 1)
CLR_GOLD_DARK = (0.75, 0.55, 0.00, 1)
CLR_WHITE     = (1.00, 1.00, 1.00, 1)
CLR_WARN_RED  = (1.00, 0.25, 0.25, 1)
CLR_WIN_BG    = (0.00, 0.20, 0.04, 1)
CLR_LOSE_BG   = (0.18, 0.00, 0.00, 1)

# --------- สถานะ ---------
STATE_FLASH      = "flash"
STATE_JUMPSCARE  = "jumpscare"
STATE_MINIGAME   = "minigame"
STATE_WIN        = "win"
STATE_LOSE       = "lose"


# ============================================================
#  Helper: วาดพื้นหลังสีทึบให้ canvas.before
# ============================================================
def fill_bg(widget, color):
    widget.canvas.before.clear()
    with widget.canvas.before:
        Color(*color)
        Rectangle(pos=(0, 0), size=Window.size)


# ============================================================
#  หน้าจอหลัก (root widget)
# ============================================================
class RansomRoot(FloatLayout):
    pass


# ============================================================
#  แอปหลัก
# ============================================================
class RansomApp(App):

    def build(self):
        Window.fullscreen = "auto"

        # ตัวแปรสถานะ
        self.state        = STATE_FLASH
        self.flash_count  = 0
        self.flash_on     = True
        self.gold         = 0
        self.time_left    = float(COUNTDOWN_SEC)
        self.coins        = []      # รายการ dict {x, y, uid}

        # บล็อก back-button บน Android
        Window.bind(on_keyboard=self._handle_keyboard)

        # ตั้งค่า Android (lock-screen flags ฯลฯ)
        if IS_ANDROID:
            self._setup_android()

        self.root_layout = RansomRoot()
        self._start_flash()
        return self.root_layout

    # -------- บล็อก back / home --------
    def _handle_keyboard(self, window, key, *args):
        """บล็อก back button ระหว่างเกม"""
        BACK = 27
        ESC  = 27
        if key in (BACK, ESC) and self.state == STATE_MINIGAME:
            return True   # กัน event ไม่ให้ออกแอป
        return False

    # -------- ตั้งค่า Android flags --------
    def _setup_android(self):
        try:
            # ขอ permissions
            request_permissions([
                Permission.SET_WALLPAPER,
                Permission.RECEIVE_BOOT_COMPLETED,
            ])

            # แสดงเหนือ lock screen + เปิดหน้าจอ
            PythonActivity = autoclass("org.kivy.android.PythonActivity")
            act = PythonActivity.mActivity
            WM_LP = autoclass("android.view.WindowManager$LayoutParams")
            win = act.getWindow()
            win.addFlags(WM_LP.FLAG_SHOW_WHEN_LOCKED)
            win.addFlags(WM_LP.FLAG_DISMISS_KEYGUARD)
            win.addFlags(WM_LP.FLAG_KEEP_SCREEN_ON)
            win.addFlags(WM_LP.FLAG_TURN_SCREEN_ON)
        except Exception as e:
            print(f"[Android setup error] {e}")

    # ============================================================
    #  PHASE 1 — FLASH
    # ============================================================
    def _start_flash(self):
        self.state       = STATE_FLASH
        self.flash_count = 0
        self.flash_on    = True
        Clock.schedule_interval(self._tick_flash, FLASH_DUR)

    def _tick_flash(self, dt):
        color = CLR_WHITE if self.flash_on else (0, 0, 0, 1)
        fill_bg(self.root_layout, color)

        self.flash_on    = not self.flash_on
        self.flash_count += 1

        if self.flash_count >= FLASH_TIMES * 2:
            Clock.unschedule(self._tick_flash)
            self._show_jumpscare()

    # ============================================================
    #  PHASE 2 — JUMPSCARE
    # ============================================================
    def _show_jumpscare(self):
        self.state = STATE_JUMPSCARE
        root = self.root_layout
        root.clear_widgets()
        fill_bg(root, CLR_RED)

        w, h = Window.size

        # --- กรอบการ์ดกลาง ---
        card = Widget()
        card_x = w * 0.05
        card_y = h * 0.28
        card_w = w * 0.90
        card_h = h * 0.40
        with card.canvas:
            Color(*CLR_CARD_BG)
            RoundedRectangle(pos=(card_x, card_y), size=(card_w, card_h), radius=[16])
            Color(*CLR_WHITE)
            Line(rounded_rectangle=(card_x, card_y, card_w, card_h, 16), width=2.5)
        root.add_widget(card)

        # --- ไอคอน "X" สไตล์ skull placeholder (วงกลมดำ) ---
        skull = Widget()
        sk_r = min(w, h) * 0.12
        sk_x = w / 2 - sk_r
        sk_y = h * 0.62
        with skull.canvas:
            Color(0.1, 0.1, 0.1, 1)
            Ellipse(pos=(sk_x, sk_y), size=(sk_r * 2, sk_r * 2))
            Color(*CLR_WHITE)
            Line(circle=(w / 2, sk_y + sk_r, sk_r * 0.85), width=3)
            # ตา
            Color(1, 0, 0, 1)
            ee = sk_r * 0.22
            Ellipse(pos=(w/2 - sk_r*0.38 - ee/2, sk_y + sk_r*0.85 - ee/2),
                    size=(ee, ee))
            Ellipse(pos=(w/2 + sk_r*0.38 - ee/2, sk_y + sk_r*0.85 - ee/2),
                    size=(ee, ee))
        root.add_widget(skull)

        # --- ชื่อ RANSOM ---
        root.add_widget(Label(
            text="RANSOM",
            font_size="56sp", bold=True, color=CLR_WHITE,
            pos_hint={"center_x": 0.5, "center_y": 0.56},
            size_hint=(1, None), height=70,
        ))

        # --- ข้อความเตือน ---
        lbl = Label(
            text=(
                "YOUR ITEMS HAVE BEEN ENCRYPTED\n\n"
                "IF YOU DO NOT PAY THIS RANSOM\n"
                "BEFORE THE TIMER ENDS,\n"
                "YOUR ITEMS WILL BE\n"
                "[color=ff4444]UNRECOVERABLE BY ANY MEANS[/color]"
            ),
            markup=True,
            font_size="18sp", bold=True,
            color=CLR_WHITE, halign="center",
            pos_hint={"center_x": 0.5, "center_y": 0.40},
            size_hint=(0.88, None), height=180,
        )
        lbl.bind(size=lbl.setter("text_size"))
        root.add_widget(lbl)

        # รอแล้วเข้า minigame
        Clock.schedule_once(lambda dt: self._start_minigame(), JUMPSCARE_HOLD)

    # ============================================================
    #  PHASE 3 — MINIGAME
    # ============================================================
    def _start_minigame(self):
        self.state     = STATE_MINIGAME
        self.gold      = 0
        self.time_left = float(COUNTDOWN_SEC)
        self.coins     = []

        root = self.root_layout
        root.clear_widgets()
        fill_bg(root, CLR_BG_DARK)

        w, h = Window.size

        # --- Header bar ---
        header = Widget()
        hbar_h = h * 0.09
        with header.canvas:
            Color(0.55, 0, 0, 1)
            Rectangle(pos=(0, h - hbar_h), size=(w, hbar_h))
            Color(1, 0.3, 0.3, 0.4)
            Line(points=[0, h - hbar_h, w, h - hbar_h], width=2)
        root.add_widget(header)

        root.add_widget(Label(
            text="RANSOM",
            font_size="32sp", bold=True, color=(1, 0.9, 0.9, 1),
            pos_hint={"center_x": 0.5, "top": 1.0},
            size_hint=(1, None), height=hbar_h,
        ))

        # --- Gold counter ---
        self.lbl_gold = Label(
            text=f"[color=ffcc00]⬡[/color] {self.gold} / {GOLD_NEEDED}",
            markup=True,
            font_size="22sp", bold=True, color=CLR_GOLD,
            pos_hint={"x": 0.02, "top": 0.91},
            size_hint=(0.55, 0.08), halign="left",
        )
        self.lbl_gold.bind(size=self.lbl_gold.setter("text_size"))
        root.add_widget(self.lbl_gold)

        # --- Timer ---
        self.lbl_timer = Label(
            text=f"TIME  {int(self.time_left)}",
            font_size="22sp", bold=True, color=CLR_WARN_RED,
            pos_hint={"right": 0.98, "top": 0.91},
            size_hint=(0.40, 0.08), halign="right",
        )
        self.lbl_timer.bind(size=self.lbl_timer.setter("text_size"))
        root.add_widget(self.lbl_timer)

        # --- คำอธิบาย ---
        root.add_widget(Label(
            text="แตะเหรียญทองเพื่อเก็บ!",
            font_size="17sp", color=(0.7, 0.7, 0.7, 1),
            pos_hint={"center_x": 0.5, "top": 0.83},
            size_hint=(1, 0.06),
        ))

        # --- Layer วาดเหรียญ ---
        self.coin_layer = Widget()
        self.coin_layer.bind(on_touch_down=self._on_coin_touch)
        root.add_widget(self.coin_layer)

        # เริ่ม timers
        Clock.schedule_interval(self._tick_timer, 1.0)
        Clock.schedule_interval(self._spawn_coin, COIN_SPAWN_RATE)

    # -------- เหรียญ --------
    def _spawn_coin(self, dt):
        if self.state != STATE_MINIGAME:
            return
        if len(self.coins) >= MAX_COINS:
            return

        w, h = Window.size
        margin  = COIN_R + 24
        min_y   = int(h * 0.10) + margin
        max_y   = int(h * 0.80) - margin

        coin = {
            "x":   random.randint(margin, w - margin),
            "y":   random.randint(min_y, max_y),
            "uid": random.randint(0, 999999),
        }
        self.coins.append(coin)
        self._redraw_coins()

    def _redraw_coins(self):
        self.coin_layer.canvas.clear()
        with self.coin_layer.canvas:
            for c in self.coins:
                cx, cy = c["x"], c["y"]
                # เงา
                Color(0, 0, 0, 0.35)
                Ellipse(pos=(cx - COIN_R + 4, cy - COIN_R - 4),
                        size=(COIN_R * 2, COIN_R * 2))
                # ตัวเหรียญสีทอง
                Color(*CLR_GOLD)
                Ellipse(pos=(cx - COIN_R, cy - COIN_R),
                        size=(COIN_R * 2, COIN_R * 2))
                # ไฮไลท์
                Color(1, 1, 0.7, 0.55)
                Ellipse(pos=(cx - COIN_R*0.5, cy + COIN_R*0.05),
                        size=(COIN_R * 0.8, COIN_R * 0.55))
                # ขอบ
                Color(*CLR_GOLD_DARK)
                Line(circle=(cx, cy, COIN_R), width=2.5)
                # ตัวอักษร $
                Color(0.6, 0.4, 0, 1)
                # (Kivy ไม่มี text บน canvas — ใส่ Label overlay แทนได้ถ้าต้องการ)

    def _on_coin_touch(self, widget, touch):
        if self.state != STATE_MINIGAME:
            return
        hit = False
        remaining = []
        for c in self.coins:
            dx = touch.x - c["x"]
            dy = touch.y - c["y"]
            if (dx*dx + dy*dy) ** 0.5 <= COIN_R * 1.25:
                self.gold += GOLD_PER_COIN
                hit = True
            else:
                remaining.append(c)

        if hit:
            self.coins = remaining
            self._redraw_coins()
            self.lbl_gold.text = f"[color=ffcc00]⬡[/color] {self.gold} / {GOLD_NEEDED}"
            if self.gold >= GOLD_NEEDED:
                self._end_game(win=True)

    # -------- นับถอยหลัง --------
    def _tick_timer(self, dt):
        if self.state != STATE_MINIGAME:
            return
        self.time_left -= 1
        self.lbl_timer.text = f"TIME  {max(0, int(self.time_left))}"
        if self.time_left <= 0:
            self._end_game(win=False)

    # ============================================================
    #  PHASE 4 — ผลลัพธ์
    # ============================================================
    def _end_game(self, win: bool):
        Clock.unschedule(self._tick_timer)
        Clock.unschedule(self._spawn_coin)
        self.state = STATE_WIN if win else STATE_LOSE

        root = self.root_layout
        root.clear_widgets()
        fill_bg(root, CLR_WIN_BG if win else CLR_LOSE_BG)

        w, h = Window.size

        # ไอคอนผลลัพธ์
        icon = Widget()
        ic_r = min(w, h) * 0.13
        ic_x = w / 2 - ic_r
        ic_y = h * 0.58
        with icon.canvas:
            if win:
                Color(0.1, 0.8, 0.2, 1)
            else:
                Color(0.85, 0.1, 0.1, 1)
            Ellipse(pos=(ic_x, ic_y), size=(ic_r*2, ic_r*2))
        root.add_widget(icon)

        # ข้อความหลัก
        if win:
            headline = "YOU SURVIVED"
            sub      = "RANSOM HAS RETREATED\nItems recovered."
            h_color  = (0.4, 1.0, 0.5, 1)
        else:
            headline = "TIME IS UP"
            sub      = "YOUR ITEMS ARE LOST\nFOREVER."
            h_color  = (1.0, 0.35, 0.35, 1)

        root.add_widget(Label(
            text=headline,
            font_size="46sp", bold=True, color=h_color,
            pos_hint={"center_x": 0.5, "center_y": 0.52},
            size_hint=(1, None), height=60,
        ))

        sub_lbl = Label(
            text=sub,
            font_size="20sp", color=CLR_WHITE, halign="center",
            pos_hint={"center_x": 0.5, "center_y": 0.42},
            size_hint=(0.9, None), height=80,
        )
        sub_lbl.bind(size=sub_lbl.setter("text_size"))
        root.add_widget(sub_lbl)

        # ปุ่มออก
        btn = Button(
            text="ออกจากเกม",
            font_size="22sp", bold=True,
            pos_hint={"center_x": 0.5, "center_y": 0.22},
            size_hint=(0.55, 0.09),
            background_color=(0.3, 0.3, 0.3, 1),
            color=CLR_WHITE,
        )
        btn.bind(on_press=lambda _: App.get_running_app().stop())
        root.add_widget(btn)


if __name__ == "__main__":
    RansomApp().run()
    