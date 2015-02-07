import os, wx, markdown
from Resources.constants import DOCUMENTATION_PATH
import wx.html as html

class CommandFrame(wx.Frame):
    def __init__(self, *args, **kw):
        wx.Frame.__init__(self, *args, **kw)
        menubar = wx.MenuBar()
        fileMenu = wx.Menu()
        closeItem = fileMenu.Append(wx.ID_ANY, 'Close...\tCtrl+W')
        self.Bind(wx.EVT_MENU, self.onClose, id=closeItem.GetId())
        menubar.Append(fileMenu, "&File")
        self.SetMenuBar(menubar)

        book = wx.Notebook(self, style=wx.NB_LEFT)

        for docfile in sorted(os.listdir(DOCUMENTATION_PATH)):
            with open(os.path.join(DOCUMENTATION_PATH, docfile), "r") as f:
                page = f.read()
                pos = page.find("\n")
                title = page[:pos]
            win = html.HtmlWindow(book)
            win.SetBorders(10)
            win.SetPage(markdown.markdown(page))
            book.AddPage(win, title)

        self.CenterOnParent()
        self.Show()

    def onClose(self, evt):
        self.Destroy()
