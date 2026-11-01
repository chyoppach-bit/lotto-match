import os
import threading

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.scrollview import ScrollView
from kivy.utils import platform

import lotto_core

if platform == "android":
    from androidstorage4kivy import SharedStorage, Chooser
else:
    Window.size = (400, 700)

OFF_COLOR = (0.9, 0.9, 0.9, 1)
ON_COLOR = (1, 0.3, 0.3, 1)


class LottoMatchApp(App):
    def build(self):
        self.title = "Lotto Matcher"
        self.selected_numbers = set()
        self.files = {1: [], 2: []}
        self.last_result_text = ""
        self.pending_slot = 1
        self.calc_gen = 0
        self.chooser = None
        if platform == "android":
            self.chooser = Chooser(self.on_android_chosen)

        root = BoxLayout(orientation="vertical", padding=10, spacing=10)

        row = BoxLayout(size_hint_y=0.1, spacing=10)
        b1 = Button(text="LOAD F1", background_color=(0.2, 0.6, 1, 1))
        b1.bind(on_release=lambda x: self.show_file_chooser(1))
        b2 = Button(text="LOAD F2", background_color=(0.2, 0.8, 0.6, 1))
        b2.bind(on_release=lambda x: self.show_file_chooser(2))
        row.add_widget(b1)
        row.add_widget(b2)
        root.add_widget(row)

        row2 = BoxLayout(size_hint_y=0.08, spacing=10)
        btn_save = Button(text="SAVE RESULT", background_color=(1, 0.6, 0.2, 1))
        btn_save.bind(on_release=self.save_result_to_file)
        row2.add_widget(btn_save)
        root.add_widget(row2)

        self.lbl_file_info = Label(
            text="No files loaded", size_hint_y=0.05, color=(0.7, 0.7, 0.7, 1)
        )
        root.add_widget(self.lbl_file_info)

        grid_scroll = ScrollView(size_hint_y=0.35)
        grid = GridLayout(cols=7, spacing=5, size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for i in range(1, 46):
            btn = Button(text=str(i), size_hint_y=None, height=50,
                         background_color=OFF_COLOR)
            btn.bind(on_release=self.toggle_number)
            grid.add_widget(btn)
        grid_scroll.add_widget(grid)
        root.add_widget(grid_scroll)

        result_scroll = ScrollView(size_hint_y=0.42)
        self.lbl_result = Label(
            text="[RESULT]\nSelect numbers or compare files.",
            halign="left", valign="top", size_hint_y=None, font_size="16sp",
        )
        # A Label has no minimum_height; size it from texture_size instead
        self.lbl_result.bind(
            width=lambda inst, w: setattr(inst, "text_size", (w, None)))
        self.lbl_result.bind(
            texture_size=lambda inst, ts: setattr(inst, "height", max(ts[1], 10)))
        result_scroll.add_widget(self.lbl_result)
        root.add_widget(result_scroll)
        return root

    def on_pause(self):
        # Keep the app alive while the system file picker is in front
        return True

    # ---------- UI helpers (always run on the main thread) ----------
    def ui(self, fn, *args):
        Clock.schedule_once(lambda dt: fn(*args))

    def set_info(self, text):
        self.lbl_file_info.text = text

    def set_result(self, text):
        self.last_result_text = text
        self.lbl_result.text = text

    # ---------- number selection ----------
    def toggle_number(self, instance):
        num = int(instance.text)
        if num in self.selected_numbers:
            self.selected_numbers.remove(num)
            instance.background_color = OFF_COLOR
        else:
            self.selected_numbers.add(num)
            instance.background_color = ON_COLOR
        self.calculate_matches_with_selected()

    def calculate_matches_with_selected(self):
        sel = sorted(self.selected_numbers)
        combs = self.files[1]
        if not combs:
            self.set_result("Selected: {}\n\n[Info] Load F1 to see matches.".format(sel))
            return
        self.calc_gen += 1
        gen = self.calc_gen
        threading.Thread(
            target=self.selection_worker, args=(gen, combs, sel), daemon=True
        ).start()

    def selection_worker(self, gen, combs, sel):
        counts = lotto_core.count_with_selection(combs, sel)
        text = "> Selected Nums: {}\n> Matches with F1 ({:,} lines):\n\n".format(
            sel, len(combs))
        for k in sorted(counts, reverse=True):
            text += "[{} Match] {:,} lines\n".format(k, counts[k])
        if gen == self.calc_gen:
            self.ui(self.set_result, text)

    # ---------- file loading ----------
    def show_file_chooser(self, slot):
        self.pending_slot = slot
        if platform == "android":
            # System file picker (no storage permission needed)
            self.chooser.choose_content("*/*")
        else:
            self.show_desktop_chooser(slot)

    def on_android_chosen(self, uris):
        if not uris:
            return
        threading.Thread(
            target=self.load_worker, args=(uris[0], self.pending_slot), daemon=True
        ).start()

    def show_desktop_chooser(self, slot):
        content = BoxLayout(orientation="vertical")
        fc = FileChooserIconView(path=os.path.expanduser("~"), filters=["*.txt", "*.csv"])
        content.add_widget(fc)
        btn = Button(text="OPEN FILE", size_hint_y=0.15)
        content.add_widget(btn)
        popup = Popup(title="Select File {} (.txt/.csv)".format(slot),
                      content=content, size_hint=(0.9, 0.9))

        def on_open(instance):
            if fc.selection:
                threading.Thread(
                    target=self.load_worker, args=(fc.selection[0], slot), daemon=True
                ).start()
                popup.dismiss()

        btn.bind(on_release=on_open)
        popup.open()

    def load_worker(self, source, slot):
        self.ui(self.set_info, "Reading file... Please wait.")
        path = source
        copied = False
        try:
            if platform == "android":
                path = SharedStorage().copy_from_shared(source)
                copied = True
            if not path:
                raise IOError("Could not open the selected file")
            combs, skipped = lotto_core.load_file(path)
        except Exception as exc:
            msg = "Error: {}".format(exc)
            self.ui(self.set_info, msg)
            return
        finally:
            if copied and path:
                try:
                    os.remove(path)
                except OSError:
                    pass

        self.files[slot] = combs
        info = "F{} loaded: {:,} lines".format(slot, len(combs))
        if skipped:
            info += " ({:,} skipped)".format(skipped)
        self.ui(self.set_info, info)

        if slot == 1:
            self.ui(self.calculate_matches_with_selected)
        elif not self.files[1]:
            self.ui(self.set_result, "F2 loaded. Load F1 to compare.")
        else:
            self.compare_two_files(info)

    def compare_two_files(self, info):
        def progress(k):
            self.ui(self.set_info, "{} | comparing... step {}/6".format(info, k))

        exact = lotto_core.count_pairs(self.files[1], self.files[2], progress)
        text = "> [F1 vs F2 Comparison Result]\n> F1 {:,} lines / F2 {:,} lines\n\n".format(
            len(self.files[1]), len(self.files[2]))
        for k in sorted(exact, reverse=True):
            text += "[{} Match] {:,} pairs\n".format(k, exact[k])
        self.ui(self.set_result, text)
        self.ui(self.set_info, "Comparison complete!")

    # ---------- saving ----------
    def save_result_to_file(self, instance):
        if not self.last_result_text:
            self.set_info("No result to save.")
            return
        try:
            if platform == "android":
                base = self.user_data_dir
            else:
                base = os.path.expanduser("~")
            path = os.path.join(base, "lotto_match_result.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.last_result_text)
            if platform == "android":
                SharedStorage().copy_to_shared(path)
                self.set_info("Saved to shared storage (Documents)")
            else:
                self.set_info("Saved to: {}".format(path))
        except Exception as exc:
            self.set_info("Save Failed: {}".format(exc))


if __name__ == "__main__":
    LottoMatchApp().run()
