# ===============================================================================
# Copyright (C) 2010 Diego Duclos
#
# This file is part of eos.
#
# eos is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 2 of the License, or
# (at your option) any later version.
#
# eos is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with eos.  If not, see <http://www.gnu.org/licenses/>.
# ===============================================================================

import re

from sqlalchemy.orm import reconstructor

import eos.db
from .eqBase import EqBase
from eos.saveddata.price import Price as types_Price
from collections import OrderedDict


from logbook import Logger

pyfalog = Logger(__name__)


class Effect(EqBase):
    """
    The effect handling class, it is used to proxy and load effect handler code,
    as well as a container for extra information regarding effects coming
    from the gamedata db.

    @ivar ID: the ID of this effect
    @ivar name: The name of this effect
    @ivar description: The description of this effect, this is usualy pretty useless
    @ivar published: Wether this effect is published or not, unpublished effects are typicaly unused.
    """
    # Filter to change names of effects to valid python method names
    nameFilter = re.compile("[^A-Za-z0-9]")

    @reconstructor
    def init(self):
        """
        Reconstructor, composes the object as we grab it from the database
        """
        self.__generated = False
        self.__effectModule = None
        self.handlerName = re.sub(self.nameFilter, "", self.name).lower()

    @property
    def handler(self):
        """
        The handler for the effect,
        It is automaticly fetched from effects/<effectName>.py if the file exists
        the first time this property is accessed.
        """
        if not self.__generated:
            pyfalog.debug("Generating effect: {0} ({1}) [runTime: {2}]", self.name, self.effectID, self.runTime)
            self.__generateHandler()

        return self.__handler

    @property
    def runTime(self):
        """
        The runTime that this effect should be run at.
        This property is also automaticly fetched from effects/<effectName>.py if the file exists.
        the possible values are:
        None, "early", "normal", "late"
        None and "normal" are equivalent, and are also the default.

        effects with an early runTime will be ran first when things are calculated,
        followed by effects with a normal runTime and as last effects with a late runTime are ran.
        """
        if not self.__generated:
            self.__generateHandler()

        return self.__runTime

    @property
    def activeByDefault(self):
        """
        The state that this effect should be be in.
        This property is also automaticly fetched from effects/<effectName>.py if the file exists.
        the possible values are:
        None, True, False

        If this is not set:
        We simply assume that missing/none = True, and set it accordingly
        (much as we set runTime to Normalif not otherwise set).
        Nearly all effect files will fall under this category.

        If this is set to True:
        We would enable it anyway, but hey, it's double enabled.
        No effect files are currently configured this way (and probably will never be).

        If this is set to False:
        Basically we simply skip adding the effect to the effect handler when the effect is called,
        much as if the run time didn't match or other criteria failed.
        """
        if not self.__generated:
            self.__generateHandler()

        return self.__activeByDefault

    @activeByDefault.setter
    def activeByDefault(self, value):
        """
        Just assign the input values to the activeByDefault attribute.
        You *could* do something more interesting here if you wanted.
        """
        self.__activeByDefault = value

    @property
    def type(self):
        """
        The type of the effect, automaticly fetched from effects/<effectName>.py if the file exists.

        Valid values are:
        "passive", "active", "projected", "gang", "structure"

        Each gives valuable information to eos about what type the module having
        the effect is. passive vs active gives eos clues about wether to module
        is activatable or not (duh!) and projected and gang each tell eos that the
        module can be projected onto other fits, or used as a gang booster module respectivly
        """
        if not self.__generated:
            self.__generateHandler()

        return self.__type

    @property
    def isImplemented(self):
        """
        Whether this effect is implemented in code or not,
        unimplemented effects simply do nothing at all when run
        """
        return self.handler != effectDummy

    def isType(self, type):
        """
        Check if this effect is of the passed type
        """
        return self.type is not None and type in self.type

    def __generateHandler(self):
        """
        Grab the handler, type and runTime from the effect code if it exists,
        if it doesn't, set dummy values and add a dummy handler
        """

        try:
            self.__effectModule = effectModule = __import__('eos.effects.' + self.handlerName, fromlist=True)
            self.__handler = getattr(effectModule, "handler", effectDummy)
            self.__runTime = getattr(effectModule, "runTime", "normal")
            self.__activeByDefault = getattr(effectModule, "activeByDefault", True)
            t = getattr(effectModule, "type", None)

            t = t if isinstance(t, tuple) or t is None else (t,)
            self.__type = t
        except ImportError as e:
            # Effect probably doesn't exist, so create a dummy effect and flag it with a warning.
            self.__handler = effectDummy
            self.__runTime = "normal"
            self.__activeByDefault = True
            self.__type = None
            pyfalog.debug("ImportError generating handler: {0}", e)
        except AttributeError as e:
            # Effect probably exists but there is an issue with it.  Turn it into a dummy effect so we can continue, but flag it with an error.
            self.__handler = effectDummy
            self.__runTime = "normal"
            self.__activeByDefault = True
            self.__type = None
            pyfalog.error("AttributeError generating handler: {0}", e)
        except Exception as e:
            self.__handler = effectDummy
            self.__runTime = "normal"
            self.__activeByDefault = True
            self.__type = None
            pyfalog.critical("Exception generating handler:")
            pyfalog.critical(e)

        self.__generated = True

    def getattr(self, key):
        if not self.__generated:
            self.__generateHandler()

        return getattr(self.__effectModule, key, None)


