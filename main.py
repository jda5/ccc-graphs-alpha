from kivy.config import Config

Config.set('kivy', 'keyboard_mode', '')  # Need to set before loading everything else

from kivy.app import App
from kivy.clock import Clock
from kivy.core.text import LabelBase
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import BooleanProperty, ListProperty, NumericProperty, ObjectProperty, StringProperty
from kivy.uix.behaviors import FocusBehavior, ButtonBehavior, TouchRippleButtonBehavior
from kivy.uix.button import Button
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.widget import Widget
from kivy.network.urlrequest import UrlRequest
from uuid import uuid4
from json import dumps
from time import time
import webbrowser

from solutions import SolutionChecker

Window.softinput_mode = ''

TEXT_SIZE = Window.height / 30
CURSOR_BLUE = [0.01, 0.33, 0.64, 1]  # Has to be RGBA as the cursor needs to disappear
CLEAR = [1, 1, 1, 0]
BACKGROUND_SCHEME = ['#C4E0E8', '#A7D2DC', '#8BC3D0', '#6EB4C4', '#51A5B8']
MODIFIER = {'8': '×', '9': '(', '0': ')', '=': '+'}

COORDINATES = (
    (1, 5, 2, 7),
    (5, 20, 3, 4),
    (-3, 22, 1, 2),
    (-1, -4, 8, 23),
    (-10, 6, -2, -2),
    (-1, -7, 19, 133),
    (14, 5, 6, 5)
)

MODEL = {
    '00': '(7-5/2-1)=2',
    '01': 'y=2x+c',
    '02': '5=2×1+c',
    '03': 'c=3',
    '04': 'y=2x+3',
    '10': '(20-4/5-3)=8',
    '11': 'y=8x+c',
    '12': '4=8×3+c',
    '13': 'c=-20',
    '14': 'y=8x-20',
    '20': '(22-2/-3-1)=-5',
    '21': 'y=-5x+c',
    '22': '2=-5×1+c',
    '23': 'c=7',
    '24': 'y=-5x+7',
    '30': '(23--4/8--1)=3',
    '31': 'y=3x+c',
    '32': '23=3×8+c',
    '33': 'c=-1',
    '34': 'y=3x-1',
    '40': '(6--2/-10--2)=-1',
    '41': 'y=-x+c',
    '42': '6=-1×-10+c',
    '43': 'c=-4',
    '44': 'y=-x-4',
    '50': '(133--7/19--1)=7',
    '51': 'y=7x+c',
    '52': '-7=7×-1+c',
    '53': 'c=0',
    '54': 'y=7x',
    '60': '(5-5/6-14)=0',
    '61': 'y=c',
    '62': '5=0×6+c',
    '63': 'c=5',
    '64': 'y=5'
}

t0 = time()
user_id = uuid4()
url = f'https://ccc-linear-graphs.firebaseio.com/{user_id}.json'
payload = {'0': {}}


def database_upload(data):
    UrlRequest(url=url, req_body=dumps(data), method='PATCH')


def time_stamp(event, question_number, *args):
    n = str(question_number)
    time_log = "%.4f" % (time() - t0)
    payload[n].update({time_log.replace('.', ','): event})  # Firebase doesn't allow decimal points.
    if len(args) > 0:
        for arg in args:
            payload[n].update(arg)


class HomeScreen(Screen):
    pass


class ImageButton(ButtonBehavior, Image):
    pass


class CCCScreen(Screen):
    pass


class CompletionScreen(Screen):
    pass


class PracticeScreen(Screen):

    buffer = NumericProperty()

    def on_pre_enter(self, *args):
        self.children[0].show_model()


