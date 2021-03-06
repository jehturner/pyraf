""" 'msgiowidget.py' -- this is a replacement for the msgiobuffer module.
   This contains the MsgIOWidget class, which is an optionally hidden
   scrolling canvas composed of a text widget and frame.  When "hidden",
   it turns into a single-line text widget.
   $Id$
"""
from __future__ import division # confidence high

# System level modules
import sys
import Tkinter as TKNTR # requires 2to3

# Our modules
from stsci.tools import irafutils, tkrotext


def is_USING_X():
    """ This is specifically in a function and not at the top
    of this module so that it is not done until needed.  We do
    not want to casually import wutil anywhere. The import mechanism
    makes this speedy on the 2nd-Nth attempt anyway. """
    from . import wutil
    return wutil.WUTIL_USING_X


class MsgIOWidget(TKNTR.Frame):

    """MsgIOWidget class"""

    def __init__(self, parent, width=100, text=""):
        """Constructor"""

        # We are the main frame that holds everything we do
        TKNTR.Frame.__init__(self, parent)
        self._parent = parent

        # Create two sub-frames, one to hold the 1-liner msg I/O, and
        # the other one to hold the whole scrollable history.
        self._nowFrame = TKNTR.Frame(self, bd=2, relief=TKNTR.SUNKEN,
                                   takefocus=False)
        self._histFrame = TKNTR.Frame(self, bd=2, relief=TKNTR.SUNKEN,
                                   takefocus=False)

        # Put in the expand/collapse button (determine it's sizes)
        self._expBttnHasTxt = True
        btxt= '+'
        if is_USING_X():
            px = 2
            py = 0
        else: # Aqua
            px = 5
            py = 3
            if TKNTR.TkVersion > 8.4:
                px = py = 0
                btxt = ''
                self._expBttnHasTxt = False
        self._expBttn = TKNTR.Checkbutton(self._nowFrame, command=self._expand,
                                        padx=px, pady=py,
                                        text=btxt, indicatoron=0,
                                        state = TKNTR.DISABLED)
        self._expBttn.pack(side=TKNTR.LEFT, padx=3)#, ipadx=0)

        # Overlay a label on the frame
        self._msgLabelVar = TKNTR.StringVar()
        self._msgLabelVar.set(text)
        self._msgLabelMaxWidth = 65 # 70 works but causes plot redraws when
                                    # the history panel is opened/closed
        self._msgLabel = TKNTR.Label(self._nowFrame,
                                   textvariable=self._msgLabelVar,
                                   anchor=TKNTR.W,
                                   justify=TKNTR.LEFT,
                                   width=self._msgLabelMaxWidth,
                                   wraplength=width-100,
                                   takefocus=False)
        self._msgLabel.pack(side=TKNTR.LEFT,
                            fill=TKNTR.X,
                            expand=False)
        self._msgLabel.bind('<Double-Button-1>', self._lblDblClk)

        self._entry = TKNTR.Entry(self._nowFrame,
                                state=TKNTR.DISABLED,
                                width=1,
                                takefocus=False,
                                relief=TKNTR.FLAT,
                                highlightthickness=0)
        self._entry.pack(side=TKNTR.LEFT, fill=TKNTR.X, expand=True)
        self._entry.bind('<Return>', self._enteredText)
        self._entryTyping = TKNTR.BooleanVar()
        self._entryTyping.set(False)

        # put in a spacer here for label height stability
        self._spacer = TKNTR.Label(self._nowFrame, text='', takefocus=False)
        self._spacer.pack(side=TKNTR.LEFT, expand=False, padx=5)

        self._nowFrame.pack(side=TKNTR.TOP, fill=TKNTR.X, expand=True)

        self._hasHistory = False
        self._histScrl = TKNTR.Scrollbar(self._histFrame)
        self._histScrl.pack(side=TKNTR.RIGHT, fill=TKNTR.Y)

        self._histText = tkrotext.ROText(self._histFrame, wrap=TKNTR.WORD,
                         takefocus=False,
                         height=10, yscrollcommand=self._histScrl.set)
# (use if just TKNTR.Text) state=TKNTR.DISABLED, takefocus=False,
#                        exportselection=True is the default
        self._histText.pack(side=TKNTR.TOP, fill=TKNTR.X, expand=True)
        self._histScrl.config(command=self._histText.yview)

        # don't pack this one now - start out with it hidden
