import ctypes
import time
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Optional, Union
from pynput import keyboard, mouse


class Direction(Enum):
    LEFT = -1
    RIGHT = 1


class ButtonState(Enum):
    NONE = auto()
    LEFT = auto()
    RIGHT = auto()


@dataclass
class Config:
    """Cfg setup"""
    movement_increment: int = 700
    activation_delay: float = 0.02
    left_move_key: mouse.Button = mouse.Button.x2  # Mouse4
    right_move_key: mouse.Button = mouse.Button.x1  # Mouse5
    activate_circle_key: keyboard.KeyCode = keyboard.KeyCode.from_char('k')
    quick_activate_key: keyboard.KeyCode = keyboard.KeyCode.from_char('e')


class MouseInput(ctypes.Structure):
    """Win API Mouse input"""
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))
    ]


class InputUnion(ctypes.Union):
    _fields_ = [("mi", MouseInput)]


class Input(ctypes.Structure):
    """Win API normal input"""
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("_input", InputUnion)
    ]


class MouseController:
    MOUSEEVENTF_MOVE = 0x0001
    INPUT_MOUSE = 0

    def move_relative(self, dx: int, dy: int) -> None:
        """Move Mouse to position"""
        mouse_input = MouseInput(
            dx=dx, 
            dy=dy, 
            mouseData=0, 
            dwFlags=self.MOUSEEVENTF_MOVE, 
            time=0, 
            dwExtraInfo=None
        )
        
        input_struct = Input(type=self.INPUT_MOUSE)
        input_struct.mi = mouse_input
        
        ctypes.windll.user32.SendInput(1, ctypes.byref(input_struct), ctypes.sizeof(input_struct))


class InputHandler:
    
    def __init__(self, config: Config = Config()):
        """InputHandler & Konfiguration"""
        self.config = config
        self.mouse_controller = MouseController()
        self.keyboard_controller = keyboard.Controller()
        self.last_button_state: ButtonState = ButtonState.NONE
        
        self.mouse_listener = mouse.Listener(on_click=self._on_click)
        self.keyboard_listener = keyboard.Listener(on_press=self._on_press)

    def start(self) -> None:
        """Start input monitoring"""
        self.mouse_listener.start()
        self.keyboard_listener.start()
        
        try:
            while self.mouse_listener.is_alive() and self.keyboard_listener.is_alive():
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self) -> None:
        """Stop monitoring"""
        self.mouse_listener.stop()
        self.keyboard_listener.stop()

    def _press_key(self, key: keyboard.KeyCode) -> None:
        self.keyboard_controller.press(key)
    
    def _release_key(self, key: keyboard.KeyCode) -> None:
        self.keyboard_controller.release(key)
    
    def _activate_circle(self) -> None:
        self._press_key(self.config.activate_circle_key)
        time.sleep(self.config.activation_delay)
        self._release_key(self.config.activate_circle_key)
        
    def _perform_mouse_movement(self, direction: Direction) -> None:
        self._press_key(self.config.activate_circle_key)
        time.sleep(self.config.activation_delay)
        self.mouse_controller.move_relative(
            direction.value * self.config.movement_increment, 0
        )
        self._release_key(self.config.activate_circle_key)
    
    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        """Callback click event"""
        if not pressed:
            return
            
        if button == self.config.left_move_key:
            if self.last_button_state == ButtonState.LEFT:
                self._activate_circle()
                self.last_button_state = ButtonState.NONE
            else:
                self._perform_mouse_movement(Direction.LEFT)
                self.last_button_state = ButtonState.LEFT
                
        elif button == self.config.right_move_key:
            if self.last_button_state == ButtonState.RIGHT:
                self._activate_circle()
                self.last_button_state = ButtonState.NONE
            else:
                self._perform_mouse_movement(Direction.RIGHT)
                self.last_button_state = ButtonState.RIGHT
    
    def _on_press(self, key: Union[keyboard.Key, keyboard.KeyCode]) -> None:
        """Callback input"""
        if key == self.config.quick_activate_key:
            self._activate_circle()


def main():
    handler = InputHandler()
    print("Mouse AA Tool running...")
    try:
        handler.start()
    except KeyboardInterrupt:
        pass
    finally:
        print("Exit")


if __name__ == "__main__":
    main()
