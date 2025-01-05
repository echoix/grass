"""
This type stub file was generated by pyright.
"""

import wx

"""
This module contains the :class:`~lib.expando.ExpandoTextCtrl`, which is a multi-line
text control that will expand its height on the fly to be able to show
all the lines of the content of the control.


Description
===========

The :class:`ExpandoTextCtrl` is a multi-line :class:`TextCtrl` that will
adjust its height on the fly as needed to accommodate the number of
lines needed to display the current content of the control.  It is
assumed that the width of the control will be a fixed value and
that only the height will be adjusted automatically.  If the
control is used in a sizer then the width should be set as part of
the initial or min size of the control.

When the control resizes itself it will attempt to also make
necessary adjustments in the sizer hierarchy it is a member of (if
any) but if that is not suffiecient then the programmer can catch
the EVT_ETC_LAYOUT_NEEDED event in the container and make any
other layout adjustments that may be needed.


Usage
=====

Sample usage::

    import wx
    from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED

    class MyFrame(wx.Frame):

        def __init__(self):

            wx.Frame.__init__(self, None, title="Test ExpandoTextCtrl")
            self.pnl = p = wx.Panel(self)
            self.eom = ExpandoTextCtrl(p, size=(250,-1),
                                       value="This control will expand as you type")
            self.Bind(EVT_ETC_LAYOUT_NEEDED, self.OnRefit, self.eom)

            # create some buttons and sizers to use in testing some
            # features and also the layout
            vBtnSizer = wx.BoxSizer(wx.VERTICAL)

            btn = wx.Button(p, -1, "Write Text")
            self.Bind(wx.EVT_BUTTON, self.OnWriteText, btn)
            vBtnSizer.Add(btn, 0, wx.ALL|wx.EXPAND, 5)

            btn = wx.Button(p, -1, "Append Text")
            self.Bind(wx.EVT_BUTTON, self.OnAppendText, btn)
            vBtnSizer.Add(btn, 0, wx.ALL|wx.EXPAND, 5)

            sizer = wx.BoxSizer(wx.HORIZONTAL)
            col1 = wx.BoxSizer(wx.VERTICAL)
            col1.Add(self.eom, 0, wx.ALL, 10)
            sizer.Add(col1)
            sizer.Add(vBtnSizer)
            p.SetSizer(sizer)

            # Put the panel in a sizer for the frame so we can use self.Fit()
            frameSizer = wx.BoxSizer()
            frameSizer.Add(p, 1, wx.EXPAND)
            self.SetSizer(frameSizer)

            self.Fit()


        def OnRefit(self, evt):
            # The Expando control will redo the layout of the
            # sizer it belongs to, but sometimes this may not be
            # enough, so it will send us this event so we can do any
            # other layout adjustments needed.  In this case we'll
            # just resize the frame to fit the new needs of the sizer.
            self.Fit()


        def OnWriteText(self, evt):
            self.eom.WriteText("This is a test...  Only a test.  If this had "
                               "been a real emergency you would have seen the "
                               "quick brown fox jump over the lazy dog.")

        def OnAppendText(self, evt):
            self.eom.AppendText("Appended text.")

    app = wx.App(0)
    frame = MyFrame()
    frame.Show()
    app.MainLoop()

"""
wxEVT_ETC_LAYOUT_NEEDED = ...
EVT_ETC_LAYOUT_NEEDED = ...
class ExpandoTextCtrl(wx.TextCtrl):
    """
    The ExpandoTextCtrl is a multi-line wx.TextCtrl that will
    adjust its height on the fly as needed to accommodate the number of
    lines needed to display the current content of the control.  It is
    assumed that the width of the control will be a fixed value and
    that only the height will be adjusted automatically.  If the
    control is used in a sizer then the width should be set as part of
    the initial or min size of the control.

    When the control resizes itself it will attempt to also make
    necessary adjustments in the sizer hierarchy it is a member of (if
    any) but if that is not suffiecient then the programmer can catch
    the EVT_ETC_LAYOUT_NEEDED event in the container and make any
    other layout adjustments that may be needed.
    """
    _defaultHeight = ...
    _leading = ...
    def __init__(self, parent, id=..., value=..., pos=..., size=..., style=..., validator=..., name=...) -> None:
        """
        Default class constructor.

        :param `parent`: parent window, must not be ``None``;
        :param integer `id`: window identifier. A value of -1 indicates a default value;
        :param string `value`: the control text label;
        :param `pos`: the control position. A value of (-1, -1) indicates a default position,
         chosen by either the windowing system or wxPython, depending on platform;
        :param `size`: the control size. A value of (-1, -1) indicates a default size,
         chosen by either the windowing system or wxPython, depending on platform;
        :param integer `style`: the underlying :class:`wx.Control` style;
        :param wx.Validator `validator`: the window validator;
        :param string `name`: the widget name.

        :type parent: :class:`wx.Window`
        :type pos: tuple or :class:`wx.Point`
        :type size: tuple or :class:`wx.Size`
        """
        ...
    
    def SetMaxHeight(self, h): # -> None:
        """
        Sets the maximum height that the control will expand to on its
        own, and adjusts it down if needed.

        :param integer `h`: the maximum control height, in pixels.
        """
        ...
    
    def GetMaxHeight(self): # -> int:
        """
        Returns the maximum height that the control will expand to on its own.

        :rtype: int
        """
        ...
    
    def SetFont(self, font):
        """
        Sets the font for the :class:`ExpandoTextCtrl`.

        :param wx.Font font: font to associate with the :class:`ExpandoTextCtrl`, pass
         ``NullFont`` to reset to the default font.

        :rtype: bool
        :returns: ``True`` if the font was really changed, ``False`` if it was already
         set to this font and nothing was done.
        """
        ...
    
    def WriteText(self, text): # -> None:
        """
        Writes the text into the text control at the current insertion position.

        :param string `text`: text to write to the text control.

        .. note::

           Newlines in the text string are the only control characters allowed, and they
           will cause appropriate line breaks. See :meth:`AppendText` for more convenient
           ways of writing to the window. After the write operation, the insertion point
           will be at the end of the inserted text, so subsequent write operations will
           be appended. To append text after the user may have interacted with the control,
           call :meth:`TextCtrl.SetInsertionPointEnd` before writing.

        """
        ...
    
    def AppendText(self, text): # -> None:
        """
        Appends the text to the end of the text control.

        :param string `text`: text to write to the text control.

        .. seealso:: :meth:`WriteText`
        """
        ...
    
    def OnTextChanged(self, evt): # -> None:
        """
        Handles the ``wx.EVT_TEXT`` event for :class:`ExpandoTextCtrl`.

        :param `event`: a :class:`CommandEvent` event to be processed.
        """
        ...
    
    def OnSize(self, evt): # -> None:
        """
        Handles the ``wx.EVT_SIZE`` event for :class:`ExpandoTextCtrl`.

        :param `event`: a :class:`wx.SizeEvent` event to be processed.
        """
        ...
    
    if 'wxGTK' in wx.PlatformInfo or 'wxOSX-cocoa' in wx.PlatformInfo:
        def GetNumberOfLines(self): # -> int:
            ...
        


