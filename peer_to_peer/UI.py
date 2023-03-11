import curses
from typing import List
from peer_to_peer.utils import User

class UI:
    def __init__(self, stdscr: curses.window, user, userlist_width=25):
        curses.use_default_colors()
        for i in range(0, curses.COLORS):
            curses.init_pair(i + 1, i, -1)
        self.stdscr = stdscr
        self.userlist = [user]
        self.inputbuffer = ""
        self.linebuffer = []
        self.chatbuffer = []

        # Curses, why must you confuse me with your height, width, y, x
        userlist_hwyx = (curses.LINES - 6, userlist_width - 1, 1, 1)
        chatbuffer_hwyx = (curses.LINES - 6, curses.COLS - userlist_width - 4, 1, userlist_width + 2)
        commandbuffer_hwyx = (1, curses.COLS - 6, curses.LINES - 4, 1)
        chatline_hwyx = (1, curses.COLS - 5, curses.LINES - 2, 1)

        self.win_userlist = stdscr.derwin(*userlist_hwyx)
        self.win_chatline = stdscr.derwin(*chatline_hwyx)
        self.win_chatbuffer = stdscr.derwin(*chatbuffer_hwyx)
        self.win_commandline = stdscr.derwin(*commandbuffer_hwyx)

        self.redraw_ui()

    def resize(self):
        #self.redraw_ui()
        return
        """Handles a change in terminal size"""
        u_h, u_w = self.win_userlist.getmaxyx()
        h, w = self.stdscr.getmaxyx()

        self.win_commandline.mvwin(h - 4, 1)
        self.win_commandline.resize(1, w - 1)

        self.win_chatline.mvwin(h - 2, 1)
        self.win_chatline.resize(1, w - 1)

        self.win_userlist.mvwin(1, 1)
        self.win_userlist.resize(h - 5, u_w)

        self.win_chatbuffer.mvwin(u_w + 2, 1)
        self.win_chatbuffer.resize(h - 5, w - u_w - 3)

        self.linebuffer = []
        for msg in self.chatbuffer:
            self._linebuffer_add(msg)

        self.redraw_ui()

    def redraw_ui(self):
        """Redraws the entire UI"""
        h, w = self.stdscr.getmaxyx()
        u_h, u_w = self.win_userlist.getmaxyx()
        self.stdscr.clear()

        self.redraw_userlist()
        self.redraw_chatbuffer()
        self.redraw_chatline()
        self.redraw_commandline()

        for y in range(0, h):
            self.stdscr.addstr(y, 0, "║")
        for y in range(0, h-1):
            self.stdscr.addstr(y, w-1, "║")
        for y in range(0,h-5):
            self.stdscr.addstr(y, u_w+1, "║")
        for x in range(1, w-1):
            self.stdscr.addstr(h - 5, x, "═")
        for x in range(1, w-1):
            self.stdscr.addstr(h - 3, x, "-")
        for x in range(0, w):
            self.stdscr.addstr(0, x, "═")
        for x in range(1, w-1):
            self.stdscr.addstr(h - 1, x, "═")
        self.stdscr.addstr(h-5, u_w+1, "╩")
        self.stdscr.addstr(h - 5, 0, "╠")
        self.stdscr.addstr(h - 5, w-1, "╣")
        self.stdscr.addstr(0, 0, "╔")
        self.stdscr.addstr(h-1, 0, "╚")
        self.stdscr.addstr(0, w - 1, "╗")
        self.stdscr.addstr(0, u_w+1, "╦")

        try:
            #screen.addch(mlines, mcols, 'c')
            self.stdscr.addch(h - 1, w - 1, "╝")
            #self.stdscr.addstr(h - 1, w - 1, "╝")
        except curses.error as e:
            pass


        #self.stdscr.vline(0, u_w + 1, "\U0001F332", h - 6)
        #self.stdscr.hline(h - 6, 0, "=", w)
        #self.stdscr.hline(h - 2, 0, "-", w)

        self.stdscr.refresh()




    def redraw_commandline(self):
        """Redraw the user input textbox"""
        h, w = self.win_commandline.getmaxyx()
        self.win_commandline.clear()
        commands = {"0": {"command": "/quit", "info": "exits the program"},
                    "1": {"command": "/filesend", "info": "sends a file given in path"},
                    "2": {"command": "/userping", "info": "pings a user specifed in parameter"},
                    "3": {"command": "/pingall", "info": "pings all users"}}

        """current_offset = 1
        self.win_commandline.addstr(0, current_offset, "Commands:")
        self.win_commandline.scrollok(True)
        current_offset += 11
        for name, command in commands.items():
            com_w = len(command["command"])
            self.win_commandline.addstr(0, current_offset, command["command"], curses.color_pair(208))
            current_offset += com_w
            self.win_commandline.addstr(0, current_offset, " - ", curses.color_pair(249))
            current_offset += 3
            com_i_w = len(command["info"])
            self.win_commandline.addstr(0, current_offset, command["info"], curses.color_pair(243))
            current_offset += com_i_w
            self.win_commandline.addstr(0, current_offset + 1, " | ")
            current_offset += 5"""

        message = "Commands: "

        purple = "\033[0;35m"
        end = "\033[0m"
        for name, command in commands.items():
            message += purple + command["command"] + end
            message += " - "
            message += command["info"]
            message += " | "
        #print(message)
        length = 150

        self.win_commandline.addstr(0, 1, message)

        self.win_commandline.refresh()


    def redraw_chatline(self):
        """Redraw the user input textbox"""
        h, w = self.win_chatline.getmaxyx()
        self.win_chatline.clear()
        self.win_chatline.addstr(0, 1, "Message:")
        start = len(self.inputbuffer) - w + 1
        if start < 0:
            start = 0
        self.win_chatline.addstr(0, 11, self.inputbuffer[start:])
        self.win_chatline.refresh()

    def redraw_userlist(self):
        """Redraw the userlist"""
        self.win_userlist.clear()
        h, w = self.win_userlist.getmaxyx()
        for i, user in enumerate(self.userlist):
            if i >= h:
                break
            # name = name.ljust(w - 1) + "|"
            #print(i, user, user.user_name)
            self.win_userlist.addstr(i, 0, user.user_name)
        self.win_userlist.refresh()

    def redraw_chatbuffer(self):
        """Redraw the chat message buffer"""
        self.win_chatbuffer.clear()
        h, w = self.win_chatbuffer.getmaxyx()
        j = len(self.linebuffer) - h
        if j < 0:
            j = 0
        for i in range(min(h, len(self.linebuffer))):
            self.win_chatbuffer.addstr(i, 0, self.linebuffer[j])
            j += 1
        self.win_chatbuffer.refresh()

    def chatbuffer_add(self, msg):
        """

        Add a message to the chat buffer, automatically slicing it to
        fit the width of the buffer

        """
        self.chatbuffer.append(msg)
        self._linebuffer_add(msg)
        #self.redraw_chatbuffer()
        #self.redraw_chatline()
        self.redraw_ui()
        self.win_chatline.cursyncup()

    def add_incoming_message(self, msg):
        self.chatbuffer.append(msg)
        self._linebuffer_add(msg)
        self.redraw_chatbuffer()
        h, w = self.win_chatline.getmaxyx()

        start = len(self.inputbuffer) - w + 11
        if start < 0:
            start = 0
        self.win_chatline.addstr(0, 0, self.inputbuffer[start:])
        self.win_chatline.refresh()



    def _linebuffer_add(self, msg):
        h, w = self.stdscr.getmaxyx()
        u_h, u_w = self.win_userlist.getmaxyx()
        w = w - u_w - 2
        while len(msg) >= w:
            self.linebuffer.append(msg[:w])
            msg = msg[w:]
        if msg:
            self.linebuffer.append(msg)

    def prompt(self, msg):
        """Prompts the user for input and returns it"""
        self.inputbuffer = msg
        self.redraw_chatline()
        res = self.wait_input()
        res = res[len(msg):]
        return res

    def wait_input(self, prompt=""):
        """

        Wait for the user to input a message and hit enter.
        Returns the message

        """
        self.inputbuffer = prompt
        self.redraw_chatline()
        self.win_chatline.cursyncup()
        last = -1
        while last != ord('\n'):
            last = self.stdscr.getch()
            if last == ord('\n'):
                tmp = self.inputbuffer
                self.inputbuffer = ""
                self.redraw_chatline()
                self.win_chatline.cursyncup()
                return tmp[len(prompt):]
            elif last == curses.KEY_BACKSPACE or last == 127:
                if len(self.inputbuffer) > len(prompt):
                    self.inputbuffer = self.inputbuffer[:-1]
            elif last == curses.KEY_RESIZE:
                self.resize()
            elif 32 <= last <= 126:
                self.inputbuffer += chr(last)
            self.redraw_chatline()