def effectDummy(*args, **kwargs):
    pass


class Item(EqBase):
    MOVE_ATTRS = (4,  # Mass
                  38,  # Capacity
                  161)  # Volume

    MOVE_ATTR_INFO = None

    ABYSSAL_TYPES = None

    @classmethod
    def getMoveAttrInfo(cls):
        info = getattr(cls, "MOVE_ATTR_INFO", None)
        if info is None:
            cls.MOVE_ATTR_INFO = info = []
            for id in cls.MOVE_ATTRS:
                info.append(eos.db.getAttributeInfo(id))

        return info

    def moveAttrs(self):
        self.__moved = True
        for info in self.getMoveAttrInfo():
            val = getattr(self, info.name, 0)
            if val != 0:
                attr = Attribute()
                attr.info = info
                attr.value = val
                self.__attributes[info.name] = attr

    @reconstructor
    def init(self):
        self.__race = None
        self.__requiredSkills = None
        self.__requiredFor = None
        self.__moved = False
        self.__offensive = None
        self.__assistive = None
        self.__overrides = None
        self.__priceObj = None
        self.__slot = None

    @property
    def attributes(self):
        if not self.__moved:
            self.moveAttrs()

        return self.__attributes

    def getAttribute(self, key, default=None):
        if key in self.attributes:
            return self.attributes[key].value
        else:
            return default

    def isType(self, type):
        for effect in self.effects.values():
            if effect.isType(type):
                return True

        return False

    @property
    def overrides(self):
        if self.__overrides is None:
            self.__overrides = {}
            overrides = eos.db.getOverrides(self.ID)
            for x in overrides:
                if x.attr.name in self.__attributes:
                    self.__overrides[x.attr.name] = x

        return self.__overrides

    def setOverride(self, attr, value):
        from eos.saveddata.override import Override
        if attr.name in self.overrides:
            override = self.overrides.get(attr.name)
            override.value = value
        else:
            override = Override(self, attr, value)
            self.overrides[attr.name] = override
        eos.db.save(override)

    def deleteOverride(self, attr):
        override = self.overrides.pop(attr.name, None)
        eos.db.saveddata_session.delete(override)
        eos.db.commit()

    srqIDMap = {182: 277, 183: 278, 184: 279, 1285: 1286, 1289: 1287, 1290: 1288}

    @property
    def requiredSkills(self):
        if self.__requiredSkills is None:
            requiredSkills = OrderedDict()
            self.__requiredSkills = requiredSkills
            # Map containing attribute IDs we may need for required skills
            # { requiredSkillX : requiredSkillXLevel }
            combinedAttrIDs = set(self.srqIDMap.keys()).union(set(self.srqIDMap.values()))
            # Map containing result of the request
            # { attributeID : attributeValue }
            skillAttrs = {}
            # Get relevant attribute values from db (required skill IDs and levels) for our item
            for attrInfo in eos.db.directAttributeRequest((self.ID,), tuple(combinedAttrIDs)):
                attrID = attrInfo[1]
                attrVal = attrInfo[2]
                skillAttrs[attrID] = attrVal
            # Go through all attributeID pairs
            for srqIDAtrr, srqLvlAttr in self.srqIDMap.items():
                # Check if we have both in returned result
                if srqIDAtrr in skillAttrs and srqLvlAttr in skillAttrs:
                    skillID = int(skillAttrs[srqIDAtrr])
                    skillLvl = skillAttrs[srqLvlAttr]
                    # Fetch item from database and fill map
                    item = eos.db.getItem(skillID)
                    requiredSkills[item] = skillLvl
        return self.__requiredSkills

    @property
    def requiredFor(self):
        if self.__requiredFor is None:
            self.__requiredFor = dict()

            # Map containing attribute IDs we may need for required skills

            # Get relevant attribute values from db (required skill IDs and levels) for our item
            q = eos.db.getRequiredFor(self.ID, self.srqIDMap)

            for itemID, lvl in q:
                # Fetch item from database and fill map
                item = eos.db.getItem(itemID)
                self.__requiredFor[item] = lvl

        return self.__requiredFor

    factionMap = {
        500001: "caldari",
        500002: "minmatar",
        500003: "amarr",
        500004: "gallente",
        500005: "jove",
        500010: "guristas",
        500011: "angel",
        500012: "blood",
        500014: "ore",
        500016: "sisters",
        500018: "mordu",
        500019: "sansha",
        500020: "serpentis"
    }

    @property
    def race(self):
        if self.__race is None:

            try:
                if self.category.categoryName == 'Structure':
                    self.__race = "upwell"
                else:
                    self.__race = self.factionMap[self.factionID]
            # Some ships (like few limited issue ships) do not have factionID set,
            # thus keep old mechanism for now
            except KeyError:
                # Define race map
                map = {
                    1  : "caldari",
                    2  : "minmatar",
                    4  : "amarr",
                    5  : "sansha",  # Caldari + Amarr
                    6  : "blood",  # Minmatar + Amarr
                    8  : "gallente",
                    9  : "guristas",  # Caldari + Gallente
                    10 : "angelserp",  # Minmatar + Gallente, final race depends on the order of skills
                    12 : "sisters",  # Amarr + Gallente
                    16 : "jove",
                    32 : "sansha",  # Incrusion Sansha
                    128: "ore",
                    135: "triglavian"
                }
                # Race is None by default
                race = None
                # Check primary and secondary required skills' races
                if race is None:
                    skillRaces = tuple([rid for rid in (s.raceID for s in tuple(self.requiredSkills.keys())) if rid])
                    if sum(skillRaces) in map:
                        race = map[sum(skillRaces)]
                        if race == "angelserp":
                            if skillRaces == (2, 8):
                                race = "angel"
                            else:
                                race = "serpentis"
                # Rely on item's own raceID as last resort
                if race is None:
                    race = map.get(self.raceID, None)
                # Store our final value
                self.__race = race
        return self.__race

    @property
    def assistive(self):
        """Detects if item can be used as assistance"""
        # Make sure we cache results
        if self.__assistive is None:
            assistive = False
            # Go through all effects and find first assistive
            for effect in self.effects.values():
                if effect.isAssistance is True:
                    # If we find one, stop and mark item as assistive
                    assistive = True
                    break
            self.__assistive = assistive
        return self.__assistive

    @property
    def offensive(self):
        """Detects if item can be used as something offensive"""
        # Make sure we cache results
        if self.__offensive is None:
            offensive = False
            # Go through all effects and find first offensive
            for effect in self.effects.values():
                if effect.isOffensive is True:
                    # If we find one, stop and mark item as offensive
                    offensive = True
                    break
            self.__offensive = offensive
        return self.__offensive

    def requiresSkill(self, skill, level=None):
        for s, l in self.requiredSkills.items():
            if isinstance(skill, str):
                if s.name == skill and (level is None or l == level):
                    return True

            elif isinstance(skill, int) and (level is None or l == level):
                if s.ID == skill:
                    return True

            elif skill == s and (level is None or l == level):
                return True

            elif hasattr(skill, "item") and skill.item == s and (level is None or l == level):
                return True

        return False

    @property
    def price(self):
        # todo: use `from sqlalchemy import inspect` instead (mac-deprecated doesn't have inspect(), was imp[lemented in 0.8)
        if self.__priceObj is not None and getattr(self.__priceObj, '_sa_instance_state', None) and self.__priceObj._sa_instance_state.deleted:
            pyfalog.debug("Price data for {} was deleted (probably from a cache reset), resetting object".format(self.ID))
            self.__priceObj = None

        if self.__priceObj is None:
            db_price = eos.db.getPrice(self.ID)
            # do not yet have a price in the database for this item, create one
            if db_price is None:
                pyfalog.debug("Creating a price for {}".format(self.ID))
                self.__priceObj = types_Price(self.ID)
                eos.db.add(self.__priceObj)
                eos.db.flush()
            else:
                self.__priceObj = db_price

        return self.__priceObj

    @property
    def isAbyssal(self):
        if Item.ABYSSAL_TYPES is None:
            Item.getAbyssalTypes()

        return self.ID in Item.ABYSSAL_TYPES

    @classmethod
    def getAbyssalTypes(cls):
        cls.ABYSSAL_TYPES = eos.db.getAbyssalTypes()

    @property
    def isCharge(self):
        return self.category.name == "Charge"

    effectSlots = { 'loPower'  : 1,
                    'medPower' : 2,
                    'hiPower'  : 3,
                    'rigSlot'  : 4,
                    'subSystem': 5 }
    @property
    def slot(self):
        if self.__slot is None:
            self.__slot = 0
            for effectName in self.effectSlots:
                if effectName in self.effects:
                    self.__slot = self.effectSlots[effectName]
                    break
        return self.__slot;

    def __repr__(self):
        return "Item(ID={}, name={}) at {}".format(
                self.ID, self.name, hex(id(self))
        )