class PracticeWindow(BoxLayout):
    question_number = NumericProperty(0)
    peeking = BooleanProperty(False)
    buffer = NumericProperty()
    comparing = BooleanProperty(False)

    def show_model(self):
        if self.peeking:
            self.ids['compare'].disabled = False
        else:
            self.ids['compare'].disabled = True

        for w in reversed(self.ids['box'].children):  # Show or destroy solutions
            if isinstance(w, LabelContainer):
                w.container.render()
        self.peeking = not self.peeking

    def compare(self):
        for i, widget in enumerate(reversed(self.ids['box'].children)):
            if isinstance(widget, LabelContainer):
                user_answer = widget.container.get_text().replace(" ", "")  # Remove whitespace
                if widget.id_number == 1:
                    correct = user_answer == '5×8=40'
                elif widget.id_number == 2:
                    correct = user_answer == '((1)/(2))'
                else:
                    correct = user_answer == 'y=-3x+4'

                if correct:  # Answer is correct
                    widget.background_label_color = '#A1D19E'  # Answer is correct
                else:
                    widget.background_label_color = '#D29DA2'  # Answer is incorrect


class RippleButton(TouchRippleButtonBehavior, Button):
    up_color = [0.3, 0.3, 0.3, 1]
    down_color = [68 / 255, 146 / 255, 191 / 255, 0.5]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def on_touch_down(self, touch):
        collide_point = self.collide_point(touch.x, touch.y)
        if collide_point and not self.disabled:
            touch.grab(self)
            self.background_color = self.down_color
            self.ripple_show(touch)
            self.dispatch('on_press')
            return True
        return False

    def on_touch_up(self, touch):
        if touch.grab_current is self:
            touch.ungrab(self)
            self.ripple_fade()
            self.background_color = self.up_color
            self.dispatch('on_release')
            return True
        return False

    def on_disabled(self, instance, value):
        pass


class TextWidget(Widget):
    text_size = NumericProperty(TEXT_SIZE)
    cells = ListProperty()
    highlight_color = ListProperty(CLEAR)

    def resize(self):
        if len(self.cells) == 0:
            width = self.text_size
        else:
            width = self.text_size * len(self.cells)

        self.size = (width, self.text_size)

    def add_text(self, text, italic, index):
        entry = Label(text=text,
                      color=(0, 0, 0, 1),
                      size=(self.text_size, self.text_size),
                      font_size=self.text_size,
                      font_name='maths_font',
                      italic=italic)
        self.cells.insert(index, entry)
        self.add_widget(entry)
        self.draw_cells(index)

    def draw_cells(self, index=0):
        for i, cell in enumerate(self.cells[index:], index):
            # self.remove_widget(cell)
            cell.pos = (self.x + self.text_size * i, self.y)
            # self.add_widget(cell)
        self.resize()

    def delete_text(self, index):
        self.remove_widget(self.cells[index - 1])
        del self.cells[index - 1]

    def highlight(self, white=True):
        if white:
            self.highlight_color = CLEAR
        else:
            self.highlight_color = [0.345, 0.42, 0.592, 0.175]


