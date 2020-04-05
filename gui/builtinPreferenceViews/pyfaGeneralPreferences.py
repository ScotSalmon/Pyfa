# noinspection PyPackageRequirements
import wx

import gui.globalEvents as GE
import gui.mainFrame
from gui.bitmap_loader import BitmapLoader
from gui.preferenceView import PreferenceView
from service.fit import Fit
from service.settings import SettingsProvider


class PFGeneralPref(PreferenceView):

    title = "General"

    def populatePanel(self, panel):
        self.mainFrame = gui.mainFrame.MainFrame.getInstance()
        self.dirtySettings = False
        self.openFitsSettings = SettingsProvider.getInstance().getSettings("pyfaPrevOpenFits",
                                                                           {"enabled": False, "pyfaOpenFits": []})

        mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.stTitle = wx.StaticText(panel, wx.ID_ANY, self.title, wx.DefaultPosition, wx.DefaultSize, 0)
        self.stTitle.Wrap(-1)
        self.stTitle.SetFont(wx.Font(12, 70, 90, 90, False, wx.EmptyString))
        mainSizer.Add(self.stTitle, 0, wx.EXPAND | wx.ALL, 5)
        
        helpCursor = wx.Cursor(wx.CURSOR_QUESTION_ARROW)

        self.m_staticline1 = wx.StaticLine(panel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        mainSizer.Add(self.m_staticline1, 0, wx.EXPAND | wx.TOP | wx.BOTTOM, 5)

        self.cbGlobalChar = wx.CheckBox(panel, wx.ID_ANY, "Use global character", wx.DefaultPosition, wx.DefaultSize,
                                        0)
        mainSizer.Add(self.cbGlobalChar, 0, wx.ALL | wx.EXPAND, 5)

        self.cbDefaultCharImplants = wx.CheckBox(panel, wx.ID_ANY, "Use character implants by default for new fits",
                                                 wx.DefaultPosition, wx.DefaultSize, 0)
        mainSizer.Add(self.cbDefaultCharImplants, 0, wx.ALL | wx.EXPAND, 5)

        self.cbGlobalDmgPattern = wx.CheckBox(panel, wx.ID_ANY, "Use global damage pattern", wx.DefaultPosition,
                                              wx.DefaultSize, 0)
        mainSizer.Add(self.cbGlobalDmgPattern, 0, wx.ALL | wx.EXPAND, 5)

        self.cbCompactSkills = wx.CheckBox(panel, wx.ID_ANY, "Compact skills needed tooltip", wx.DefaultPosition,
                                           wx.DefaultSize, 0)
        mainSizer.Add(self.cbCompactSkills, 0, wx.ALL | wx.EXPAND, 5)

        self.cbFilterBySkills = wx.CheckBox(panel, wx.ID_ANY, "Filter by skills (experimental)", wx.DefaultPosition,
                                           wx.DefaultSize, 0)
        mainSizer.Add(self.cbFilterBySkills, 0, wx.ALL | wx.EXPAND, 5)

        self.cbFitColorSlots = wx.CheckBox(panel, wx.ID_ANY, "Color fitting view by slot", wx.DefaultPosition,
                                           wx.DefaultSize, 0)
        mainSizer.Add(self.cbFitColorSlots, 0, wx.ALL | wx.EXPAND, 5)

        self.cbReopenFits = wx.CheckBox(panel, wx.ID_ANY, "Reopen previous fits on startup", wx.DefaultPosition,
                                        wx.DefaultSize, 0)
        mainSizer.Add(self.cbReopenFits, 0, wx.ALL | wx.EXPAND, 5)

        self.cbRackSlots = wx.CheckBox(panel, wx.ID_ANY, "Separate Racks", wx.DefaultPosition, wx.DefaultSize, 0)
        mainSizer.Add(self.cbRackSlots, 0, wx.ALL | wx.EXPAND, 5)

        labelSizer = wx.BoxSizer(wx.VERTICAL)
        self.cbRackLabels = wx.CheckBox(panel, wx.ID_ANY, "Show Rack Labels", wx.DefaultPosition, wx.DefaultSize, 0)
        labelSizer.Add(self.cbRackLabels, 0, wx.ALL | wx.EXPAND, 5)
        mainSizer.Add(labelSizer, 0, wx.LEFT | wx.EXPAND, 30)

        self.cbShowTooltip = wx.CheckBox(panel, wx.ID_ANY, "Show fitting tab tooltips", wx.DefaultPosition, wx.DefaultSize, 0)
        mainSizer.Add(self.cbShowTooltip, 0, wx.ALL | wx.EXPAND, 5)

        self.cbGaugeAnimation = wx.CheckBox(panel, wx.ID_ANY, "Animate gauges", wx.DefaultPosition, wx.DefaultSize, 0)
        mainSizer.Add(self.cbGaugeAnimation, 0, wx.ALL | wx.EXPAND, 5)

        self.cbOpenFitInNew = wx.CheckBox(panel, wx.ID_ANY, "Open fittings in a new page by default",
                                          wx.DefaultPosition, wx.DefaultSize, 0)
        mainSizer.Add(self.cbOpenFitInNew, 0, wx.ALL | wx.EXPAND, 5)

        self.cbShowShipBrowserTooltip = wx.CheckBox(panel, wx.ID_ANY, "Show ship browser tooltip",
                                          wx.DefaultPosition, wx.DefaultSize, 0)
        mainSizer.Add(self.cbShowShipBrowserTooltip, 0, wx.ALL | wx.EXPAND, 5)


        self.cbReloadAll = wx.CheckBox(panel, wx.ID_ANY, "Change charge in all modules of the same type",
                                       wx.DefaultPosition, wx.DefaultSize, 0)
        if "wxGTK" not in wx.PlatformInfo:
            self.cbReloadAll.SetCursor(helpCursor)
        self.cbReloadAll.SetToolTip(wx.ToolTip(
            'When disabled, reloads charges just in selected modules. Action can be reversed by holding Ctrl or Alt key while changing charge.'))
        mainSizer.Add(self.cbReloadAll, 0, wx.ALL | wx.EXPAND, 5)

        self.rbAddLabels = wx.RadioBox(panel, -1, "Extra info in Additions panel tab names", wx.DefaultPosition, wx.DefaultSize, ["None", "Quantity of active items", "Quantity of all items"], 1, wx.RA_SPECIFY_COLS)
        mainSizer.Add(self.rbAddLabels, 0, wx.EXPAND | wx.TOP | wx.RIGHT | wx.BOTTOM, 10)
        self.rbAddLabels.Bind(wx.EVT_RADIOBOX, self.OnAddLabelsChange)

        self.sFit = Fit.getInstance()

        self.cbGlobalChar.SetValue(self.sFit.serviceFittingOptions["useGlobalCharacter"])
        self.cbDefaultCharImplants.SetValue(self.sFit.serviceFittingOptions["useCharacterImplantsByDefault"])
        self.cbGlobalDmgPattern.SetValue(self.sFit.serviceFittingOptions["useGlobalDamagePattern"])
        self.cbFitColorSlots.SetValue(self.sFit.serviceFittingOptions["colorFitBySlot"] or False)
        self.cbRackSlots.SetValue(self.sFit.serviceFittingOptions["rackSlots"] or False)
        self.cbRackLabels.SetValue(self.sFit.serviceFittingOptions["rackLabels"] or False)
        self.cbCompactSkills.SetValue(self.sFit.serviceFittingOptions["compactSkills"] or False)
        self.cbReopenFits.SetValue(self.openFitsSettings["enabled"])
        self.cbShowTooltip.SetValue(self.sFit.serviceFittingOptions["showTooltip"] or False)
        self.cbGaugeAnimation.SetValue(self.sFit.serviceFittingOptions["enableGaugeAnimation"])
        self.cbOpenFitInNew.SetValue(self.sFit.serviceFittingOptions["openFitInNew"])
        self.cbShowShipBrowserTooltip.SetValue(self.sFit.serviceFittingOptions["showShipBrowserTooltip"])
        self.cbReloadAll.SetValue(self.sFit.serviceFittingOptions["ammoChangeAll"])
        self.rbAddLabels.SetSelection(self.sFit.serviceFittingOptions["additionsLabels"])
        self.cbFilterBySkills.SetValue(self.sFit.serviceFittingOptions["filterBySkills"] or False)

        self.cbGlobalChar.Bind(wx.EVT_CHECKBOX, self.OnCBGlobalCharStateChange)
        self.cbDefaultCharImplants.Bind(wx.EVT_CHECKBOX, self.OnCBDefaultCharImplantsStateChange)
        self.cbGlobalDmgPattern.Bind(wx.EVT_CHECKBOX, self.OnCBGlobalDmgPatternStateChange)
        self.cbFitColorSlots.Bind(wx.EVT_CHECKBOX, self.onCBGlobalColorBySlot)
        self.cbRackSlots.Bind(wx.EVT_CHECKBOX, self.onCBGlobalRackSlots)
        self.cbRackLabels.Bind(wx.EVT_CHECKBOX, self.onCBGlobalRackLabels)
        self.cbCompactSkills.Bind(wx.EVT_CHECKBOX, self.onCBCompactSkills)
        self.cbReopenFits.Bind(wx.EVT_CHECKBOX, self.onCBReopenFits)
        self.cbShowTooltip.Bind(wx.EVT_CHECKBOX, self.onCBShowTooltip)
        self.cbGaugeAnimation.Bind(wx.EVT_CHECKBOX, self.onCBGaugeAnimation)
        self.cbOpenFitInNew.Bind(wx.EVT_CHECKBOX, self.onCBOpenFitInNew)
        self.cbShowShipBrowserTooltip.Bind(wx.EVT_CHECKBOX, self.onCBShowShipBrowserTooltip)
        self.cbReloadAll.Bind(wx.EVT_CHECKBOX, self.onCBReloadAll)
        self.cbFilterBySkills.Bind(wx.EVT_CHECKBOX, self.onCBFilterBySkills)

        self.cbRackLabels.Enable(self.sFit.serviceFittingOptions["rackSlots"] or False)

        panel.SetSizer(mainSizer)
        panel.Layout()

    def onCBGlobalColorBySlot(self, event):
        # todo: maybe create a SettingChanged event that we can fire, and have other things hook into, instead of having the preference panel itself handle the
        # updating of things related to settings.
        self.sFit.serviceFittingOptions["colorFitBySlot"] = self.cbFitColorSlots.GetValue()
        fitID = self.mainFrame.getActiveFit()
        self.sFit.refreshFit(fitID)

        iView = self.mainFrame.marketBrowser.itemView
        if iView.active:
            iView.update(iView.active)

        wx.PostEvent(self.mainFrame, GE.FitChanged(fitIDs=(fitID,)))
        event.Skip()

    def onCBGlobalRackSlots(self, event):
        self.sFit.serviceFittingOptions["rackSlots"] = self.cbRackSlots.GetValue()
        self.cbRackLabels.Enable(self.cbRackSlots.GetValue())
        fitID = self.mainFrame.getActiveFit()
        self.sFit.refreshFit(fitID)
        wx.PostEvent(self.mainFrame, GE.FitChanged(fitIDs=(fitID,)))
        event.Skip()

    def onCBGlobalRackLabels(self, event):
        self.sFit.serviceFittingOptions["rackLabels"] = self.cbRackLabels.GetValue()
        fitID = self.mainFrame.getActiveFit()
        self.sFit.refreshFit(fitID)
        wx.PostEvent(self.mainFrame, GE.FitChanged(fitIDs=(fitID,)))
        event.Skip()

    def OnCBGlobalCharStateChange(self, event):
        self.sFit.serviceFittingOptions["useGlobalCharacter"] = self.cbGlobalChar.GetValue()
        event.Skip()

    def OnCBDefaultCharImplantsStateChange(self, event):
        self.sFit.serviceFittingOptions["useCharacterImplantsByDefault"] = self.cbDefaultCharImplants.GetValue()
        event.Skip()

    def OnCBGlobalDmgPatternStateChange(self, event):
        self.sFit.serviceFittingOptions["useGlobalDamagePattern"] = self.cbGlobalDmgPattern.GetValue()
        event.Skip()

    def onCBCompactSkills(self, event):
        self.sFit.serviceFittingOptions["compactSkills"] = self.cbCompactSkills.GetValue()
        fitID = self.mainFrame.getActiveFit()
        self.sFit.refreshFit(fitID)
        wx.PostEvent(self.mainFrame, GE.FitChanged(fitIDs=(fitID,)))
        event.Skip()

    def onCBReopenFits(self, event):
        self.openFitsSettings["enabled"] = self.cbReopenFits.GetValue()

    def onCBShowTooltip(self, event):
        self.sFit.serviceFittingOptions["showTooltip"] = self.cbShowTooltip.GetValue()

    def onCBGaugeAnimation(self, event):
        self.sFit.serviceFittingOptions["enableGaugeAnimation"] = self.cbGaugeAnimation.GetValue()

    def onCBOpenFitInNew(self, event):
        self.sFit.serviceFittingOptions["openFitInNew"] = self.cbOpenFitInNew.GetValue()

    def onCBShowShipBrowserTooltip(self, event):
        self.sFit.serviceFittingOptions["showShipBrowserTooltip"] = self.cbShowShipBrowserTooltip.GetValue()

    def onCBReloadAll(self, event):
        self.sFit.serviceFittingOptions["ammoChangeAll"] = self.cbReloadAll.GetValue()

    def onCBFilterBySkills(self, event):
        self.sFit.serviceFittingOptions["filterBySkills"] = self.cbFilterBySkills.GetValue()
        # TODO: maybe refresh browsers here

    def OnAddLabelsChange(self, event):
        self.sFit.serviceFittingOptions["additionsLabels"] = event.GetInt()
        fitID = self.mainFrame.getActiveFit()
        self.sFit.refreshFit(fitID)
        wx.PostEvent(self.mainFrame, GE.FitChanged(fitIDs=(fitID,)))
        event.Skip()

    def getImage(self):
        return BitmapLoader.getBitmap("prefs_settings", "gui")


PFGeneralPref.register()
