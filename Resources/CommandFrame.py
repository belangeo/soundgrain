"""
Copyright 2009-2017 Olivier Belanger

This file is part of SoundGrain.

SoundGrain is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

SoundGrain is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with SoundGrain.  If not, see <http://www.gnu.org/licenses/>.
"""

import wx, os, markdown, webbrowser
import wx.html as html
from Resources.constants import DOCUMENTATION_PATH
from pyo.lib._wxwidgets import BACKGROUND_COLOUR

class MyHtmlWindow(html.HtmlWindow):
    def __init__(self, parent):
        html.HtmlWindow.__init__(self, parent)
        self.parent = parent
        self.SetBackgroundColour(BACKGROUND_COLOUR)
        self.SetBorders(10)

    def OnLinkClicked(self, linkinfo):
        link = linkinfo.GetHref()
        if link in os.listdir(DOCUMENTATION_PATH):
            with open(os.path.join(DOCUMENTATION_PATH, link), "r") as f:
                title = f.readline()[:-1]
            count = self.parent.GetPageCount()
            for i in range(count):
                if self.parent.GetPageText(i) == title:
                    self.parent.ChangeSelection(i)
                    break
        else:
            webbrowser.open(link, 2)

class CommandFrame(wx.Frame):
    def __init__(self, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        closeItem = fileMenu.Append(wx.ID_ANY, 'Close...\tCtrl+W')
        self.Bind(wx.EVT_MENU, self.onClose, id=closeItem.GetId())
        menubar.Append(fileMenu, "&File")
        self.SetMenuBar(menubar)

        self.book = wx.Notebook(self, style=wx.NB_TOP)

        for docfile in sorted([f for f in os.listdir(DOCUMENTATION_PATH) if f.endswith(".md")]):
            with open(os.path.join(DOCUMENTATION_PATH, docfile), "r") as f:
                page = f.read()
                pos = page.find("\n")
                title = page[:pos]
            win = MyHtmlWindow(self.book)
            win.SetPage(markdown.markdown(page))
            self.book.AddPage(win, title)

        self.CenterOnParent()
        self.Show()

    def onClose(self, evt):
        self.Destroy()