class FractionWidget(Widget):
    text_size = NumericProperty(TEXT_SIZE)
    spacing = NumericProperty()
    numerator = ObjectProperty()
    denominator = ObjectProperty()

    def resize(self):
        self.spacing = self.numerator.height / 4
        height = self.numerator.height + self.denominator.height + self.spacing
        width = max(self.numerator.width, self.denominator.width)
        self.size = (width, height)

    # def recenter(self):
    #     if len(self.numerator.cells) < len(self.denominator.cells):
    #         left_spacing = (self.width - self.numerator.width) / 2
    #         self.numerator.x = self.x + left_spacing
    #         for index, label in enumerate(self.numerator.cells):
    #             label.x = self.x + left_spacing + self.text_size * index
    #     elif len(self.numerator.cells) > len(self.denominator.cells):
    #         left_spacing = (self.width - self.denominator.width) / 2
    #         self.denominator.x = self.x + left_spacing
    #         for index, label in enumerate(self.denominator.cells):
    #             label.x = self.x + left_spacing + self.text_size * index
    #     else:
    #         self.numerator.x = self.x
    #         self.denominator.x = self.x
    #         for index, (label_top, label_bottom) in enumerate(zip(self.numerator.cells, self.denominator.cells)):
    #             label_top.x = label_bottom.x = self.x + self.text_size * index

    def recenter(self):
        """
        Repositions the numerator / denominator so that it is in the middle of the fraction (whichever is shorter)
        :return:
        """
        if len(self.numerator.cells) != len(self.denominator.cells):
            term = self.numerator if (len(self.numerator.cells) < len(self.denominator.cells)) else self.denominator
            left_spacing = (self.width - term.width) / 2  # Space to the left of the term and the start of the fraction
            term.x = self.x + left_spacing  # Reposition the TextWidget
            term.draw_cells()
            # for index, label in enumerate(term.cells):
            #     label.x = self.x + left_spacing + self.text_size * index
        else:
            self.numerator.x = self.denominator.x = self.x
            # self.denominator.x = self.x
            # for index, (label_top, label_bottom) in enumerate(zip(self.numerator.cells, self.denominator.cells)):
            #     label_top.x = label_bottom.x = self.x + self.text_size * index

    def get_text(self):
        numerator = ''.join([char.text for char in self.numerator.cells])
        denominator = ''.join([char.text for char in self.denominator.cells])
        return f'(({numerator})/({denominator}))'


class Cursor(Widget):
    numerator = BooleanProperty(True)
    fraction = BooleanProperty(False)
    index = NumericProperty(0)
    fraction_index = NumericProperty(0)
    color = ListProperty(CLEAR)
    blink_on = BooleanProperty(True)
    focus = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.blink_event = Clock.schedule_interval(lambda dx: self.blink(), 0.53)

    def reset(self):
        self.numerator = True
        self.fraction = False
        self.index = 0
        self.fraction_index = 0
        self.reposition()

    def move_cursor(self, direction):
        self.reset_blinking()
        if self.fraction and direction == 'left':
            if self.fraction_index > 0:
                self.fraction_index -= 1
            else:
                if self.index > 0:
                    self.fraction = False
                    self.change_highlight()
                    self.index -= 1
        elif self.fraction and direction == 'right':
            if self.numerator:
                if self.fraction_index < len(self.parent.widgets[self.index - 1].numerator.cells):
                    self.fraction_index += 1
                else:
                    self.fraction = False
                    self.change_highlight()
            else:
                if self.fraction_index < len(self.parent.widgets[self.index - 1].denominator.cells):
                    self.fraction_index += 1
                else:
                    self.fraction = False
                    self.change_highlight()
        elif self.fraction and self.numerator and direction == 'down':
            self.numerator = False
            self.change_highlight()
            if self.fraction_index > len(self.parent.widgets[self.index - 1].denominator.cells):
                self.fraction_index = len(self.parent.widgets[self.index - 1].denominator.cells)
        elif self.fraction and not self.numerator and direction == 'up':
            self.numerator = True
            self.change_highlight()
            if self.fraction_index > len(self.parent.widgets[self.index - 1].numerator.cells):
                self.fraction_index = len(self.parent.widgets[self.index - 1].numerator.cells)
        elif direction == 'left':
            if self.index > 0:
                if self.is_fraction():
                    self.fraction = True
                    self.numerator = False
                    self.change_highlight()
                    self.fraction_index = len(self.parent.widgets[self.index - 1].denominator.cells)
                else:
                    self.fraction = False
                    self.index -= 1
        elif direction == 'right':
            if self.index < len(self.parent.widgets):
                self.index += 1
                if self.is_fraction():
                    self.fraction = True
                    self.numerator = True
                    self.fraction_index = 0
                    self.change_highlight()
                else:
                    self.fraction = False  # Maybe delete
        self.reposition()

    def reposition(self):
        if len(self.parent.widgets) == 0:
            self.pos = self.parent.x, self.parent.y + (self.parent.height - self.height) / 2
            return
        i = max(0, self.index - 1)  # Prevents index-1 < 0
        if self.fraction:
            fraction = self.parent.widgets[i]
            if self.numerator:
                self.pos = (fraction.numerator.x + fraction.text_size * self.fraction_index,
                            fraction.numerator.y)
            else:
                self.pos = (fraction.denominator.x + fraction.text_size * self.fraction_index,
                            fraction.denominator.y)
        else:
            distance = self.parent.x
            for widget in self.parent.widgets[:self.index]:
                distance += widget.width
            self.pos = distance, self.parent.y + (self.parent.height - self.height) / 2

    def is_fraction(self):
        if isinstance(self.parent.widgets[self.index - 1], FractionWidget):
            return True
        else:
            return False

    def change_highlight(self, clear=False):
        if self.fraction and not clear:
            if self.numerator:
                self.parent.widgets[self.index - 1].denominator.highlight()
                self.parent.widgets[self.index - 1].numerator.highlight(white=False)
            else:
                self.parent.widgets[self.index - 1].denominator.highlight(white=False)
                self.parent.widgets[self.index - 1].numerator.highlight()
        else:
            # If the cursor moves outside of the fraction we need to access all fraction widgets and remove
            # their highlight
            for widget in self.parent.widgets:
                if isinstance(widget, FractionWidget):
                    widget.denominator.highlight()
                    widget.numerator.highlight()

    def reset_blinking(self):
        self.color = CURSOR_BLUE
        self.blink_on = True

    def blink(self):
        if self.focus:
            if self.blink_on:
                self.color = CURSOR_BLUE
            else:
                self.color = CLEAR
            self.blink_on = not self.blink_on


