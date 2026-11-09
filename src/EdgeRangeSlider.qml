import QtQuick
import QtQuick.Controls

RangeSlider {
    id: control
    property real minimumGap: 0
    property bool panEnabled: false
    property color trackColor
    property color rangeColor
    property color leftColor
    property color rightColor
    property color leftBorder
    property color rightBorder
    readonly property int handleSize: 24
    signal edited()

    implicitHeight: 40
    leftPadding: handleSize
    rightPadding: handleSize

    function moveEndpoint(which, value) {
        if (stepSize > 0)
            value = from + Math.round((value - from) / stepSize) * stepSize
        if (which === 1)
            first.value = Math.max(from, Math.min(second.value - minimumGap, value))
        else
            second.value = Math.min(to, Math.max(first.value + minimumGap, value))
        edited()
    }

    first.onMoved: moveEndpoint(1, first.value)
    second.onMoved: moveEndpoint(2, second.value)

    background: Rectangle {
        x: control.leftPadding
        y: (control.height - height) / 2
        width: control.availableWidth
        height: 5
        radius: 3
        color: control.trackColor
        Rectangle {
            x: Math.min(control.first.visualPosition, control.second.visualPosition) * parent.width
            width: Math.abs(control.second.visualPosition - control.first.visualPosition) * parent.width
            height: parent.height
            radius: 3
            color: control.rangeColor
        }
    }

    first.handle: Rectangle {
        objectName: "leftRangeHandle"
        x: control.leftPadding + control.first.visualPosition * control.availableWidth
           - (control.mirrored ? 0 : width)
        y: (control.height - height) / 2
        width: control.handleSize
        height: width
        radius: width / 2
        color: control.leftColor
        border.color: control.leftBorder
        border.width: pointer.dragTarget === 1 ? 4 : 2
    }

    second.handle: Rectangle {
        objectName: "rightRangeHandle"
        x: control.leftPadding + control.second.visualPosition * control.availableWidth
           - (control.mirrored ? width : 0)
        y: (control.height - height) / 2
        width: control.handleSize
        height: width
        radius: width / 2
        color: control.rightColor
        border.color: control.rightBorder
        border.width: pointer.dragTarget === 2 ? 4 : 2
    }

    MouseArea {
        id: pointer
        anchors.fill: parent
        z: 2
        preventStealing: true
        cursorShape: Qt.SizeHorCursor
        property int dragTarget: 0
        property real pressX: 0
        property real low: 0
        property real high: 0

        function hits(handle, x, y) {
            return x >= handle.x && x <= handle.x + handle.width
                && y >= handle.y && y <= handle.y + handle.height
        }

        onPressed: function(mouse) {
            pressX = mouse.x
            low = control.first.value
            high = control.second.value
            var start = control.leftPadding + control.first.visualPosition * control.availableWidth
            var end = control.leftPadding + control.second.visualPosition * control.availableWidth
            if (hits(control.first.handle, mouse.x, mouse.y)) {
                dragTarget = 1
            } else if (hits(control.second.handle, mouse.x, mouse.y)) {
                dragTarget = 2
            } else if (control.panEnabled && mouse.x > Math.min(start, end) && mouse.x < Math.max(start, end)) {
                dragTarget = 3
            } else {
                dragTarget = Math.abs(mouse.x - start) <= Math.abs(mouse.x - end) ? 1 : 2
                var ratio = (mouse.x - control.leftPadding) / Math.max(1, control.availableWidth)
                control.moveEndpoint(dragTarget, control.from + (control.mirrored ? 1 - ratio : ratio) * (control.to - control.from))
                low = control.first.value
                high = control.second.value
            }
            control.edited()
        }

        onPositionChanged: function(mouse) {
            if (!pressed || !dragTarget)
                return
            var delta = (mouse.x - pressX) / Math.max(1, control.availableWidth) * (control.to - control.from)
            if (control.mirrored)
                delta = -delta
            if (dragTarget === 3) {
                var start = Math.max(control.from, Math.min(control.to - (high - low), low + delta))
                control.setValues(start, start + high - low)
                control.edited()
            } else {
                control.moveEndpoint(dragTarget, (dragTarget === 1 ? low : high) + delta)
            }
        }
        onReleased: dragTarget = 0
        onCanceled: dragTarget = 0
    }
}