class MetaData(EqBase):
    pass


class ItemEffect(EqBase):
    pass


class AttributeInfo(EqBase):
    pass


class Attribute(EqBase):
    pass


class Category(EqBase):
    pass


class AlphaClone(EqBase):
    @reconstructor
    def init(self):
        self.skillCache = {}

        for x in self.skills:
            self.skillCache[x.typeID] = x

    def getSkillLevel(self, skill):
        if skill.item.ID in self.skillCache:
            return self.skillCache[skill.item.ID].level
        else:
            return None


class AlphaCloneSkill(EqBase):
    pass


class Group(EqBase):
    pass


class DynamicItem(EqBase):
    pass


class DynamicItemAttribute(EqBase):
    pass


class DynamicItemItem(EqBase):
    pass


class MarketGroup(EqBase):
    def __repr__(self):
        return "MarketGroup(ID={}, name={}, parent={}) at {}".format(
                self.ID, self.name, getattr(self.parent, "name", None), self.name, hex(id(self))
        )


class MetaGroup(EqBase):
    pass


class MetaType(EqBase):
    pass


class Unit(EqBase):

    def __init__(self):
        self.name = None
        self.displayName = None

    @property
    def translations(self):
        """ This is a mapping of various tweaks that we have to do between the internal representation of an attribute
        value and the display (for example, 'Millisecond' units have the display name of 's', so we have to convert value
        from ms to s) """
        # Each entry contains:
        # Function to convert value to display value
        # Function to convert value to display format (which sometimes can be a string)
        # Function which controls unit name used with attribute
        # Function to convert display value to value
        return {
            "Inverse Absolute Percent": (
                lambda v: (1 - v) * 100,
                lambda v: (1 - v) * 100,
                lambda u: u,
                lambda d: -1 * (d / 100) + 1),
            "Inversed Modifier Percent": (
                lambda v: (1 - v) * 100,
                lambda v: (1 - v) * 100,
                lambda u: u,
                lambda d: -1 * (d / 100) + 1),
            "Modifier Percent": (
                lambda v: (v - 1) * 100,
                lambda v: ("%+.2f" if ((v - 1) * 100) % 1 else "%+d") % ((v - 1) * 100),
                lambda u: u,
                lambda d: (d / 100) + 1),
            "Volume": (
                lambda v: v,
                lambda v: v,
                lambda u: "m³",
                lambda d: d),
            "Sizeclass": (
                lambda v: v,
                lambda v: v,
                lambda u: "",
                lambda d: d),
            "Absolute Percent": (
                lambda v: v * 100,
                lambda v: v * 100,
                lambda u: u,
                lambda d: d / 100),
            "Milliseconds": (
                lambda v: v / 1000,
                lambda v: v / 1000,
                lambda u: u,
                lambda d: d * 1000),
            "Boolean": (
                lambda v: True if v else False,
                lambda v: "Yes" if v else "No",
                lambda u: "",
                lambda d: 1.0 if d == "Yes" else 0.0),
            "typeID": (
                self.itemIDCallback,
                self.itemIDCallback,
                lambda u: "",
                None),  # we could probably convert these back if we really tried hard enough
            "groupID": (
                self.groupIDCallback,
                self.groupIDCallback,
                lambda u: "",
                None),
            "attributeID": (
                self.attributeIDCallback,
                self.attributeIDCallback,
                lambda u: "",
                None),
        }

    @staticmethod
    def itemIDCallback(v):
        v = int(v)
        item = eos.db.getItem(int(v))
        return "%s (%d)" % (item.name, v) if item is not None else str(v)

    @staticmethod
    def groupIDCallback(v):
        v = int(v)
        group = eos.db.getGroup(v)
        return "%s (%d)" % (group.name, v) if group is not None else str(v)

    @staticmethod
    def attributeIDCallback(v):
        v = int(v)
        if not v:  # some attributes come through with a value of 0? See #1387
            return "%d" % v
        attribute = eos.db.getAttributeInfo(v, eager="unit")
        return "%s (%d)" % (attribute.name.capitalize(), v)

    def PreformatValue(self, value):
        """Attributes have to be translated certain ways based on their unit (ex: decimals converting to percentages).
        This allows us to get an easy representation of how the attribute should be printed """

        override = self.translations.get(self.name)
        if override is not None:
            return override[1](value), override[2](self.displayName)

        return value, self.displayName

    def SimplifyValue(self, value):
        """Takes the internal representation value and convert it into the display value"""

        override = self.translations.get(self.name)
        if override is not None:
            return override[0](value)

        return value

    def ComplicateValue(self, value):
        """Takes the display value and turns it back into the internal representation of it"""

        override = self.translations.get(self.name)
        if override is not None:
            return override[3](value)

        return value

class Traits(EqBase):
    pass