class Container(Widget):
    text_size = NumericProperty(TEXT_SIZE)
    cursor = ObjectProperty()
    widgets = ListProperty()
    render_text = StringProperty()
    peek = BooleanProperty(True)
    widget_storage = ListProperty()
    peek_storage = ListProperty()

    def new_widget(self, text, italic=False, fraction=False):
        if self.cursor.fraction:
            fraction = self.widgets[max(0, self.cursor.index - 1)]
            if self.cursor.numerator:
                fraction.numerator.add_text(text=text, italic=italic, index=self.cursor.fraction_index)
            else:
                fraction.denominator.add_text(text=text, italic=italic, index=self.cursor.fraction_index)
            self.cursor.fraction_index += 1
            fraction.resize()
            fraction.recenter()
            self.reposition_widgets()
            self.cursor.reposition()
            return
        elif fraction:
            entry = FractionWidget()
            entry.resize()
            self.cursor.fraction_index = 0
            self.cursor.fraction = True
            self.cursor.numerator = True
        else:
            entry = Label(text=text,
                          color=(0, 0, 0, 1),
                          size=(self.text_size, self.text_size),
                          font_size=self.text_size,
                          font_name='maths_font',
                          italic=italic)
        self.widgets.insert(self.cursor.index, entry)
        self.add_widget(entry)
        self.reposition_widgets()
        self.cursor.index += 1
        self.cursor.reposition()
        if fraction:
            self.cursor.change_highlight()

    def reposition_widgets(self, rotation=False):
        for wid_list in (self.widgets, self.peek_storage):
            if wid_list == self.peek_storage and not rotation:
                continue  # This prevents the peek widgets being repositioned every time the user creates a widget
            for i, widget in enumerate(wid_list):
                if i == 0:
                    widget.pos = self.x, self.y + (self.height - widget.height) / 2
                else:
                    widget.pos = wid_list[i - 1].x + wid_list[i - 1].width, self.y + (self.height - widget.height) / 2
                if isinstance(widget, FractionWidget):
                    widget.numerator.draw_cells()
                    widget.denominator.draw_cells()
                    widget.resize()
                    widget.recenter()

    def backspace(self):
        if self.cursor.index > 0:
            if self.cursor.is_fraction():
                if self.cursor.fraction_index > 0 and self.cursor.fraction:
                    if self.cursor.numerator:
                        self.widgets[self.cursor.index - 1].numerator.delete_text(index=self.cursor.fraction_index)
                    else:
                        self.widgets[self.cursor.index - 1].denominator.delete_text(index=self.cursor.fraction_index)
                    self.cursor.fraction_index -= 1
                else:
                    self.remove_widget(self.widgets[self.cursor.index - 1])
                    del self.widgets[self.cursor.index - 1]
                    self.cursor.index -= 1
                    self.cursor.fraction = False
            else:
                self.remove_widget(self.widgets[self.cursor.index - 1])
                del self.widgets[self.cursor.index - 1]
                self.cursor.index -= 1
            self.reposition_widgets()
            self.cursor.reposition()

    def get_text(self):
        text = []
        for widget in self.widgets:
            if isinstance(widget, FractionWidget):
                text.append(widget.get_text())
            else:
                text.append(widget.text)
        return ''.join(text)

    def render(self):
        if self.peek:
            self.widget_storage = self.children[:]
            self.clear_widgets()
            if len(self.peek_storage) == 0:
                build_fraction = False
                add_numerator = True
                weak_index = 0
                prev = None
                for char in self.render_text:
                    if prev is None:
                        x_pos = self.x
                    else:
                        x_pos = prev.x + prev.width
                    i = False
                    if char == '(':
                        build_fraction = True
                        add_numerator = True
                        fraction_widget = FractionWidget()
                        fraction_widget.resize()
                        fraction_widget.pos = (x_pos, self.y + (self.height - fraction_widget.height) / 2)
                        weak_index = 0
                    elif char == ')':
                        build_fraction = False
                        fraction_widget.resize()
                        fraction_widget.recenter()
                        self.add_widget(fraction_widget)
                        self.peek_storage.append(fraction_widget)
                        prev = fraction_widget
                    else:
                        if char not in '0123456789-=×+':
                            i = True
                        if build_fraction:
                            if char == '/':
                                add_numerator = False
                                weak_index = 0
                            elif add_numerator:
                                fraction_widget.numerator.add_text(text=char, italic=i, index=weak_index)
                                weak_index += 1
                            else:
                                fraction_widget.denominator.add_text(text=char, italic=i, index=weak_index)
                                weak_index += 1
                        else:
                            widget = Label(
                                text=char,
                                pos=(x_pos, self.y + (self.height - self.text_size) / 2),
                                color=(0, 0, 0, 1),
                                size=(self.text_size, self.text_size),
                                font_size=self.text_size,
                                font_name='maths_font',
                                markup=True,
                                italic=i
                            )
                            self.add_widget(widget)
                            self.peek_storage.append(widget)
                            prev = widget
            else:
                for widget in self.peek_storage:
                    self.add_widget(widget)
                self.reposition_widgets(rotation=True)
            self.parent.container_opacity = 1
        else:
            self.clear_widgets()
            for widget in self.widget_storage:
                self.add_widget(widget)
            self.parent.container_opacity = 0
        self.peek = not self.peek

    def reset(self):
        self.clear_widgets()
        self.add_widget(self.cursor)
        self.cursor.reset()
        self.widgets = []
        self.widget_storage = []
        self.peek_storage = []
        self.peek = True

    on_size = lambda self, *args: self.reposition_widgets(rotation=True)


