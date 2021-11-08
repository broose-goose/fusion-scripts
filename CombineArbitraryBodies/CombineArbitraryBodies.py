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

        bodySelections = adsk.core.SelectionCommandInput.cast(eventArgs.command.commandInputs.itemById('combine_bodies'))
        
        messageOut = "Forgot to set:"

        if bodySelections.selectionCount < 2:
            messageOut += "\nAt least two bodies"
        if messageOut != "Forgot to set:":
            messageOut += "\nD:"
            _ui.messageBox(messageOut)
        else:
            _ui.messageBox("running")
            self.run(
                self.GetSelections(bodySelections, 2),
            )
    


    def run(
        self,
        bodies: List[adsk.fusion.BRepBody]
    ):
        try:

            _ui.messageBox("Okay, going for it D:")
           
            rootComp = _design.rootComponent
            occs = rootComp.occurrences
            subComp1 = occs.item(0).component

            baseFeats = subComp1.features.baseFeatures
            baseFeat = baseFeats.add()

            tempBrepMgr = adsk.fusion.TemporaryBRepManager.get()
            baseBody: adsk.fusion.BRepBody = None
            collection: adsk.core.ObjectCollection = adsk.core.ObjectCollection.create()
            transform = adsk.core.Matrix3D.create()
            
            baseFeat.startEdit()

            for body in bodies:
                tempBody = tempBrepMgr.copy(body)
                transform.translation = adsk.core.Vector3D.create(5.0, 5.0, 0.0)
                tempBrepMgr.transform(tempBody, transform)
                if baseBody == None:
                    baseBody = subComp1.bRepBodies.add(tempBody, baseFeat)
                else:
                    copyBody = subComp1.bRepBodies.add(tempBody, baseFeat)
                    collection.add(copyBody)

            combineFeatures = subComp1.features.combineFeatures
            combineFeatureInput = combineFeatures.createInput(baseBody, collection)
            combineFeatureInput.operation = 0
            combineFeatureInput.isKeepToolBodies = False
            combineFeatureInput.isNewComponent = False
            combineFeatures.add(combineFeatureInput)

            baseFeat.finishEdit()

            _ui.messageBox("Hope i did something D:")

        except:
            if _ui:
                _ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))



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

        tileBody = inputs.addSelectionInput('combine_bodies', 'Any solid / surface body', 'Select the tiled body to pattern')
        tileBody.addSelectionFilter('SolidBodies')
        tileBody.addSelectionFilter('SurfaceBodies')
        tileBody.setSelectionLimits(2,0)

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