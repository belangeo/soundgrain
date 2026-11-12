"""Character filtering shared by numeric text controls."""

import re
import wx


def filterNumericChar(evt, allowList=False):
    # Leave editing shortcuts and navigation to the text control.
    key = evt.GetKeyCode()
    if evt.ControlDown() or evt.MetaDown() or evt.AltDown():
        evt.Skip()
        return
    if wx.WXK_NUMPAD0 <= key <= wx.WXK_NUMPAD9:
        char = str(key - wx.WXK_NUMPAD0)
    elif key in (wx.WXK_NUMPAD_DECIMAL, wx.WXK_DECIMAL):
        char = '.'
    elif key == wx.WXK_NUMPAD_SUBTRACT:
        char = '-'
    elif key == wx.WXK_NUMPAD_ADD:
        char = '+'
    else:
        code = evt.GetUnicodeKey()
        if code == wx.WXK_NONE or code < 32 or code == 127:
            evt.Skip()
            return
        char = chr(code)
    if char not in ('0123456789.+-, ' if allowList else '0123456789.+-'):
        return
    if allowList and char == ' ':
        evt.Skip()
        return
    control = evt.GetEventObject()
    start, end = control.GetSelection()
    current = control.GetValue()
    candidate = current[:start] + char + current[end:]
    # Permit incomplete edits such as '-' or '.', and preserve existing
    # scientific notation loaded from a project or pasted by the user.
    parts = candidate.split(',') if allowList else [candidate]
    if (not any(not part.strip() for part in parts[:-1]) and
            all(re.fullmatch(r'[+-]?[0-9]*(?:\.[0-9]*)?(?:[eE][+-]?[0-9]*)?', part.strip())
                for part in parts)):
        evt.Skip()