#       self._histFrame.pack(side=TKNTR.TOP, fill=TKNTR.X)

        ### Do not pack the main frame here.  Let the application do it. ###

        # At very end of ctor, add the init text to our history
        self._appendToHistory(text)


    def _lblDblClk(self, event=None):
        if self._hasHistory:
            # change the button appearance
            self._expBttn.toggle() # or .select() / .deselect()
            # and then act as if it was clicked
            self._expand()


    def _expand(self):
        ism = self._histFrame.winfo_ismapped()
        if ism: # need to collapse
            self._histFrame.pack_forget()
            if self._expBttnHasTxt:
                self._expBttn.configure(text='+')
        else:   # need to expand
            self._histFrame.pack(side=TKNTR.TOP, fill=TKNTR.BOTH, expand=True) #.X)
            if self._expBttnHasTxt:
                self._expBttn.configure(text='-')
            if self._hasHistory:
                self._histText.see(TKNTR.END)


    def updateIO(self, text=""):
        """ Update the text portion of the scrolling canvas """
        # Update the class variable with the latest text, and append the
        # new text to the end of the history.
        self._appendToHistory(text)
        self._msgLabelVar.set(text)
        # this is a little debugging "easter egg"
        if text.find('long debug line') >=0:
           self.updateIO('and now we are going to talk and talk for a while'+\
                         ' about nothing at all because we want a lot of text')
        self._nowFrame.update_idletasks()


    def readline(self):
        """ Set focus to the entry widget and return it's contents """
        # Find what had focus up to this point
        lastFoc = self.focus_get()

        # Collapse the label as much as possible, it is too big on Linux & OSX
        lblTxt = self._msgLabelVar.get()
        lblTxtLen = len(lblTxt.strip())
        lblTxtLen -= 3
        self._msgLabel.configure(width=min(self._msgLabelMaxWidth, lblTxtLen))

        # Enable the entry widget
        self._entry.configure(state=TKNTR.NORMAL, relief=TKNTR.SUNKEN, width=15,
                              takefocus=True, highlightthickness=2)
        self._entry.focus_set()
        self._entryTyping.set(True)

        # Wait until they are done entering their answer
        self._entry.wait_variable(self._entryTyping)

        # By now they have hit enter
        ans = self._entry.get().strip()

        # Clear and disable the entry widget
        self._entry.delete(0, TKNTR.END)
        self._entry.configure(state=TKNTR.DISABLED, takefocus=False, width=1,
                              relief=TKNTR.FLAT, highlightthickness=0)
        self._entryTyping.set(False)

        # Expand the label back to normal width
        self._msgLabel.configure(width=self._msgLabelMaxWidth)

        # list the answer
        self.updateIO(ans)

        # return focus
        if lastFoc:
            lastFoc.focus_set()

        # return the answer - important to have the "\n" on it
        return ans+"\n"


    def _enteredText(self, event=None):
        self._entryTyping.set(False) # end the waiting
        self._expBttn.focus_set()


    def _appendToHistory(self, txt):
        # sanity check - need no blank lines in the history
        if len(txt.strip()) < 1:
            return

        # enable widget temporarily so we can add text
#       self._histText.config(state=TKNTR.NORMAL)
#       self._histText.delete(1.0, END)

        # add the new text
        if self._hasHistory:
            self._histText.insert(TKNTR.END, '\n'+txt.strip(), force=True)
        else:
            self._histText.insert(TKNTR.END, txt.strip(), force=True)
            self._hasHistory = True

        # disable it again
#       self._histText.config(state=TKNTR.DISABLED)

        # show it
        if self._histFrame.winfo_ismapped():
            self._histText.see(TKNTR.END)
#       self._histFrame.update_idletasks()

        # finally, make sure expand/collapse button is enabled now
        self._expBttn.configure(state = TKNTR.NORMAL)


# Test the above class
if __name__ == '__main__':

    import sys, time

    m = None

    def quit():
        sys.exit()

    def clicked():
        m.updateIO("Clicked at "+time.asctime())

    def ask():
        m.updateIO("Type something in:")
        out = m.readline()

    # create the initial Tk window and immediately withdraw it
    irafutils.init_tk_default_root()

    # make our test window
    top = TKNTR.Toplevel()
    f = TKNTR.Frame(top, width=500, height=300)
    b = TKNTR.Button(f, text='Click Me', command=clicked)
    b.pack(side=TKNTR.LEFT, fill=TKNTR.X, expand=1)
    q = TKNTR.Button(f, text='Buh-Bye', command=quit)
    q.pack(side=TKNTR.LEFT)
    f.pack(side=TKNTR.TOP, fill=TKNTR.X) # , expand=1)
    p = TKNTR.Button(top, text='Prompt Me', command=ask)
    p.pack(side=TKNTR.TOP, fill=TKNTR.X, expand=1)
    fill = TKNTR.Frame(top, height=200, bg="green")
    fill.pack(side=TKNTR.TOP, fill=TKNTR.BOTH, expand=1)
    m = MsgIOWidget(top, 500, "Tiptop")
    m.pack(side=TKNTR.BOTTOM, fill=TKNTR.X)
    for i in range(10):
        t = "Text " + str(i)
        m.updateIO(t)
    m.updateIO("What is your quest?")
    inputValue = m.readline()

    # start
    top.mainloop()
