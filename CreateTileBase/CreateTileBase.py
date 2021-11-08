import adsk.core, adsk.fusion, adsk.cam, traceback

from typing import List, Callable, Tuple


_app = adsk.core.Application.cast(None)
_ui = adsk.core.UserInterface.cast(None)
_design = adsk.fusion.Design.cast(None)
_handlers = []


# Event handler for the execute event.
class MyExecuteHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandEventArgs.cast(args)

        outerProfileSelections = adsk.core.SelectionCommandInput.cast(eventArgs.command.commandInputs.itemById('outer_profile'))
        innerFaceSelections = adsk.core.SelectionCommandInput.cast(eventArgs.command.commandInputs.itemById('inner_face'))
        tileBodySelections = adsk.core.SelectionCommandInput.cast(eventArgs.command.commandInputs.itemById('tile_body'))
        blankBodySelections = adsk.core.SelectionCommandInput.cast(eventArgs.command.commandInputs.itemById('blank_body'))
        toleranceFloatSelection = adsk.core.FloatSliderCommandInput.cast(eventArgs.command.commandInputs.itemById('tolerance_float'))

        tolerance = round(toleranceFloatSelection.valueOne, 2)
        
        messageOut = "Forgot to set:"
        if outerProfileSelections.selectionCount == 0:
            messageOut += "\nOuter Profile"
        if innerFaceSelections.selectionCount == 0:
            messageOut += "\nInner Profiles"
        if tileBodySelections.selectionCount == 0:
            messageOut += "\nTile Bodies"
        if blankBodySelections.selectionCount == 0:
            messageOut += "\nBlank Body"
        if messageOut != "Forgot to set:":
            messageOut += "\nD:"
            _ui.messageBox(messageOut)
        else:
            _ui.messageBox("running")
            self.run(
                self.GetSelections(outerProfileSelections, 1),
                self.GetSelections(innerFaceSelections, 0),
                self.GetSelections(tileBodySelections, 2),
                self.GetSelections(blankBodySelections, 2),
                tolerance
            )
    
    def run(
        self,
        outerProfiles: List[adsk.fusion.Profile],
        innerFaces: List[adsk.fusion.BRepFace],
        tileBodies: List[adsk.fusion.BRepBody],
        blankBody: List[adsk.fusion.BRepBody],
        tolerance: float
    ):
        try:

            global _design

            tileDim = self.GetTileDim(blankBody)
            (minPoint, maxPoint) = self.GetGridBounds(outerProfiles)

            xIter = round((maxPoint.x - minPoint.x) / tileDim, 0)
            yIter = round((maxPoint.y - minPoint.y) / tileDim, 0)

            _ui.messageBox("from ({}, {}) to ({}, {}) with tile {} for {} columns and {} rows and tolerance {}".format(
                minPoint.x, minPoint.y,
                maxPoint.x, maxPoint.y,
                tileDim,
                xIter, yIter,
                tolerance
            ))

            if not xIter.is_integer() or not yIter.is_integer():
                _ui.messageBox("Couldn't subdivide outer profiles by tiles evenly D:")
                return

            tileBodiesWrapped = self.WrapBodies(tileBodies)
            blankBodiesWrapped = self.WrapBodies(blankBody)

            xIter = int(xIter)
            yIter = int(yIter)

            transform = adsk.core.Matrix3D.create()

            _ui.messageBox("Okay, going for it D:")

           
            rootComp = _design.rootComponent
            occs = rootComp.occurrences
            subComp1 = occs.item(0).component

            baseFeats = subComp1.features.baseFeatures
            baseFeat = baseFeats.add()

            tempBrepMgr = adsk.fusion.TemporaryBRepManager.get()

            baseFeat.startEdit()

            for x in range(xIter):
                x_pos_min = minPoint.x + tileDim * x
                x_pos_max = x_pos_min + tileDim
                for y in range(yIter):
                    y_pos_min = minPoint.y + tileDim * y
                    y_pos_max = y_pos_min + tileDim
                    tile_on_face = self.IsTileOnFace(
                        innerFaces, x_pos_min, x_pos_max, 
                        y_pos_min, y_pos_max, tolerance
                    )
                    if tile_on_face:
                        bodiesWrapped = tileBodiesWrapped
                    else:
                        bodiesWrapped = blankBodiesWrapped

                    for (body, vec) in bodiesWrapped:
                        tempBody = tempBrepMgr.copy(body)
                        transform.translation = adsk.core.Vector3D.create(
                            x_pos_min - vec.x, 
                            y_pos_min - vec.y,
                            0.0
                        )
                        tempBrepMgr.transform(tempBody, transform)
                        subComp1.bRepBodies.add(tempBody, baseFeat)

            baseFeat.finishEdit()

            _ui.messageBox("Hope i did something D:")

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))


    def IsTileOnFace(
        self, faces: List[adsk.fusion.BRepFace], x0: int,
        x1: int, y0: int, y1: int, tolerance: float
    ) -> bool:
        points = [
            adsk.core.Point3D.create(x0 + tolerance, y0 + tolerance, 0),
            adsk.core.Point3D.create(x0 + tolerance, y1 - tolerance, 0),
            adsk.core.Point3D.create(x1 - tolerance, y0 + tolerance, 0),
            adsk.core.Point3D.create(x1 - tolerance, y1 - tolerance, 0),
        ]
        for face in faces:
            evaluator = face.evaluator
            for p1 in points:
                (res, param) = evaluator.getParameterAtPoint(p1)
                (res, p2) = evaluator.getPointAtParameter(param)
                if p1.isEqualTo(p2) and evaluator.isParameterOnFace(param):
                    return True
        return False



    def GetTileDim(self, blankBody: List[adsk.fusion.BRepBody]):
        firstBody = blankBody[0]
        maxPoint = firstBody.boundingBox.maxPoint
        minPoint = firstBody.boundingBox.minPoint
        # should be square, shouldn't matter
        if maxPoint.x != minPoint.x:
            return maxPoint.x - minPoint.x
        else:
            return maxPoint.y - minPoint.y

    def GetGridBounds(self, outerFaces: List[adsk.fusion.Profile]):
        minPoint: adsk.core.Point3D = None
        maxPoint: adsk.core.Point3D = None

        for face in outerFaces:
            box = face.boundingBox
            if minPoint == None:
                minPoint = box.minPoint.copy()
            if box.minPoint.x <= minPoint.x and box.minPoint.y <= minPoint.y:
                minPoint = box.minPoint.copy()
            if maxPoint == None:
                maxPoint = box.maxPoint.copy()
            if box.maxPoint.x >= maxPoint.x and box.maxPoint.y >= maxPoint.y:
                maxPoint = box.maxPoint.copy()
            minPoint.x = round(minPoint.x, 2)
            minPoint.y = round(minPoint.y, 2)
            maxPoint.x = round(maxPoint.x, 2)
            maxPoint.y = round(maxPoint.y, 2)

        return minPoint, maxPoint

    def WrapBodies(self, bodies: List[adsk.fusion.BRepBody]) -> List[Tuple[adsk.fusion.BRepBody, adsk.core.Point3D]]:
        wrappedBodies = []
        for body in bodies:
            minPoint = body.boundingBox.minPoint
            wrappedBodies.append((body, minPoint))
        return wrappedBodies
            
                
    def GetSelections(self, sel: adsk.core.SelectionCommandInput, typeOfThing: int):
        selections = []
        selectionType = ""

        for i in range(sel.selectionCount):
            selection = sel.selection(i).entity
            if typeOfThing == 0:
                selection = adsk.fusion.BRepFace.cast(selection)
                selectionType = "BRepFace"
            elif typeOfThing == 1:
                selection = adsk.fusion.Profile.cast(selection)
                selectionType = "Profile"
            elif typeOfThing == 2:
                selection = adsk.fusion.BRepBody.cast(selection)
                selectionType = "BRepBody"

            if selection == None:
                _ui.messageBox("Error casting entity as " + selectionType)

            selections.append(selection)

        return selections
        



