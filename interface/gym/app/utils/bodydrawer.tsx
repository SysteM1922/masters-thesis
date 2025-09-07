import { NormalizedLandmark, DrawingUtils, PoseLandmarker } from '@mediapipe/tasks-vision';

const HEX_GREEN = "#30ff30"
const HEX_RED = "#ff0000"

const LINE_WIDTH = 5;

const LEFT_ARM_CONNECTIONS = [
  { start: 11, end: 13 },
  { start: 13, end: 15 },
];

const RIGHT_ARM_CONNECTIONS = [
  { start: 12, end: 14 },
  { start: 14, end: 16 },
];

const TORSO_CONNECTIONS = [
  { start: 11, end: 12 },
  { start: 11, end: 23 },
  { start: 12, end: 24 },
  { start: 23, end: 24 },
];

const LEFT_LEG_CONNECTIONS = [
  { start: 23, end: 25 },
  { start: 25, end: 27 },
];

const RIGHT_LEG_CONNECTIONS = [
  { start: 24, end: 26 },
  { start: 26, end: 28 },
];

export class BodyDrawer {

  drawingUtils : DrawingUtils;

  constructor(drawingUtils: DrawingUtils) {
    this.drawingUtils = drawingUtils;
    // Initialize any necessary properties
  }

  drawFromJson(json : { [key: string]: boolean | null }, landmarks: NormalizedLandmark[]) {
    // Draw the body parts based on the JSON input

    this.drawingUtils.drawLandmarks(landmarks, { radius: 5, lineWidth: LINE_WIDTH, color: '#FFFFFF' });
    this.drawingUtils.drawConnectors(landmarks, PoseLandmarker.POSE_CONNECTIONS, { lineWidth: LINE_WIDTH, color: '#FFFFFF' });

    for (const key in json) {
      switch (key) {
        case 'left_arm':
          if (json[key] === null) {
            break;
          }
          this.drawingUtils.drawConnectors(landmarks, LEFT_ARM_CONNECTIONS, { lineWidth: LINE_WIDTH, color: json[key] ? HEX_GREEN : HEX_RED });
          break;
        case 'right_arm':
          if (json[key] === null) {
            break;
          }
          this.drawingUtils.drawConnectors(landmarks, RIGHT_ARM_CONNECTIONS, { lineWidth: LINE_WIDTH, color: json[key] ? HEX_GREEN : HEX_RED });
          break;
        case 'torso':
          if (json[key] === null) {
            break;
          }
          this.drawingUtils.drawConnectors(landmarks, TORSO_CONNECTIONS, { lineWidth: LINE_WIDTH, color: json[key] ? HEX_GREEN : HEX_RED });
          break;
        case 'left_leg':
          if (json[key] === null) {
            break;
          }
          this.drawingUtils.drawConnectors(landmarks, LEFT_LEG_CONNECTIONS, { lineWidth: LINE_WIDTH, color: json[key] ? HEX_GREEN : HEX_RED });
          break;
        case 'right_leg':
          if (json[key] === null) {
            break;
          }
          this.drawingUtils.drawConnectors(landmarks, RIGHT_LEG_CONNECTIONS, { lineWidth: LINE_WIDTH, color: json[key] ? HEX_GREEN : HEX_RED });
          break;
        default:
          break;
      }
    }
  }
}
