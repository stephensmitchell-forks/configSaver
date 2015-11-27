#Author-Patrick Rainsberry
#Description-Save and retrieve display conditions of the model



import adsk.core, adsk.fusion, traceback

from xml.etree import ElementTree
from xml.etree.ElementTree import SubElement

from os.path import expanduser
import os

# global event handlers referenced for the duration of the command
handlers = []

menu_panel = 'InspectPanel'
commandResources = './resources'

modifyState = ''

commandId = 'configSave'
commandName = 'Config Saver'
commandDescription = 'Manage Suppression of Parts'

CS_CmdId = 'CS_CmdId'
CS_DC_CmdId = 'CS_DC_CmdId2'
USA_CmdId = 'CS_USA_CmdId2'
MC1_CmdId = 'MC1_CmdId'
MC2_CmdId = 'MC2_CmdId'

cmdIds = [CS_CmdId, CS_DC_CmdId, USA_CmdId, MC1_CmdId, MC2_CmdId]

def commandDefinitionById(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox('commandDefinition id is not specified')
        return None
    commandDefinitions_ = ui.commandDefinitions
    commandDefinition_ = commandDefinitions_.itemById(id)
    return commandDefinition_

def commandControlByIdForNav(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox('commandControl id is not specified')
        return None
    toolbars_ = ui.toolbars
    toolbarNav_ = toolbars_.itemById('NavToolbar')
    toolbarControls_ = toolbarNav_.controls
    toolbarControl_ = toolbarControls_.itemById(id)
    return toolbarControl_

def commandControlByIdForPanel(id):
    app = adsk.core.Application.get()
    ui = app.userInterface
    if not id:
        ui.messageBox('commandControl id is not specified')
        return None
    workspaces_ = ui.workspaces
    modelingWorkspace_ = workspaces_.itemById('FusionSolidEnvironment')
    toolbarPanels_ = modelingWorkspace_.toolbarPanels
    toolbarPanel_ = toolbarPanels_.item(0)
    toolbarControls_ = toolbarPanel_.controls
    toolbarControl_ = toolbarControls_.itemById(id)
    return toolbarControl_

def destroyObject(uiObj, tobeDeleteObj):
    if uiObj and tobeDeleteObj:
        if tobeDeleteObj.isValid:
            tobeDeleteObj.deleteMe()
        else:
            uiObj.messageBox('tobeDeleteObj is not a valid object')
                    
def updateXML(tree, fileName, state):
    
    root = tree.getroot()
    
    config = root.find("state[@name='%s']" % (state))
    
    if config is not None:
        root.remove(config)
    
    tree.write(fileName)
    
def updateParams(inputs):
    
    # Get Fusion Objects
    app = adsk.core.Application.get()
    ui  = app.userInterface
    design = app.activeProduct
    unitsMgr = design.unitsManager
    
    if inputs.count < 1:
        ui.messageBox('No User Parameters in the model')
        return          
    
    # Set all parameter values based on the input form                            
    for param in design.userParameters:
        inputExpresion = inputs.itemById(param.name).value
        
        # Use Fusion Units Manager to validate user expresion                        
        if unitsMgr.isValidExpression(inputExpresion, unitsMgr.defaultLengthUnits):
            
            # Set parameter value from input form                         
            param.expression = inputExpresion
        else:
            ui.messageBox("The following expresion was invalid: \n" +
                            param.name + '\n' +
                            inputExpresion)
                            
def writeXML(tree, newState, fileName, dims):
    
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    ui = app.userInterface
    
    # Get XML Root node
    root = tree.getroot()
    
    # Create a new State in the file
    state = SubElement( root, 'state', name=newState )
      
    # Get All components in design
    allComponents = design.allComponents
    for comp in allComponents:
        
        # Get All features inside the component
        allFeatures = comp.features
        for feature in allFeatures:
            
            # Record feature suppression state
            if feature is not None:               
                if feature.timelineObject.isSuppressed:                               
                    # ui.messageBox(str(feature.name) + " Is Suppressed")
                    SubElement( state, 'feature', component=comp.name, name=feature.name, suppress = 'suppressed')
                else:
                    # ui.messageBox(str(feature.name) + " Is Unsuppressed")
                    SubElement( state, 'feature', component=comp.name, name=feature.name, suppress = 'unSuppressed')
    
    if dims:
        # Get All parameters in design
        userParams = design.userParameters
        for param in userParams:
#            ui.messageBox(str(param.name) + "  " + str(param.value))
            # Record feature suppression state
            if param is not None:               
                SubElement( state, 'parameter', value=str(param.value), name=param.name)

    tree.write(fileName)

def openXML(tree, state):
    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)
    # ui = app.userInterface

    # Get XML Root node
    root = tree.getroot()

    # Get All components in design
    allComponents = design.allComponents
    for comp in allComponents:
        
        # Get All features inside the component
        allFeatures = comp.features
        for feature in allFeatures:
            
            # Find feature saved state and set value
            if feature is not None:
                test = root.find("state[@name='%s']/feature[@name='%s'][@component='%s']" % (state, feature.name, comp.name))
                if test is not None:
                    if test.get('suppress') == 'suppressed':
                        # ui.messageBox(str(feature.name) + " Is Suppressed")
                        feature.timelineObject.isSuppressed = True
                    else:
                        # ui.messageBox(str(feature.name) + " Is Unsuppressed")
                        feature.timelineObject.isSuppressed = False

    # Get All parameters in design
    allParams = design.allParameters
    for param in allParams:

        # Apply Saved dimension info
        if param is not None:                       
            test = root.find("state[@name='%s']/parameter[@name='%s']" % (state, param.name))
            if test is not None:
                param.value = float(test.get('value'))

def getFileName():
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface
        doc = app.activeDocument
        
        home = expanduser("~")
        home += '/configSaver/'
        
        if not os.path.exists(home):
            os.makedirs(home)
        
        fileName = home  + doc.name[0:doc.name.rfind(' v')] + '.xml'
        if not os.path.isfile(fileName):
            new_file = open( fileName, 'w' )                        
            new_file.write( '<?xml version="1.0"?>' )
            new_file.write( "<configSaves /> ")
            new_file.close()
        
        return fileName
    
    except:
        if ui:
            ui.messageBox('File Creation failed:\n{}'
            .format(traceback.format_exc()))
def unsuppressAll():

    app = adsk.core.Application.get()
    design = adsk.fusion.Design.cast(app.activeProduct)

    # Get All components in design
    allComponents = design.allComponents
    for comp in allComponents:
        
        # Get All features inside the component
        allFeatures = comp.features
        for feature in allFeatures:
            
            # Unsuppress feature
            if feature is not None:
                feature.timelineObject.isSuppressed = False

def run(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        class CS_InputChangedHandler(adsk.core.InputChangedEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:
                    command = args.firingEvent.sender
                    inputs = command.commandInputs
                    
                    if inputs.itemById('save').value:
                        inputs.itemById('currentState').isVisible = False
                        inputs.itemById('newName').isEnabled = True
                        inputs.itemById('newName').isVisible = True
                        inputs.itemById('dims').isEnabled = True
                    else:
                        inputs.itemById('currentState').isVisible = True
                        inputs.itemById('newName').isVisible = False
                        inputs.itemById('dims').isVisible = True
                        inputs.itemById('dims').isEnabled = False
                        inputs.itemById('newName').isEnabled = False
                        inputs.itemById('save').isVisible = True

                except:
                    if ui:
                        ui.messageBox('Input changed event failed: {}').format(traceback.format_exc())
        
        # Handle the input changed event.        
        class CS_executePreviewHandler(adsk.core.CommandEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                app = adsk.core.Application.get()
                ui  = app.userInterface
                try:
                    command = args.firingEvent.sender
                    inputs = command.commandInputs
                    state = inputs.itemById('currentState').selectedItem.name
                    
                    if state != 'Current' and not inputs.itemById('save').value:
                        fileName = getFileName()                    
                        tree = ElementTree.parse(fileName)
                        openXML(tree, state)
                    
                except:
                    if ui:
                        ui.messageBox('command executed failed:\n{}'
                        .format(traceback.format_exc()))       
                        
        class CS_CreatedHandler(adsk.core.CommandCreatedEventHandler):
            def __init__(self):
                super().__init__() 
            def notify(self, args):
                try:
                    cmd = args.command
                    onExecute = CS_ExecuteHandler()
                    cmd.execute.add(onExecute)
                    onChange = CS_InputChangedHandler()
                    cmd.inputChanged.add(onChange)
                    onUpdate = CS_executePreviewHandler()
                    cmd.executePreview.add(onUpdate)
                    
                    # keep the handler referenced beyond this function
                    handlers.append(onExecute)  
                    handlers.append(onChange)
                    handlers.append(onUpdate)
                    
                    fileName = getFileName()                    
                    tree = ElementTree.parse(fileName)
                    root = tree.getroot()
                    
                    inputs = cmd.commandInputs
                    
                    dropDown = inputs.addDropDownCommandInput('currentState', 'Select Saved Config:', adsk.core.DropDownStyles.TextListDropDownStyle)
                    dropDownItems = dropDown.listItems
                    
                    dropDownItems.add('Current', True)
                    
                    for state in root.findall('state'):
                        dropDownItems.add(state.get('name'), False,)
                        
                    inputs.addBoolValueInput('save', 'Save current suppression condition?', True)
                    inputs.addStringValueInput('newName', 'New Config Name:', 'New Config')        
                    inputs.addBoolValueInput('dims', 'Save DImension Information also?', True)
                    inputs.itemById('newName').isEnabled = False
                    inputs.itemById('newName').isVisible = False
                        
                except:
                    if ui:
                        ui.messageBox('Panel command created failed:\n{}'
                        .format(traceback.format_exc()))     

        class CS_ExecuteHandler(adsk.core.CommandEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:  
                    command = args.firingEvent.sender
                    inputs = command.commandInputs
                    state = inputs.itemById('currentState').selectedItem.name
                    fileName = getFileName()                    
                    tree = ElementTree.parse(fileName)
                    
                    if inputs.itemById('save').value:
                        writeXML(tree, inputs.itemById('newName').value, fileName, inputs.itemById('dims').value)
                    else:
                        openXML(tree, state)  
                    
                    
                except:
                    if ui:
                        ui.messageBox('command executed failed:\n{}'
                        .format(traceback.format_exc()))   
        class USA_CreatedHandler(adsk.core.CommandCreatedEventHandler):
            def __init__(self):
                super().__init__() 
            def notify(self, args):
                try:
                    cmd = args.command
                    onExecute = USA_ExecuteHandler()
                    cmd.execute.add(onExecute)
                    # keep the handler referenced beyond this function
                    handlers.append(onExecute)               
                except:
                    if ui:
                        ui.messageBox('Panel command created failed:\n{}'
                        .format(traceback.format_exc()))     

        class USA_ExecuteHandler(adsk.core.CommandEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:
                    unsuppressAll()
                except:
                    if ui:
                        ui.messageBox('command executed failed:\n{}'
                        .format(traceback.format_exc()))    
                                  

        class MC1_ExecuteHandler(adsk.core.CommandEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:
                    global modifyState
                    MC1_Command = args.firingEvent.sender
                    MC1_inputs = MC1_Command.commandInputs
                    modifyState = MC1_inputs.itemById('currentState').selectedItem.name

                    fileName = getFileName()                    
                    tree = ElementTree.parse(fileName)

                    openXML(tree, modifyState)  
                    
                    # Execute the next command.
                    cmdDef = ui.commandDefinitions.itemById(MC2_CmdId)
                    cmdDef.execute()
                except:
                    if ui:
                        ui.messageBox('command executed failed:\n{}'
                        .format(traceback.format_exc()))  
        
        class MC1_executePreviewHandler(adsk.core.CommandEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:
                    command = args.firingEvent.sender
                    inputs = command.commandInputs
                    state = inputs.itemById('currentState').selectedItem.name
                    
                    if state != 'Current':
                        fileName = getFileName()                    
                        tree = ElementTree.parse(fileName)
                        openXML(tree, state)
                        
                except:
                    if ui:
                        ui.messageBox('command executed failed:\n{}'
                        .format(traceback.format_exc())) 
        
        class MC1_CreatedHandler(adsk.core.CommandCreatedEventHandler):
            def __init__(self):
                super().__init__() 
            def notify(self, args):
                try:
                    global modifyState
                    
                    cmd = args.command
                    on_MC1_Execute = MC1_ExecuteHandler()
                    cmd.execute.add(on_MC1_Execute)
                    on_MC1_Update = MC1_executePreviewHandler()
                    cmd.executePreview.add(on_MC1_Update)
                    
                    # keep the handler referenced beyond this function
                    handlers.append(on_MC1_Execute)  
                    handlers.append(on_MC1_Update)
                    
                    fileName = getFileName()                    
                    tree = ElementTree.parse(fileName)
                    root = tree.getroot()
                    
                    inputs = cmd.commandInputs
                    
                    dropDown = inputs.addDropDownCommandInput('currentState', 'Select Saved Config:', adsk.core.DropDownStyles.TextListDropDownStyle)
                    dropDownItems = dropDown.listItems
                    
                    dropDownItems.add('Current', True)
                    
                    for state in root.findall('state'):
                        dropDownItems.add(state.get('name'), False,)

                except:
                    if ui:
                        ui.messageBox('Panel command created failed:\n{}'
                        .format(traceback.format_exc()))     

        class MC2_ExecuteHandler(adsk.core.CommandEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:

                    cmd = args.firingEvent.sender
                    inputs = cmd.commandInputs
                    fileName = getFileName()                    
                    tree = ElementTree.parse(fileName)
                    
                    updateParams(inputs)

                    state = modifyState
                    
                    updateXML(tree, fileName, state)
                    writeXML(tree, state, fileName, True)
                
                except:
                    if ui:
                        ui.messageBox('command executed failed:\n{}'
                        .format(traceback.format_exc()))  
        
        class MC2_executePreviewHandler(adsk.core.CommandEventHandler):
            def __init__(self):
                super().__init__()
            def notify(self, args):
                try:
                    cmd = args.firingEvent.sender
                    inputs = cmd.commandInputs
                    updateParams(inputs)
                    
                except:
                    if ui:
                        ui.messageBox('command executed failed:\n{}'
                        .format(traceback.format_exc())) 
        
        class MC2_CreatedHandler(adsk.core.CommandCreatedEventHandler):
            def __init__(self):
                super().__init__() 
            def notify(self, args):
                try:
                    app = adsk.core.Application.get()

                    cmd = args.command
                    on_MC2_Execute = MC2_ExecuteHandler()
                    cmd.execute.add(on_MC2_Execute)
                    on_MC2_Preview = MC2_executePreviewHandler()
                    cmd.executePreview.add(on_MC2_Preview)
                    
                    # keep the handler referenced beyond this function
                    handlers.append(on_MC2_Execute)  
                    handlers.append(on_MC2_Preview)
                    inputs = cmd.commandInputs
                    
                    state = modifyState
                    
                    inputs.addTextBoxCommandInput('text', 'Configuration being Modified:', state, 1, True)                    
                    
                    fileName = getFileName()                    
                    tree = ElementTree.parse(fileName)
                    root = tree.getroot()
                    
                    config = root.find("state[@name='%s']" % (state))
                    
                    if config is not None:
                        
                        design = app.activeProduct
                        for param in design.userParameters: 

                            inp = inputs.addStringValueInput(param.name, param.name, param.expression)
                            inp.isVisible = True
 
#                        Possible future add ability to edit Suppression state graphically                       
#                        for feature in config.iter('feature'):                  
#                            if str(feature.get('suppress')) == 'suppressed':
#                                text = str(feature.get('component'))
#                                text += " / "
#                                f_name = str(feature.get('name'))
##                                ui.messageBox(text + "  " + f_name)
#                                text += f_name
#                                inputs.addBoolValueInput('f_name', text, True, '', True)
                except:
                    if ui:
                        ui.messageBox('Panel command created failed:\n{}'
                        .format(traceback.format_exc()))     
                       
        # Get the UserInterface object and the CommandDefinitions collection.
        cmdDefs = ui.commandDefinitions

        # add a command button on Quick Access Toolbar
        toolbars_ = ui.toolbars
        navBar = toolbars_.itemById('NavToolbar')
        toolbarControlsNAV = navBar.controls
        
        dropControl = toolbarControlsNAV.addDropDown(CS_DC_CmdId, commandResources + '/DC', CS_DC_CmdId) 
        
        CS_Control = toolbarControlsNAV.itemById(CS_CmdId)
        if not CS_Control:
            CS_cmdDef = cmdDefs.itemById(CS_CmdId)
            if not CS_cmdDef:
                # commandDefinitionNAV = cmdDefs.addSplitButton(showAllBodiesCmdId, otherCmdDefs, True)
                CS_cmdDef = cmdDefs.addButtonDefinition(CS_CmdId, 'Config Saver', 'Save Suppresion State of Features',commandResources)
            onCommandCreated = CS_CreatedHandler()
            CS_cmdDef.commandCreated.add(onCommandCreated)
            # keep the handler referenced beyond this function
            handlers.append(onCommandCreated)
            CS_Control = dropControl.controls.addCommand(CS_cmdDef)
            CS_Control.isVisible = True
        
        
        USA_Control = toolbarControlsNAV.itemById(USA_CmdId)
        if not USA_Control:
            USA_cmdDef = cmdDefs.itemById(USA_CmdId)
            if not USA_cmdDef:
                # commandDefinitionNAV = cmdDefs.addSplitButton(showAllBodiesCmdId, otherCmdDefs, True)
                USA_cmdDef = cmdDefs.addButtonDefinition(USA_CmdId, 'Unsuppress All', 'Unsuppress all features in the timeline',commandResources)
            onCommandCreated = USA_CreatedHandler()
            USA_cmdDef.commandCreated.add(onCommandCreated)
            # keep the handler referenced beyond this function
            handlers.append(onCommandCreated)
            USA_Control = dropControl.controls.addCommand(USA_cmdDef)
            USA_Control.isVisible = True
            
        MC1_Control = toolbarControlsNAV.itemById(MC1_CmdId)
        if not MC1_Control:
            MC1_cmdDef = cmdDefs.itemById(MC1_CmdId)
            if not MC1_cmdDef:
                # commandDefinitionNAV = cmdDefs.addSplitButton(showAllBodiesCmdId, otherCmdDefs, True)
                MC1_cmdDef = cmdDefs.addButtonDefinition(MC1_CmdId, 'Modify Configuration', 'Allows you to change the definition of a config',commandResources)
            onCommandCreated = MC1_CreatedHandler()
            MC1_cmdDef.commandCreated.add(onCommandCreated)
            # keep the handler referenced beyond this function
            handlers.append(onCommandCreated)
            MC1_Control = dropControl.controls.addCommand(MC1_cmdDef)
            MC1_Control.isVisible = True   
            
        MC2_Control = toolbarControlsNAV.itemById(MC2_CmdId)
        if not MC2_Control:
            MC2_cmdDef = cmdDefs.itemById(MC2_CmdId)
            if not MC2_cmdDef:
                # commandDefinitionNAV = cmdDefs.addSplitButton(showAllBodiesCmdId, otherCmdDefs, True)
                MC2_cmdDef = cmdDefs.addButtonDefinition(MC2_CmdId, 'Modify Configuration', 'Allows you to change the definition of a config',commandResources)
            onCommandCreated = MC2_CreatedHandler()
            MC2_cmdDef.commandCreated.add(onCommandCreated)
            # keep the handler referenced beyond this function
            handlers.append(onCommandCreated)
            
    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))

def stop(context):
    ui = None
    try:
        app = adsk.core.Application.get()
        ui  = app.userInterface

        objArrayNav = []
        
        for cmdId in cmdIds:
            commandControlNav_ = commandControlByIdForNav(cmdId)
            if commandControlNav_:
                objArrayNav.append(commandControlNav_)
    
            commandDefinitionNav_ = commandDefinitionById(cmdId)
            if commandDefinitionNav_:
                objArrayNav.append(commandDefinitionNav_)
            
        for obj in objArrayNav:
            destroyObject(ui, obj)

    except:
        if ui:
            ui.messageBox('Failed:\n{}'.format(traceback.format_exc()))
