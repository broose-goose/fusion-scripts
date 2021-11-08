#Author-
#Description-Takes a box full of "tile bodies" and generates position file for light boards, and labels each light on or off

import adsk.core, adsk.fusion, adsk.cam, traceback

from time import sleep

def run(context):
    _ui = None
    try:
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface
        _design = adsk.fusion.Design.cast(_app.activeProduct)
        if not _design:
            _ui.messageBox('No active Fusion 360 design', 'No Design')
            return

        _features = _design.rootComponent.features
        _extrude = _features.extrudeFeatures.item(0).bodies.item(0)
        _rpattern = _features.rectangularPatternFeatures.item(0).bodies
        _mirror_1 = _features.mirrorFeatures.item(0)
        _mirror_2 = _features.mirrorFeatures.item(1)
        _mirror_3 = _features.mirrorFeatures.item(2)

        _front_bodies = []
        _front_bodies.append(_extrude)
        
        for pat_index in range(_rpattern.count):
            _body = _rpattern.item(pat_index)
            _front_bodies.append(pat_index)

        _ui.messageBox(str(len(_front_bodies)))




    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
