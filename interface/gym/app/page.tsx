"use client"

import { redirect } from 'next/navigation';
import Image from "next/image";
import { useEffect } from "react";

export default function Root() {

  useEffect(() => {
    redirect("/workout");
  }, []);

  return (
    <main>
      <h1>Welcome to the Gym App</h1>
      <Image src="/gym.jpg" alt="Gym" width={500} height={300} />
    </main>
  );
}
