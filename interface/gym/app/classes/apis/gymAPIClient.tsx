import axios, { AxiosInstance } from "axios";

const SERVICES_API_HOST: string = process.env.SERVICES_API_HOST ?? ""
const SERVICES_API_PORT: number = parseInt(process.env.SERVICES_API_PORT ?? "0");

const HOUSE_ID: string = process.env.HOUSE_ID ?? "";
const DIVISION_NAME: string = process.env.DIVISION_NAME ?? "";

class GymAPIClient {

  private exerciseId: string = "";

  private static instance: AxiosInstance = axios.create({
    baseURL: `https://${SERVICES_API_HOST}:${SERVICES_API_PORT}/v1/gym`,
    timeout: 5000,
    headers: { "Content-Type": "application/json" },
  });

  static async startExercise<T>() {
    const now = new Date().toISOString();
    const response = await this.instance.post<T>("/exercise", {
      house_id: HOUSE_ID,
      division: DIVISION_NAME,
      timestamp: now
    });
    console.log(response);
    // missing handle response
  }

  private static async addFrames<T>() {

  }
}

export default GymAPIClient;