class LabelContainer(FocusBehavior, BoxLayout):
    container = ObjectProperty()
    peek_text = StringProperty()
    text = StringProperty()
    id_number = NumericProperty()
    background_label_color = StringProperty()
    container_opacity = NumericProperty(1)
    grandparent = ObjectProperty()
    x_counter = NumericProperty()
    y_counter = NumericProperty()
    tutorial = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(lambda *args: self.tint())

    def on_touch_down(self, touch):
        if self.grandparent.comparing:
            if self.collide_point(*touch.pos):
                self.container.render()

        elif not self.grandparent.peeking:
            if self.collide_point(*touch.pos) and self.focus:  # If the widget has focus and is touched
                cursor = self.container.cursor
                # If the touch is less than the container move cursor to start or if there are no widgets
                if touch.x <= self.container.x or len(self.container.widgets) == 0:
                    cursor.index = 0
                else:
                    for index, widget in enumerate(self.container.widgets):
                        if widget.collide_point(*touch.pos):
                            if isinstance(widget, FractionWidget):
                                cursor.fraction = True
                                cursor.index = index + 1
                                if touch.y > self.center_y:  # Numerator selected
                                    cursor.numerator = True
                                    if len(widget.numerator.cells) == 0:  # No text in widget
                                        cursor.fraction_index = 0
                                    else:
                                        for i, cell in enumerate(widget.numerator.cells):
                                            if cell.collide_point(*touch.pos):  # Touch collides with a cell
                                                if touch.x > cell.center_x:
                                                    cursor.fraction_index = i + 1
                                                else:
                                                    cursor.fraction_index = i

                                                    # I don't know how this works anymore
                                else:
                                    cursor.numerator = False
                                    if len(widget.denominator.cells) == 0:  # No text in widget
                                        cursor.fraction_index = 0
                                    else:
                                        for i, cell in enumerate(widget.denominator.cells):
                                            if cell.collide_point(*touch.pos):  # Touch collides with a cell
                                                if touch.x > cell.center_x:
                                                    cursor.fraction_index = i + 1
                                                else:
                                                    cursor.fraction_index = i
                                break
                            else:  # If the collision is not with a fraction
                                cursor.fraction = False
                                if touch.x > widget.center_x:  # Finds the closest "gap" between widgets
                                    cursor.index = index + 1
                                else:
                                    cursor.index = index
                                break
                    # If the touch is greater than the right of last widget
                    if self.container.widgets[-1].right < touch.x:
                        cursor.fraction = False
                        cursor.index = len(self.container.widgets)  # Move cursor to end
                cursor.change_highlight()
                cursor.reposition()
            if not self.collide_point(*touch.pos):
                return
            if (not self.disabled and self.is_focusable and
                    ('button' not in touch.profile or
                     not touch.button.startswith('scroll'))):
                self.focus = True
                FocusBehavior.ignored_touch.append(touch)
        return super(FocusBehavior, self).on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.focus and not self.grandparent.peeking:
            self.x_counter += touch.dx
            self.y_counter += touch.dy
            if self.x_counter >= self.container.text_size:
                self.container.cursor.move_cursor('right')
                self.x_counter = 0
            elif self.x_counter <= -self.container.text_size:
                self.container.cursor.move_cursor('left')
                self.x_counter = 0
            if self.y_counter >= self.container.text_size:
                self.container.cursor.move_cursor('up')
                self.y_counter = 0
            elif self.y_counter <= -self.container.text_size:
                self.container.cursor.move_cursor('down')
                self.y_counter = 0

    def tint(self):
        self.background_label_color = BACKGROUND_SCHEME[self.id_number]  # Changes the background to blue
        if not self.tutorial:
            self.peek_text = MODEL[str(self.grandparent.question_number) + str(self.id_number)]  # Change the peek text

    def _on_focus(self, instance, value, *args):
        if self.keyboard_mode == 'auto':
            if value:
                self._bind_keyboard()
                if self.grandparent.buffer == 0:
                    self.grandparent.buffer = Window.keyboard_height
                self.parent.parent.do_scroll_y = True
                if instance.id_number == 3 or instance.id_number == 4:
                    self.parent.parent.scroll_to(self.parent.children[0], padding=0)
                else:
                    self.parent.parent.scroll_to(instance, padding=0)
                self.container.cursor.focus = True
                self.container.cursor.reset_blinking()
                if self.container.cursor.fraction:
                    self.container.cursor.change_highlight()
            else:
                self._unbind_keyboard()
                self.parent.parent.scroll_to(self.parent.children[-1])  # Scroll to top
                self.parent.parent.do_scroll_y = False  # Stop scrolling
                self.container.cursor.color = CLEAR  # Clear cursor
                self.container.cursor.focus = False  # Lift cursor
                if self.container.cursor.fraction:
                    self.container.cursor.change_highlight(clear=True)

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        container = self.container
        if keycode[1] == 'escape':
            return
        elif keycode[1] == 'enter':
            return
        elif keycode[1] == 'left' or keycode[1] == 'right' or keycode[1] == 'up' or keycode[1] == 'down':
            container.cursor.move_cursor(keycode[1])
        elif keycode[1] == 'backspace':
            container.backspace()
        else:
            if len(container.widgets) > 0:  # Otherwise I'll get a stupid index error
                if container.widgets[-1].right > container.right * 0.95:  # Don't let new text go off screen
                    return False  # May cause an error with fractions but at this point I don't really care
            if 'shift' in modifiers and text in MODIFIER:
                container.new_widget(text=MODIFIER[text])
            elif keycode[1] not in ['shift', 'alt', 'super', 'tab', 'lctrl', 'rctrl', 'capslock', 'rshift',
                                    'alt-gr']:
                container.cursor.reset_blinking()
                if keycode[1] == '/':
                    container.new_widget(text='/', fraction=True)
                else:
                    if keycode[1] in '0123456789-=×+':
                        container.new_widget(text=text)
                    elif keycode[1].isalpha():
                        container.new_widget(text=text, italic=True)
        return False


