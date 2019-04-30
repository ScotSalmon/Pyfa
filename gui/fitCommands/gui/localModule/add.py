import wx

import gui.mainFrame
from gui import globalEvents as GE
from gui.fitCommands.calc.module.localAdd import CalcAddLocalModuleCommand
from gui.fitCommands.helpers import InternalCommandHistory, ModuleInfo, restoreRemovedDummies
from service.fit import Fit


class GuiAddLocalModuleCommand(wx.Command):

    def __init__(self, fitID, itemID):
        wx.Command.__init__(self, True, 'Add Local Module')
        self.internalHistory = InternalCommandHistory()
        self.fitID = fitID
        self.itemID = itemID
        self.savedRemovedDummies = None

    def Do(self):
        cmd = CalcAddLocalModuleCommand(fitID=self.fitID, newModInfo=ModuleInfo(itemID=self.itemID))
        success = self.internalHistory.submit(cmd)
        sFit = Fit.getInstance()
        sFit.recalc(self.fitID)
        self.savedRemovedDummies = sFit.fill(self.fitID)
        wx.PostEvent(
            gui.mainFrame.MainFrame.getInstance(),
            GE.FitChanged(fitID=self.fitID, action='modadd', typeID=self.itemID)
            if success else
            GE.FitChanged(fitID=self.fitID))
        return success

    def Undo(self):
        sFit = Fit.getInstance()
        fit = sFit.getFit(self.fitID)
        restoreRemovedDummies(fit, self.savedRemovedDummies)
        success = self.internalHistory.undoAll()
        sFit.recalc(self.fitID)
        sFit.fill(self.fitID)
        wx.PostEvent(
            gui.mainFrame.MainFrame.getInstance(),
            GE.FitChanged(fitID=self.fitID, action='moddel', typeID=self.itemID)
            if success else
            GE.FitChanged(fitID=self.fitID))
        return success
