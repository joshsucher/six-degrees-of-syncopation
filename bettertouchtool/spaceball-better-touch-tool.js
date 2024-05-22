let mouseButtonPressedTime = null;
let isDragging = false;
let isButtonPressed = false;

function unpackAxis(highByte, lowByte) {
  // Combine the high and low bytes into a 16-bit value
  let combined = (highByte << 8) | lowByte;

  // Check if the value is negative (signed 16-bit)
  if (combined & 0x8000) {
    combined -= 65536;
  }

  return combined;
}

async function analyzeDeviceInput(targetDevice, reportID, reportDataHex) {
    let reportBuffer = buffer.Buffer.from(reportDataHex, 'hex');

  // Extract the button states from the report buffer
  let buttonStates = reportBuffer.readUInt8(1);

  // Check the state of buttons 1, 2, and 3
  let isButton1Pressed = (buttonStates & 0x0001) !== 0;
  let isButton2Pressed = (buttonStates & 0x0002) !== 0;
  let isButton3Pressed = (buttonStates & 0x0004) !== 0;
  let isButton4Pressed = (buttonStates & 0x0008) !== 0;
  let isButton5Pressed = (buttonStates & 0x0010) !== 0;
  let isButton6Pressed = (buttonStates & 0x0020) !== 0;
  let isButton7Pressed = (buttonStates & 0x0040) !== 0;
  let isButton8Pressed = (buttonStates & 0x0080) !== 0;

  // Extract the button states from the report buffer
  let isMouseButtonPressed = reportBuffer.readUInt8(2);

    // Extract the raw axis values from the report buffer using correct indices
    let rawLeftRight = unpackAxis(reportBuffer.readUInt8(3), reportBuffer.readUInt8(4));
    let rawUpDown = unpackAxis(reportBuffer.readUInt8(5), reportBuffer.readUInt8(6));
    let rawRotateLeftRight = unpackAxis(reportBuffer.readUInt8(7), reportBuffer.readUInt8(8));
    let rawInOut = unpackAxis(reportBuffer.readUInt8(9), reportBuffer.readUInt8(10)) - 512;

    // Log the raw axis values
    log(`Raw Axis Values:`);
    log(`Left/Right: ${rawLeftRight}`);
    log(`Up/Down: ${rawUpDown}`);
    log(`Force: ${rawInOut}`);
    log(`Rotate Left/Right: ${rawRotateLeftRight}`);

  // Handle media control buttons
  if (isButton1Pressed) {
    log("Volume Down");
    let volumeDownActionDefinition = {
      "BTTPredefinedActionType": 25,
      "BTTPredefinedActionName": "Volume Down"
    };
    await callBTT('trigger_action', { json: JSON.stringify(volumeDownActionDefinition) });
  }

  if (isButton2Pressed) {
    log("Volume Up");
    let volumeUpActionDefinition = {
      "BTTPredefinedActionType": 24,
      "BTTPredefinedActionName": "Volume Up"
    };
    await callBTT('trigger_action', { json: JSON.stringify(volumeUpActionDefinition) });
  }

  if (isButton3Pressed) {
    log("Play/Pause");
    let playPauseActionDefinition = {
      "BTTPredefinedActionType": 23,
      "BTTPredefinedActionName": "Play/Pause"
    };
    await callBTT('trigger_action', { json: JSON.stringify(playPauseActionDefinition) });
  }

    if (isButton4Pressed) {
    log("Mute");
    let muteActionDefinition = {
      "BTTPredefinedActionType": 22,
      "BTTPredefinedActionName": "Mute"
    };
    await callBTT('trigger_action', { json: JSON.stringify(muteActionDefinition) });
  }

  if (isButton5Pressed) {
    log("Brightness Down");
    let brightnessDownActionDefinition = {
      "BTTPredefinedActionType": 29,
      "BTTPredefinedActionName": "Brightness Down"
    };
    await callBTT('trigger_action', { json: JSON.stringify(brightnessDownActionDefinition) });
  }

  if (isButton6Pressed) {
    log("Brightness Up");
    let brightnessUpActionDefinition = {
      "BTTPredefinedActionType": 28,
      "BTTPredefinedActionName": "Brightness Up"
    };
    await callBTT('trigger_action', { json: JSON.stringify(brightnessUpActionDefinition) });
  }

  if (isButton7Pressed) {
    log("Previous");
    let previousActionDefinition = {
      "BTTPredefinedActionType": 26,
      "BTTPredefinedActionName": "Previous"
    };
    await callBTT('trigger_action', { json: JSON.stringify(previousActionDefinition) });
  }

  if (isButton8Pressed) {
    log("Next");
    let nextActionDefinition = {
      "BTTPredefinedActionType": 27,
      "BTTPredefinedActionName": "Next"
    };
    await callBTT('trigger_action', { json: JSON.stringify(nextActionDefinition) });
  }

  // Handle the mouse button press and release
  if (isMouseButtonPressed) {
    if (!isButtonPressed) {
      isButtonPressed = true;
      mouseButtonPressedTime = Date.now();
    } else {
      let pressDuration = Date.now() - mouseButtonPressedTime;
      if (pressDuration > 250 && !isDragging) {
        // Start mouse drag if the button is held down for more than 250ms
        log("Starting mouse drag");
        let startDragActionDefinition = {
          "BTTPredefinedActionType": 65,
          "BTTPredefinedActionName": "Start Mouse Drag"
        };
        await callBTT('trigger_action', { json: JSON.stringify(startDragActionDefinition) });
        isDragging = true;
      }
    }
  } else {
    if (isButtonPressed) {
      if (isDragging) {
        // Stop mouse drag when the button is released
        log("Stopping mouse drag");
        let stopDragActionDefinition = {
          "BTTPredefinedActionType": 66,
          "BTTPredefinedActionName": "Stop Mouse Drag"
        };
        await callBTT('trigger_action', { json: JSON.stringify(stopDragActionDefinition) });
      } else {
        // Perform a regular Left Click if the button is released before Start Mouse Drag
        log("Regular Left Click");
        let leftClickActionDefinition = {
          "BTTPredefinedActionType": 3,
          "BTTPredefinedActionName": "Left Click"
        };
        await callBTT('trigger_action', { json: JSON.stringify(leftClickActionDefinition) });
      }
    }
    isDragging = false;
    isButtonPressed = false;
    mouseButtonPressedTime = null;
  }

    // Calculate the mouse movement based on the axis values with a slower scaling factor
    let scalingFactor = 200; // Adjust this value to control the mouse movement speed
    let mouseMoveX = Math.round(rawLeftRight / scalingFactor);
    let mouseMoveY = Math.round(rawUpDown / scalingFactor);
    let scrollLR = 0;
    if (Math.abs(Math.round(rawRotateLeftRight / scalingFactor)) > 30) {
    scrollLR = Math.round(rawRotateLeftRight / scalingFactor);
    }

    // Log the joystick input and mouse movement
    log(`Mouse Movement: X=${mouseMoveX}, Y=${mouseMoveY}`);
    log(`Scroll Movement: ${scrollLR}`);

  // Handle scrolling based on rotation
  if (rawRotateLeftRight !== 0) {
    log("Scrolling");
    let scrollActionDefinition = {
      "BTTPredefinedActionType": 272,
      "BTTPredefinedActionName": "Send Scroll Event",
      "BTTScrollBy": `{0, ${scrollLR}}`
    };
    await callBTT('trigger_action', { json: JSON.stringify(scrollActionDefinition) });
  }

  // Move the mouse relative to its current position using the callBTT function
  if (!isButtonPressed || isDragging || !rawRotateLeftRight) {
    let actionDefinition = {
      "BTTPredefinedActionType": 153,
      "BTTPredefinedActionName": "Move Mouse To Position",
      "BTTMoveMouseToPosition": `{${mouseMoveX}, ${mouseMoveY}}`,
      "BTTMoveMouseRelative": "6" // Ensure this is correctly set to move relatively
    };
    await callBTT('trigger_action', { json: JSON.stringify(actionDefinition) });
  }

    let actionDefinition = {
      "BTTPredefinedActionType": 153,
      "BTTPredefinedActionName": "Move Mouse To Position",
      "BTTMoveMouseToPosition": `{${mouseMoveX}, ${mouseMoveY}}`,
      "BTTMoveMouseRelative": "6" // Ensure this is correctly set to move relatively
    };
    await callBTT('trigger_action', { json: JSON.stringify(actionDefinition) });

    returnToBTT(result);
}

// Advanced, optional. Use if you want to trigger commands that send data to
// the device, from a BTT predefined action.
// See https://docs.folivora.ai/1500\_generic\_devices.html
async function executeBTTCommand(targetDevice, commandName, commandInput) {
  log("execute command: " + commandName)

  switch (commandName) {
    case "exampleCommand": {
      // send any hex string to the device
      let deviceResponse = await bttSendDataToDevice({
        BTTActionSendDataTargetDevice: targetDevice,
        BTTActionSendDataData: 'FEEDC0DE',
        BTTActionSendDataReportType: 1,
        BTTActionSendDataResponseType: -1,
        BTTActionSendDataResponsePrefix: ''
      });
      break;
    }
  }

  return 'done executing ' + commandName
}