class NavigationPane(BoxLayout):
    question_text = StringProperty()
    score = NumericProperty(150)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        Clock.schedule_once(lambda x: self.on_start())

    def on_start(self):
        self.hide_show(self.ids['next'], hide=True)
        self.hide_show(self.ids['peek'], hide=True)
        self.hide_show(self.ids['compare'], hide=True)
        x1, y1, x2, y2 = COORDINATES[self.parent.question_number]
        self.question_text = f'Find the equation of a line that goes through the coordinates [b]({x1}, {y1})[/b] and ' \
                             f'[b]({x2}, {y2})[/b] '

    def ready(self, instance):
        time_stamp('initial-peek-end', self.parent.question_number)
        self.parent.peek()
        self.hide_show(instance, hide=True)
        self.hide_show(self.ids['peek'], hide=False)
        self.hide_show(self.ids['compare'], hide=False)

    def next_button(self):
        self.hide_show(self.ids['peek'], hide=True)
        self.hide_show(self.ids['compare'], hide=True)
        self.hide_show(self.ids['next'], hide=False)

    def update_progress(self):
        """
        Takes current the question number, and updates the corresponding circle
        :return:
        """
        self.ids[str(self.parent.question_number)].color = [84 / 255, 166 / 255, 78 / 255, 1]

    @staticmethod
    def hide_show(widget, hide):  # Hides a button by reducing its size to 0 and disabling it
        if hide:
            widget.height, widget.size_hint_y, widget.opacity, widget.disabled = 0, None, 0, True
        else:
            widget.height, widget.size_hint_y, widget.opacity, widget.disabled = 1, 0.4, 1, False
            # Declaring a constant size_hint for all widgets might cause problems later