# Event handler for the commandCreated event.
class MyCommandCreatedHandler(adsk.core.CommandCreatedEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        eventArgs = adsk.core.CommandCreatedEventArgs.cast(args)
        cmd = eventArgs.command
        inputs = cmd.commandInputs

        onExecute = MyExecuteHandler()
        cmd.execute.add(onExecute)
        _handlers.append(onExecute)
        
        onDestroy = MyDestroyHandler()
        cmd.destroy.add(onDestroy)
        _handlers.append(onDestroy)        
        
        # Add some inputs to the command dialog.
        outerProfiles = inputs.addSelectionInput('outer_profile', 'Outer Profiles', 'Select any profiles to be grouted')
        outerProfiles.addSelectionFilter('Profiles')
        outerProfiles.setSelectionLimits(1,0)

        innerFace = inputs.addSelectionInput('inner_face', 'Inner Faces', 'Select any inner surfaces to be tiled')
        innerFace.addSelectionFilter('PlanarFaces')
        innerFace.setSelectionLimits(1,0)

        tileBody = inputs.addSelectionInput('tile_body', 'Tiled Bodies', 'Select the tiled body to pattern')
        tileBody.addSelectionFilter('SolidBodies')
        tileBody.addSelectionFilter('SurfaceBodies')
        tileBody.setSelectionLimits(1,0)

        blankBody = inputs.addSelectionInput('blank_body', 'Blank Bodies', 'Select a tiled body to pattern')
        blankBody.addSelectionFilter('SolidBodies')
        blankBody.setSelectionLimits(1,1)

        toleranceFloat = inputs.addFloatSliderCommandInput('tolerance_float', 'Tolerance', 'cm', 0.0, 1.0, False)

        txt = inputs.addStringValueInput('info', '', 'Select things bitch')
        txt.isReadOnly = True
 
    

# Event handler for the destroy event.
class MyDestroyHandler(adsk.core.CommandEventHandler):
    def __init__(self):
        super().__init__()
    def notify(self, args):
        # Terminate the script.
        adsk.terminate()
        
        
def run(context):
    try:
        global _app, _ui, _design
        _app = adsk.core.Application.get()
        _ui  = _app.userInterface
        _design = adsk.fusion.Design.cast(_app.activeProduct)
        if not _design:
            _ui.messageBox('No active Fusion 360 design', 'No Design')
            return

        # Create the command definition.
        cmdDef = _ui.commandDefinitions.itemById('select_slate_definitions')
        if cmdDef:
            cmdDef.deleteMe()
            
        cmdDef = _ui.commandDefinitions.addButtonDefinition('select_slate_definitions', 'Slate Definitions', 'Slate Definitions', '')
        
        # Connect to the command created event.
        onCommandCreated = MyCommandCreatedHandler()
        cmdDef.commandCreated.add(onCommandCreated)
        _handlers.append(onCommandCreated)  
        
        # Execute the command.
        cmdDef.execute()
        
        # Set this so the script doesn't automatically terminate after running the run function.
        adsk.autoTerminate(False)
    except:
        if _ui:
            _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))