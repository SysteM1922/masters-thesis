"use client"

import { redirect } from 'next/navigation';
import Image from "next/image";
import { useEffect } from "react";

export default function Root() {

  useEffect(() => {

    const checkAndRequestPermissions = async () => {
      try {
        // Check if permissions are already granted
        const cameraPermission = await navigator.permissions.query({ name: 'camera' as PermissionName });
        const microphonePermission = await navigator.permissions.query({ name: 'microphone' as PermissionName });

        if (cameraPermission.state === 'granted' && microphonePermission.state === 'granted') {
          console.log("Permissions already granted");
          return true;
        }
      } catch (error) {
        console.log("Permission API not supported", error);
      }

      // Request permissions if not already granted
      const askPermissions = async () => {
        return new Promise<void>((resolve, reject) => {
          navigator.mediaDevices.getUserMedia({ audio: true, video: true })
            .then(() => {
              resolve()
            })
            .catch((error) => {
              reject(error)
            })
        })
      }

      askPermissions().then(() => {
        console.log("Microphone and camera permission granted");
        return true;
      }).catch((error) => {
        console.error("Microphone permission denied", error);
        alert("Microphone permission is required for voice commands. Please allow microphone access and refresh the page.");
        return false;
      });
    };

    checkAndRequestPermissions().then((granted) => {
      if (granted) {
        redirect("/workout");
      }
    });

  }, []);

  return (
    <main>
      <h1>Welcome to the Gym App</h1>
      <Image src="/gym.jpg" alt="Gym" width={500} height={300} />
    </main>
  );
}