class CCCWindow(BoxLayout):
    question_number = NumericProperty(0)
    peeking = BooleanProperty(False)
    buffer = NumericProperty()
    comparing = BooleanProperty(False)

    def on_start(self):
        time_stamp('ccc-started', self.question_number)
        self.peek()
        self.ids['navigation'].update_progress()

    def compare(self):
        """
        Gets each inputted text and runs this through the solution checker. Uses the eval() method and LabelContainer
        ID to call correct solution checker function
        :return:
        """
        mark = {'correct': {}, 'incorrect': {}}  # Assess the number of incorrect / correct responses
        x1, y1, x2, y2 = COORDINATES[self.question_number]
        solution_checker = SolutionChecker(x1, y1, x2, y2)
        for i, widget in enumerate(reversed(self.ids['box'].children)):
            if isinstance(widget, LabelContainer):
                user_answer = widget.container.get_text().replace(" ", "")  # Remove whitespace

                if widget.id_number == 0:
                    correct = solution_checker.step_one(user_answer)
                elif widget.id_number == 1:
                    correct = solution_checker.step_two(user_answer)
                elif widget.id_number == 2:
                    correct = solution_checker.step_three(user_answer)
                elif widget.id_number == 3:
                    correct = solution_checker.step_four(user_answer)
                else:
                    correct = solution_checker.step_five(user_answer)

                if correct:  # Answer is correct
                    widget.background_label_color = '#A1D19E'  # Answer is correct
                    self.ids['navigation'].score += 100
                    mark['correct'].update({str(i): user_answer.replace("/", "!")})  # Need to replace '/' for firebase
                else:
                    widget.background_label_color = '#D29DA2'  # Answer is incorrect
                    mark['incorrect'].update({str(i): user_answer.replace("/", "!")})

        self.ids['navigation'].next_button()
        self.comparing = True
        time_stamp(f'compare-button-pressed', self.question_number, mark, {'score': str(self.children[-1].score)})

    def peek(self):
        if not self.peeking:
            self.children[-1].score -= 150
            self.ids['navigation'].ids['compare'].disabled = True
        else:
            self.ids['navigation'].ids['compare'].disabled = False
        for w in reversed(self.ids['box'].children):  # Show or destroy solutions
            if isinstance(w, LabelContainer):
                w.container.render()
        self.peeking = not self.peeking
        time_stamp(f'peek-button-pressed-{self.peeking}', self.question_number)

    def next_question(self):
        global payload
        time_stamp('question-end', self.question_number)
        database_upload(payload)
        self.question_number += 1
        payload = {str(self.question_number): {}}
        time_stamp('question-start', self.question_number)
        self.comparing = False
        if self.question_number == len(COORDINATES):  # Has finished all the questions
            self.parent.parent.current = 'completion_screen'
        else:
            for child in self.ids['box'].children:
                if isinstance(child, LabelContainer):
                    child.tint()
                    child.container.reset()
            nav = self.ids['navigation']
            nav.hide_show(nav.ids['next'], hide=True)
            nav.hide_show(nav.ids['ready'], hide=False)
            x1, y1, x2, y2 = COORDINATES[self.question_number]
            nav.question_text = f'Find the equation of a line that goes through the coordinates [b]({x1}, {y1})[/b] ' \
                                f'and [b]({x2}, {y2})[/b] '
            nav.update_progress()
            nav.score += 150
            self.peek()


class MainApp(App):
    def build(self):
        return Builder.load_file("main.kv")

    def change_screen(self, screen, transition=None):
        screen_manager = self.root.ids['screen_manager']
        if transition:
            screen_manager.transition = transition
        screen_manager.current = screen

    @staticmethod
    def visit_url(link):
        if link == 'https://lboro.onlinesurveys.ac.uk/ccc-linear-graphs-copy':
            link = link + f'?token={user_id}&xx'
        webbrowser.open(link)


if __name__ == '__main__':
    Window.clearcolor = (1, 1, 1, 1)
    LabelBase.register(name='maths_font',
                       fn_regular='./fonts/maths_font_regular.ttf',
                       fn_italic='./fonts/maths_font_italic.ttf')
    LabelBase.register(name='montserrat',
                       fn_regular='./fonts/montserrat_regular.ttf',
                       fn_bold='./fonts/montserrat_bold.ttf')
    LabelBase.register(name='icons',
                       fn_regular='./fonts/icons.ttf')
    MainApp().run()
